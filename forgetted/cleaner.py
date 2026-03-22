"""
forgetted.cleaner — Session log finder and deleter.

After exiting forgetted mode, the session log covering the forgetted window
must be removed so no trace of the private conversation persists on disk.

Deletion is recoverable by default: uses ``send2trash`` if available,
otherwise renames the file with a ``.deleted`` suffix (can be manually
restored or purged later).
"""

import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def find_session_log(session_id: str, agents_dir: str) -> Optional[Path]:
    """Locate the .jsonl session log for a given session ID.

    Searches recursively under *agents_dir* for any ``.jsonl`` file whose
    name contains the *session_id*.

    Parameters
    ----------
    session_id : str
        The session identifier to search for.
    agents_dir : str
        Root directory to search (e.g., ``~/.openclaw/agents/``).

    Returns
    -------
    Path or None
        Path to the matching session log, or None if not found.
    """
    root = Path(agents_dir)
    if not root.exists():
        return None

    for jsonl_file in root.rglob("*.jsonl"):
        if session_id in jsonl_file.stem:
            logger.debug("🫥 Found session log: %s", jsonl_file)
            return jsonl_file

    return None


def delete_session_log(session_log: Path) -> bool:
    """Remove a session log file safely (recoverable).

    Attempts ``send2trash`` first (moves to OS trash). Falls back to
    renaming with a ``.deleted`` suffix if send2trash is unavailable.

    Parameters
    ----------
    session_log : Path
        Path to the .jsonl session log to delete.

    Returns
    -------
    bool
        True if the file was successfully removed/renamed.
    """
    if not session_log.exists():
        logger.warning("🫥 Session log not found: %s", session_log)
        return False

    # Try send2trash first — moves to OS trash (recoverable).
    try:
        from send2trash import send2trash
        send2trash(str(session_log))
        logger.info("🫥 Session log trashed: %s", session_log)
        return True
    except ImportError:
        pass
    except Exception as exc:
        logger.warning("🫥 send2trash failed (%s), falling back to rename", exc)

    # Fallback: rename with .deleted suffix (manually recoverable).
    deleted_path = session_log.with_suffix(session_log.suffix + ".deleted")
    try:
        session_log.rename(deleted_path)
        logger.info("🫥 Session log renamed to %s", deleted_path)
        return True
    except OSError as exc:
        logger.error("🫥 Failed to delete session log: %s", exc)
        return False
