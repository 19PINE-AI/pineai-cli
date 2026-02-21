"""pine auth login|request|verify|status|logout — shared authentication for Voice & Assistant."""

import json
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
    """Log in with email verification (interactive)."""
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


@auth.command("request")
@click.option("--email", required=True, help="Pine AI account email")
@click.option("--base-url", default=None, help="Pine AI base URL override")
@handle_api_errors
def request_code(email: str, base_url: Optional[str]):
    """Request a verification code (non-interactive)."""
    from pine_assistant.client import AsyncPineAI

    async def _request():
        cfg = load_config()
        url = base_url or cfg.get("base_url", "https://www.19pine.ai")
        client = AsyncPineAI(base_url=url)
        result = await client.auth.request_code(email)
        click.echo(json.dumps({"request_token": result["request_token"], "email": email}))

    run_async(_request())


@auth.command("verify")
@click.option("--email", required=True, help="Pine AI account email")
@click.option("--request-token", required=True, help="Token from 'pine auth request'")
@click.option("--code", required=True, help="Verification code from email")
@click.option("--base-url", default=None, help="Pine AI base URL override")
@handle_api_errors
def verify_code(email: str, request_token: str, code: str, base_url: Optional[str]):
    """Verify code and save credentials (non-interactive)."""
    from pine_assistant.client import AsyncPineAI

    async def _verify():
        cfg = load_config()
        url = base_url or cfg.get("base_url", "https://www.19pine.ai")
        client = AsyncPineAI(base_url=url)
        verify = await client.auth.verify_code(email, code, request_token)

        save_config({
            **cfg,
            "access_token": verify["access_token"],
            "user_id": verify["id"],
            "email": verify["email"],
            "base_url": url,
        })
        click.echo(json.dumps({"status": "authenticated", "email": verify["email"], "user_id": verify["id"]}))

    run_async(_verify())


@auth.command("status")
@click.option("--json-output", "--json", is_flag=True, help="Output as JSON")
def status(json_output: bool):
    """Show current authentication status."""
    cfg = load_config()
    if json_output:
        authenticated = bool(cfg.get("access_token"))
        click.echo(json.dumps({
            "authenticated": authenticated,
            "email": cfg.get("email"),
            "user_id": cfg.get("user_id"),
            "base_url": cfg.get("base_url", "https://www.19pine.ai"),
        }))
    elif cfg.get("access_token"):
        console.print(f"[green]● Logged in[/green]  {cfg.get('email', '?')}  (user {cfg.get('user_id', '?')})")
        console.print(f"[dim]Base URL: {cfg.get('base_url', 'https://www.19pine.ai')}[/dim]")
    else:
        console.print("[yellow]○ Not logged in.[/yellow]  Run [bold]pine auth login[/bold].")


@auth.command("logout")
def logout():
    """Clear saved credentials."""
    save_config({})
    console.print("[green]✓ Logged out. Credentials removed.[/green]")
