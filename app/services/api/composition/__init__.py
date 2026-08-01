"""Internal canonical application composition seam."""

from app.services.api.composition.application import app, create_app
from app.services.api.composition.broker_config import build_broker_connection_config
from app.services.api.composition.in_process import (
    build_in_process_graph,
    get_required_provider_names,
)
from app.services.api.composition.lifecycle import StartupError, lifespan

__all__ = (
    "StartupError",
    "app",
    "build_broker_connection_config",
    "build_in_process_graph",
    "create_app",
    "get_required_provider_names",
    "lifespan",
)
