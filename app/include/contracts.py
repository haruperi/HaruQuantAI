"""Temporary migration bridge to app.core.data.contracts."""

import sys

from app.core.data import contracts as _implementation

sys.modules[__name__] = _implementation
