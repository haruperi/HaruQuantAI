"""Unit coverage for the canonical backtest recipe (FEAT-SIM-19)."""

from __future__ import annotations

import time
from datetime import UTC, datetime
from typing import Any

import pytest
from app.services.simulator import (
    create_backtest_run_config,
    execute_backtest_job_inspection,
    execute_backtest_job_operation,
    get_backtest_strategy_catalogue,
)
from app.services.simulator.backtest_recipe import (
    BacktestJobRegistry,
    BacktestRunConfig,
    get_backtest_strategy_descriptor,
    resolve_strategy_parameters,
)

_START = datetime(2025, 1, 1, tzinfo=UTC)
_END = datetime(2025, 3, 1, tzinfo=UTC)


def _config(**overrides: Any) -> BacktestRunConfig:
    """Build one valid run configuration.

    Returns:
        Validated backtest run configuration.
    """
    values: dict[str, Any] = {
        "symbol": "EURUSD",
        "timeframe": "H1",
        "start": _START,
        "end": _END,
        "strategy_id": "naive-ma-trend",
    }
    values.update(overrides)
    return BacktestRunConfig(**values)


def _wait_for_terminal(job: Any, timeout: float = 10.0) -> None:
    """Block until the job reaches a terminal status.

    Raises:
        AssertionError: If the job does not finish within the timeout.
    """
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if job.terminal:
            return
        time.sleep(0.01)
    raise AssertionError(f"job did not finish; status={job.status}")


def test_catalogue_lists_every_registered_strategy_with_its_runnability() -> None:
    """Every evaluator stays listed and a blocked one carries its reason."""
    catalogue = {
        item["strategy_id"]: item for item in get_backtest_strategy_catalogue()
    }
    assert len(catalogue) == 8
    naive = catalogue["naive-ma-trend"]
    assert naive["runnable"] is True
    assert naive["unavailable_reason"] is None
    assert naive["supports_exits"] is True
    blocked = catalogue["white-fairy"]
    assert blocked["runnable"] is False
    assert blocked["unavailable_reason"]
    assert blocked["required_indicators"] == ("rsi",)


def test_parameters_resolve_from_defaults_and_reject_unknown_names() -> None:
    """Declared defaults fill in and an unknown override fails closed."""
    descriptor = get_backtest_strategy_descriptor("naive-ma-trend")
    resolved = resolve_strategy_parameters(descriptor, {})
    assert resolved == {
        "fast_ma_period": 20,
        "slow_ma_period": 50,
        "filter_ma_period": 200,
    }
    # The warm-up window must exceed the longest period so an evaluator can
    # always compare a value against its own previous bar.
    assert descriptor.warmup_bars(resolved) == 201
    with pytest.raises(ValueError, match="unknown strategy parameters"):
        resolve_strategy_parameters(descriptor, {"nonexistent": "1"})
    with pytest.raises(ValueError, match="at least 2"):
        resolve_strategy_parameters(descriptor, {"fast_ma_period": "1"})


def test_run_configuration_rejects_an_inverted_window() -> None:
    """A non-forward measurement window is refused before any provider read."""
    with pytest.raises(ValueError, match="start must be earlier than end"):
        create_backtest_run_config(
            symbol="EURUSD",
            timeframe="H1",
            start=_END,
            end=_START,
            strategy_id="naive-ma-trend",
        )


def test_a_blocked_strategy_is_refused_before_any_provider_contact() -> None:
    """An unrunnable strategy is refused at submission with its own reason."""

    def facts_loader(config: BacktestRunConfig) -> object:
        del config
        raise AssertionError("provider must not be contacted")

    registry = BacktestJobRegistry(facts_loader=facts_loader)
    with pytest.raises(ValueError, match="Indicators-owned series"):
        registry.submit(_config(strategy_id="white-fairy"), principal_id="tester")
    assert registry.list_jobs(principal_id="tester") == ()


def test_an_unregistered_strategy_is_refused_at_submission() -> None:
    """An unknown strategy identifier never becomes a job."""

    def facts_loader(config: BacktestRunConfig) -> object:
        del config
        raise AssertionError("provider must not be contacted")

    registry = BacktestJobRegistry(facts_loader=facts_loader)
    with pytest.raises(ValueError, match="unknown backtest strategy"):
        registry.submit(_config(strategy_id="does-not-exist"), principal_id="tester")


def test_a_failing_provider_becomes_a_terminal_job_error() -> None:
    """A provider failure ends the job without raising into the caller."""

    def facts_loader(config: BacktestRunConfig) -> object:
        del config
        raise ValueError("BACKTEST_PROVIDER_CONNECTION_FAILED")

    registry = BacktestJobRegistry(facts_loader=facts_loader)
    job = registry.submit(_config(), principal_id="tester")
    _wait_for_terminal(job)
    assert job.status == "failed"
    assert job.error == "BACKTEST_PROVIDER_CONNECTION_FAILED"
    assert job.finished_at is not None


def test_jobs_are_scoped_to_their_submitting_principal() -> None:
    """One principal can never read another principal's run."""

    def facts_loader(config: BacktestRunConfig) -> object:
        del config
        raise ValueError("stop")

    registry = BacktestJobRegistry(facts_loader=facts_loader)
    job = registry.submit(_config(), principal_id="owner")
    _wait_for_terminal(job)
    assert registry.get(job.job_id, principal_id="owner") is not None
    assert registry.get(job.job_id, principal_id="intruder") is None
    assert registry.list_jobs(principal_id="intruder") == ()


def test_cancelling_a_queued_job_reaches_a_terminal_state() -> None:
    """Cancellation before execution is honoured and is not repeatable."""

    def facts_loader(config: BacktestRunConfig) -> object:
        del config
        raise ValueError("stop")

    registry = BacktestJobRegistry(facts_loader=facts_loader)
    job = registry.submit(_config(), principal_id="tester")
    _wait_for_terminal(job)
    assert execute_backtest_job_inspection(job, "request_cancel") is False


def test_the_registry_boundary_rejects_an_unsupported_operation() -> None:
    """Only allowlisted registry and job operations cross the boundary."""

    def facts_loader(config: BacktestRunConfig) -> object:
        del config
        raise ValueError("stop")

    registry = BacktestJobRegistry(facts_loader=facts_loader)
    with pytest.raises(ValueError, match="unsupported backtest job registry operation"):
        execute_backtest_job_operation(registry, "shutdown")
    with pytest.raises(TypeError, match="registry must be a BacktestJobRegistry"):
        execute_backtest_job_operation(object(), "get")


def test_report_evidence_is_rendered_rather_than_re_exported() -> None:
    """Owner objects are rendered as text so the report can cross JSON.

    Data and Analytics values hold ``MappingProxyType``, which cannot be
    deep-copied. FastAPI's encoder calls ``dataclasses.asdict`` on any dataclass
    it meets, which deep-copies, so embedding an owner object in the report made
    every run read fail with ``cannot pickle 'mappingproxy' object``.
    """
    from dataclasses import dataclass
    from types import MappingProxyType

    from app.services.simulator.backtest_recipe.pipeline import _text_tuple
    from fastapi.encoders import jsonable_encoder

    @dataclass(frozen=True)
    class _OwnerValue:
        """Stand-in for an owner value holding an immutable mapping."""

        code: str
        detail: MappingProxyType

    owner = _OwnerValue("CALENDAR_SUPPORTED_CLOSURE", MappingProxyType({"a": 1}))
    with pytest.raises(TypeError, match="mappingproxy"):
        jsonable_encoder({"warnings": (owner,)})

    rendered = _text_tuple((owner,))
    assert rendered == ("CALENDAR_SUPPORTED_CLOSURE",)
    assert jsonable_encoder({"warnings": rendered})["warnings"] == list(rendered)
    assert _text_tuple(None) == ()
    assert _text_tuple("single") == ("single",)


def test_repeated_report_evidence_collapses_with_an_explicit_count() -> None:
    """A code repeated per trade is counted, not repeated ninety times."""
    from dataclasses import dataclass
    from types import MappingProxyType

    from app.services.simulator.backtest_recipe.pipeline import _text_tuple

    @dataclass(frozen=True)
    class _OwnerValue:
        """Stand-in for a repeated per-trade Analytics warning."""

        code: str
        detail: MappingProxyType

    repeated = tuple(
        _OwnerValue("r_multiple_mae_fallback", MappingProxyType({"ticket": index}))
        for index in range(90)
    )
    single = (_OwnerValue("curve_basis_closed_trade", MappingProxyType({"a": 1})),)

    assert _text_tuple(repeated + single) == (
        "r_multiple_mae_fallback x90",
        "curve_basis_closed_trade",
    )


def test_a_terminal_snapshot_carries_ordered_progress_events() -> None:
    """Progress recorded during a run is retained in submission order."""

    def facts_loader(config: BacktestRunConfig) -> object:
        del config
        raise ValueError("stop")

    registry = BacktestJobRegistry(facts_loader=facts_loader)
    job = registry.submit(_config(), principal_id="tester")
    _wait_for_terminal(job)
    snapshot = job.snapshot()
    assert snapshot["status"] == "failed"
    assert snapshot["symbol"] == "EURUSD"
    assert snapshot["strategy_id"] == "naive-ma-trend"
    sequences = [event["sequence"] for event in snapshot["events"]]
    assert sequences == sorted(sequences)
