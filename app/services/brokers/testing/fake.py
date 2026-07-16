"""Deterministic complete broker adapter test double."""

# ruff: noqa: ANN401 - generated fixed protocol methods preserve fixture types.

from collections.abc import Mapping
from typing import Any

from app.services.brokers.contracts import (
    BrokerCapability,
    BrokerCapabilityId,
    BrokerConnectionConfig,
    BrokerConnectionState,
    BrokerError,
    BrokerResult,
)
from app.services.brokers.contracts.protocols import _UnsupportedAdapterBase


class FakeBrokerAdapter(_UnsupportedAdapterBase):
    """Isolated fixture/result adapter with per-operation error injection."""

    _ENFORCE_DECLARED_AVAILABILITY = False

    def __init__(
        self,
        config: BrokerConnectionConfig,
        capabilities: Mapping[BrokerCapabilityId, BrokerCapability],
        *,
        fixtures: Mapping[BrokerCapabilityId, object] | None = None,
        errors: Mapping[BrokerCapabilityId, BrokerError] | None = None,
    ) -> None:
        super().__init__(config, capabilities)
        self._fixtures = dict(fixtures or {})
        self._errors = dict(errors or {})

    async def connect(self) -> BrokerResult[None]:
        """Establish a deterministic local verified session."""
        await self._transition(BrokerConnectionState.CONNECTING)
        self._session_generation += 1
        await self._transition(BrokerConnectionState.READY)
        return self._result(BrokerCapabilityId.CONNECT)

    def inject_error(
        self, operation: BrokerCapabilityId, error: BrokerError | None
    ) -> None:
        """Set or clear the exact operation's canonical failure."""
        if error is None:
            self._errors.pop(operation, None)
        else:
            self._errors[operation] = error

    async def _invoke(self, operation: BrokerCapabilityId) -> BrokerResult[Any]:
        error = self._errors.get(operation)
        if error is not None:
            self._last_error = error
            return self._result(operation, error=error)
        if operation not in self._fixtures:
            return self._unsupported(operation)
        return self._result(operation, data=self._fixtures[operation])


def _make_fake_method(operation: BrokerCapabilityId) -> Any:
    async def _method(
        self: FakeBrokerAdapter, *args: object, **kwargs: object
    ) -> BrokerResult[Any]:
        del args, kwargs
        return await self._invoke(operation)

    _method.__name__ = operation.value
    return _method


for _operation_id in BrokerCapabilityId:
    if _operation_id not in {
        BrokerCapabilityId.CONNECT,
        BrokerCapabilityId.DISCONNECT,
        BrokerCapabilityId.RECONNECT,
        BrokerCapabilityId.IS_CONNECTED,
        BrokerCapabilityId.GET_CONNECTION_STATUS,
        BrokerCapabilityId.GET_LAST_ERROR,
        BrokerCapabilityId.CONNECTION_EVENTS,
        BrokerCapabilityId.GET_FEATURE_FLAGS,
        BrokerCapabilityId.SUPPORTS,
    }:
        setattr(
            FakeBrokerAdapter, _operation_id.value, _make_fake_method(_operation_id)
        )
