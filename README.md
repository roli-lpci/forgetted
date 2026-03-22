# forgetted 🫥

> *Branch the timeline, but never merge back.*

Selective memory governance for AI agents.

**forgetted** is not incognito mode. It's a memory architecture primitive — a fork without consequence. Your agent keeps full context from the past, but nothing from the forgetted window persists into the future.

Traditional incognito is dumb: no past, no future, fully isolated.
**forgetted** gives you: full continuity + selective non-persistence.

> "I want context… but I don't want consequences."

## Installation

```bash
pip install forgetted
```

For recoverable trash deletion (recommended):

```bash
pip install forgetted[trash]
```

## Quick Start

```python
from forgetted import is_forget_trigger, ForgetGuard, create_checkpoint

# Detect trigger in user message
if is_forget_trigger(user_message):
    # Save checkpoint before branching
    create_checkpoint("Discussing API design for v2", workspace_path)
    
    # Block all writes to protected paths — fork without consequence
    with ForgetGuard(workspace_path):
        # ... agent runs with full context, but writes silently vanish ...
        pass
    
    # After exiting: clean up session log
    from forgetted import find_session_log, delete_session_log
    log = find_session_log(session_id, agents_dir)
    if log:
        delete_session_log(log)
```

## What Gets Blocked

| Layer | Status | Notes |
|---|---|---|
| Memory files (`memory/*.md`) | ✅ Blocked | Daily logs, checkpoints |
| Deliverables log | ✅ Blocked | Shared audit trail |
| Session logs (`*.jsonl`) | ✅ Blocked + cleaned | Deleted on exit |
| Vector DB (embeddings) | 🔜 v0.2 | mem0, chromadb |
| Derived summaries | 🔜 v0.2 | Compaction outputs |
| Tool output logs | 🔜 v0.2 | External tool traces |

## The Test

If I use forgetted like this:
1. I ask something sensitive in a forgetted window
2. I exit
3. Later I ask something related in normal mode

Can the agent infer anything from that prior interaction?

**If yes → we failed. If no → we built something real.**

## How It Works

### ForgetGuard

Patches `builtins.open` to intercept writes to protected paths. Returns no-op file handles — agent code doesn't crash, writes just vanish. Reads are never blocked.

### Checkpoint

Before entering forgetted mode, saves a compact resumption file. On the next normal session, the checkpoint is loaded and consumed (single-use). This preserves continuity without the forgetted content.

### Cleaner

After the forgetted window ends, finds and removes the session log. Uses `send2trash` (OS trash, recoverable) if available, otherwise renames with `.deleted` suffix.

## Components

| Module | Purpose |
|---|---|
| `trigger` | Detect forgetted activation in user messages |
| `guard` | Context manager that blocks file writes to protected paths |
| `checkpoint` | Create and load resumption files |
| `cleaner` | Find and safely delete session logs |

## What This Really Is

This is not a UX feature. It's:

- **A memory governance primitive** — user-controlled memory architecture for AI systems
- **A fork without consequence** — like git: you branch, but you never merge back
- **Controlling gradient flow across time** — preventing session state from shaping future behavior

## License

Apache-2.0
