"""MetaTrader 5 Expert Advisor (MQL5) strategy export descriptor.

Description:
    Registers the MetaTrader 5 (.mq5) platform descriptor and renders
    deterministic MQL5 Expert Advisor source code from NormalizedStrategy AST
    nodes using shared wizard template helpers.

Purpose:
    FEAT-EXTEND-CODE-MQL5: Phase 5.10 (WO-WZ-TEMPLATE-COHORTS, Gate G10)
    MetaTrader 5 export target descriptor.

Key Capabilities:
    - FR-extend-mql5-descriptor: Publishes MQL5_DESCRIPTOR with .mq5 extension
      and CTrade/MqlRates capability metadata.
    - FR-extend-mql5-render: Renders MQL5 Expert Advisor source code from
      NormalizedStrategy with explicit requirement logging.

Python API Usage:
    from app.extend.code.mql5.descriptor import MQL5_DESCRIPTOR, render_mql5

    code = render_mql5(normalized_strategy)

CLI Usage:
    uv run python -m pytest tests/workspace/algo_wizard --no-cov -q
"""

from __future__ import annotations

from app.core.host.logging import get_logger
from app.core.wizard.template_helpers import (
    PlatformDescriptorSpec,
    render_jinja_template,
)
from app.core.wizard.transform import MQL5_TEMPLATE, NormalizedStrategy

logger = get_logger(__name__)

MQL5_DESCRIPTOR = PlatformDescriptorSpec(
    platform_id="mql5",
    label="MetaTrader 5 Expert Advisor (MQL5)",
    extension=".mq5",
    language="MQL5",
    supports_stop_loss=True,
    supports_take_profit=True,
    options=("ctrade_execution", "mqlrates_series"),
)


def render_mql5(strategy: NormalizedStrategy) -> str:
    """Render deterministic MetaTrader 5 (.mq5) code from NormalizedStrategy."""
    logger.info(
        "FR-extend-mql5-render: rendering strategy_id=%s extension=%s",
        strategy.strategy_id,
        MQL5_DESCRIPTOR.extension,
    )
    return render_jinja_template(MQL5_TEMPLATE, strategy)


__all__ = ["MQL5_DESCRIPTOR", "render_mql5"]
