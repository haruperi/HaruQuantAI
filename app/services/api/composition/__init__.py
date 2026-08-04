"""Internal canonical application composition seam."""

from app.services.api.composition.agentic_dependencies import (
    build_api_agentic_dependencies,
)
from app.services.api.composition.application import app, create_app
from app.services.api.composition.broker_config import build_broker_connection_config
from app.services.api.composition.in_process import (
    build_in_process_graph,
    get_required_provider_names,
)
from app.services.api.composition.lifecycle import StartupError, lifespan
from app.services.api.composition.optimization_dependencies import (
    build_api_optimization_dependencies,
)
from app.services.api.composition.portfolio_dependencies import (
    build_api_portfolio_dependencies,
)
from app.services.api.composition.simulation_dependencies import (
    build_api_simulation_dependencies,
)
from app.services.api.composition.trading_dependencies import (
    build_api_trading_dependencies,
)

__all__ = (
    "StartupError",
    "app",
    "build_api_agentic_dependencies",
    "build_api_optimization_dependencies",
    "build_api_portfolio_dependencies",
    "build_api_simulation_dependencies",
    "build_api_trading_dependencies",
    "build_broker_connection_config",
    "build_in_process_graph",
    "create_app",
    "get_required_provider_names",
    "lifespan",
)
