"""Temporary migration bridge to app.core.enums."""

import sys

from app.core import enums as _implementation

sys.modules[__name__] = _implementation
