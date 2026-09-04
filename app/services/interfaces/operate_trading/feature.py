"""Feature lifecycle mount for the governed trading gateway."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.contracts.interfaces.capabilities import OPERATE_TRADING_CAPABILITY
from app.contracts.trading.capabilities import (
    ACCOUNT_OPERATIONS_CAPABILITY,
    DISPATCH_ORDERS_CAPABILITY,
    MANAGE_TRADING_SESSIONS_CAPABILITY,
)
from app.services.interfaces.operate_trading.config import (
    OperateTradingConfig,
    from_dict,
)
from app.services.interfaces.operate_trading.gateway import TradingGateway
from app.services.interfaces.operate_trading.manifest import SPEC

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext
    from app.kernel.feature import FeatureSpec


class OperateTradingFeature:
    """Composable feature package providing trading operations."""

    def __init__(self, spec: FeatureSpec = SPEC) -> None:
        """Initialize the feature with its specification.

        Args:
            spec: Feature specification declaring the served capability.
        """
        self.spec = spec
        self._gateway: TradingGateway | None = None

    @property
    def gateway(self) -> TradingGateway | None:
        """Return the mounted gateway, or None before mount.

        Returns:
            Active gateway instance if mounted, otherwise None.
        """
        return self._gateway

    async def mount(self, context: FeatureContext, config: object) -> None:
        """Mount the gateway against optional upstream Trading providers.

        Args:
            context: Scoped runtime context for this feature.
            config: Mapping, OperateTradingConfig, or None.

        Raises:
            ValueError: If configuration contains unknown keys.
            TypeError: If configuration has an unsupported type.
        """
        if config is None or isinstance(config, dict):
            parsed = from_dict(config)
        elif isinstance(config, OperateTradingConfig):
            parsed = config
        else:
            message = (
                "operate-trading configuration must be a mapping, "
                "OperateTradingConfig, or None"
            )
            raise TypeError(message)

        # Upstream trading capabilities are optional at this phase
        account_ops = context.optional(ACCOUNT_OPERATIONS_CAPABILITY)
        dispatch_orders = context.optional(DISPATCH_ORDERS_CAPABILITY)
        trading_sessions = context.optional(MANAGE_TRADING_SESSIONS_CAPABILITY)

        gateway = TradingGateway(
            config=parsed,
            account_operations=account_ops,
            dispatch_orders=dispatch_orders,
            trading_sessions=trading_sessions,
        )
        context.register_callback(gateway.close)
        context.provide(OPERATE_TRADING_CAPABILITY, gateway)
        self._gateway = gateway


def feature() -> OperateTradingFeature:
    """Factory for discovery via entry points.

    Returns:
        New OperateTradingFeature instance.
    """
    return OperateTradingFeature()
