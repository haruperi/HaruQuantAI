"""SYS-WF-003 deterministic advisory Optimization core integration."""

from app.services.optimization.execution import SimulationAnalyticsBacktestAdapter
from app.services.optimization.public_api import run_parameter_sweep
from app.services.strategy import StrategyConfig, validate_strategy_config
from app.utils import logger

from tests.analytics._support import _report
from tests.data.helpers import make_dataset
from tests.optimization.unit.test_adapter import _auth
from tests.optimization.unit.test_search_contracts import search_request
from tests.simulator.unit.test_reporting_contracts import _result
from tests.strategy.unit.test_models import make_ref


def test_sys_wf_003_advisory_optimization_core() -> None:
    """Data/Strategy references, Simulation, Analytics, and Optimization align."""
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
    strategy_config = StrategyConfig(
        strategy_id="mean-reversion",
        strategy_version="1.0.0",
        config_schema_version="v1",
        parameters=parameters,
        request_id="req-system-optimization",
    )
    strategy_ref = make_ref()
    strategy_manifest = strategy_ref.manifest.model_copy(
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
    validation = validate_strategy_config(
        strategy_ref.model_copy(update={"manifest": strategy_manifest}),
        strategy_config,
    )
    simulation_request = captured["request"]
    assert dataset.schema_id == "data.market_dataset.v1"
    assert simulation_request.schema_id == "simulation.backtest_request.v1"
    assert result.ranked_candidates
    assert result.diagnostics["search"]
    assert validation.status == "success"
