# Pine CLI

Unified command-line interface for [Pine AI](https://www.19pine.ai) — voice calls and assistant tasks from your terminal.

## Install

```bash
pip install pine-cli
```

Or install from source:

```bash
cd pine-cli
pip install -e .
```

## Quick Start

```bash
# Authenticate (shared credentials for voice & assistant)
pine auth login

# Make a voice call
pine voice call \
  --to "+14155551234" \
  --name "Dr. Smith Office" \
  --context "I'm a patient needing a follow-up" \
  --objective "Schedule an appointment for next week"

# Check call status
pine voice status <call-id>

# Start an assistant chat
pine chat

# Send a one-shot message
pine send "Negotiate my Comcast bill down"

# List sessions
pine sessions list

# Start a task
pine task start <session-id>
```

## Commands

### Authentication

| Command | Description |
|---------|-------------|
| `pine auth login` | Log in with email verification |
| `pine auth status` | Show current auth status |
| `pine auth logout` | Clear saved credentials |

### Voice Calls

| Command | Description |
|---------|-------------|
| `pine voice call` | Make a phone call via Pine AI voice agent |
| `pine voice status <id>` | Check call status / get result |

**Voice call options:**

```
--to           Phone number (E.164 format, required)
--name         Callee name (required)
--context      Background context (required)
--objective    Call goal (required)
--instructions Detailed strategy
--caller       negotiator | communicator
--voice        male | female
--max-duration 1-120 minutes
--summary      Enable LLM summary
--wait         Wait for completion (default: yes)
--no-wait      Fire and forget
--json         JSON output
```

### Assistant

| Command | Description |
|---------|-------------|
| `pine chat [session-id]` | Interactive REPL chat |
| `pine send <message>` | One-shot message |
| `pine sessions list` | List sessions |
| `pine sessions get <id>` | Get session details |
| `pine sessions create` | Create new session |
| `pine sessions delete <id>` | Delete session |
| `pine task start <id>` | Start task execution |
| `pine task stop <id>` | Stop a running task |

## Configuration

Credentials are stored at `~/.pine/config.json` after `pine auth login`. Both voice and assistant commands share the same authentication.

## Dependencies

- [pine-voice](https://pypi.org/project/pine-voice/) — Pine AI Voice SDK
- [pine-assistant](https://pypi.org/project/pine-assistant/) — Pine AI Assistant SDK
- [click](https://click.palletsprojects.com/) — CLI framework
- [rich](https://rich.readthedocs.io/) — Terminal formatting
# pine-cli
