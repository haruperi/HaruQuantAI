"""Unit tests for all-or-nothing portfolio simulation."""

from collections.abc import Mapping
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

import pytest
from app.services.simulator.errors import SimulationError
from app.services.simulator.run import (
    PortfolioBacktestRequestV1,
    PortfolioComponentRequest,
    run_portfolio_backtest,
)
from app.utils import AuthContext, canonical_digest

from tests.simulator.unit.test_orchestrator import (
    FakeDependencies,
    _auth,
    _dataset,
    _fx_evidence,
    _request,
)


def _portfolio_request() -> PortfolioBacktestRequestV1:
    """Build a one-component reconciled portfolio request."""
    dataset = _dataset("req-66666666-6666-4666-8666-666666666666")
    child = _request(dataset, suffix="6")
    component = PortfolioComponentRequest(
        component_id="component-1",
        capital_weight=Decimal(1),
        risk_budget=Decimal(100),
        risk_decision_id="risk-1",
        metrics_ref="metrics-1",
        backtest_request=child,
    )
    fx_evidence = _fx_evidence(dataset)
    payload: dict[str, object] = {
        "request_id": "req-77777777-7777-4777-8777-777777777777",
        "workflow_id": "wf-77777777-7777-4777-8777-777777777777",
        "correlation_id": "cor-77777777-7777-4777-8777-777777777777",
        "portfolio_id": "portfolio",
        "construction_result_id": "construction",
        "construction_version": "v1",
        "components": (component.model_dump(mode="python", warnings=False),),
        "measurement_start": dataset.start,
        "measurement_end": dataset.start + timedelta(days=30),
        "base_currency": "USD",
        "fx_evidence_ids": ("fx-1",),
        "fx_evidence_versions": (fx_evidence.contract_version,),
        "fx_evidence_hashes": (
            canonical_digest(fx_evidence.model_dump(mode="python", warnings=False)),
        ),
        "execution_profile_version": "v1",
        "risk_policy_version": "v1",
        "seed": 7,
        "initial_balance": Decimal(10_000),
        "runtime_profile": "simulation",
        "execution_route": "sim",
    }
    payload["config_hash"] = PortfolioBacktestRequestV1.calculate_config_hash(payload)
    return PortfolioBacktestRequestV1.model_validate(payload)


def _portfolio_auth(request: PortfolioBacktestRequestV1) -> AuthContext:
    """Build matching portfolio authentication evidence."""
    child_auth = _auth(request.components[0].backtest_request)
    return child_auth.model_copy(
        update={
            "request_id": request.request_id,
            "workflow_id": request.workflow_id,
            "correlation_id": request.correlation_id,
        }
    )


def test_portfolio_run_fails_closed_on_incomplete_component(tmp_path: Path) -> None:
    """Map any component failure to an incomplete aggregate failure."""
    request = _portfolio_request()
    dataset = _dataset("req-66666666-6666-4666-8666-666666666666")
    dependencies = FakeDependencies(tmp_path, dataset)

    def fail_load(request_value: object) -> object:
        """Inject a controlled component failure."""
        del request_value
        raise SimulationError("SIM_DATA_STALE", "Injected stale evidence")

    dependencies.load_market_data = fail_load  # type: ignore[method-assign]
    with pytest.raises(SimulationError) as captured:
        run_portfolio_backtest(
            request,
            _portfolio_auth(request),
            dependencies,  # type: ignore[arg-type]
        )
    assert captured.value.code == "SIM_COMPONENT_INCOMPLETE"


def test_portfolio_run_fails_closed_on_unreconciled_aggregate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Reject an aggregate whose arithmetic does not match the components."""
    import app.services.simulator.run.portfolio as portfolio_module

    request = _portfolio_request()
    dataset = _dataset("req-66666666-6666-4666-8666-666666666666")
    dependencies = FakeDependencies(tmp_path, dataset)
    original = portfolio_module._reconcile

    def drifting_reconcile(
        request_value: object,
        results: object,
        aggregate_net_profit: Decimal,
    ) -> object:
        """Inject an aggregate total that disagrees with the components."""
        return original(
            request_value,  # type: ignore[arg-type]
            results,  # type: ignore[arg-type]
            aggregate_net_profit + Decimal(1),
        )

    monkeypatch.setattr(portfolio_module, "_reconcile", drifting_reconcile)
    with pytest.raises(SimulationError) as captured:
        run_portfolio_backtest(
            request,
            _portfolio_auth(request),
            dependencies,  # type: ignore[arg-type]
        )
    assert captured.value.code == "SIM_AGGREGATE_UNRECONCILED"


def test_portfolio_run_fails_closed_on_unresolvable_fx(tmp_path: Path) -> None:
    """Fail the whole run closed when referenced FX evidence is missing."""
    request = _portfolio_request()
    dataset = _dataset("req-66666666-6666-4666-8666-666666666666")
    dependencies = FakeDependencies(tmp_path, dataset)

    def empty_fx(evidence_ids: tuple[str, ...]) -> Mapping[str, object]:
        """Return no evidence for any requested identifier."""
        del evidence_ids
        return {}

    dependencies.resolve_fx_evidence = empty_fx  # type: ignore[method-assign]
    with pytest.raises(SimulationError) as captured:
        run_portfolio_backtest(
            request,
            _portfolio_auth(request),
            dependencies,  # type: ignore[arg-type]
        )
    assert captured.value.code == "SIM_FX_EVIDENCE_UNAVAILABLE"


def test_portfolio_return_series_is_measured_not_supplied(tmp_path: Path) -> None:
    """Derive return evidence from the component's own simulated equity."""
    request = _portfolio_request()
    dataset = _dataset("req-66666666-6666-4666-8666-666666666666")
    dependencies = FakeDependencies(tmp_path, dataset)
    result = run_portfolio_backtest(
        request,
        _portfolio_auth(request),
        dependencies,  # type: ignore[arg-type]
    )
    series = result.component_return_series[0]
    component_row = result.component_results[0]
    assert series.simulation_result_id == component_row.simulation_result_id
    assert len(series.observations) == 30
    timestamps = tuple(item.timestamp for item in series.observations)
    assert timestamps == tuple(sorted(set(timestamps)))
    assert all(
        request.measurement_start <= value <= request.measurement_end
        for value in timestamps
    )
    assert all(row.reconciled for row in result.component_results)
    assert (dependencies.artifact_root / result.aggregate_metrics_ref).is_file()
    assert result.component_results[0].account_currency == request.base_currency
    assert any(
        observation.return_value != Decimal(0) for observation in series.observations
    )


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        ("fx_evidence_versions", ("v2",)),
        ("fx_evidence_hashes", ("F" * 64,)),
    ],
)
def test_portfolio_request_rejects_invalid_fx_identity_bindings(
    field: str,
    replacement: tuple[str, ...],
) -> None:
    """Reject malformed FX version or hash bindings before provider access."""
    request = _portfolio_request()
    payload = request.model_dump(mode="python", warnings=False)
    payload[field] = replacement
    payload["config_hash"] = PortfolioBacktestRequestV1.calculate_config_hash(payload)

    with pytest.raises(ValueError, match="FX evidence"):
        PortfolioBacktestRequestV1.model_validate(payload)


def test_portfolio_run_rejects_resolved_fx_hash_mismatch(tmp_path: Path) -> None:
    """Bind resolved Data evidence to the exact request-declared digest."""
    request = _portfolio_request()
    dataset = _dataset("req-66666666-6666-4666-8666-666666666666")
    dependencies = FakeDependencies(tmp_path, dataset)
    replacement = _fx_evidence(dataset).model_copy(
        update={"path_policy_id": "different-policy"}
    )

    def mismatched_fx(evidence_ids: tuple[str, ...]) -> Mapping[str, object]:
        return dict.fromkeys(evidence_ids, replacement)

    dependencies.resolve_fx_evidence = mismatched_fx  # type: ignore[method-assign]
    with pytest.raises(SimulationError) as captured:
        run_portfolio_backtest(
            request,
            _portfolio_auth(request),
            dependencies,  # type: ignore[arg-type]
        )

    assert captured.value.code == "SIM_FX_EVIDENCE_UNAVAILABLE"
