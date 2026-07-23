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

if TYPE_CHECKING:
    from app.services.data.contracts import (
        DataQualityReport,
        MarketDataset,
    )

from app.services.data.quality.anomalies import (
    detect_extreme_spread_widening,
    detect_flatline_periods,
    detect_price_jumps,
    detect_zero_volume_bars,
)
from app.services.data.quality.asset_metadata import validate_symbol_metadata
from app.services.data.quality.contracts import QualityFlag, aggregate_flags
from app.services.data.quality.policy import (
    QualityPolicy,
    get_quality_policy,
    summarize_quality_remediation,
)
from app.services.data.quality.series import (
    detect_timestamp_gaps,
    inspect_dataset_quality,
    inspect_records_quality,
)


def inspect_data_quality(
    dataset: MarketDataset,
) -> DataQualityReport:
    """Inspect one canonical dataset through the package quality facade.

    Args:
        dataset: Canonical dataset whose series evidence must be measured.

    Returns:
        Deterministic bounded quality evidence.
    """
    return inspect_dataset_quality(dataset)


__all__ = [
    "QualityFlag",
    "QualityPolicy",
    "aggregate_flags",
    "detect_extreme_spread_widening",
    "detect_flatline_periods",
    "detect_price_jumps",
    "detect_timestamp_gaps",
    "detect_zero_volume_bars",
    "get_quality_policy",
    "inspect_data_quality",
    "inspect_dataset_quality",
    "inspect_records_quality",
    "summarize_quality_remediation",
    "validate_symbol_metadata",
]
