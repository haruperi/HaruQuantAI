"""Executable Research contracts usage example.

Demonstrates Research contract models, configurations, scorecards, and quality reports.
"""

import sys
from pathlib import Path

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.research.contracts import (
    CleaningConfig,
    DataQualityReport,
    EnrichmentConfig,
    FeatureConfig,
    ResearchResourceLimits,
    ResearchScorecard,
)


def example_contracts() -> None:
    """Demonstrate Research domain contract configurations and models."""
    print("=" * 80)
    print("Research Example 1: Domain Configurations and Scorecards")
    print("=" * 80)

    # 1. Resource limits
    limits = ResearchResourceLimits(500_000, 600.0, 52_428_800)
    print(f"Resource Limits max rows: {limits.max_rows}")

    # 2. Cleaning config
    cleaning = CleaningConfig("UTC", "error", "none", "keep_warn", "error")
    print(f"CleaningConfig timezone: {cleaning.timezone}")

    # 3. Enrichment config
    enrichment = EnrichmentConfig("EURUSD", True, True, False, True)
    print(f"EnrichmentConfig symbol: {enrichment.symbol}")

    # 4. Feature config
    features = FeatureConfig(
        windows={"sma": 20},
        forward_horizons=(1, 5),
        allowed_forward_columns=("forward_1", "forward_5"),
        nan_policy="preserve",
    )
    print(f"FeatureConfig windows: {features.windows}")

    # 5. Data Quality Report
    quality = DataQualityReport((), (), ("schema",), ())
    print(f"DataQualityReport fatal issues: {len(quality.fatal_issues)}")

    # 6. Research Scorecard
    scorecard = ResearchScorecard(
        "v1",
        ({"criterion": "quality", "score": 20},),
        20.0,
        "INSUFFICIENT_EVIDENCE",
        ("More evidence required",),
        (),
        True,
    )
    print(
        f"ResearchScorecard readiness: {scorecard.readiness}, score: {scorecard.final_score}"
    )


def main() -> None:
    """Run Research contracts usage example."""
    example_contracts()


if __name__ == "__main__":
    main()
