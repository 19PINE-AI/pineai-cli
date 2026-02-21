"""Shared configuration and client helpers."""

import asyncio
import json
from pathlib import Path
from typing import Any

from rich.console import Console

CONFIG_DIR = Path.home() / ".pine"
CONFIG_FILE = CONFIG_DIR / "config.json"

console = Console()


def load_config() -> dict[str, Any]:
    try:
        return json.loads(CONFIG_FILE.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_config(cfg: dict[str, Any]) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2) + "\n")


def require_auth() -> dict[str, Any]:
    """Return config or exit if not logged in."""
    cfg = load_config()
    if not cfg.get("access_token") or not cfg.get("user_id"):
        console.print("[red]Not logged in. Run [bold]pine auth login[/bold] first.[/red]")
        raise SystemExit(1)
    return cfg


def get_voice_client():
    """Build an authenticated PineVoice (sync) client."""
    from pine_voice import PineVoice

    cfg = require_auth()
    return PineVoice(access_token=cfg["access_token"], user_id=cfg["user_id"])


def get_assistant_client():
    """Build an authenticated AsyncPineAI client."""
    from pine_assistant.client import AsyncPineAI

    cfg = require_auth()
    return AsyncPineAI(
        access_token=cfg["access_token"],
        user_id=cfg["user_id"],
        base_url=cfg.get("base_url", "https://www.19pine.ai"),
    )


def run_async(coro):
    """Run an async coroutine from sync context."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def handle_api_errors(fn):
    """Decorator that catches SDK exceptions and prints user-friendly messages."""
    import functools

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except SystemExit:
            raise
        except KeyboardInterrupt:
            console.print("\n[dim]Interrupted.[/dim]")
            raise SystemExit(130)
        except Exception as exc:
            _print_api_error(exc)
            raise SystemExit(1)

    return wrapper


def _print_api_error(exc: Exception) -> None:
    code = getattr(exc, "code", None)
    message = str(exc)
    if code:
        console.print(f"[red]Error ({code}):[/red] {message}")
    else:
        console.print(f"[red]Error:[/red] {message}")
