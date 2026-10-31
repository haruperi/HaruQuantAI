"""TradeStation and MultiCharts EasyLanguage strategy export descriptor.

Description:
    Registers the EasyLanguage (.eld) platform descriptor and renders
    deterministic TradeStation / MultiCharts EasyLanguage source code from
    NormalizedStrategy AST nodes using shared wizard template helpers.

Purpose:
    FEAT-EXTEND-CODE-EASYLANGUAGE: Phase 5.10 (WO-WZ-TEMPLATE-COHORTS, Gate G10)
    EasyLanguage export target descriptor.

Key Capabilities:
    - FR-extend-easylanguage-descriptor: Publishes EASYLANGUAGE_DESCRIPTOR with
      .eld extension and template option metadata.
    - FR-extend-easylanguage-render: Renders EasyLanguage strategy code from
      NormalizedStrategy with explicit requirement logging.

Python API Usage:
    from app.extend.code.easylanguage.descriptor import (
        EASYLANGUAGE_DESCRIPTOR,
        render_easylanguage,
    )

    code = render_easylanguage(normalized_strategy)

CLI Usage:
    uv run python -m pytest tests/workspace/algo_wizard --no-cov -q
"""

from __future__ import annotations

from app.core.host.logging import get_logger
from app.core.wizard.template_helpers import (
    PlatformDescriptorSpec,
    render_jinja_template,
)
from app.core.wizard.transform import EASYLANGUAGE_TEMPLATE, NormalizedStrategy

logger = get_logger(__name__)

EASYLANGUAGE_DESCRIPTOR = PlatformDescriptorSpec(
    platform_id="easylanguage",
    label="TradeStation / MultiCharts EasyLanguage",
    extension=".eld",
    language="EasyLanguage",
    supports_stop_loss=True,
    supports_take_profit=True,
    options=("legacy_color_value", "next_bar_market"),
)


def render_easylanguage(strategy: NormalizedStrategy) -> str:
    """Render deterministic EasyLanguage (.eld) code from NormalizedStrategy."""
    logger.info(
        "FR-extend-easylanguage-render: rendering strategy_id=%s extension=%s",
        strategy.strategy_id,
        EASYLANGUAGE_DESCRIPTOR.extension,
    )
    return render_jinja_template(EASYLANGUAGE_TEMPLATE, strategy)


__all__ = ["EASYLANGUAGE_DESCRIPTOR", "render_easylanguage"]
