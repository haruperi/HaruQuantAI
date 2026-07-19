"""Tests for the Optimization execution adapter."""

# ruff: noqa: INP001

from datetime import UTC, datetime

import pytest
from app.services.optimization.errors import OptimizationError
from app.services.optimization.execution import (
    EngineOptimizationResult,
    SimulationAnalyticsBacktestAdapter,
    execute_candidate,
)
from app.utils import AuthContext
from tests.analytics.usage.test_usage_reports import _report
from tests.optimization.unit.test_execution_contracts import execution_request
from tests.simulator.unit.test_reporting_contracts import _result


class FakeAdapter:
    """Deterministic compatible adapter fixture."""

    contract_version = "v1"
    engine_type = "event_driven"
    engine_version = "v1"
    deterministic = True

    def execute(self, request):
        """Return matching measured evidence."""
        report, _ = _report()
        return EngineOptimizationResult(
            candidate_hash=request.candidate_hash,
            simulation_run_id="run-1",
            simulation_request_hash="8" * 64,
            analytics_report=report,
            runtime_ms=1.0,
            engine_type=self.engine_type,
            engine_version=self.engine_version,
        )


def _auth() -> AuthContext:
    """Build matching test authority."""
    request = execution_request()
    return AuthContext(
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


def test_simulation_adapter_packages_exact_public_request() -> None:
    """Concrete adapter constructs the receiver-owned Simulation request."""
    captured = {}

    def runner(request, auth_context, dependencies):
        captured["request"] = request
        captured["auth"] = auth_context
        captured["dependencies"] = dependencies
        return _result()

    _, config = _report()
    dependencies = object()
    adapter = SimulationAnalyticsBacktestAdapter(
        auth_context=_auth(),
        simulation_dependencies=dependencies,
        analytics_config=config,
        engine_type="event_driven",
        engine_version="v1",
        simulation_runner=runner,
    )
    result = execute_candidate(execution_request(), adapter, deterministic_only=True)
    assert captured["request"].parameters == {"period": 14}
    assert captured["request"].risk_policy_hash == "e" * 64
    assert result.analytics_report.schema_id == "analytics.performance_report.v1"
