"""pine voice call|status — Pine AI voice calls."""

import json
from contextlib import nullcontext
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from pine_cli.config import get_voice_client, handle_api_errors

console = Console()


@click.group()
def voice():
    """Voice call commands."""


@voice.command("call")
@click.option("--to", "phone", required=True, help="Phone number in E.164 format (e.g. +14155551234)")
@click.option("--name", required=True, help="Name of the person/business being called")
@click.option("--context", required=True, help="Background context for the call")
@click.option("--objective", required=True, help="What the call should achieve")
@click.option("--instructions", default=None, help="Detailed strategy or instructions")
@click.option("--caller", type=click.Choice(["negotiator", "communicator"]), default=None,
              help="Caller persona (default: negotiator)")
@click.option("--voice", "voice_gender", type=click.Choice(["male", "female"]), default=None,
              help="Voice gender (default: female)")
@click.option("--max-duration", type=click.IntRange(1, 120), default=None,
              help="Max call duration in minutes (1-120)")
@click.option("--summary/--no-summary", default=False, help="Enable LLM summary of the call")
@click.option("--wait/--no-wait", default=True, help="Wait for call to complete (default: wait)")
@click.option("--json-output", "--json", is_flag=True, help="Output as JSON")
@handle_api_errors
def call_cmd(phone, name, context, objective, instructions, caller, voice_gender,
             max_duration, summary, wait, json_output):
    """Make a phone call via Pine AI voice agent."""
    client = get_voice_client()

    call_kwargs = dict(
        to=phone, name=name, context=context, objective=objective,
        instructions=instructions, caller=caller, voice=voice_gender,
        max_duration_minutes=max_duration, enable_summary=summary,
    )
    call_kwargs = {k: v for k, v in call_kwargs.items() if v is not None}

    if not wait:
        with console.status("Initiating call…"):
            initiated = client.calls.create(**call_kwargs)
        if json_output:
            click.echo(json.dumps({"call_id": initiated.call_id, "status": initiated.status}))
        else:
            console.print(f"[green]✓ Call initiated[/green]  ID: [bold]{initiated.call_id}[/bold]")
            console.print(f"[dim]Check status: pine voice status {initiated.call_id}[/dim]")
        return

    def _on_progress(progress):
        if not json_output:
            dur = f" ({progress.duration_seconds}s)" if progress.duration_seconds else ""
            console.print(f"[dim]  ● {progress.status}{dur}[/dim]")

    if not json_output:
        console.print(f"[cyan]Calling {name} at {phone}…[/cyan]")
    with console.status("Call in progress…") if not json_output else nullcontext():
        result = client.calls.create_and_wait(**call_kwargs, on_progress=_on_progress)

    if json_output:
        click.echo(json.dumps({
            "call_id": result.call_id, "status": result.status,
            "duration_seconds": result.duration_seconds,
            "summary": result.summary, "credits_charged": result.credits_charged,
            "transcript": [{"speaker": t.speaker, "text": t.text} for t in result.transcript],
        }, indent=2))
        return

    _render_result(result)


@voice.command("status")
@click.argument("call_id")
@click.option("--json-output", "--json", is_flag=True, help="Output as JSON")
@handle_api_errors
def status_cmd(call_id, json_output):
    """Check the status of a voice call."""
    client = get_voice_client()

    with console.status("Fetching call status…"):
        result = client.calls.get(call_id)

    if json_output:
        data = {"call_id": result.call_id, "status": result.status}
        if hasattr(result, "summary"):
            data.update(
                duration_seconds=result.duration_seconds,
                summary=result.summary,
                credits_charged=result.credits_charged,
                transcript=[{"speaker": t.speaker, "text": t.text} for t in result.transcript],
            )
        click.echo(json.dumps(data, indent=2))
        return

    if hasattr(result, "summary"):
        _render_result(result)
    else:
        console.print(f"Call [bold]{result.call_id}[/bold]  Status: [yellow]{result.status}[/yellow]")
        if result.duration_seconds:
            console.print(f"Duration: {result.duration_seconds}s")


def _render_result(result):
    """Pretty-print a completed CallResult."""
    color = {"completed": "green", "failed": "red", "cancelled": "yellow"}.get(result.status, "white")
    console.print(f"\n[{color} bold]{result.status.upper()}[/{color} bold]  "
                  f"Call [bold]{result.call_id}[/bold]")
    console.print(f"Duration: {result.duration_seconds}s  |  Credits: {result.credits_charged}")

    if result.summary:
        console.print(Panel(result.summary, title="Summary", border_style="cyan"))

    if result.transcript:
        table = Table(title="Transcript", show_lines=True, expand=True)
        table.add_column("Speaker", style="bold", width=8)
        table.add_column("Text")
        for entry in result.transcript:
            style = "green" if entry.speaker == "agent" else "white"
            table.add_row(entry.speaker, entry.text, style=style)
        console.print(table)
