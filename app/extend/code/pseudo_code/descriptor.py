"""Human-readable strategy pseudocode (.txt) export descriptor.

Description:
    Registers the PseudoCode (.txt) platform descriptor and renders structured
    human-readable English specifications of strategy parameters, universe,
    timeframes, and rules from NormalizedStrategy AST nodes.

Purpose:
    FEAT-EXTEND-CODE-PSEUDOCODE: Phase 5.10 (WO-WZ-TEMPLATE-COHORTS, Gate G10)
    PseudoCode export target descriptor.

Key Capabilities:
    - FR-extend-pseudocode-descriptor: Publishes PSEUDO_CODE_DESCRIPTOR with .txt
      extension and human-readable specification options.
    - FR-extend-pseudocode-render: Renders structured strategy pseudocode from
      NormalizedStrategy with explicit requirement logging.

Python API Usage:
    from app.extend.code.pseudo_code.descriptor import (
        PSEUDO_CODE_DESCRIPTOR,
        render_pseudo_code,
    )

    text = render_pseudo_code(normalized_strategy)

CLI Usage:
    uv run python -m pytest tests/workspace/algo_wizard --no-cov -q
"""

from __future__ import annotations

from app.core.host.logging import get_logger
from app.core.wizard.template_helpers import (
    PlatformDescriptorSpec,
    render_pseudocode_source,
)
from app.core.wizard.transform import NormalizedStrategy

logger = get_logger(__name__)

PSEUDO_CODE_DESCRIPTOR = PlatformDescriptorSpec(
    platform_id="pseudo_code",
    label="Human-Readable Strategy Pseudocode",
    extension=".txt",
    language="Pseudocode",
    supports_stop_loss=True,
    supports_take_profit=True,
    options=("structured_header", "rule_table"),
)


def render_pseudo_code(
    strategy: NormalizedStrategy,
    *,
    display_name: str | None = None,
    schema_version: str = "1.0.0",
    symbols: tuple[str, ...] = ("EURUSD",),
    primary_timeframe: str = "H1",
    additional_timeframes: tuple[str, ...] = (),
    description: str = "",
) -> str:
    """Render deterministic human-readable pseudocode (.txt) from NormalizedStrategy."""
    logger.info(
        "FR-extend-pseudocode-render: rendering strategy_id=%s extension=%s",
        strategy.strategy_id,
        PSEUDO_CODE_DESCRIPTOR.extension,
    )
    return render_pseudocode_source(
        strategy,
        display_name=display_name,
        schema_version=schema_version,
        symbols=symbols,
        primary_timeframe=primary_timeframe,
        additional_timeframes=additional_timeframes,
        description=description,
    )


__all__ = ["PSEUDO_CODE_DESCRIPTOR", "render_pseudo_code"]
