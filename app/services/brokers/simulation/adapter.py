"""Private socket-free adapter backed by an injected authority port."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import TYPE_CHECKING, cast, override

from app.services.brokers._shared.base import _UnsupportedAdapterBase
from app.services.brokers.canonical_contracts import (
    BrokerCapabilityId,
    BrokerConnectionConfig,
    BrokerConnectionEvent,
    BrokerConnectionState,
    BrokerConnectionStatus,
    StandardResponse,
)
from app.services.brokers.simulation.lifecycle import lifecycle_state_from_response

if TYPE_CHECKING:
    from app.services.brokers.simulation.contracts import SimulationAuthorityPort


class SimulationBrokerAdapter(_UnsupportedAdapterBase):
    """Delegate admitted broker behavior without owning simulation semantics."""

    def __init__(
        self, config: BrokerConnectionConfig, authority_port: object | None
    ) -> None:
        """Initialize the adapter with an exact structural authority.

        Args:
            config: Exact simulation connection configuration.
            authority_port: Object implementing the Brokers-owned port.

        Raises:
            TypeError: If the injected authority does not satisfy the port.
        """
        required = (
            "connect",
            "disconnect",
            "reconnect",
            "is_connected",
            "get_connection_status",
            "ping",
            "connection_events",
            "finalize_session",
        )
        if authority_port is None or any(
            not callable(getattr(authority_port, name, None)) for name in required
        ):
            raise TypeError("authority_port must satisfy SimulationAuthorityPort")
        super().__init__(config)
        self._authority = cast("SimulationAuthorityPort", authority_port)

    async def _delegate_lifecycle(self, operation: str) -> StandardResponse[object]:
        """Delegate and synchronize one lifecycle operation.

        Args:
            operation: Authority method name.

        Returns:
            Unmodified canonical authority response.
        """
        try:
            response = await getattr(self._authority, operation)()
        except Exception as error:  # noqa: BLE001 - public boundary normalization.
            capability = (
                BrokerCapabilityId.DISCONNECT
                if operation == "finalize_session"
                else BrokerCapabilityId(operation)
            )
            return cast(
                "StandardResponse[object]", self._exception_result(capability, error)
            )
        state = lifecycle_state_from_response(operation, response)
        if state is not None:
            self._state = state
            if (
                operation in {"connect", "reconnect"}
                and state is BrokerConnectionState.READY
            ):
                self._session_generation += 1
        return cast("StandardResponse[object]", response)

    @override
    async def connect(self) -> StandardResponse[None]:
        """Connect the injected authority session.

        Returns:
            Canonical authority response.
        """
        return cast("StandardResponse[None]", await self._delegate_lifecycle("connect"))

    @override
    async def disconnect(self) -> StandardResponse[None]:
        """Disconnect the injected authority session.

        Returns:
            Canonical authority response.
        """
        return cast(
            "StandardResponse[None]", await self._delegate_lifecycle("disconnect")
        )

    @override
    async def reconnect(self) -> StandardResponse[None]:
        """Reconnect the injected authority session.

        Returns:
            Canonical authority response.
        """
        return cast(
            "StandardResponse[None]", await self._delegate_lifecycle("reconnect")
        )

    @override
    async def is_connected(self) -> StandardResponse[bool]:
        """Read connectivity from the injected authority.

        Returns:
            Canonical authority response.
        """
        return cast(
            "StandardResponse[bool]", await self._delegate_lifecycle("is_connected")
        )

    @override
    async def get_connection_status(self) -> StandardResponse[BrokerConnectionStatus]:
        """Read detailed status from the injected authority.

        Returns:
            Canonical authority response.
        """
        return cast(
            "StandardResponse[BrokerConnectionStatus]",
            await self._delegate_lifecycle("get_connection_status"),
        )

    async def ping(self) -> StandardResponse[None]:
        """Ping the injected authority.

        Returns:
            Canonical authority response, or disconnected failure.
        """
        if self._state is not BrokerConnectionState.READY:
            return self._not_connected(BrokerCapabilityId.PING)
        return cast("StandardResponse[None]", await self._delegate_lifecycle("ping"))

    @override
    def connection_events(self) -> AsyncIterator[BrokerConnectionEvent]:
        """Return the authority-owned deterministic event stream.

        Returns:
            Authority event iterator.
        """
        return self._authority.connection_events()

    async def finalize_session(self) -> StandardResponse[None]:
        """Finalize the run-scoped authority session.

        Returns:
            Canonical authority response.
        """
        return cast(
            "StandardResponse[None]",
            await self._delegate_lifecycle("finalize_session"),
        )


__all__ = ("SimulationBrokerAdapter",)
