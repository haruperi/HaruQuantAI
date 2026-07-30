"""Unit tests for the Research core metric profile."""

import pandas as pd
from app.services.research import (
    build_core_metric_profile,
    build_default_registry,
    create_research_value,
)
from app.utils import get_logger

logger = get_logger(__name__)

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
    prepared = create_research_value(
        "PreparedDataset",
        frame,
        "v1",
        create_research_value("DataQualityReport", (), (), ("schema",), ()),
        _HASH,
        _HASH,
        ("fixture",),
    )
    profile = build_core_metric_profile(
        prepared,
        registry=build_default_registry(),
        limits=create_research_value("ResearchResourceLimits", 10, 10.0, 1024),
    )
    assert len(profile.metrics) == 7
    assert profile.dataset_hash == _HASH
    assert profile.warnings


def test_profile_defaults_to_default_registry() -> None:
    """FR-RES-049: registry is optional and defaults to the seven-family registry."""
    logger.debug("Testing Research metric profile default registry")
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
    prepared = create_research_value(
        "PreparedDataset",
        frame,
        "v1",
        create_research_value("DataQualityReport", (), (), ("schema",), ()),
        _HASH,
        _HASH,
        ("fixture",),
    )
    profile = build_core_metric_profile(
        prepared,
        limits=create_research_value("ResearchResourceLimits", 10, 10.0, 1024),
    )
    assert len(profile.metrics) == 7
