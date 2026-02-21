"""pine sessions list|get|create|delete — session management."""

import asyncio
import json

import click
from rich.console import Console
from rich.table import Table

from pine_cli.config import get_assistant_client, run_async, handle_api_errors, format_timestamp

console = Console()


@click.group()
def sessions():
    """Session management commands."""


@sessions.command("list")
@click.option("--state", default=None, help="Filter by state (e.g. init, active, task_finished)")
@click.option("--limit", default=10, type=int, help="Max results (default: 10)")
@click.option("--offset", default=0, type=int, help="Skip first N results (for pagination)")
@click.option("--json-output", "--json", is_flag=True, help="Output as JSON")
@handle_api_errors
def sessions_list(state, limit, offset, json_output):
    """List sessions."""
    async def _list():
        client = get_assistant_client()
        result = await client.sessions.list(state=state, limit=limit, offset=offset)
        if json_output:
            click.echo(json.dumps(result, indent=2))
            return
        total = result['total']
        end = min(offset + limit, total)
        title = f"Sessions {offset + 1}–{end} of {total}" if offset else f"Sessions ({total} total)"
        table = Table(title=title)
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
                          s.get("title", ""), format_timestamp(s.get("updated_at", "")))
        console.print(table)
        if end < total:
            next_offset = offset + limit
            console.print(f"[dim]Showing {offset + 1}–{end} of {total}. Next page: pine sessions list --offset {next_offset}[/dim]")

    run_async(_list())


@sessions.command("get")
@click.argument("session_id")
@click.option("--limit", default=30, type=int, help="Max conversation messages (default: 30)")
@click.option("--json-output", "--json", is_flag=True, help="Output as JSON")
@handle_api_errors
def sessions_get(session_id, limit, json_output):
    """Get session details and conversation history."""
    async def _get():
        client = get_assistant_client()

        metadata = await client.sessions.get(session_id)

        await client.connect()
        try:
            await client.join_session(session_id)
            history = await client.get_history(session_id, max_messages=limit, order="asc")
            client.leave_session(session_id)
            await asyncio.sleep(1)
        finally:
            await client.disconnect()

        if json_output:
            metadata["messages"] = history.get("messages", [])
            click.echo(json.dumps(metadata, indent=2))
            return

        console.print(f"[bold]Session {metadata['id']}[/bold]")
        console.print(f"  State: {metadata.get('state', '?')}")
        console.print(f"  Title: {metadata.get('title', '—')}")
        console.print(f"  Created: {format_timestamp(metadata.get('created_at', ''))}")
        console.print(f"  Updated: {format_timestamp(metadata.get('updated_at', ''))}")
        console.print(f"  URL: https://www.19pine.ai/app/chat/{metadata['id']}")

        messages = history.get("messages", [])
        if not messages:
            console.print("\n[dim]No messages.[/dim]")
            return

        console.print(f"\n[bold]Conversation ({len(messages)} messages):[/bold]")
        for msg in messages:
            _print_history_message(msg)
        console.print()

    run_async(_get())


def _print_history_message(msg):
    """Render a single history message."""
    meta = msg.get("metadata", {})
    source = meta.get("source", {})
    role = source.get("role", "unknown")
    ts = meta.get("timestamp", "")
    msg_type = msg.get("type", "")
    payload = msg.get("payload", {})
    data = payload.get("data", {}) if isinstance(payload.get("data"), dict) else {}

    fts = format_timestamp(ts)

    if msg_type == "session:message" and role == "user":
        content = data.get("content", "")
        console.print(f"\n[bold cyan]You[/bold cyan]  [dim]{fts}[/dim]")
        if content:
            console.print(f"  {content}")
    elif msg_type == "session:text":
        content = data.get("content", "")
        console.print(f"\n[bold green]Pine AI[/bold green]  [dim]{fts}[/dim]")
        if content:
            console.print(f"  {content}")
    elif msg_type == "session:work_log":
        steps = data.get("steps", [])
        for step in steps:
            details = step.get("step_details", "")
            title = step.get("step_title", "")
            if details:
                console.print(f"\n[bold green]Pine AI[/bold green]  [dim]{fts}[/dim]  [dim]({title})[/dim]")
                console.print(f"  {details}")
    elif msg_type in ("session:form_to_user", "session:ask_for_location",
                      "session:three_way_call", "session:interactive_auth_confirmation"):
        console.print(f"\n[bold yellow]Pine AI ({msg_type})[/bold yellow]  [dim]{fts}[/dim]")
        console.print(f"  {json.dumps(data, indent=2)}")


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
