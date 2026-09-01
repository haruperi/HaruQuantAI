"""Deterministic provider dispatch for the public Broker capabilities.

The dispatcher owns no provider SDK, account policy, symbol catalogue, or fallback
logic. A request either resolves to exactly one installed provider profile or fails
closed. Order attempts are remembered only long enough to route the legacy JOURNAL
operation to the same provider; Trading remains the durable reconciliation owner.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.contracts.broker.errors import BrokerFailure
from app.contracts.broker.models import (
    ManageSessionsRequest,
    ManageSessionsSuccess,
    ReadProviderStateRequest,
    ReadProviderStateSuccess,
    TransportOrdersRequest,
    TransportOrdersSuccess,
)
from app.contracts.common.models import ProblemDetails
from app.services.brokers.dispatch_providers.config import DispatchProvidersConfig

if TYPE_CHECKING:
    from app.contracts.broker.internal import BrokerProviderGateway
    from app.contracts.broker.models import BrokerSessionRef
    from app.contracts.common.models import Uuid7


def _failure(request_id: Uuid7, code: str, detail: str) -> BrokerFailure:
    """Build one stable fail-closed Broker failure."""
    return BrokerFailure(
        request_id=request_id,
        code=code,  # type: ignore[arg-type]
        problem=ProblemDetails(
            status=503 if code == "CAPABILITY_UNAVAILABLE" else 422,
            code=code,
            detail=detail,
            request_id=request_id,
        ),
    )


class DispatchProvidersService:
    """Sole public Broker provider dispatcher."""

    def __init__(
        self,
        gateways: tuple[BrokerProviderGateway, ...],
        config: DispatchProvidersConfig,
    ) -> None:
        """Initialize deterministic routing over installed gateways.

        Args:
            gateways: Installed provider-local gateways.
            config: Strict dispatcher configuration.

        Raises:
            ValueError: Duplicate profile ownership is configured while strict
                duplicate rejection is enabled.
        """
        self._gateways = gateways
        self._operation_routes: dict[Uuid7, BrokerProviderGateway] = {}
        if config.reject_duplicate_profiles:
            profile_ids = tuple(gateway.profile_id for gateway in gateways)
            if len(set(profile_ids)) != len(profile_ids):
                raise ValueError("provider profile_id ownership must be unique")

    def _route(
        self,
        session: BrokerSessionRef,
        request_id: Uuid7,
    ) -> BrokerProviderGateway | BrokerFailure:
        matches = tuple(gateway for gateway in self._gateways if gateway.accepts(session))
        if not matches:
            return _failure(
                request_id,
                "CAPABILITY_UNAVAILABLE",
                "No installed Broker provider owns the requested profile",
            )
        if len(matches) != 1:
            return _failure(
                request_id,
                "BROKER_VALIDATION_FAILED",
                "More than one Broker provider owns the requested profile",
            )
        return matches[0]

    async def manage_sessions(
        self,
        request: ManageSessionsRequest,
    ) -> ManageSessionsSuccess | BrokerFailure:
        """Route one session lifecycle request without fallback."""
        assert request.session is not None
        gateway = self._route(request.session, request.request_id)
        if isinstance(gateway, BrokerFailure):
            return gateway
        return await gateway.manage_sessions(request)

    async def read_provider_state(
        self,
        request: ReadProviderStateRequest,
    ) -> ReadProviderStateSuccess | BrokerFailure:
        """Route one genuine provider read without fallback."""
        assert request.session is not None
        gateway = self._route(request.session, request.request_id)
        if isinstance(gateway, BrokerFailure):
            return gateway
        return await gateway.read_provider_state(request)

    async def transport_orders(
        self,
        request: TransportOrdersRequest,
    ) -> TransportOrdersSuccess | BrokerFailure:
        """Route one authorized transport request to its exact provider."""
        if request.operation == "JOURNAL":
            assert request.operation_id is not None
            gateway = self._operation_routes.get(request.operation_id)
            if gateway is None:
                return _failure(
                    request.request_id,
                    "CAPABILITY_UNAVAILABLE",
                    "No active provider route is known for the requested operation",
                )
            return await gateway.transport_orders(request)

        assert request.operation_request is not None
        operation_request = request.operation_request
        gateway = self._route(operation_request.session, request.request_id)
        if isinstance(gateway, BrokerFailure):
            return gateway
        if not gateway.supports_order_transport:
            return _failure(
                request.request_id,
                "CAPABILITY_UNAVAILABLE",
                "Selected Broker provider is read-only",
            )
        self._operation_routes[operation_request.operation_id] = gateway
        return await gateway.transport_orders(request)
