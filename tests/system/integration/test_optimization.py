"""SYS-WF-003 Optimization through approved Strategy adoption integration."""

from contextlib import AbstractContextManager
from pathlib import Path

from app.services.api.identity import require_auth_context
from app.services.api.routes import strategies
from app.services.api.routes.strategies import router as strategies_router
from app.services.data import DataSettings, data_settings_context
from app.services.optimization import run_parameter_sweep
from app.services.optimization.execution import SimulationAnalyticsBacktestAdapter
from app.services.strategy import (
    StrategyConfig,
    StrategyEnvironment,
    StrategyParameterUpdateRequest,
    StrategyRef,
)
from app.utils import logger
from fastapi import FastAPI

from tests.analytics._support import _report
from tests.api._support import post_json
from tests.data.helpers import make_dataset
from tests.optimization.unit.test_adapter import _auth
from tests.optimization.unit.test_search_contracts import search_request
from tests.simulator.unit.test_reporting_contracts import _result
from tests.strategy.unit.test_catalog import make_registration
from tests.strategy.unit.test_models import make_auth, make_policy


def _storage(root: Path) -> AbstractContextManager[None]:
    """Build isolated SYS-WF-003 persistence settings.

    Args:
        root: Temporary data root.

    Returns:
        Data settings context.
    """
    return data_settings_context(
        DataSettings(
            database_url="sqlite:///sys-wf-003.sqlite3",
            data_dir=root,
            sqlite_busy_timeout_seconds=1.5,
            write_lock_lease_seconds=30,
        )
    )


def _api() -> FastAPI:
    """Build the authenticated API composition for SYS-WF-003.

    Returns:
        Configured FastAPI application.
    """
    app = FastAPI()
    app.include_router(strategies_router)
    app.dependency_overrides[require_auth_context] = make_auth
    app.dependency_overrides[strategies._strategy_validation_policy] = make_policy
    return app


def test_sys_wf_003_approved_optimization_adoption(tmp_path: Path) -> None:
    """Verify advisory Optimization requires API approval before adoption."""
    logger.debug("Testing SYS-WF-003 deterministic advisory core")
    dataset = make_dataset()
    captured: dict[str, object] = {}

    def runner(request, auth_context, dependencies):
        """Capture the registered Simulation request and return deterministic output."""
        logger.debug("Running SYS-WF-003 deterministic Simulation fixture")
        captured["request"] = request
        captured["auth"] = auth_context
        captured["dependencies"] = dependencies
        return _result()

    _, analytics_config = _report()
    adapter = SimulationAnalyticsBacktestAdapter(
        auth_context=_auth(),
        simulation_dependencies=object(),
        analytics_config=analytics_config,
        engine_type="event_driven",
        engine_version="v1",
        simulation_runner=runner,
    )
    result = run_parameter_sweep(search_request(), adapter)
    parameters = result.ranked_candidates[0]["executable_parameters"]
    registration = make_registration()
    strategy_manifest = registration.manifest.model_copy(
        update={
            "config_schema": {
                "type": "object",
                "properties": {
                    "enabled": {"type": "boolean"},
                    "period": {"type": "integer", "minimum": 1},
                },
                "required": ("enabled",),
                "additionalProperties": False,
            }
        }
    )
    registration = registration.model_copy(
        update={
            "manifest": strategy_manifest,
            "config_schema": strategy_manifest.config_schema,
        }
    )
    strategy_config = StrategyConfig(
        strategy_id="mean-reversion",
        strategy_version="1.0.0",
        config_schema_version="v1",
        parameters=parameters,
        request_id="req-system-optimization",
    )
    strategy_ref = StrategyRef(
        strategy_id=registration.strategy_id,
        exact_version=registration.strategy_version,
        environment=StrategyEnvironment.RESEARCH,
        request_id=registration.request_id,
        correlation_id=registration.correlation_id,
    )
    update = StrategyParameterUpdateRequest(
        command_id="command-approved-optimization-adoption",
        strategy_id=registration.strategy_id,
        strategy_version=registration.strategy_version,
        parameters=parameters,
        optimization_result_ref=result.search_id,
        principal_id="builder",
        reason="explicitly approved optimization selection",
        ref=strategy_ref,
        config=strategy_config,
        authorization_ref="approval-sys-wf-003",
        requested_at=registration.requested_at,
        request_id=registration.request_id,
        correlation_id=registration.correlation_id,
    )

    app = _api()
    with _storage(tmp_path):
        registration_status, registration_body = post_json(
            app,
            "/api/strategies/registrations",
            registration.model_dump(mode="json"),
        )
        adoption_status, adoption_body = post_json(
            app,
            "/api/strategies/parameter-updates",
            update.model_dump(mode="json"),
        )

    simulation_request = captured["request"]
    assert dataset.schema_id == "data.market_dataset.v1"
    assert simulation_request.schema_id == "simulation.backtest_request.v1"
    assert result.ranked_candidates
    assert result.diagnostics["search"]
    assert registration_status == 200
    assert registration_body["status"] == "ACCEPTED"
    assert adoption_status == 200
    assert adoption_body["status"] == "ACCEPTED"
    assert adoption_body["validated_config"]["normalized_parameters"] == parameters
