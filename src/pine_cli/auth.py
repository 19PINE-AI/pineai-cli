"""pine auth login|status|logout — shared authentication for Voice & Assistant."""

from typing import Optional

import click
from rich.console import Console

from pine_cli.config import load_config, save_config, run_async, handle_api_errors

console = Console()


@click.group()
def auth():
    """Authentication commands."""


@auth.command("login")
@click.option("--base-url", default=None, help="Pine AI base URL override")
@handle_api_errors
def login(base_url: Optional[str]):
    """Log in with email verification."""
    from pine_assistant.client import AsyncPineAI

    async def _login():
        cfg = load_config()
        url = base_url or cfg.get("base_url", "https://www.19pine.ai")
        client = AsyncPineAI(base_url=url)

        email = click.prompt("Email")
        with console.status("Sending verification code…"):
            result = await client.auth.request_code(email)
        console.print("[green]✓ Code sent — check your email.[/green]")

        code = click.prompt("Verification code")
        with console.status("Verifying…"):
            verify = await client.auth.verify_code(email, code, result["request_token"])

        save_config({
            **cfg,
            "access_token": verify["access_token"],
            "user_id": verify["id"],
            "email": verify["email"],
            "base_url": url,
        })
        console.print(f"[green]✓ Logged in as {verify['email']}[/green]  (user {verify['id']})")
        console.print("[dim]Credentials saved to ~/.pine/config.json[/dim]")

    run_async(_login())


@auth.command("status")
def status():
    """Show current authentication status."""
    cfg = load_config()
    if cfg.get("access_token"):
        console.print(f"[green]● Logged in[/green]  {cfg.get('email', '?')}  (user {cfg.get('user_id', '?')})")
        console.print(f"[dim]Base URL: {cfg.get('base_url', 'https://www.19pine.ai')}[/dim]")
    else:
        console.print("[yellow]○ Not logged in.[/yellow]  Run [bold]pine auth login[/bold].")


@auth.command("logout")
def logout():
    """Clear saved credentials."""
    save_config({})
    console.print("[green]✓ Logged out. Credentials removed.[/green]")
