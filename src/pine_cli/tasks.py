"""pine task start|stop — task lifecycle commands."""

import click
from rich.console import Console

from pine_cli.config import get_assistant_client, run_async, handle_api_errors

console = Console()


@click.group()
def task():
    """Task lifecycle commands."""


@task.command("start")
@click.argument("session_id")
@handle_api_errors
def task_start(session_id):
    """Start task execution for a session."""
    async def _start():
        client = get_assistant_client()
        with console.status("Starting task…"):
            result = await client.sessions.start_task(session_id)
        console.print(f"[green]✓ Task started[/green]  {result.get('message', 'OK')}")

    run_async(_start())


@task.command("stop")
@click.argument("session_id")
@handle_api_errors
def task_stop(session_id):
    """Stop a running task."""
    async def _stop():
        client = get_assistant_client()
        with console.status("Stopping task…"):
            result = await client.sessions.stop_task(session_id)
        console.print(f"[green]✓ Task stopped[/green]  {result.get('message', 'OK')}")

    run_async(_stop())
