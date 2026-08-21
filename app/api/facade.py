"""Root unified public API facade for HaruQuantAI."""

from typing import TYPE_CHECKING

from app.api.broker import BrokerAPI
from app.api.data import DataAPI
from app.api.risk import RiskAPI
from app.api.system import SystemAPI

if TYPE_CHECKING:
    from app.composition.engine import CompositionEngine
    from app.kernel.registry import ServiceRegistry


class HaruQuantAPI:
    """Unified, capability-aware public facade for HaruQuantAI.

    Provides stable domain gateways (`data`, `broker`, `risk`, `system`) that
    dynamically resolve active capability implementations without hardcoded
    dependencies on specific service features.
    """

    def __init__(
        self,
        registry: ServiceRegistry,
        engine: CompositionEngine | None = None,
    ) -> None:
        """Initialize HaruQuantAPI.

        Args:
            registry: Central ServiceRegistry.
            engine: Optional CompositionEngine.
        """
        self._registry = registry
        self._engine = engine

        self.data = DataAPI(registry)
        self.broker = BrokerAPI(registry)
        self.risk = RiskAPI(registry)
        self.system = SystemAPI(registry, engine)

    @property
    def registry(self) -> ServiceRegistry:
        """Return the underlying ServiceRegistry."""
        return self._registry

    @property
    def engine(self) -> CompositionEngine | None:
        """Return the underlying CompositionEngine if attached."""
        return self._engine


def create_api(
    engine: CompositionEngine | None = None,
    registry: ServiceRegistry | None = None,
) -> HaruQuantAPI:
    """Create a unified HaruQuantAPI facade instance.

    Args:
        engine: Optional CompositionEngine.
        registry: Optional ServiceRegistry (defaults to engine's registry if omitted).

    Returns:
        Configured HaruQuantAPI instance.
    """
    if registry is not None:
        reg = registry
    elif engine is not None:
        reg = engine.registry
    else:
        from app.kernel.registry import ServiceRegistry

        reg = ServiceRegistry()

    return HaruQuantAPI(registry=reg, engine=engine)
