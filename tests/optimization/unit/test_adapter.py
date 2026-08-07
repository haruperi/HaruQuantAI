"""Tests for the Optimization execution adapter."""

from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from app.services.optimization.contracts import OptimizationError
from app.services.optimization.execution import (
    EngineOptimizationResult,
    SimulationAnalyticsBacktestAdapter,
    execute_candidate,
)
from app.utils import create_auth_context

from tests.analytics._support import _report
from tests.optimization.unit.test_execution_contracts import execution_request
from tests.simulator.unit.test_reporting_contracts import _result

_REPORT, _ANALYTICS_CONFIG = _report()


class FakeAdapter:
    """Deterministic compatible adapter fixture."""

    contract_version = "v1"
    engine_type = "event_driven"
    engine_version = "v1"
    deterministic = True

    def execute(self, request):
        """Return matching measured evidence."""
        return EngineOptimizationResult(
            candidate_hash=request.candidate_hash,
            simulation_run_id="run-1",
            simulation_request_hash="8" * 64,
            analytics_report=_REPORT,
            runtime_ms=1.0,
            engine_type=self.engine_type,
            engine_version=self.engine_version,
        )


def _auth() -> object:
    """Build matching test authority."""
    request = execution_request()
    return create_auth_context(
        contract_version="v1",
        schema_id="utils.auth_context.v1",
        principal_id="optimization-test",
        principal_type="SERVICE_ACCOUNT",
        roles=("builder",),
        permissions=("simulation:run",),
        scopes=("simulation:run",),
        tenant_or_environment="test",
        request_id=request.request_id,
        workflow_id=request.workflow_id,
        correlation_id=request.correlation_id,
        issued_at=datetime(2024, 1, 1, tzinfo=UTC),
    )


def test_execute_candidate_fails_closed_on_version_mismatch() -> None:
    """Compatibility is checked before invoking execution."""
    adapter = FakeAdapter()
    adapter.engine_version = "v2"
    with pytest.raises(OptimizationError) as captured:
        execute_candidate(execution_request(), adapter, deterministic_only=True)
    assert captured.value.code == "OPT_ADAPTER_INCOMPATIBLE"


def test_simulation_adapter_packages_exact_public_request(mocker) -> None:
    """Concrete adapter constructs the receiver-owned Simulation request."""
    captured = {}

    def runner(request, auth_context, dependencies):
        captured["request"] = request
        captured["auth"] = auth_context
        captured["dependencies"] = dependencies
        return _result()

    mocker.patch(
        "app.services.optimization.execution.adapter.build_performance_report",
        return_value=_REPORT,
    )
    mocker.patch(
        "app.services.optimization.execution.adapter.is_analytics_value",
        return_value=True,
    )
    mocker.patch(
        "app.services.optimization.execution.adapter.calculate_simulation_backtest_config_hash",
        return_value="7" * 64,
    )
    mocker.patch(
        "app.services.optimization.execution.adapter.create_simulation_value",
        side_effect=lambda _name, **fields: SimpleNamespace(**fields),
    )
    mocker.patch(
        "app.services.optimization.execution.adapter.is_simulation_value",
        return_value=True,
    )
    mocker.patch(
        "app.services.optimization.execution.adapter.get_simulation_value_field",
        side_effect=getattr,
    )
    mocker.patch(
        "app.services.optimization.execution.adapter.dump_simulation_value",
        side_effect=lambda value: value.model_dump(mode="json"),
    )
    dependencies = object()
    adapter = SimulationAnalyticsBacktestAdapter(
        auth_context=_auth(),
        simulation_dependencies=dependencies,
        analytics_config=_ANALYTICS_CONFIG,
        engine_type="event_driven",
        engine_version="v1",
        simulation_runner=runner,
    )
    result = execute_candidate(execution_request(), adapter, deterministic_only=True)
    assert captured["request"].parameters == {"period": 14}
    assert captured["request"].risk_policy_hash == "e" * 64
    assert result.analytics_report.schema_id == "analytics.performance_report.v1"
