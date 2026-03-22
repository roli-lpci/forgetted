"""
incognito.guard — Write-blocking interceptor for incognito mode.

Monkey-patches ``builtins.open`` while active so that any attempt to write
(modes 'w', 'a', 'x' and their binary variants) to protected paths inside
the workspace silently returns a no-op file handle.  Reads are never blocked.

Protected paths:
    - memory/ directory (daily logs, checkpoints)
    - DELIVERABLES.md
    - Any *.jsonl file (session logs)

Design decision: we patch builtins.open rather than wrapping individual tool
calls because agent frameworks may write through many layers.  The patch is
scoped to the guard's lifetime and restored on stop().
"""

import builtins
import io
import logging
import re
from pathlib import Path
from typing import Optional, Set

logger = logging.getLogger(__name__)

# Modes that involve writing — we block these on protected paths.
_WRITE_MODES = re.compile(r"[wax+]", re.IGNORECASE)

# Default protected path patterns (relative to workspace root).
_DEFAULT_PROTECTED = {
    "memory",           # entire memory/ directory tree
    "DELIVERABLES.md",  # shared deliverables log
}

# File extensions that are always blocked inside the workspace.
_BLOCKED_EXTENSIONS = {".jsonl"}


class IncognitoGuard:
    """Context manager that blocks file writes to protected workspace paths.

    Parameters
    ----------
    workspace_path : str
        Absolute path to the agent workspace root.
    extra_protected : set[str], optional
        Additional relative paths or directory names to protect.

    Usage
    -----
    ::

        guard = IncognitoGuard("/path/to/workspace")
        guard.start()
        # ... agent runs, writes to memory/ are silently discarded ...
        guard.stop()

    Or as a context manager::

        with IncognitoGuard("/path/to/workspace"):
            ...
    """

    def __init__(self, workspace_path: str, extra_protected: Optional[Set[str]] = None):
        self.workspace = Path(workspace_path).resolve()
        self.protected = _DEFAULT_PROTECTED | (extra_protected or set())
        self.active = False
        self._original_open = None
        self._blocked_count = 0

    # -- public API ---------------------------------------------------------

    def start(self):
        """Activate write blocking.  Patches ``builtins.open``."""
        if self.active:
            return
        self._original_open = builtins.open
        self._blocked_count = 0
        builtins.open = self._patched_open  # type: ignore[assignment]
        self.active = True
        logger.info("🕶️  Incognito guard active — writes to protected paths are blocked")

    def stop(self):
        """Deactivate write blocking.  Restores original ``builtins.open``."""
        if not self.active:
            return
        builtins.open = self._original_open  # type: ignore[assignment]
        self._original_open = None
        self.active = False
        logger.info("🕶️  Incognito guard stopped — %d write(s) blocked", self._blocked_count)

    @property
    def blocked_count(self) -> int:
        """Number of write attempts blocked since guard was started."""
        return self._blocked_count

    # -- context manager ----------------------------------------------------

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
        return False

    # -- internal -----------------------------------------------------------

    def _is_protected(self, filepath: Path) -> bool:
        """Check if *filepath* falls under a protected path."""
        try:
            resolved = filepath.resolve()
        except (OSError, ValueError):
            return False

        # Must be inside the workspace to be subject to protection.
        try:
            rel = resolved.relative_to(self.workspace)
        except ValueError:
            return False

        # Check extension blocklist (e.g., .jsonl anywhere in workspace).
        if resolved.suffix in _BLOCKED_EXTENSIONS:
            return True

        # Check protected directories and files.
        rel_parts = rel.parts
        for protected in self.protected:
            # Direct filename match (e.g., "DELIVERABLES.md").
            if rel_parts and rel_parts[-1] == protected:
                return True
            # Directory match (e.g., "memory" matches memory/anything).
            if protected in rel_parts:
                return True

        return False

    def _is_write_mode(self, mode: str) -> bool:
        """Return True if *mode* involves writing."""
        return bool(_WRITE_MODES.search(mode))

    def _patched_open(self, file, mode="r", *args, **kwargs):
        """Replacement for builtins.open that intercepts protected writes."""
        filepath = Path(str(file))

        if self._is_write_mode(mode) and self._is_protected(filepath):
            self._blocked_count += 1
            logger.debug("🕶️  Blocked write to %s (mode=%s)", filepath, mode)
            # Return a no-op StringIO/BytesIO depending on mode.
            if "b" in mode:
                return io.BytesIO()
            return io.StringIO()

        return self._original_open(file, mode, *args, **kwargs)
