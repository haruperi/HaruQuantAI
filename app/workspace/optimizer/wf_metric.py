"""Source-resolved walk-forward metric projection helper.

Description:
    Selects one metric from the first walk-forward result record in accordance
    with observed SQX FitnessMethodWFResult lookup policies.

Purpose:
    FEAT-OPTIMIZER-WF-METRIC: First walk-forward result metric projection.

Key Capabilities:
    - FR-optimizer-first-wf-metric: Extract raw metric value from head of WF results.

Python API Usage:
    from app.workspace.optimizer.wf_metric import first_wf_metric
    val = first_wf_metric([{"NetProfit": 12.5}], "NetProfit")  # 12.5

CLI Usage:
    python -m app.cli optimizer project-wf-metric --metric NetProfit
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from app.core.host.logging import get_logger

logger = get_logger(__name__)


def first_wf_metric(
    results: Sequence[Mapping[str, float]] | None,
    metric: str,
) -> float:
    """Project single named metric from the first walk-forward result mapping.

    Args:
        results: Sequence of walk-forward result dictionaries, or None.
        metric: Non-empty string identifier of the target metric.

    Returns:
        Float value of the metric from the first result, defaulting to 0.0 if missing
        or if results is None or empty.

    Raises:
        ValueError: If metric is not a non-empty string.
    """
    if not isinstance(metric, str) or not metric:
        raise ValueError("metric must be non-empty")

    if not results:
        logger.debug(
            "Walk-forward results sequence is empty or None; defaulting to 0.0"
        )
        return 0.0

    raw_val = results[0].get(metric, 0.0)
    logger.debug("Projected first WF metric %s: %s", metric, raw_val)
    return float(raw_val)
