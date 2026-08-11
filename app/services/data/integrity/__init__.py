"""Is this series trustworthy?

Owns series-level quality inspection: gaps, duplicates, spikes, flat-lines,
zero-volume runs, and spread breaches, plus deterministic scoring and remediation
evidence. Returns evidence only — it never mutates, repairs, drops, or interpolates a
record, and the calling workflow owns the fail-closed decision.

Record-level invariants live in ``models/records.py``, enforced at contract
construction. This package does not repeat them.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.services.data.contracts.responses import (
    StandardResponse,
    data_start_time,
    run_data_operation,
    unwrap_data_response,
)
from app.utils import generate_id

if TYPE_CHECKING:
    from app.services.data.contracts import (
        DataQualityReport,
        MarketDataset,
    )

from app.services.data.integrity.anomalies import (
    detect_clock_drift,
    detect_extreme_spread_widening,
    detect_flatline_periods,
    detect_out_of_order_records,
    detect_price_jumps,
    detect_source_disagreement,
    detect_stale_quote,
    detect_zero_volume_bars,
)
from app.services.data.integrity.asset_metadata import validate_symbol_metadata
from app.services.data.integrity.contracts import QualityFlag, aggregate_flags
from app.services.data.integrity.policy import (
    QualityPolicy,
    get_quality_policy,
    summarize_quality_remediation,
)
from app.services.data.integrity.series import (
    detect_timestamp_gaps,
    inspect_dataset_quality,
    inspect_records_quality,
)


def inspect_data_quality(
    dataset: MarketDataset,
) -> StandardResponse[DataQualityReport]:
    """Inspect one canonical dataset through the package quality facade.

    Args:
        dataset: Canonical dataset whose series evidence must be measured.

    Returns:
        Standard response carrying deterministic bounded quality evidence.
    """
    request_id = generate_id("req")
    return run_data_operation(
        operation="data.quality.inspect_data_quality",
        request_id=request_id,
        start_time=data_start_time(),
        raw=lambda: unwrap_data_response(
            inspect_dataset_quality(dataset),
            operation="data.quality.inspect_data_quality",
            request_id=request_id,
        ),
    )


__all__ = [
    "QualityFlag",
    "QualityPolicy",
    "aggregate_flags",
    "detect_clock_drift",
    "detect_extreme_spread_widening",
    "detect_flatline_periods",
    "detect_out_of_order_records",
    "detect_price_jumps",
    "detect_source_disagreement",
    "detect_stale_quote",
    "detect_timestamp_gaps",
    "detect_zero_volume_bars",
    "get_quality_policy",
    "inspect_data_quality",
    "inspect_dataset_quality",
    "inspect_records_quality",
    "summarize_quality_remediation",
    "validate_symbol_metadata",
]
