"""Dukascopy JForex IStrategy Java export descriptor.

Description:
    Registers the JForex (.java) platform descriptor and renders deterministic
    Dukascopy JForex IStrategy Java classes from NormalizedStrategy AST nodes
    using shared wizard template helpers.

Purpose:
    FEAT-EXTEND-CODE-JFOREX: Phase 5.10 (WO-WZ-TEMPLATE-COHORTS, Gate G10)
    JForex export target descriptor.

Key Capabilities:
    - FR-extend-jforex-descriptor: Publishes JFOREX_DESCRIPTOR with .java
      extension and IStrategy capability metadata.
    - FR-extend-jforex-render: Renders JForex IStrategy Java source code from
      NormalizedStrategy with explicit requirement logging.

Python API Usage:
    from app.extend.code.jforex.descriptor import JFOREX_DESCRIPTOR, render_jforex

    code = render_jforex(normalized_strategy)

CLI Usage:
    uv run python -m pytest tests/workspace/algo_wizard --no-cov -q
"""

from __future__ import annotations

from app.core.host.logging import get_logger
from app.core.wizard.template_helpers import (
    PlatformDescriptorSpec,
    render_jforex_source,
)
from app.core.wizard.transform import NormalizedStrategy

logger = get_logger(__name__)

JFOREX_DESCRIPTOR = PlatformDescriptorSpec(
    platform_id="jforex",
    label="Dukascopy JForex Strategy (Java)",
    extension=".java",
    language="Java",
    supports_stop_loss=True,
    supports_take_profit=True,
    options=("configurable_annotations", "bid_bar_evaluation"),
)


def render_jforex(strategy: NormalizedStrategy) -> str:
    """Render deterministic Dukascopy JForex (.java) code from NormalizedStrategy."""
    logger.info(
        "FR-extend-jforex-render: rendering strategy_id=%s extension=%s",
        strategy.strategy_id,
        JFOREX_DESCRIPTOR.extension,
    )
    return render_jforex_source(strategy)


__all__ = ["JFOREX_DESCRIPTOR", "render_jforex"]
