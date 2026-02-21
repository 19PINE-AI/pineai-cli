"""pine sessions list|get|create|delete — session management."""

import json

import click
from rich.console import Console
from rich.table import Table

from pine_cli.config import get_assistant_client, run_async, handle_api_errors

console = Console()


@click.group()
def sessions():
    """Session management commands."""


@sessions.command("list")
@click.option("--state", default=None, help="Filter by state (e.g. init, active, task_finished)")
@click.option("--limit", default=10, type=int, help="Max results (default: 10)")
@click.option("--json-output", "--json", is_flag=True, help="Output as JSON")
@handle_api_errors
def sessions_list(state, limit, json_output):
    """List sessions."""
    async def _list():
        client = get_assistant_client()
        result = await client.sessions.list(state=state, limit=limit)
        if json_output:
            click.echo(json.dumps(result, indent=2))
            return
        table = Table(title=f"Sessions ({result['total']} total)")
        table.add_column("ID", style="bold", no_wrap=True)
        table.add_column("State")
        table.add_column("Title", max_width=50)
        table.add_column("Updated")
        for s in result["sessions"]:
            state_color = {
                "chat": "green", "task_processing": "blue", "task_finished": "cyan",
                "init": "yellow", "active": "green",
            }.get(s.get("state", ""), "white")
            table.add_row(s["id"], f"[{state_color}]{s.get('state', '')}[/{state_color}]",
                          s.get("title", ""), s.get("updated_at", ""))
        console.print(table)

    run_async(_list())


@sessions.command("get")
@click.argument("session_id")
@click.option("--json-output", "--json", is_flag=True, help="Output as JSON")
@handle_api_errors
def sessions_get(session_id, json_output):
    """Get session details."""
    async def _get():
        client = get_assistant_client()
        result = await client.sessions.get(session_id)
        if json_output:
            click.echo(json.dumps(result, indent=2))
            return
        console.print(f"[bold]Session {result['id']}[/bold]")
        console.print(f"  State: {result.get('state', '?')}")
        console.print(f"  Title: {result.get('title', '—')}")
        console.print(f"  Created: {result.get('created_at', '?')}")
        console.print(f"  Updated: {result.get('updated_at', '?')}")
        console.print(f"  URL: https://www.19pine.ai/app/chat/{result['id']}")

    run_async(_get())


@sessions.command("create")
@click.option("--json-output", "--json", is_flag=True, help="Output as JSON")
@handle_api_errors
def sessions_create(json_output):
    """Create a new session."""
    async def _create():
        client = get_assistant_client()
        with console.status("Creating session…"):
            session = await client.sessions.create()
        if json_output:
            click.echo(json.dumps(session, indent=2))
        else:
            console.print(f"[green]✓ Session created:[/green]  [bold]{session['id']}[/bold]")
            console.print(f"[dim]URL: https://www.19pine.ai/app/chat/{session['id']}[/dim]")

    run_async(_create())


@sessions.command("delete")
@click.argument("session_id")
@click.option("-f", "--force", is_flag=True, help="Force delete")
@handle_api_errors
def sessions_delete(session_id, force):
    """Delete a session."""
    async def _delete():
        client = get_assistant_client()
        with console.status("Deleting session…"):
            await client.sessions.delete(session_id, force_delete=force)
        console.print(f"[green]✓ Session {session_id} deleted.[/green]")

    run_async(_delete())
