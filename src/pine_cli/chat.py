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
    """Interactive chat with Pine AI (REPL)."""
    async def _chat():
        client = get_assistant_client()
        await client.connect()

        sid = session_id
        if not sid:
            with console.status("Creating session…"):
                s = await client.sessions.create()
                sid = s["id"]
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
@click.option("-s", "--session", "session_id", default=None, help="Existing session ID")
@click.option("--json-output", "--json", is_flag=True, help="Output as JSON")
@handle_api_errors
def send_cmd(message: str, session_id: Optional[str], json_output: bool):
    """Send a one-shot message to Pine AI."""
    async def _send():
        client = get_assistant_client()
        await client.connect()

        sid = session_id
        try:
            if not sid:
                s = await client.sessions.create()
                sid = s["id"]
                if not json_output:
                    console.print(f"[dim]Session: {sid}[/dim]")

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
