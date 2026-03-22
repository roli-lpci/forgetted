# incognito-agent 🕶️

Mid-conversation incognito mode for AI agents.

When triggered, the incognito system:

1. **Checkpoints** — saves a compact resumption file of the current session context
2. **Blocks writes** — intercepts all file writes to memory, logs, and deliverables
3. **Self-cleans** — deletes the session log for the incognito window on exit
4. **Resumes** — next session picks up from the checkpoint, with no trace of the private conversation

## Installation

```bash
pip install incognito-agent
```

For recoverable trash deletion (recommended):

```bash
pip install incognito-agent[trash]
```

## Quick Start

```python
from incognito import is_incognito_trigger, IncognitoGuard, create_checkpoint

# Detect trigger in user message
if is_incognito_trigger(user_message):
    # Save checkpoint before going dark
    create_checkpoint("Discussing API design for v2", workspace_path)
    
    # Block all writes to protected paths
    with IncognitoGuard(workspace_path):
        # ... agent runs normally but writes are silently discarded ...
        pass
    
    # After exiting: clean up session log
    from incognito import find_session_log, delete_session_log
    log = find_session_log(session_id, agents_dir)
    if log:
        delete_session_log(log)
```

## Components

| Module | Purpose |
|---|---|
| `trigger` | Detect incognito activation in user messages |
| `guard` | Context manager that blocks file writes to protected paths |
| `checkpoint` | Create and load resumption files |
| `cleaner` | Find and safely delete session logs |

## How It Works

### Write Blocking

`IncognitoGuard` patches `builtins.open` to intercept writes to protected paths:

- `memory/` — daily logs, checkpoints
- `DELIVERABLES.md` — shared audit trail
- `*.jsonl` — session log files

Writes to these paths return a no-op file handle. Reads are never blocked. Writes to unprotected paths pass through normally.

### Session Cleanup

After the incognito window ends, `cleaner.delete_session_log()` removes the session log. It uses `send2trash` (OS trash, recoverable) if available, otherwise renames the file with a `.deleted` suffix.

## License

Apache-2.0
