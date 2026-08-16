"""Unit tests for exact Simulation request contracts."""

from datetime import timedelta
from decimal import Decimal

import pytest
from app.services.simulator.errors import unwrap_simulation_response
from app.services.simulator.reporting import ReturnObservation
from app.services.simulator.run import (
    PortfolioBacktestRequest,
    PortfolioComponentRequest,
)
from app.utils import canonical_digest
from pydantic import ValidationError

from tests.simulator.component.test_orchestrator import _dataset, _fx_evidence, _request


def test_request_matches_project_section_5_exactly() -> None:
    """Forbid unknown request material and preserve exact identity fields."""
    dataset = _dataset("req-55555555-5555-4555-8555-555555555555")
    request = _request(dataset)
    payload = request.model_dump(mode="python", warnings=False) | {"raw_code": "unsafe"}
    with pytest.raises(ValidationError, match="extra"):
        type(request).model_validate(payload)


def test_portfolio_request_is_self_contained() -> None:
    """Accept only Simulation-owned immutable component projections."""
    dataset = _dataset("req-66666666-6666-4666-8666-666666666666")
    child = _request(dataset, suffix="6")
    observations = tuple(
        ReturnObservation(
            timestamp=dataset.start + timedelta(seconds=index),
            return_value=Decimal("0.001"),
        )
        for index in range(30)
    )
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
        "measurement_start": observations[0].timestamp,
        "measurement_end": observations[-1].timestamp,
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
    payload["config_hash"] = unwrap_simulation_response(
        PortfolioBacktestRequest.calculate_config_hash(payload),
        operation="simulation.run.portfolio_backtest_request_v1.calculate_config_hash",
    )
    request = PortfolioBacktestRequest.model_validate(payload)
    assert request.components[0].backtest_request is not None


def test_emit_simulation_audit_exception_handling() -> None:
    """Test emit_simulation_audit converting unexpected persistence exceptions to SimulationError."""
    from datetime import UTC, datetime
    from types import SimpleNamespace

    from app.services.simulator.errors import SimulationError
    from app.services.simulator.run.audit import emit_simulation_audit

    class FailingDeps:
        def persist_audit_event(self, _event: object) -> object:
            raise RuntimeError("Database connection crashed")

    deps = FailingDeps()
    auth = SimpleNamespace(
        principal_id="user1", request_id="req1", correlation_id="cor1"
    )
    with pytest.raises(SimulationError, match="Simulation audit persistence failed"):
        emit_simulation_audit(
            dependencies=deps,  # type: ignore[arg-type]
            auth_context=auth,
            action="run_started",
            timestamp=datetime.now(UTC),
            payload={},
        )


def test_portfolio_run_grid_and_validation_error_paths() -> None:
    """Test portfolio grid construction and component validation error paths."""
    from datetime import UTC, datetime, timedelta

    from app.services.simulator.errors import SimulationError
    from app.services.simulator.run.portfolio import _measurement_grid

    now = datetime.now(UTC)
    # Test invalid span <= 0
    with pytest.raises(SimulationError, match="Measurement window cannot carry"):
        _measurement_grid(now, now, 30)

    # Test count < 30
    with pytest.raises(SimulationError, match="Measurement window cannot carry"):
        _measurement_grid(now, now + timedelta(days=1), 10)
