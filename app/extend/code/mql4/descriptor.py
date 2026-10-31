"""MetaTrader 4 Expert Advisor (MQL4) strategy export descriptor.

Description:
    Registers the MetaTrader 4 (.mq4) platform descriptor and renders
    deterministic MQL4 Expert Advisor source code from NormalizedStrategy AST
    nodes using shared wizard template helpers.

Purpose:
    FEAT-EXTEND-CODE-MQL4: Phase 5.10 (WO-WZ-TEMPLATE-COHORTS, Gate G10)
    MetaTrader 4 export target descriptor.

Key Capabilities:
    - FR-extend-mql4-descriptor: Publishes MQL4_DESCRIPTOR with .mq4 extension
      and OrderSend/MagicNumber capability metadata.
    - FR-extend-mql4-render: Renders MQL4 Expert Advisor source code from
      NormalizedStrategy with explicit requirement logging.

Python API Usage:
    from app.extend.code.mql4.descriptor import MQL4_DESCRIPTOR, render_mql4

    code = render_mql4(normalized_strategy)

CLI Usage:
    uv run python -m pytest tests/workspace/algo_wizard --no-cov -q
"""

from __future__ import annotations

from app.core.host.logging import get_logger
from app.core.wizard.template_helpers import (
    PlatformDescriptorSpec,
    render_jinja_template,
)
from app.core.wizard.transform import MQL4_TEMPLATE, NormalizedStrategy

logger = get_logger(__name__)

MQL4_DESCRIPTOR = PlatformDescriptorSpec(
    platform_id="mql4",
    label="MetaTrader 4 Expert Advisor (MQL4)",
    extension=".mq4",
    language="MQL4",
    supports_stop_loss=True,
    supports_take_profit=True,
    options=("property_strict", "magic_number_filter"),
)


def render_mql4(strategy: NormalizedStrategy) -> str:
    """Render deterministic MetaTrader 4 (.mq4) code from NormalizedStrategy."""
    logger.info(
        "FR-extend-mql4-render: rendering strategy_id=%s extension=%s",
        strategy.strategy_id,
        MQL4_DESCRIPTOR.extension,
    )
    return render_jinja_template(MQL4_TEMPLATE, strategy)


__all__ = ["MQL4_DESCRIPTOR", "render_mql4"]
