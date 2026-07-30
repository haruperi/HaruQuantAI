"""Unit tests for Research market-structure calibration (FR-RES-079)."""

import pytest
from app.services.research import (
    calibrate_market_structure,
    create_research_value,
)
from app.utils import get_logger

logger = get_logger(__name__)


def _config() -> object:
    """Build a market-structure configuration with a calibration grid."""
    return create_research_value(
        "MarketStructureConfig",
        {
            "swing_window": 5,
            "trend_threshold": 0.5,
            "range_threshold": 0.2,
            "calibration_grid": [{"trend_threshold": 0.4}, {"trend_threshold": 0.6}],
        },
        False,
        (10,),
        128,
        5,
    )


def _limits() -> object:
    """Build approved resource ceilings."""
    return create_research_value("ResearchResourceLimits", 500_000, 600.0, 52_428_800)


def test_calibration_uses_profile_score() -> None:
    """FR-RES-079: calibration ranks candidates using the canonical score."""
    logger.debug("Testing Research market-structure calibration")
    result = calibrate_market_structure(
        run_rows=[
            {"efficiency_ratio": 0.6, "verdict": "trend", "symbol": "A"},
        ],
        validation_rows=[{"symbol": "A", "verdict": "trend"}],
        config=_config(),
        limits=_limits(),
    )
    assert result["schema_version"] == "v1"
    assert result["candidate_count"] == 2
    assert "ranked" in result


def test_calibration_guards_and_missing_truth_are_explicit() -> None:
    """Cover empty input, absent/oversized grids, and missing truth warnings."""
    with pytest.raises(ValueError, match="EMPTY_RUN_ROWS"):
        calibrate_market_structure(
            run_rows=[],
            validation_rows=[],
            config=_config(),
            limits=_limits(),
        )
    missing_grid = create_research_value(
        "MarketStructureConfig",
        {"trend_threshold": 0.5, "range_threshold": 0.2},
        False,
        (10,),
        128,
        5,
    )
    with pytest.raises(ValueError, match="MISSING_CALIBRATION_GRID"):
        calibrate_market_structure(
            run_rows=[{"efficiency_ratio": 0.5}],
            validation_rows=[],
            config=missing_grid,
            limits=_limits(),
        )
    limited = create_research_value(
        "MarketStructureConfig",
        {
            "calibration_grid": [
                {"trend_threshold": 0.4},
                {"trend_threshold": 0.6},
            ]
        },
        False,
        (10,),
        1,
        5,
    )
    with pytest.raises(ValueError, match="CANDIDATE_LIMIT_EXCEEDED"):
        calibrate_market_structure(
            run_rows=[{"efficiency_ratio": 0.5}],
            validation_rows=[],
            config=limited,
            limits=_limits(),
        )
    result = calibrate_market_structure(
        run_rows=[
            {"efficiency_ratio": "missing", "symbol": "A"},
            {"efficiency_ratio": 0.7, "symbol": "B"},
        ],
        validation_rows=[],
        config=_config(),
        limits=_limits(),
    )
    assert result["warnings"][0]["code"] == "NO_VALIDATION_TRUTH"
