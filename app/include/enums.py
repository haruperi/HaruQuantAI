"""Temporary migration bridge to app.core.enums."""

from __future__ import annotations

import sys

from app.core import enums as _implementation
from app.core.enums import *  # noqa: F403

sys.modules[__name__] = _implementation
