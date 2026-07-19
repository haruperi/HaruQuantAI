"""Unit tests for the Research core metric profile."""

import pandas as pd
from app.services.research.contracts import (
    DataQualityReport,
    PreparedDataset,
    ResearchResourceLimits,
)
from app.services.research.metrics import (
    build_core_metric_profile,
    build_default_registry,
)
from app.utils import logger

_HASH = "e" * 64


def test_profile_preserves_undefined_reason_and_provenance() -> None:
    """Verify seven families and hashes are preserved with explicit undefined data."""
    logger.debug("Testing Research metric profile evidence")
    frame = pd.DataFrame(
        {
            "open": [1.0],
            "high": [2.0],
            "low": [0.5],
            "close": [1.5],
            "volume": [10.0],
            "spread": [0.1],
        },
        index=pd.date_range("2026-01-01", periods=1, tz="UTC"),
    )
    prepared = PreparedDataset(
        frame,
        "v1",
        DataQualityReport((), (), ("schema",), ()),
        _HASH,
        _HASH,
        ("fixture",),
    )
    profile = build_core_metric_profile(
        prepared,
        registry=build_default_registry(),
        limits=ResearchResourceLimits(10, 10.0, 1024),
    )
    assert len(profile.metrics) == 7
    assert profile.dataset_hash == _HASH
    assert profile.warnings
