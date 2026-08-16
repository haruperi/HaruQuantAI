"""Tests for Optimization execution contracts."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from app.services.optimization.execution import (
    BacktestExecutionAdapter,
    BacktestExecutionContext,
    BacktestExecutionRequest,
    EngineOptimizationResult,
)
from pydantic import ValidationError

from tests.analytics._support import _report


def execution_context() -> BacktestExecutionContext:
    """Build complete Simulation request provenance."""
    return BacktestExecutionContext(
        strategy_id="strategy-1",
        strategy_version="v1",
        strategy_config_ref="strategy-config",
        strategy_config_hash="a" * 64,
        data_ref="dataset",
        data_version="v1",
        data_hash="b" * 64,
        tick_generation_ref="tick-profile",
        tick_generation_version="v1",
        tick_generation_hash="c" * 64,
        execution_profile_ref="execution-profile",
        execution_profile_version="v1",
        execution_profile_hash="d" * 64,
        risk_policy_ref="risk-policy",
        risk_policy_version="v1",
        risk_policy_hash="e" * 64,
        symbol="EURUSD",
        timeframe="M1",
        start=datetime(2025, 1, 1, tzinfo=UTC),
        end=datetime(2025, 1, 2, tzinfo=UTC),
        initial_balance=Decimal(10_000),
        account_currency="USD",
        runtime_profile="simulation",
        canonical=True,
        cost_model_hash="f" * 64,
        realism_hash="1" * 64,
        objective_hash="2" * 64,
        engine_type="event_driven",
        engine_version="v1",
        module_version="v1",
        execution_model_ref="execution-model-v1",
        execution_model_hash="3" * 64,
        calculation_model_hash="4" * 64,
        calculation_artifact_checksum="5" * 64,
        calibration_artifact_checksum="6" * 64,
        realism_stream_identity_hash="7" * 64,
        source_lineage_hash="8" * 64,
        tick_lineage_hash="9" * 64,
        market_evidence_class="genuine_bid_ask_ticks",
        market_evidence_eligible=True,
        required_clock_edges=(),
        evidenced_clock_edges=(),
        provider_specification_revisions=(
            {
                "revision_id": "revision-1",
                "checksum": "a" * 64,
                "provider": "mt5",
                "server": "demo-server",
                "environment": "demo",
                "account_digest": "b" * 64,
                "symbol": "EURUSD",
                "observed_at": datetime(2025, 1, 1, tzinfo=UTC),
                "effective_from": datetime(2025, 1, 1, tzinfo=UTC),
                "effective_to": None,
                "historical_provenance": None,
            },
        ),
        initial_authority_state_hash="c" * 64,
        certification_target="demo",
        close_open_positions_at_end=True,
    )


def execution_request() -> BacktestExecutionRequest:
    """Build a complete candidate execution request."""
    return BacktestExecutionRequest(
        candidate_hash="9" * 64,
        executable_parameters={"period": 14},
        seed=7,
        request_id="req-aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
        workflow_id="wf-bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
        correlation_id="cor-cccccccc-cccc-4ccc-8ccc-cccccccccccc",
        context=execution_context(),
    )


def test_execution_context_rejects_non_utc_window() -> None:
    """Execution times must be ordered and UTC."""
    payload = execution_context().model_dump(mode="python")
    payload["end"] = datetime(2025, 1, 1, tzinfo=UTC) - timedelta(seconds=1)
    with pytest.raises(ValidationError, match="ordered UTC"):
        BacktestExecutionContext.model_validate(payload)


def test_execution_request_carries_all_simulation_provenance() -> None:
    """Candidate requests include complete immutable context."""
    assert execution_request().context.risk_policy_hash == "e" * 64


def test_execution_request_rejects_missing_provenance() -> None:
    """Blank required invariant provenance fails before adapter invocation."""
    payload = execution_context().model_dump(mode="python")
    payload["data_ref"] = ""
    with pytest.raises(ValidationError, match="non-empty"):
        BacktestExecutionContext.model_validate(payload)


def test_adapter_protocol_contract() -> None:
    """The receiver-owned port declares exactly one execution method."""
    assert callable(BacktestExecutionAdapter.__dict__["execute"])
    assert "contract_version" in BacktestExecutionAdapter.__annotations__


def test_engine_result_rejects_inconsistent_candidate_hash() -> None:
    """Malformed candidate identity cannot enter measured result evidence."""
    report, _ = _report()
    with pytest.raises(ValidationError, match="hashes"):
        EngineOptimizationResult(
            candidate_hash="bad",
            simulation_run_id="run-1",
            simulation_request_hash="a" * 64,
            analytics_report=report,
            runtime_ms=1.0,
            engine_type="event_driven",
            engine_version="v1",
        )
