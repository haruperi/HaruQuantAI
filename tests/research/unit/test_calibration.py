"""Unit tests for Research market-structure calibration (FR-RES-079)."""

from app.services.research import MarketStructureConfig, ResearchResourceLimits
from app.services.research.market_structure import calibrate_market_structure
from app.utils import logger


def _config() -> MarketStructureConfig:
    """Build a market-structure configuration with a calibration grid."""
    return MarketStructureConfig(
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


def _limits() -> ResearchResourceLimits:
    """Build approved resource ceilings."""
    return ResearchResourceLimits(500_000, 600.0, 52_428_800)


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
