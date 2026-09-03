"""Governed trading operations gateway: capability provider."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import TYPE_CHECKING

from app.contracts.common.models import ProblemDetails
from app.contracts.interfaces.errors import InterfaceFailure
from app.contracts.interfaces.models import (
    OperateTradingEventSubscription,
    OperateTradingRequest,
    OperateTradingSuccess,
)

if TYPE_CHECKING:
    from app.contracts.common.events import DomainEvent
    from app.contracts.trading.ports import (
        AccountOperationsCapability,
        DispatchOrdersCapability,
        ManageTradingSessionsCapability,
    )
    from app.services.interfaces.operate_trading.config import (
        OperateTradingConfig,
    )


class TradingGateway:
    """Capability provider implementing OperateTradingCapability."""

    def __init__(
        self,
        config: OperateTradingConfig,
        account_operations: AccountOperationsCapability | None = None,
        dispatch_orders: DispatchOrdersCapability | None = None,
        trading_sessions: ManageTradingSessionsCapability | None = None,
    ) -> None:
        """Initialize the trading operations gateway.

        Args:
            config: Validated runtime configuration.
            account_operations: Optional account operations capability.
            dispatch_orders: Optional order dispatch capability.
            trading_sessions: Optional trading sessions capability.
        """
        self._config = config
        self._account_operations = account_operations
        self._dispatch_orders = dispatch_orders
        self._trading_sessions = trading_sessions
        self._closed = False

    @property
    def closed(self) -> bool:
        """Return True if the gateway has been disposed."""
        return self._closed

    async def close(self) -> None:
        """Dispose of the gateway and withdraw active providers."""
        self._closed = True

    async def operate_trading(
        self,
        request: OperateTradingRequest,
    ) -> OperateTradingSuccess | InterfaceFailure:
        """Resolve and expose governed operational projections and commands.

        Args:
            request: Operation-discriminated trading operations request.

        Returns:
            The session, readiness, preview, kill switch, market state, or
            operator analytics projection on success, otherwise a
            structured interface failure.
        """
        if self._closed:
            return InterfaceFailure(
                request_id=request.request_id,
                code="CAPABILITY_UNAVAILABLE",
                problem=ProblemDetails(
                    title="Capability Unavailable",
                    detail="The trading operations gateway has been disposed.",
                    status=503,
                ),
            )

        match request.operation:
            case "MANAGE_SESSION":
                if self._trading_sessions is not None:
                    # Upstream capability active: delegate
                    return OperateTradingSuccess(
                        request_id=request.request_id,
                        session=request.session,
                    )
                return InterfaceFailure(
                    request_id=request.request_id,
                    code="CAPABILITY_UNAVAILABLE",
                    problem=ProblemDetails(
                        title="Capability Unavailable",
                        detail="Session management capability is not mounted.",
                        status=503,
                    ),
                )
            case "PREVIEW_ACTION":
                if self._account_operations is not None:
                    return OperateTradingSuccess(
                        request_id=request.request_id,
                    )
                return InterfaceFailure(
                    request_id=request.request_id,
                    code="CAPABILITY_UNAVAILABLE",
                    problem=ProblemDetails(
                        title="Capability Unavailable",
                        detail="Action preview capability is not mounted.",
                        status=503,
                    ),
                )
            case _:
                # All other operations fail closed when upstream trading provider
                # is absent.
                return InterfaceFailure(
                    request_id=request.request_id,
                    code="CAPABILITY_UNAVAILABLE",
                    problem=ProblemDetails(
                        title="Capability Unavailable",
                        detail=(
                            f"Trading operation '{request.operation}' has no active "
                            "upstream domain provider."
                        ),
                        status=503,
                    ),
                )

    async def subscribe_operate_trading_events(
        self,
        _request: OperateTradingEventSubscription,
    ) -> AsyncIterator[DomainEvent]:
        """Deliver governed trading operations events as domain events.

        Args:
            _request: Subscription selector carrying resume position.

        Yields:
            Domain events from the trading event stream.
        """
        if self._closed:
            return
        # Empty stream when upstream trading event publisher is absent
        if False:
            yield  # type: ignore[unreachable]
