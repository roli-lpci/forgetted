"""
incognito.checkpoint — Checkpoint creation and resume logic.

Before entering incognito mode, the agent saves a compact summary of the
current session state.  On the next normal session, the checkpoint is loaded
(providing continuity) and then deleted (single-use).

Checkpoint files live at ``<workspace>/memory/incognito-checkpoint.md``.
"""

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

_CHECKPOINT_FILENAME = "incognito-checkpoint.md"


def create_checkpoint(context_summary: str, workspace: str) -> Path:
    """Write a compact resumption file before entering incognito mode.

    Parameters
    ----------
    context_summary : str
        A concise summary of the current session context — open tasks,
        last topic discussed, any pending decisions.
    workspace : str
        Absolute path to the agent workspace root.

    Returns
    -------
    Path
        Absolute path to the created checkpoint file.
    """
    memory_dir = Path(workspace) / "memory"
    memory_dir.mkdir(parents=True, exist_ok=True)

    checkpoint_path = memory_dir / _CHECKPOINT_FILENAME
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    content = (
        f"# Incognito Checkpoint\n"
        f"*Created: {timestamp}*\n\n"
        f"## Session Context\n"
        f"{context_summary}\n\n"
        f"## Instructions\n"
        f"This checkpoint was created before an incognito window. "
        f"Resume from the context above. The incognito conversation "
        f"has been erased — do not attempt to recover it.\n"
    )

    checkpoint_path.write_text(content, encoding="utf-8")
    logger.info("🕶️  Checkpoint saved to %s", checkpoint_path)
    return checkpoint_path


def load_checkpoint(workspace: str) -> Optional[str]:
    """Read the checkpoint file if it exists, then delete it.

    The checkpoint is single-use: once loaded, it's consumed.

    Parameters
    ----------
    workspace : str
        Absolute path to the agent workspace root.

    Returns
    -------
    str or None
        Checkpoint content, or None if no checkpoint exists.
    """
    checkpoint_path = Path(workspace) / "memory" / _CHECKPOINT_FILENAME

    if not checkpoint_path.exists():
        return None

    content = checkpoint_path.read_text(encoding="utf-8")
    checkpoint_path.unlink()
    logger.info("🕶️  Checkpoint loaded and consumed from %s", checkpoint_path)
    return content
