"""Tests for analytics contracts models and schema validation."""

from __future__ import annotations

import pytest
from app.services.analytics.contracts.models import (
    AnalyticsReport,
    AnalyticsWarning,
    BenchmarkData,
    DashboardPayload,
    ErrorPayload,
    Lineage,
    PortfolioAnalyticsReport,
    QualityFlag,
    ReproducibilityHashes,
    SchemaCompatibilityMatrix,
    ToolEnvelope,
    TradingResult,
    TruncationMetadata,
    validate_schema_version,
)
from app.utils.errors import ValidationError


def test_lineage_instantiation() -> None:
    """Test Lineage model properties and default factory values."""
    lin = Lineage(
        run_id="run-123",
        strategy_id="strat-xyz",
        dataset_hash="hash-abc",
        cost_model="standard-costs",
        fill_model="standard-fills",
        risk_policy_version="1.0",
        journal_reference="journal-ref-1",
        source_metadata={"custom_key": "custom_val"},
    )
    assert lin.run_id == "run-123"
    assert lin.strategy_id == "strat-xyz"
    assert lin.dataset_hash == "hash-abc"
    assert lin.cost_model == "standard-costs"
    assert lin.fill_model == "standard-fills"
    assert lin.risk_policy_version == "1.0"
    assert lin.journal_reference == "journal-ref-1"
    assert lin.source_metadata == {"custom_key": "custom_val"}

    # Test defaults
    default_lin = Lineage()
    assert default_lin.run_id is None
    assert default_lin.source_metadata == {}


def test_benchmark_data_instantiation() -> None:
    """Test BenchmarkData fields and defaults."""
    timestamps = (
        "2026-01-01T00:00:00Z",
        "2026-01-02T00:00:00Z",
        "2026-01-03T00:00:00Z",
    )
    bench = BenchmarkData(
        symbol="SPY",
        prices=(100.0, 101.5, 102.0),
        returns=(0.0, 0.015, 0.005),
        timestamps=timestamps,
        metadata={"source": "provider-a"},
    )
    assert bench.symbol == "SPY"
    assert bench.prices == (100.0, 101.5, 102.0)
    assert bench.returns == (0.0, 0.015, 0.005)
    assert bench.timestamps == timestamps
    assert bench.metadata == {"source": "provider-a"}


def test_trading_result_instantiation() -> None:
    """Test TradingResult model properties and nested dependencies."""
    result = TradingResult(
        schema_version="1.3.1",
        result_id="res-1",
        environment="backtest",
        account_base_currency="USD",
        trades=({"id": "t1", "pnl": 100.0},),
        equity_curve=({"time": "2026-01-01T00:00:00Z", "value": 10000.0},),
        benchmark=BenchmarkData(symbol="QQQ"),
        lineage=Lineage(run_id="run-1"),
    )
    assert result.schema_version == "1.3.1"
    assert result.result_id == "res-1"
    assert result.environment == "backtest"
    assert result.account_base_currency == "USD"
    assert len(result.trades) == 1
    assert len(result.equity_curve) == 1
    assert result.benchmark is not None
    assert result.benchmark.symbol == "QQQ"
    assert result.lineage.run_id == "run-1"


def test_reproducibility_hashes_instantiation() -> None:
    """Test ReproducibilityHashes model fields."""
    hashes = ReproducibilityHashes(
        input_hash="ihash123",
        config_hash="chash456",
        report_hash="rhash789",
    )
    assert hashes.input_hash == "ihash123"
    assert hashes.config_hash == "chash456"
    assert hashes.report_hash == "rhash789"


def test_warnings_and_quality_flags_instantiation() -> None:
    """Test AnalyticsWarning and QualityFlag fields."""
    warning = AnalyticsWarning(
        code="LOW_SAMPLE_SIZE",
        severity="warning",
        affected_section="trade_metrics",
        source_context="Trade count is 15, minimum required is 30.",
        detail={"count": 15},
    )
    assert warning.code == "LOW_SAMPLE_SIZE"
    assert warning.severity == "warning"
    assert warning.affected_section == "trade_metrics"
    assert warning.source_context == "Trade count is 15, minimum required is 30."
    assert warning.detail == {"count": 15}

    flag = QualityFlag(
        code="UNSTABLE_CURVE",
        severity="major",
        affected_section="equity_metrics",
        source_context="R-squared is negative.",
        detail={"r2": -0.1},
    )
    assert flag.code == "UNSTABLE_CURVE"
    assert flag.severity == "major"
    assert flag.affected_section == "equity_metrics"
    assert flag.source_context == "R-squared is negative."
    assert flag.detail == {"r2": -0.1}


def test_analytics_report_instantiation() -> None:
    """Test AnalyticsReport fields and defaults."""
    warn = AnalyticsWarning(
        code="WARN_A", severity="warning", affected_section="drawdown"
    )
    q_flag = QualityFlag(
        code="FLAG_A", severity="informational", affected_section="ratios"
    )
    report = AnalyticsReport(
        schema_version="1.3.1",
        report_id="rep-123",
        report_status="completed",
        sections={"summary": {"total_profit": 500.0}},
        warnings=(warn,),
        quality_flags=(q_flag,),
        lineage=Lineage(run_id="run-123"),
        hashes=ReproducibilityHashes(report_hash="hash-rep"),
    )
    assert report.schema_version == "1.3.1"
    assert report.report_id == "rep-123"
    assert report.report_status == "completed"
    assert report.sections == {"summary": {"total_profit": 500.0}}
    assert len(report.warnings) == 1
    assert report.warnings[0].code == "WARN_A"
    assert len(report.quality_flags) == 1
    assert report.quality_flags[0].code == "FLAG_A"
    assert report.lineage.run_id == "run-123"
    assert report.hashes.report_hash == "hash-rep"


def test_portfolio_analytics_report_instantiation() -> None:
    """Test PortfolioAnalyticsReport fields and defaults."""
    report = PortfolioAnalyticsReport(
        schema_version="1.3.1",
        portfolio_run_id="port-run-123",
        account_base_currency="EUR",
        component_count=5,
        aggregate_metrics={"total_return": 12.5},
        warnings=(),
        lineage=Lineage(run_id="port-run-123"),
    )
    assert report.schema_version == "1.3.1"
    assert report.portfolio_run_id == "port-run-123"
    assert report.account_base_currency == "EUR"
    assert report.component_count == 5
    assert report.aggregate_metrics == {"total_return": 12.5}
    assert len(report.warnings) == 0
    assert report.lineage.run_id == "port-run-123"


def test_dashboard_payload_instantiation() -> None:
    """Test DashboardPayload and TruncationMetadata fields."""
    meta = TruncationMetadata(
        truncated=True,
        original_point_count=1200,
        returned_point_count=500,
        truncation_method="lttb",
        truncation_reason="configured size limits reached",
    )
    assert meta.truncated is True
    assert meta.original_point_count == 1200
    assert meta.returned_point_count == 500
    assert meta.truncation_method == "lttb"
    assert meta.truncation_reason == "configured size limits reached"

    payload = DashboardPayload(
        schema_version="1.3.1",
        charts={"equity": [1, 2, 3]},
        tables={"summary": [{"metric": "Sharpe", "value": 1.8}]},
        truncation=meta,
    )
    assert payload.schema_version == "1.3.1"
    assert payload.charts == {"equity": [1, 2, 3]}
    assert payload.tables == {"summary": [{"metric": "Sharpe", "value": 1.8}]}
    assert payload.truncation.truncated is True


def test_tool_envelope_instantiation() -> None:
    """Test ToolEnvelope and ErrorPayload fields."""
    err = ErrorPayload(
        code="INVALID_INPUT",
        message="Missing trades field.",
        details={"field": "trades"},
    )
    assert err.code == "INVALID_INPUT"
    assert err.message == "Missing trades field."
    assert err.details == {"field": "trades"}

    envelope = ToolEnvelope(
        schema_version="1.3.1",
        status="success",
        message="Analytics overview generated successfully.",
        data={"some_key": "some_value"},
        error=None,
        metadata={"request_id": "req-1"},
    )
    assert envelope.schema_version == "1.3.1"
    assert envelope.status == "success"
    assert envelope.message == "Analytics overview generated successfully."
    assert envelope.data == {"some_key": "some_value"}
    assert envelope.error is None
    assert envelope.metadata == {"request_id": "req-1"}


def test_validate_schema_version_success() -> None:
    """Test validate_schema_version with direct matches."""
    matrix: SchemaCompatibilityMatrix = {
        "1.0.0": "legacy_adapted",
        "1.1.0": "legacy_adapted",
        "1.2.0": "deprecated",
        "1.3.1": "accepted",
        "2.0.0": "unsupported_future",
    }
    assert validate_schema_version("1.3.1", matrix) == "accepted"
    assert validate_schema_version("1.2.0", matrix) == "deprecated"


def test_validate_schema_version_prefix_fallback() -> None:
    """Test validate_schema_version prefix matching (major.minor fallback)."""
    matrix: SchemaCompatibilityMatrix = {
        "1.0.0": "legacy_adapted",
        "1.3.1": "accepted",
    }
    # 1.3.2 is not in matrix, but starts with 1.3
    assert validate_schema_version("1.3.2", matrix) == "legacy_adapted"


def test_validate_schema_version_explicit_rejections() -> None:
    """Test validate raises ValidationError for rejected/future versions."""
    matrix: SchemaCompatibilityMatrix = {
        "1.2.0": "rejected",
        "2.0.0": "unsupported_future",
        "1.3.1": "accepted",
    }
    with pytest.raises(ValidationError) as exc_info:
        validate_schema_version("1.2.0", matrix)
    assert "explicitly rejected" in str(exc_info.value)

    with pytest.raises(ValidationError) as exc_info:
        validate_schema_version("2.0.0", matrix)
    assert "future version not yet supported" in str(exc_info.value)


def test_validate_schema_version_unsupported() -> None:
    """Test validate raises ValidationError for completely unknown versions."""
    matrix: SchemaCompatibilityMatrix = {
        "1.3.1": "accepted",
    }
    with pytest.raises(ValidationError) as exc_info:
        validate_schema_version("3.0.0", matrix)
    assert "Unsupported schema version" in str(exc_info.value)
