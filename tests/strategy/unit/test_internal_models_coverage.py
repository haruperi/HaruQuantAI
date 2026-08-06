"""Unit test coverage for internal Strategy persistence models and protocol default methods."""

from datetime import UTC, datetime

import pytest
from app.services.strategy.contracts.factories import create_strategy_signal
from app.services.strategy.event.state import _StrategyRuntimeState
from app.services.strategy.registry.models import (
    _StrategyBootstrapSummary,
    _StrategyConfigRecord,
    _StrategyDefinition,
)
from app.services.strategy.signals.protocol import SignalEvaluator
from app.services.strategy.signals.records import _StrategySignalRecord


def test_strategy_runtime_state_model() -> None:
    """Verify _StrategyRuntimeState model construction and fields.

    Returns:
        None.
    """
    now = datetime.now(UTC)
    state = _StrategyRuntimeState(
        config_id="cfg-1",
        state_version=1,
        evaluation_status="ready",
        bars_processed=10,
        last_evidence_at=now,
        last_signal_id="sig-1",
        local_state={"key": "val"},
        local_state_hash="a" * 64,
        request_id="req-1",
        correlation_id="cor-1",
        created_at=now,
        updated_at=now,
    )
    assert state.config_id == "cfg-1"
    assert state.state_version == 1
    assert state.evaluation_status == "ready"


def test_strategy_registry_models() -> None:
    """Verify registry internal models construction.

    Returns:
        None.
    """
    now = datetime.now(UTC)
    definition = _StrategyDefinition(
        strategy_id="strat-1",
        evaluator_key="eval-1",
        strategy_code="code-1",
        display_name="Strat 1",
        strategy_class="trend",
        owner_ref="owner-1",
        description="desc",
        lifecycle_status="active",
        created_at=now,
        updated_at=now,
    )
    assert definition.strategy_id == "strat-1"

    config_rec = _StrategyConfigRecord(
        config_id="cfg-1",
        version_id="ver-1",
        strategy_id="strat-1",
        strategy_version="1.0.0",
        config_hash="b" * 64,
        config_schema_version="v1",
        config_json="{}",
        policy_version="v1",
        runtime_profile="RESEARCH",
        lifecycle_status="active",
        request_id="req-1",
        correlation_id="cor-1",
        created_at=now,
    )
    assert config_rec.config_id == "cfg-1"

    summary = _StrategyBootstrapSummary(
        bootstrap_status="ok",
        registered_strategies=7,
        configured_strategies=7,
        descriptors=(),
    )
    assert summary.registered_strategies == 7


def test_signal_evaluator_protocol_not_implemented() -> None:
    """Verify SignalEvaluator protocol raises NotImplementedError on direct call.

    Returns:
        None.
    """

    class _DummyEvaluator(SignalEvaluator):
        strategy_id = "test"
        strategy_version = "1.0.0"
        module_path = "test"
        source_hash = "a" * 64
        artifact_hash = "a" * 64
        dependency_hash = "a" * 64

    evaluator = _DummyEvaluator()
    with pytest.raises(NotImplementedError):
        SignalEvaluator.evaluate_signals(evaluator, None, (), None, None)  # type: ignore[arg-type]


def test_strategy_signal_record_model() -> None:
    """Verify _StrategySignalRecord model construction.

    Returns:
        None.
    """
    now = datetime.now(UTC)
    signal = create_strategy_signal(
        signal_id="c" * 64,
        signal_name="LONG_ENTRY",
        strategy_id="strat-1",
        strategy_version="1.0.0",
        symbol="EURUSD",
        side="BUY",
        active=True,
        timestamp=now,
        lineage={"config_hash": "c" * 64},
        facts={},
    )
    from app.services.strategy.contracts import StrategySignal

    _StrategySignalRecord.model_rebuild(
        _types_namespace={"StrategySignal": StrategySignal}
    )
    record = _StrategySignalRecord(
        signal=signal,
        config_id="cfg-1",
        sequence=1,
        intent_id="int-1",
        publication_status="generated",
        risk_submission_ref=None,
        request_id="req-1",
        correlation_id="cor-1",
        created_at=now,
        updated_at=now,
    )
    assert record.signal.signal_id == "c" * 64
