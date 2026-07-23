"""Deterministic complete broker adapter test double."""

# ruff: noqa: ANN401 - generated fixed protocol methods preserve fixture types.

import inspect
import types
from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any, cast, get_args, get_origin, get_type_hints, override

from app.services.brokers.adapter_runtime.subscription import _BrokerSubscription
from app.services.brokers.contracts import (
    BrokerCapability,
    BrokerCapabilityId,
    BrokerConnectionConfig,
    BrokerConnectionState,
    BrokerError,
    BrokerErrorCode,
    BrokerResult,
    BrokerSubscriptionInfo,
)
from app.services.brokers.contracts.protocols import (
    BrokerAdapter,
    _UnsupportedAdapterBase,
)
from app.utils import generate_id

_SUBSCRIPTION_OPERATIONS = {
    BrokerCapabilityId.SUBSCRIBE_QUOTES,
    BrokerCapabilityId.SUBSCRIBE_BARS,
    BrokerCapabilityId.SUBSCRIBE_ORDER_BOOK,
}


class FakeBrokerAdapter(_UnsupportedAdapterBase):
    """Isolated fixture/result adapter with per-operation error injection.

    The fake honours its supplied capability declaration exactly as a real
    adapter does: a fixture or injected error registered against a capability
    declared `UNAVAILABLE` never bypasses the fail-closed gate. Subscription
    operations return genuine bounded FIFO handles sized by the configured
    `stream_buffer_size`, so backpressure and resynchronization behave
    identically to the real provider adapters.
    """

    def __init__(
        self,
        config: BrokerConnectionConfig,
        capabilities: Mapping[BrokerCapabilityId, BrokerCapability] | None = None,
        *,
        fixtures: Mapping[BrokerCapabilityId, object] | None = None,
        errors: Mapping[BrokerCapabilityId, BrokerError] | None = None,
    ) -> None:
        """Initialize the FakeBrokerAdapter instance.

        Args:
            config: Immutable connection configuration for this instance.
            capabilities: Optional non-production capability declaration used
                by contract tests. Production adapters never accept this input.
            fixtures: Optional per-operation deterministic success payloads.
            errors: Optional per-operation deterministic canonical failures.
        """
        super().__init__(config)
        if capabilities is not None:
            self._capabilities = dict(capabilities)
        self._fixtures: dict[BrokerCapabilityId, object] = {}
        for operation, fixture in (fixtures or {}).items():
            self._validate_fixture(operation, fixture)
            self._fixtures[operation] = fixture
        self._errors = dict(errors or {})
        self._subscriptions: dict[str, _BrokerSubscription[Any]] = {}

    @override
    async def connect(self) -> BrokerResult[None]:
        """Establish a deterministic local verified session.

        Returns:
            A successful canonical connection result.
        """
        await self._transition(BrokerConnectionState.CONNECTING)
        self._session_generation += 1
        await self._transition(BrokerConnectionState.READY)
        return self._result(BrokerCapabilityId.CONNECT)

    def inject_error(
        self, operation: BrokerCapabilityId, error: BrokerError | None
    ) -> None:
        """Set or clear the exact operation's canonical failure.

        Args:
            operation: Capability whose deterministic outcome is being set.
            error: Canonical failure to return, or `None` to clear it.
        """
        if error is None:
            self._errors.pop(operation, None)
        else:
            self._errors[operation] = error

    async def publish(self, subscription_id: str, event: object) -> bool:
        """Publish one event into an owned bounded subscription.

        Args:
            subscription_id: Identifier of a subscription owned by this fake.
            event: Canonical event delivered to the bounded FIFO queue.

        Returns:
            Whether the event was accepted without terminal overflow.

        Raises:
            KeyError: If this instance does not own the subscription.
        """
        return await self._subscriptions[subscription_id].publish(event)

    async def _invoke(self, operation: BrokerCapabilityId) -> BrokerResult[Any]:
        """Return the deterministic outcome declared for one operation.

        Args:
            operation: Capability being exercised.

        Returns:
            The injected error, the registered fixture, or a fail-closed
            unsupported result when no fixture exists.
        """
        error = self._errors.get(operation)
        if error is not None:
            self._last_error = error
            return self._result(operation, error=error)
        if operation in _SUBSCRIPTION_OPERATIONS:
            return self._open_subscription(operation)
        if operation not in self._fixtures:
            return self._unsupported(operation)
        fixture = self._fixtures[operation]
        self._validate_fixture(operation, fixture)
        return self._result(operation, data=fixture)

    @staticmethod
    def _validate_fixture(
        operation: BrokerCapabilityId,
        fixture: object,
    ) -> None:
        """Validate a fixture against the protocol's success payload.

        Args:
            operation: Capability receiving the fixture.
            fixture: Proposed deterministic success payload.

        Raises:
            TypeError: If the payload cannot satisfy the public result contract.
        """
        if operation in _SUBSCRIPTION_OPERATIONS:
            if not (
                isinstance(fixture, tuple)
                and all(isinstance(symbol, str) and symbol for symbol in fixture)
            ):
                raise TypeError("subscription fixture must be a tuple of symbols")
            return
        method = getattr(BrokerAdapter, operation.value)
        return_type = get_type_hints(method)["return"]
        payload_type = get_args(return_type)[0]
        if not _matches_payload(fixture, payload_type):
            message = f"{operation.value} fixture does not match {payload_type!r}"
            raise TypeError(message)

    def _open_subscription(
        self, operation: BrokerCapabilityId
    ) -> BrokerResult[_BrokerSubscription[Any]]:
        """Create one bounded FIFO subscription owned by this instance.

        Args:
            operation: Subscription capability being opened.

        Returns:
            A canonical result carrying the bounded subscription handle.
        """
        symbols = self._fixtures.get(operation)
        subscription_id = generate_id("evt")
        info = BrokerSubscriptionInfo(
            subscription_id=subscription_id,
            capability=operation,
            symbols=tuple(symbols) if isinstance(symbols, tuple) else ("FAKE",),
            created_at=datetime.now(UTC),
            buffer_size=self._config.stream_buffer_size,
        )
        handle: _BrokerSubscription[Any] = _BrokerSubscription(
            broker=self._config.broker_id,
            environment=self._config.environment,
            adapter_version=self.ADAPTER_VERSION,
            info=info,
        )
        self._subscriptions[subscription_id] = handle
        return self._result(operation, data=handle)

    async def unsubscribe(self, subscription_id: str) -> BrokerResult[None]:
        """Terminate exactly one owned subscription.

        Args:
            subscription_id: Identifier supplied by the caller.

        Returns:
            A successful result, or `BROKER_SUBSCRIPTION_NOT_FOUND` when this
            instance does not own the subscription.
        """
        error = self._errors.get(BrokerCapabilityId.UNSUBSCRIBE)
        if error is not None:
            self._last_error = error
            return self._result(BrokerCapabilityId.UNSUBSCRIBE, error=error)
        handle = self._subscriptions.pop(subscription_id, None)
        if handle is None:
            return self._result(
                BrokerCapabilityId.UNSUBSCRIBE,
                error=BrokerError(
                    code=BrokerErrorCode.BROKER_SUBSCRIPTION_NOT_FOUND,
                    message="Subscription is not owned by this adapter",
                    capability=BrokerCapabilityId.UNSUBSCRIBE,
                ),
            )
        await handle.unsubscribe()
        return self._result(BrokerCapabilityId.UNSUBSCRIBE)

    async def list_subscriptions(
        self,
    ) -> BrokerResult[tuple[BrokerSubscriptionInfo, ...]]:
        """List immutable metadata for subscriptions owned by this instance.

        Returns:
            A canonical result carrying this instance's subscription metadata.
        """
        return self._result(
            BrokerCapabilityId.LIST_SUBSCRIPTIONS,
            data=tuple(handle.info for handle in self._subscriptions.values()),
        )


def _make_fake_method(operation: BrokerCapabilityId) -> Any:
    """Build one generated fixture-backed protocol method.

    Args:
        operation: Capability represented by the generated method.

    Returns:
        An asynchronous method returning the operation's deterministic outcome.
    """

    async def _method(
        self: FakeBrokerAdapter, *args: object, **kwargs: object
    ) -> BrokerResult[Any]:
        """Return the deterministic outcome for the generated operation.

        Args:
            self: Fake adapter receiving the generated operation.
            args: Positional arguments accepted for signature compatibility.
            kwargs: Keyword arguments accepted for signature compatibility.

        Returns:
            The operation result.
        """
        del args, kwargs
        return await self._invoke(operation)

    _method.__name__ = operation.value
    protocol_method = getattr(BrokerAdapter, operation.value)
    _method.__annotations__ = dict(protocol_method.__annotations__)
    _method.__signature__ = inspect.signature(protocol_method)  # type: ignore[attr-defined]
    return _method


# Operations whose behaviour the fake inherits from the shared lifecycle base
# or defines explicitly above; every other capability is backed by a fixture.
_RESERVED_OPERATIONS = {
    BrokerCapabilityId.CONNECT,
    BrokerCapabilityId.DISCONNECT,
    BrokerCapabilityId.RECONNECT,
    BrokerCapabilityId.IS_CONNECTED,
    BrokerCapabilityId.GET_CONNECTION_STATUS,
    BrokerCapabilityId.GET_LAST_ERROR,
    BrokerCapabilityId.CONNECTION_EVENTS,
    BrokerCapabilityId.GET_FEATURE_FLAGS,
    BrokerCapabilityId.SUPPORTS,
    BrokerCapabilityId.UNSUBSCRIBE,
    BrokerCapabilityId.LIST_SUBSCRIPTIONS,
}

for _operation_id in BrokerCapabilityId:
    if _operation_id not in _RESERVED_OPERATIONS:
        setattr(
            FakeBrokerAdapter, _operation_id.value, _make_fake_method(_operation_id)
        )


def _matches_payload(  # noqa: PLR0911
    value: object,
    expected: object,
) -> bool:
    """Return whether a value satisfies a resolved payload annotation.

    Args:
        value: Fixture value under validation.
        expected: Resolved payload annotation inside ``BrokerResult``.

    Returns:
        Whether the value satisfies the annotation recursively.
    """
    if expected is Any:
        return True
    if expected is None or expected is type(None):
        return value is None
    origin = get_origin(expected)
    args = get_args(expected)
    if origin in {types.UnionType, getattr(types, "UnionType", object)}:
        return any(_matches_payload(value, item) for item in args)
    if origin is tuple:
        if not isinstance(value, tuple):
            return False
        if len(args) == len((None, None)) and args[1] is Ellipsis:
            return all(_matches_payload(item, args[0]) for item in value)
        return len(value) == len(args) and all(
            _matches_payload(item, item_type)
            for item, item_type in zip(value, args, strict=True)
        )
    if origin is not None:
        if not isinstance(value, origin):
            return False
        if origin.__name__ == "BrokerPage" and args:
            return all(_matches_payload(item, args[0]) for item in value.items)
        return True
    return isinstance(value, cast("type[object]", expected))
