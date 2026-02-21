"""
Pine CLI — unified command-line interface for Pine AI.

Commands:
  pine auth login|status|logout   Authentication
  pine voice call|status          Voice calls
  pine chat [session-id]          Interactive assistant chat
  pine send <message>             One-shot assistant message
  pine sessions list|get|create|delete  Session management
  pine task start|stop            Task lifecycle
"""

import click

from pine_cli import __version__


@click.group()
@click.version_option(__version__, prog_name="pine")
def main():
    """Pine AI CLI — voice calls & assistant tasks from your terminal."""


from pine_cli.auth import auth
from pine_cli.voice import voice
from pine_cli.chat import chat_cmd, send_cmd
from pine_cli.sessions import sessions
from pine_cli.tasks import task

main.add_command(auth)
main.add_command(voice)
main.add_command(chat_cmd)
main.add_command(send_cmd)
main.add_command(sessions)
main.add_command(task)


if __name__ == "__main__":
    main()
