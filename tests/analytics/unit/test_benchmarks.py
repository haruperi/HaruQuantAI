"""Unit tests for Analytics benchmark evidence."""

import json
from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from app.services.analytics.adapters.results import adapt_trading_result
from app.services.analytics.contracts import RiskFreeRateEvidence
from app.services.analytics.metrics.benchmarks import (
    align_benchmark_series,
    calculate_benchmark_evidence,
)
from app.services.data import (
    build_data_quality_report,
    build_market_dataset,
    build_ohlcv_record,
)
from app.utils import generate_id, get_logger

logger = get_logger(__name__)

from tests.analytics.component.test_results_adapter import (  # noqa: E402
    _config,
    _source,
)

NOW = datetime(2026, 7, 19, tzinfo=UTC)
_GOLDEN_DIRECTORY = Path("tests/analytics/fixtures/golden")


def test_align_benchmark_series_uses_timestamp_intersection() -> None:
    """Only matching UTC timestamps enter benchmark calculations."""
    logger.debug("Testing Analytics benchmark timestamp intersection")
    strategy = (
        {"timestamp": NOW, "value": 0.1},
        {"timestamp": NOW.replace(day=20), "value": 0.2},
    )
    benchmark = ({"timestamp": NOW.replace(day=20), "value": 0.3},)
    assert align_benchmark_series(strategy, benchmark) == ((0.2,), (0.3,))


def test_benchmark_zero_variance_is_undefined() -> None:
    """A constant benchmark yields explicit undefined relative evidence."""
    logger.debug("Testing Analytics zero-variance benchmark")
    config = replace(
        _config(),
        risk_free_rate=RiskFreeRateEvidence(
            rate=Decimal(0),
            unit="annual_decimal",
            source="unit-test",
            as_of=NOW,
        ),
    )
    start = NOW.replace(day=18)
    bars = (
        build_ohlcv_record(
            timestamp=start,
            source="unit-test",
            source_symbol="BENCH",
            available_at=NOW,
            open=Decimal(100),
            high=Decimal(100),
            low=Decimal(100),
            close=Decimal(100),
            volume=Decimal(1),
            price_unit="index_points",
            volume_unit="contracts",
        ),
        build_ohlcv_record(
            timestamp=NOW,
            source="unit-test",
            source_symbol="BENCH",
            available_at=NOW,
            open=Decimal(100),
            high=Decimal(101),
            low=Decimal(100),
            close=Decimal(101),
            volume=Decimal(1),
            price_unit="index_points",
            volume_unit="contracts",
        ),
    )
    benchmark = build_market_dataset(
        normalization_version="v1",
        data_kind="bars",
        symbol="BENCH",
        timeframe="1d",
        records=bars,
        start=start,
        end=NOW,
        available_at=NOW,
        record_count=2,
        quality_report=build_data_quality_report(
            quality_status="perfect",
            quality_decision="accepted",
            quality_score=Decimal(100),
            record_count=2,
            checked_count=2,
            truncated=False,
            sample_limit=10,
            schema_version="v1",
            generated_at=NOW,
        ),
        source_metadata={"source": "unit-test"},
        license_metadata={"status": "approved"},
        cache_status="miss",
        workflow_context="backtest",
        precision_policy="decimal_string",
        request_id=generate_id("req"),
    )
    result = adapt_trading_result(
        _source(),
        source_contract="simulation.result",
        initial_balance=Decimal(1000),
        account_currency="USD",
        config=config,
        benchmark=benchmark,
    )
    section = calculate_benchmark_evidence(result, config=config)
    metrics = {item.metric_key: item for item in section.metrics}
    for metric_key, metric in metrics.items():
        fixture = json.loads(
            (_GOLDEN_DIRECTORY / f"{metric_key}.json").read_text(encoding="utf-8")
        )
        assert metric.status == fixture["expected_status"]
        assert metric.value == fixture["expected_value"]
