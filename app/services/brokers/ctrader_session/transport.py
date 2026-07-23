"""cTrader request correlation and session transport boundary."""

# ruff: noqa: TRY004 - an unexpected provider response is invalid provider evidence.

from __future__ import annotations

import asyncio
import importlib
import time
from collections import deque
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.services.brokers.contracts import BrokerConnectionConfig
from app.services.brokers.adapter_runtime.circuit_breaker import (
    _TransportCircuitBreaker,
)
from app.services.brokers.contracts import BrokerErrorCode
from app.services.brokers.contracts.protocols import (
    _CircuitOpenError,
    _RateLimitedError,
)
from app.utils import logger

type _Sender = Callable[[object], Awaitable[object]]
type _EventHandler = Callable[[object], None]
type _EventRegistrar = Callable[[_EventHandler], None]


class _CTraderTransport:
    """Own one session and prevent same-type response cross-correlation."""

    def __init__(
        self,
        config: BrokerConnectionConfig,
        *,
        sender: _Sender | None = None,
        register_event_handler: _EventRegistrar | None = None,
        unregister_event_handler: _EventRegistrar | None = None,
        latency_sink: Callable[[float], None] | None = None,
    ) -> None:
        """Initialize the _CTraderTransport instance.

        Args:
            config: Immutable connection configuration for this session.
            sender: Async provider sender; the default Spotware sender is
                supplied by `ctrader/network.py`.
            register_event_handler: Registrar for adapter-owned provider events.
            unregister_event_handler: Deregistrar for the same handler.
            latency_sink: Optional receiver for the measured milliseconds spent
                awaiting each provider response, used to separate provider
                latency from local adapter overhead.
        """
        self._config = config
        self._sender = sender
        self._latency_sink = latency_sink
        self._register_event_handler = register_event_handler
        self._unregister_event_handler = unregister_event_handler
        self._locks: dict[type[object], asyncio.Lock] = {}
        self._connected = False
        self._circuit = _TransportCircuitBreaker(
            failure_threshold=config.circuit_failure_threshold,
            recovery_timeout_sec=config.circuit_recovery_timeout_sec,
            half_open_max_calls=config.circuit_half_open_max_calls,
        )
        self._rate_lock = asyncio.Lock()
        self._history_requests: deque[float] = deque()
        self._other_requests: deque[float] = deque()

    @property
    def connected(self) -> bool:
        """Return current authenticated transport state."""
        return self._connected

    async def connect(self) -> bool:
        """Load the pinned SDK and establish only a configured session.

        Returns:
            Whether a configured sender is ready.
        """
        importlib.import_module("ctrader_open_api")
        if self._sender is None:
            logger.bind(
                broker=self._config.broker_id.value,
                environment=self._config.environment.value,
                result="error",
            ).warning("cTrader transport has no session sender; failing closed")
            return False
        self._connected = True
        logger.bind(
            broker=self._config.broker_id.value,
            environment=self._config.environment.value,
            result="success",
        ).info("cTrader transport session established")
        return True

    async def send(
        self,
        request: object,
        response_type: type[object],
        *,
        request_id: str | None = None,
    ) -> object:
        """Correlate by native ID or serialize the same response type.

        Returns:
            Exact typed provider response.

        Raises:
            ConnectionError: If no authenticated sender is available.
            _CircuitOpenError: If the circuit rejects the call.
            OSError: If provider transport fails.
            TimeoutError: If the configured request timeout expires.
            ValueError: If response type or native correlation is invalid.
        """
        if not self._connected or self._sender is None:
            raise ConnectionError("cTrader session is not connected")
        lock = self._locks.setdefault(response_type, asyncio.Lock())
        async with lock:
            if await self._circuit.before_call() is not None:
                raise _CircuitOpenError("cTrader transport circuit is open")
            await self._admit_rate(type(request).__name__)
            started = time.perf_counter()
            try:
                response = await asyncio.wait_for(
                    self._sender(request), timeout=self._config.request_timeout_sec
                )
            except TimeoutError, OSError, ConnectionError:
                await self._circuit.record_failure(
                    BrokerErrorCode.BROKER_PROVIDER_ERROR
                )
                raise
            else:
                await self._circuit.record_success()
            finally:
                if self._latency_sink is not None:
                    self._latency_sink((time.perf_counter() - started) * 1000.0)
            if not isinstance(response, response_type):
                raise ValueError("unexpected cTrader response type")
            native_id = getattr(response, "clientMsgId", None)
            if request_id is not None and native_id not in {None, request_id}:
                raise ValueError("cTrader native request ID mismatch")
            return response

    async def _admit_rate(self, request_name: str) -> None:
        """Admit one request within the provider's per-connection window.

        Args:
            request_name: Concrete protobuf request class name.

        Raises:
            _RateLimitedError: If the known one-second bound is exhausted.
        """
        is_history = any(
            marker in request_name
            for marker in ("Trendbar", "Reconcile", "DealList", "OrderList")
        )
        window = self._history_requests if is_history else self._other_requests
        limit = 5 if is_history else 50
        now = time.monotonic()
        async with self._rate_lock:
            while window and now - window[0] >= 1.0:
                window.popleft()
            if len(window) >= limit:
                raise _RateLimitedError("cTrader request window exhausted")
            window.append(now)

    def register_event_handler(self, handler: _EventHandler) -> None:
        """Register one adapter-owned provider-event handler.

        Args:
            handler: Callback to receive extracted provider events.

        Raises:
            ConnectionError: If the concrete transport has no event source.
        """
        if self._register_event_handler is None:
            raise ConnectionError("cTrader transport has no provider event source")
        self._register_event_handler(handler)

    def unregister_event_handler(self, handler: _EventHandler) -> None:
        """Unregister one adapter-owned provider-event handler.

        Args:
            handler: Previously registered callback.
        """
        if self._unregister_event_handler is not None:
            self._unregister_event_handler(handler)

    async def close(self) -> None:
        """Release the owned session state."""
        self._connected = False
        logger.bind(
            broker=self._config.broker_id.value,
            environment=self._config.environment.value,
        ).info("cTrader transport session released")
