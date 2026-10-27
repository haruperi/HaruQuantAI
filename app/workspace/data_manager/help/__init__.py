"""Data Manager contextual help, tutorials, and documentation package.

Description:
    Provides topic-based guidance, interactive tutorial steps, and links to
    external documentation for all Data Manager workspace features.
"""

from __future__ import annotations

from ._cli import (
    register_help_commands,
    run_help_command,
)
from ._helpers import (
    _DONOR_ARTICLES,
    _MAX_NOTE_LENGTH,
    _TOPIC_OVERVIEW,
    _TOPICS,
    _TUTORIALS,
)
from .feature import Help
from .http import register_help_routes

__all__ = [
    "_DONOR_ARTICLES",
    "_MAX_NOTE_LENGTH",
    "_TOPICS",
    "_TOPIC_OVERVIEW",
    "_TUTORIALS",
    "Help",
    "register_help_commands",
    "register_help_routes",
    "run_help_command",
]
