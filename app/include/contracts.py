"""Temporary migration bridge to app.core.data.contracts."""

from __future__ import annotations

import sys

from app.core.data import contracts as _implementation
from app.core.data.contracts import *  # noqa: F403

sys.modules[__name__] = _implementation
