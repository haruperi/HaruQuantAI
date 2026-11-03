"""Compatibility import for the shared core HSL models module.

Description:
    Preserves existing workspace imports while the core owns HSL semantics.
Purpose:
    FEAT-WIZARD-HSL-LANGUAGE: Shared strategy language ownership.
Key Capabilities:
    - FR-hsl-import-compatibility: Retain the core module identity and diagnostics.
Python API Usage:
    import app.workspace.algo_wizard.models
CLI Usage:
    uv run pytest tests/workspace/algo_wizard --no-cov
"""

from __future__ import annotations

import sys

from app.core.trading.strategy.hsl import models as _implementation
from app.core.trading.strategy.hsl.models import *  # noqa: F403

sys.modules[__name__] = _implementation
