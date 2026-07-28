"""Bounded opt-in stability and robustness evaluation for Research."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from app.services.research.contracts import (
    MarketStructureQualityReport,
    ResearchWarning,
)
from app.services.research.market_structure.profile import (
    canonical_structure_score,
)
from app.utils import get_logger

logger = get_logger(__name__)

if TYPE_CHECKING:
    from collections.abc import Mapping

    from app.services.research.contracts import (
        MarketStructureConfig,
        PreparedDataset,
        ResearchResourceLimits,
    )

type JSONValue = (
    None | bool | int | float | str | list["JSONValue"] | Mapping[str, "JSONValue"]
)


def evaluate_market_structure_quality(
    prepared: PreparedDataset,
    *,
    config: MarketStructureConfig,
    limits: ResearchResourceLimits,
) -> MarketStructureQualityReport:
    """Run bounded temporal stability and parameter robustness when enabled.

    Stability and robustness are explicitly opt-in due to cost. When disabled,
    an empty advisory report is returned with a structured warning.

    Args:
        prepared: Prepared Research dataset.
        config: Bounded market-structure settings.
        limits: Approved resource ceilings.

    Returns:
        Advisory ``MarketStructureQualityReport``.

    Raises:
        ValueError: If resources are exceeded.
    """
    logger.info("Evaluating Research market-structure quality")
    if len(prepared.data) > limits.max_rows:
        raise ValueError("RES_RESOURCE_LIMIT_EXCEEDED", "ROW_LIMIT_EXCEEDED")
    if not config.enable_quality:
        return MarketStructureQualityReport(
            "v1",
            {},
            {},
            {},
            0.0,
            (
                ResearchWarning(
                    "QUALITY_DISABLED",
                    "Market-structure quality evaluation is opt-in and disabled",
                    "info",
                    "enable_quality",
                    {},
                ),
            ),
        )
    close = prepared.data["close"].astype("float64")
    trend_threshold = float(
        config.profile.get("trend_threshold", 0.5)  # type: ignore[arg-type]
    )
    range_threshold = float(
        config.profile.get("range_threshold", 0.2)  # type: ignore[arg-type]
    )
    stability_rows: list[JSONValue] = []
    for window in config.quality_windows:
        if len(close) < window:
            continue
        segment = close.tail(window)
        net = abs(float(segment.iloc[-1] - segment.iloc[0]))
        path = float(segment.diff().abs().sum())
        ratio = net / path if path > 0 else 0.0
        score = canonical_structure_score(
            efficiency_ratio=ratio,
            trend_threshold=trend_threshold,
            range_threshold=range_threshold,
        )
        stability_rows.append({"window": window, "score": score})
    robustness_values: list[float] = []
    for offset in (-0.1, 0.0, 0.1):
        adj_threshold = max(0.01, trend_threshold + offset)
        net = abs(float(close.iloc[-1] - close.iloc[0]))
        path = float(close.diff().abs().sum())
        ratio = net / path if path > 0 else 0.0
        robustness_values.append(
            canonical_structure_score(
                efficiency_ratio=ratio,
                trend_threshold=adj_threshold,
                range_threshold=range_threshold,
            )
        )
    robustness_std = (
        float(np.std(robustness_values, ddof=0)) if robustness_values else 0.0
    )
    return MarketStructureQualityReport(
        "v1",
        {"windows": stability_rows},
        {"score_std": robustness_std, "threshold_offsets": [-0.1, 0.0, 0.1]},
        {"calibrated": False},
        0.0,
        (),
    )


__all__ = ("evaluate_market_structure_quality",)
