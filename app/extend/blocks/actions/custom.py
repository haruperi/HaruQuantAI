"""Custom action re-export module.

Description:
    Re-exports custom action building blocks for arbitrary script execution.
Purpose:
    FEAT-ACTION-BLOCKS: StrategyQuant donor-faithful action blocks.
Key Capabilities:
    - FR-ACTIONS-CUSTOM-REEXPORT: Re-export of custom action blocks.
Python API Usage:
    from app.extend.blocks.actions.custom import CustomAction, custom_action
CLI Usage:
    uv run pytest tests/extend/blocks/test_actions.py --no-cov
"""

from __future__ import annotations

from app.extend.blocks.actions.custom_action import (
    CustomAction,
    custom_action,
)

__all__ = ["CustomAction", "custom_action"]
