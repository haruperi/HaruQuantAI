"""Host telemetry owner: the bounded in-process observation stream.

One host owner = one file: this module owns the public ``Telemetry``
protocol, the ``HOST_TELEMETRY`` capability token (``host.telemetry@1``),
and the public value types exchanged with observers. The concrete
provider and lifecycle feature are private, and
``_telemetry_feature`` is a composition-only constructor used solely
by the host composition root.

The owner provides bounded event observation: immutable portable
events, explicit subscription handles, per-observer failure
isolation, and a bounded diagnostic ring. It does not own logging
backends, persistence, transport, product metrics, or any plugin
contract.

Purity and concurrency: importing this module performs no I/O and no
environment, task, or thread effects. The provider holds no locks
and is intended for a single event loop under runtime-owned
lifecycles.
"""

from __future__ import annotations

import asyncio
import inspect
import math
from collections import deque
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

from app.kernel.capability import Capability
from app.kernel.context import FeatureContext, KernelDiagnostic
from app.kernel.feature import FeatureSpec

MAX_EVENT_FIELDS = 32
MAX_FIELD_LENGTH = 512
FIELD_PAIR_SIZE = 2
DEFAULT_MAX_SUBSCRIBERS = 64
DEFAULT_DIAGNOSTIC_CAPACITY = 256

type TelemetryValue = str | int | float | bool | None
type TelemetryHandler = Callable[["TelemetryEvent"], Awaitable[None] | None]


class TelemetryLevel(StrEnum):
    """Portable event importance without binding consumers to logging libraries.

    The closed set (``debug``, ``info``, ``warning``, ``error``) is the
    only level vocabulary :class:`TelemetryEvent` accepts.
    """

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class TelemetryError(RuntimeError):
    """Base error for unavailable or invalid telemetry operations."""


class TelemetryClosedError(TelemetryError):
    """Raised when an operation targets a closed telemetry provider.

    Both ``subscribe`` and ``emit`` fail closed once the runtime that
    owns the provider has shut down.
    """


class TelemetryCapacityError(TelemetryError):
    """Raised when the configured subscription bound is exhausted.

    Capacity is restored only by closing an active subscription; the
    bound itself is fixed at composition time.
    """


@dataclass(frozen=True, slots=True)
class TelemetryEvent:
    """Describe one immutable, bounded host observation.

    Frozen and slotted. Names and string values are bounded by
    ``MAX_FIELD_LENGTH``; fields are bounded to ``MAX_EVENT_FIELDS``
    key/value pairs whose keys are unique and whose values are
    portable scalars (``str``, ``int``, ``float``, ``bool``,
    ``None``) with finite numerics, so a delivered event can never
    carry mutable or unbounded state.

    Raises:
        ValueError: If the name is empty, untrimmed, or overlong;
            if ``fields`` is not a bounded tuple; or if a key is
            duplicated, untrimmed, or overlong, a string value is
            overlong, or a numeric value is not finite.
        TypeError: If ``level`` is not a :class:`TelemetryLevel`, an
            item is not a key/value tuple, or a value is not a
            portable scalar.
    """

    name: str
    level: TelemetryLevel = TelemetryLevel.INFO
    fields: tuple[tuple[str, TelemetryValue], ...] = ()

    def __post_init__(self) -> None:
        """Validate portable field values and deterministic field identity."""
        if (
            not self.name
            or self.name != self.name.strip()
            or len(self.name) > MAX_FIELD_LENGTH
        ):
            raise ValueError("Telemetry event names must be nonempty and bounded")
        if type(self.level) is not TelemetryLevel:
            raise TypeError("Telemetry event levels must use TelemetryLevel")
        if type(self.fields) is not tuple or len(self.fields) > MAX_EVENT_FIELDS:
            raise ValueError("Telemetry event fields must be a bounded tuple")
        seen: set[str] = set()
        for item in self.fields:
            if type(item) is not tuple or len(item) != FIELD_PAIR_SIZE:
                raise TypeError("Telemetry fields must be key/value tuples")
            key, value = item
            if (
                not key
                or key != key.strip()
                or key in seen
                or len(key) > MAX_FIELD_LENGTH
            ):
                raise ValueError("Telemetry field keys must be unique and bounded")
            if type(value) not in (str, int, float, bool, type(None)):
                raise TypeError("Telemetry fields accept only portable scalar values")
            if isinstance(value, str) and len(value) > MAX_FIELD_LENGTH:
                raise ValueError("Telemetry string fields must be bounded")
            if isinstance(value, float) and not math.isfinite(value):
                raise ValueError("Telemetry numeric fields must be finite")
            seen.add(key)


@dataclass(frozen=True, slots=True)
class TelemetryDeliveryFailure:
    """Attribute one observer failure without exposing an exception object.

    Attributes:
        subscription_id: Numeric identity of the failing subscription.
        error_type: Exception class name of the observer failure.
        message: Bounded exception text (truncated to
            ``MAX_FIELD_LENGTH``).
    """

    subscription_id: int
    error_type: str
    message: str


@dataclass(frozen=True, slots=True)
class TelemetryDeliveryReport:
    """Report successful and failed observer deliveries for one emit.

    Attributes:
        delivered: Number of observers that accepted the event without
            raising.
        failures: One bounded attribution per observer that raised;
            delivery to the remaining observers was still attempted.
    """

    delivered: int
    failures: tuple[TelemetryDeliveryFailure, ...] = ()


class TelemetrySubscription(Protocol):
    """Idempotent lifecycle handle for one observation subscription.

    The handle is the only supported way to withdraw an observer;
    dropping the handle does not unsubscribe.
    """

    def close(self) -> None:
        """Remove this subscription if it remains active.

        Closing an already-closed handle is a no-op; the subscription
        slot is immediately reusable afterwards.
        """
        ...


class Telemetry(Protocol):
    """Bounded host observation service exposed through a typed capability.

    Consumers resolve this protocol via the ``HOST_TELEMETRY``
    capability (``host.telemetry@1``); the implementing service is
    private to this owner and lives exactly as long as the runtime
    that published it.
    """

    def subscribe(self, handler: TelemetryHandler) -> TelemetrySubscription:
        """Register an observer and return its explicit lifecycle handle.

        Args:
            handler: Callable accepting one :class:`TelemetryEvent`,
                returning ``None`` or an awaitable.

        Returns:
            The idempotent handle that removes this observer.

        Raises:
            TelemetryClosedError: If the provider is closed.
            TelemetryCapacityError: If the configured subscriber bound
                is already exhausted.
        """
        ...

    async def emit(self, event: TelemetryEvent) -> TelemetryDeliveryReport:
        """Deliver an event while isolating observer failures.

        Delivery visits the handler snapshot taken when the emit
        starts; subscriptions opened or closed by handlers during the
        emit do not join or leave that in-flight snapshot.

        Args:
            event: The immutable event to deliver.

        Returns:
            Per-emit delivery counts and bounded failure
            attributions; each observer failure is also recorded as a
            lifecycle diagnostic.

        Raises:
            TelemetryClosedError: If the provider is closed.

        Note:
            An exception raised by any observer never propagates into
            the emitting caller; it is captured as a
            :class:`TelemetryDeliveryFailure` instead. Only genuine
            cancellation of the emitting task itself propagates.
        """
        ...

    @property
    def diagnostics(self) -> tuple[KernelDiagnostic, ...]:
        """Return a bounded immutable snapshot of lifecycle diagnostics.

        The ring keeps at most the configured number of entries;
        observer failures append ``host.telemetry.subscriber_failed``
        diagnostics. The returned tuple is a point-in-time copy.
        """
        ...


HOST_TELEMETRY = Capability[Telemetry](
    "host.telemetry", major=1, description="Bounded host observation stream"
)


class _Subscription:
    """Private explicit handle whose close() runs exactly once."""

    def __init__(self, remove: Callable[[int], None], subscription_id: int) -> None:
        self._remove = remove
        self._subscription_id = subscription_id
        self._closed = False

    def close(self) -> None:
        """Remove the subscription once; subsequent calls are no-ops."""
        if self._closed:
            return
        self._closed = True
        self._remove(self._subscription_id)


class _TelemetryService:
    """Private in-process provider behind the ``HOST_TELEMETRY`` token."""

    def __init__(self, max_subscribers: int, diagnostic_capacity: int) -> None:
        if max_subscribers < 1 or diagnostic_capacity < 1:
            raise ValueError("Telemetry bounds must be positive")
        self._max_subscribers = max_subscribers
        self._handlers: dict[int, TelemetryHandler] = {}
        self._next_subscription_id = 1
        self._closed = False
        self._diagnostics: deque[KernelDiagnostic] = deque(maxlen=diagnostic_capacity)

    @property
    def diagnostics(self) -> tuple[KernelDiagnostic, ...]:
        """Copy the bounded diagnostic ring at a point in time."""
        return tuple(self._diagnostics)

    def record_diagnostic(self, diagnostic: KernelDiagnostic) -> None:
        """Append one diagnostic, dropping the oldest beyond capacity."""
        self._diagnostics.append(diagnostic)

    def subscribe(self, handler: TelemetryHandler) -> TelemetrySubscription:
        """Register a handler or fail closed/for-capacity as documented."""
        if self._closed:
            raise TelemetryClosedError("Telemetry provider is closed")
        if len(self._handlers) >= self._max_subscribers:
            raise TelemetryCapacityError("Telemetry subscriber capacity reached")
        subscription_id = self._next_subscription_id
        self._next_subscription_id += 1
        self._handlers[subscription_id] = handler
        return _Subscription(self._remove, subscription_id)

    def _remove(self, subscription_id: int) -> None:
        """Drop a subscription id if it is still registered."""
        self._handlers.pop(subscription_id, None)

    async def emit(self, event: TelemetryEvent) -> TelemetryDeliveryReport:
        """Deliver to the start-of-emit handler snapshot, isolating failures."""
        if self._closed:
            raise TelemetryClosedError("Telemetry provider is closed")
        delivered = 0
        failures: list[TelemetryDeliveryFailure] = []
        for subscription_id, handler in tuple(self._handlers.items()):
            try:
                result = handler(event)
                if inspect.isawaitable(result):
                    await result
                delivered += 1
            except asyncio.CancelledError as error:
                task = asyncio.current_task()
                if task is not None and task.cancelling():
                    raise
                failures.append(self._failure(subscription_id, error))
            except Exception as error:  # noqa: BLE001 - observer isolation boundary
                failures.append(self._failure(subscription_id, error))
        return TelemetryDeliveryReport(delivered, tuple(failures))

    def _failure(
        self, subscription_id: int, error: BaseException
    ) -> TelemetryDeliveryFailure:
        """Turn an observer exception into a bounded failure plus diagnostic."""
        failure = TelemetryDeliveryFailure(
            subscription_id,
            type(error).__name__,
            str(error)[:MAX_FIELD_LENGTH],
        )
        self.record_diagnostic(
            KernelDiagnostic(
                "host.telemetry.subscriber_failed",
                str(subscription_id),
                failure.error_type,
            )
        )
        return failure

    def close(self) -> None:
        """Close once and drop handlers so later subscribe/emit fail closed."""
        if self._closed:
            return
        self._closed = True
        self._handlers.clear()


class _TelemetryFeature:
    spec = FeatureSpec(
        "host.telemetry",
        provides=frozenset({HOST_TELEMETRY}),
        description="Own the bounded in-process host observation stream",
    )

    def __init__(self, max_subscribers: int, diagnostic_capacity: int) -> None:
        self._service = _TelemetryService(max_subscribers, diagnostic_capacity)

    def diagnose(self, diagnostic: KernelDiagnostic) -> None:
        """Forward one lifecycle diagnostic into the bounded ring."""
        self._service.record_diagnostic(diagnostic)

    async def start(self, context: FeatureContext) -> None:
        """Register close-on-shutdown, then publish the capability."""
        context.on_close(self._service.close)
        context.provide(HOST_TELEMETRY, self._service)


def _telemetry_feature(
    *,
    max_subscribers: int = DEFAULT_MAX_SUBSCRIBERS,
    diagnostic_capacity: int = DEFAULT_DIAGNOSTIC_CAPACITY,
) -> _TelemetryFeature:
    """Construct the telemetry owner for the host composition root only."""
    return _TelemetryFeature(max_subscribers, diagnostic_capacity)


__all__ = (
    "HOST_TELEMETRY",
    "Telemetry",
    "TelemetryCapacityError",
    "TelemetryClosedError",
    "TelemetryDeliveryFailure",
    "TelemetryDeliveryReport",
    "TelemetryError",
    "TelemetryEvent",
    "TelemetryHandler",
    "TelemetryLevel",
    "TelemetrySubscription",
    "TelemetryValue",
)
