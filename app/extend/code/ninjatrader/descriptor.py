"""NinjaTrader 8 NinjaScript (C#) strategy export descriptor.

Description:
    Registers the NinjaTrader 8 (.cs) platform descriptor and renders
    deterministic C# NinjaScript Strategy classes from NormalizedStrategy AST
    nodes using shared wizard template helpers.

Purpose:
    FEAT-EXTEND-CODE-NINJATRADER: Phase 5.10 (WO-WZ-TEMPLATE-COHORTS, Gate G10)
    NinjaTrader 8 export target descriptor.

Key Capabilities:
    - FR-extend-ninjatrader-descriptor: Publishes NINJATRADER_DESCRIPTOR with .cs
      extension and OnBarUpdate capability metadata.
    - FR-extend-ninjatrader-render: Renders NinjaTrader 8 C# source code from
      NormalizedStrategy with explicit requirement logging.

Python API Usage:
    from app.extend.code.ninjatrader.descriptor import (
        NINJATRADER_DESCRIPTOR,
        render_ninjatrader,
    )

    code = render_ninjatrader(normalized_strategy)

CLI Usage:
    uv run python -m pytest tests/workspace/algo_wizard --no-cov -q
"""

from __future__ import annotations

from app.core.host.logging import get_logger
from app.core.wizard.template_helpers import (
    PlatformDescriptorSpec,
    render_ninjatrader_source,
)
from app.core.wizard.transform import NormalizedStrategy

logger = get_logger(__name__)

NINJATRADER_DESCRIPTOR = PlatformDescriptorSpec(
    platform_id="ninjatrader",
    label="NinjaTrader 8 NinjaScript (C#)",
    extension=".cs",
    language="C#",
    supports_stop_loss=True,
    supports_take_profit=True,
    options=("on_bar_update", "warmup_guard"),
)


def render_ninjatrader(strategy: NormalizedStrategy) -> str:
    """Render deterministic NinjaTrader 8 (.cs) code from NormalizedStrategy."""
    logger.info(
        "FR-extend-ninjatrader-render: rendering strategy_id=%s extension=%s",
        strategy.strategy_id,
        NINJATRADER_DESCRIPTOR.extension,
    )
    return render_ninjatrader_source(strategy)


__all__ = ["NINJATRADER_DESCRIPTOR", "render_ninjatrader"]
