"""Internal canonical application composition seam."""

from app.services.api.composition.application import app, create_app
from app.services.api.composition.broker_config import (
    build_broker_connection_config,
    build_system_broker_connection_config,
)
from app.services.api.composition.in_process import (
    build_in_process_graph,
    get_required_provider_names,
)
from app.services.api.composition.lifecycle import StartupError, lifespan
from app.services.api.widgets.agentic.orchestration import (
    build_api_agentic_dependencies,
)
from app.services.api.widgets.optimization.orchestration import (
    build_api_optimization_dependencies,
)
from app.services.api.widgets.portfolio.orchestration import (
    build_api_portfolio_dependencies,
)
from app.services.api.widgets.risk.orchestration import (
    build_api_risk_dependencies,
)
from app.services.api.widgets.simulation.orchestration import (
    build_api_simulation_dependencies,
)
from app.services.api.widgets.strategies.orchestration import (
    build_api_strategy_dependencies,
)
from app.services.api.widgets.trading.orchestration import (
    build_api_trading_dependencies,
)

__all__ = (
    "StartupError",
    "app",
    "build_api_agentic_dependencies",
    "build_api_optimization_dependencies",
    "build_api_portfolio_dependencies",
    "build_api_risk_dependencies",
    "build_api_simulation_dependencies",
    "build_api_strategy_dependencies",
    "build_api_trading_dependencies",
    "build_broker_connection_config",
    "build_in_process_graph",
    "build_system_broker_connection_config",
    "create_app",
    "get_required_provider_names",
    "lifespan",
)
