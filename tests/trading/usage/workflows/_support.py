"""Shared, non-workflow infrastructure for Trading workflow examples."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from tests.trading import conftest as examples

__all__ = ["examples"]
