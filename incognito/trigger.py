"""
incognito.trigger — Detect incognito mode activation in user messages.

Supports exact commands (/incognito) and natural-language variants
("go incognito", "incognito mode"). Case-insensitive matching.
"""

from typing import List

# Trigger phrases — checked via substring match against lowercased input.
# Ordered from most specific to least to short-circuit quickly.
TRIGGERS: List[str] = [
    "/incognito",
    "incognito mode",
    "go incognito",
]


def is_incognito_trigger(message: str) -> bool:
    """Check whether a user message contains an incognito trigger.

    Parameters
    ----------
    message : str
        Raw user message text.

    Returns
    -------
    bool
        True if the message activates incognito mode.
    """
    lowered = message.lower()
    return any(trigger in lowered for trigger in TRIGGERS)
