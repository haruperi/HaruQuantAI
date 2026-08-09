"""Public immutable Strategy registry feature exports."""

from app.services.strategy.registry.catalogue import (
    bootstrap_builtin_strategies,
    list_builtin_strategy_descriptors,
)
from app.services.strategy.registry.configuration import validate_strategy_config
from app.services.strategy.registry.lifecycle import govern_strategy_lifecycle
from app.services.strategy.registry.listing import (
    get_strategy_definition,
    list_strategy_configs,
    list_strategy_definitions,
    list_strategy_versions,
    resolve_strategy_config,
)
from app.services.strategy.registry.optimization import (
    adopt_approved_optimization_parameters,
)
from app.services.strategy.registry.parameters import update_strategy_parameters
from app.services.strategy.registry.registration import register_strategy_version
from app.services.strategy.registry.resolution import validate_strategy_ref

__all__ = [
    "adopt_approved_optimization_parameters",
    "bootstrap_builtin_strategies",
    "get_strategy_definition",
    "govern_strategy_lifecycle",
    "list_builtin_strategy_descriptors",
    "list_strategy_configs",
    "list_strategy_definitions",
    "list_strategy_versions",
    "register_strategy_version",
    "resolve_strategy_config",
    "update_strategy_parameters",
    "validate_strategy_config",
    "validate_strategy_ref",
]
