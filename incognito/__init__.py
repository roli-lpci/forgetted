"""
incognito-agent — Mid-conversation incognito mode for AI agents.

When triggered, the incognito system:
1. Checkpoints the current session context into a resumption file
2. Blocks all file writes to protected paths (memory, logs, deliverables)
3. Self-cleans the session log for the incognito window on exit
4. Enables seamless resume from the checkpoint in the next session

This is a software wrapper around the agent's tool execution layer,
not a prompt template.

Author: Hermes Labs
License: Apache-2.0
"""

from .checkpoint import create_checkpoint, load_checkpoint
from .cleaner import delete_session_log, find_session_log
from .guard import IncognitoGuard
from .trigger import TRIGGERS, is_incognito_trigger

__version__ = "0.1.0"
__author__ = "Hermes Labs"
__all__ = [
    "create_checkpoint",
    "load_checkpoint",
    "delete_session_log",
    "find_session_log",
    "IncognitoGuard",
    "is_incognito_trigger",
    "TRIGGERS",
]
