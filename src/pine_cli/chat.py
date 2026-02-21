"""pine chat / pine send — interactive and one-shot messaging."""

import json
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel

from pine_assistant.models.events import S2CEvent
from pine_cli.config import get_assistant_client, run_async, handle_api_errors

console = Console()


@click.command("chat")
@click.argument("session_id", required=False)
@handle_api_errors
def chat_cmd(session_id: Optional[str]):
    """Interactive chat with Pine AI (REPL).

    Optionally pass a SESSION_ID to resume. Without one, shows recent
    sessions so you can pick an existing session or create a new one.
    """
    async def _chat():
        client = get_assistant_client()

        sid = session_id
        if not sid:
            sid = await _pick_or_create_session(client)
            if not sid:
                return

        await client.connect()
        console.print(f"[dim]Session: {sid}[/dim]")
        await client.join_session(sid)
        console.print("[cyan]Type your message (Ctrl+C or /quit to exit)[/cyan]\n")

        try:
            while True:
                msg = click.prompt("You", prompt_suffix=": ")
                if msg.strip().lower() in ("/quit", "/exit"):
                    break
                async for event in client.chat(sid, msg):
                    _print_event(event)
        except (KeyboardInterrupt, EOFError):
            console.print()
        finally:
            client.leave_session(sid)
            await client.disconnect()

    run_async(_chat())


@click.command("send")
@click.argument("message")
@click.option("-s", "--session", "session_id", default=None, help="Session ID to send the message to")
@click.option("--new", "create_new", is_flag=True, help="Create a new session, then send")
@click.option("--json-output", "--json", is_flag=True, help="Output as JSON")
@handle_api_errors
def send_cmd(message: str, session_id: Optional[str], create_new: bool, json_output: bool):
    """Send a message to a Pine AI session.

    Requires either --session/-s to target an existing session,
    or --new to create a fresh session first.
    """
    if not session_id and not create_new:
        raise click.UsageError("Provide --session/-s SESSION_ID or --new to create one.")
    if session_id and create_new:
        raise click.UsageError("Cannot use --session and --new together.")

    async def _send():
        client = get_assistant_client()

        sid = session_id
        if create_new:
            s = await client.sessions.create()
            sid = s["id"]
            if json_output:
                click.echo(json.dumps({"type": "session_created", "data": {"session_id": sid}}))
            else:
                console.print(f"[green]✓ Session created:[/green]  [bold]{sid}[/bold]")

        await client.connect()
        try:
            await client.join_session(sid)
            async for event in client.chat(sid, message):
                if json_output:
                    click.echo(json.dumps({"type": event.type, "data": event.data}))
                else:
                    _print_event(event)

            client.leave_session(sid)
        finally:
            await client.disconnect()

    run_async(_send())


async def _pick_or_create_session(client) -> Optional[str]:
    """Show recent sessions and let the user pick one or create a new session."""
    page_size = 10
    offset = 0
    all_items: list = []

    while True:
        with console.status("Fetching sessions…"):
            result = await client.sessions.list(limit=page_size, offset=offset)

        page = result.get("sessions", [])
        total = result.get("total", 0)
        all_items.extend(page)

        if not all_items:
            console.print("[dim]No existing sessions found.[/dim]")
            choice = "n"
        else:
            console.print("[bold]Recent sessions:[/bold]")
            for i, s in enumerate(all_items, 1):
                title = s.get("title") or "[dim]untitled[/dim]"
                state = s.get("state", "")
                console.print(f"  [bold]{i}.[/bold] {title}  [dim]({state})[/dim]  [dim]{s['id']}[/dim]")
            has_more = len(all_items) < total
            console.print(f"  [bold]n.[/bold] Create a new session")
            if has_more:
                console.print(f"  [bold]m.[/bold] Show more  [dim]({len(all_items)} of {total})[/dim]")
            console.print()
            choice = click.prompt("Select a session (number, 'n', or 'm')" if has_more
                                  else "Select a session (number or 'n')", default="1")

        cmd = choice.strip().lower()

        if cmd == "n":
            with console.status("Creating session…"):
                s = await client.sessions.create()
            console.print(f"[green]✓ Session created:[/green]  [bold]{s['id']}[/bold]")
            return s["id"]

        if cmd == "m" and len(all_items) < total:
            offset = len(all_items)
            continue

        try:
            idx = int(choice) - 1
            if 0 <= idx < len(all_items):
                return all_items[idx]["id"]
            console.print("[red]Invalid selection.[/red]")
            return None
        except ValueError:
            console.print("[red]Invalid selection.[/red]")
            return None


def _print_event(event):
    """Render a chat event to the console."""
    if event.type == S2CEvent.SESSION_TEXT:
        data = event.data if isinstance(event.data, dict) else {}
        content = data.get("content", "")
        if content:
            console.print(f"[green]Pine AI:[/green] {content}")
    elif event.type == S2CEvent.SESSION_FORM_TO_USER:
        data = event.data if isinstance(event.data, dict) else {}
        msg = data.get("message_to_user", "")
        console.print(Panel(f"[yellow]{msg}[/yellow]\n{json.dumps(data, indent=2)}",
                            title="Form Required", border_style="yellow"))
    elif event.type == S2CEvent.SESSION_STATE:
        data = event.data if isinstance(event.data, dict) else {}
        state = data.get("content", "")
        if state:
            console.print(f"[dim]  ● state → {state}[/dim]")
    elif event.type == S2CEvent.SESSION_THINKING:
        console.print("[dim]  ● thinking…[/dim]")
    elif event.type == S2CEvent.SESSION_WORK_LOG:
        data = event.data if isinstance(event.data, dict) else {}
        steps = data.get("steps", [])
        for step in steps:
            console.print(f"[dim]  ● {step.get('step_title', '')} [{step.get('status', '')}][/dim]")
