"""Shared, non-workflow infrastructure for Analytics workflow examples."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from tests.analytics import _support as examples

__all__ = ["examples"]
