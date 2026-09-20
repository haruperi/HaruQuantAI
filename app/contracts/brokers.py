"""Public contracts, protocols, DTOs, and capabilities for the Brokers domain.

Purpose:
    Defines the public boundaries, immutable data transfer objects, typed
    protocols, capability tokens, and stable error types for broker catalog
    management, remote transport connections, market data feed connectors
    (Dukascopy, SQ Equity, SQ Futures, Darwinex, Crypto, Yahoo, MT5, cTrader),
    connection health, reconciliation, and fail-closed isolation fencing.

Architecture Invariants:
    * FIP-04: Pure architectural boundaries. No private implementation imports.
    * FR-BROKERS-TRANSPORT_BOUNDARY: Pure transport boundary. Connectors handle
      remote sessions and stream raw payloads; zero data storage, compression,
      or transformation.
    * FR-BROKERS-CREDENTIAL_ISOLATION: Zero plaintext credentials in configs,
      databases, or logs.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any, Protocol

from app.kernel.capability import Capability

# ---------------------------------------------------------------------------
# Enums and Value Types
# ---------------------------------------------------------------------------


class ConnectionState(StrEnum):
    """Lifecycle connection states for broker and feed adapters."""

    DISABLED = "disabled"
    CONNECTING = "connecting"
    READY = "ready"
    DEGRADED = "degraded"
    RECONNECTING = "reconnecting"
    FAILED = "failed"
    CLOSED = "closed"


class OrderSide(StrEnum):
    """Trading order directions."""

    BUY = "buy"
    SELL = "sell"


class OrderType(StrEnum):
    """Trading order types."""

    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"


# ---------------------------------------------------------------------------
# Data Transfer Objects
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class BrokerProfile:
    """Immutable declaration of a broker's platform and symbol traits.

    Mirrors the StrategyQuant X BROKER definition and postfix mapping.
    """

    id: int
    name: str
    is_system: bool
    description: str = ""
    stockpicker_use: bool = False
    mt_use: bool = False
    server_timezone: str = "UTC"
    postfix: str = ""
    enabled: bool = True


@dataclass(frozen=True, slots=True)
class BrokerConnectionConfig:
    """Connection parameters and credentials reference for a broker/feed.

    Credentials strictly reference an OS secret store key, never plaintext.
    """

    connection_id: str
    broker_id: int
    provider_name: str
    environment: str = "demo"  # 'demo' or 'live'
    endpoint: str = ""
    secret_key_ref: str = ""
    timeout_s: float = 30.0
    rate_limit_rps: float = 10.0
    settings: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class RawTransportChunk:
    """Raw transport payload acquired from an external broker or feed.

    Adheres strictly to FR-BROKERS-TRANSPORT_BOUNDARY (pure transport).
    """

    provider: str
    symbol: str
    sequence_num: int
    timestamp_utc: datetime
    payload_bytes: bytes
    is_eof: bool = False
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ConnectionHealth:
    """Health metrics and latency observations for an active connection.

    `latency_ms` represents measured round-trip probe duration in real mode,
    or 0.0 in mock/simulated mode.
    """

    provider: str
    state: ConnectionState
    latency_ms: float = 0.0
    last_heartbeat_utc: datetime | None = None
    error_message: str | None = None


@dataclass(frozen=True, slots=True)
class BrokerOrderIntent:
    """Normalized intent to submit an order to an external trading provider."""

    intent_id: str
    broker_id: int
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: float
    price: float | None = None
    stop_loss: float | None = None
    take_profit: float | None = None
    idempotency_key: str = ""


@dataclass(frozen=True, slots=True)
class BrokerExecutionAck:
    """Normalized acknowledgement or execution receipt from a broker."""

    ack_id: str
    intent_id: str
    provider_ticket: str
    status: str
    price: float
    filled_quantity: float
    timestamp_utc: datetime
    error_message: str | None = None
    is_simulated: bool = False


@dataclass(frozen=True, slots=True)
class ReconciliationReport:
    """Outcome of reconciling internal intents against provider snapshots."""

    provider: str
    matched_count: int
    ambiguous_count: int
    missing_count: int
    timestamp_utc: datetime
    discrepancies: tuple[str, ...] = ()


# ---------------------------------------------------------------------------
# Domain Exceptions
# ---------------------------------------------------------------------------


class BrokerError(Exception):
    """Base exception for all Brokers domain failures."""


class BrokerConnectionError(BrokerError):
    """Raised when establishing or maintaining a remote connection fails."""


class BrokerAuthenticationError(BrokerError):
    """Raised when authentication against an external provider fails."""


class BrokerFencedError(BrokerError):
    """Raised when an operation is rejected because the provider is fenced."""


class BrokerReconciliationError(BrokerError):
    """Raised when post-disconnect reconciliation detects unrecoverable state."""


class UnsupportedCapabilityError(BrokerError):
    """Raised when a requested order or feed capability is not supported."""


# ---------------------------------------------------------------------------
# Service Protocols
# ---------------------------------------------------------------------------


class BrokerCatalogService(Protocol):
    """Protocol for managing broker profiles, postfixes, and timezones."""

    async def get_profiles(self) -> list[BrokerProfile]:
        """Return all registered broker profiles."""
        ...

    async def get_profile(self, broker_id: int) -> BrokerProfile | None:
        """Get a broker profile by integer ID."""
        ...

    async def get_profile_by_name(self, name: str) -> BrokerProfile | None:
        """Get a broker profile by exact name."""
        ...

    async def create_profile(self, profile: BrokerProfile) -> BrokerProfile:
        """Persist a new broker profile."""
        ...

    async def delete_profile(self, broker_id: int) -> bool:
        """Delete a user-defined broker profile (system profiles are protected)."""
        ...

    def resolve_broker_symbol(self, symbol: str, broker_id: int) -> str:
        """Apply broker postfix to symbol (e.g. EURUSD -> EURUSD_roboforex)."""
        ...

    def strip_broker_postfix(self, broker_symbol: str, broker_id: int) -> str:
        """Strip broker postfix back to canonical symbol."""
        ...

    def get_broker_timezone(self, broker_id: int) -> str:
        """Return the server timezone string for the given broker."""
        ...


class BrokerFeedConnector(Protocol):
    """Protocol for external market data feed transport connectors.

    Errors raised:
        * BrokerConnectionError: DNS failure, connection refused, timeout, or TLS
          failure.
        * BrokerAuthenticationError: Missing or invalid API key, token, or license.
        * UnsupportedCapabilityError: Unsupported timeframe, symbol, or date span.
        * BrokerFencedError: Provider locked in fail-closed isolation fence.
    """

    @property
    def provider_name(self) -> str:
        """Identifier of the feed provider."""
        ...

    async def connect(self, config: BrokerConnectionConfig) -> None:
        """Initialize connection session to the provider."""
        ...

    async def disconnect(self) -> None:
        """Terminate connection session."""
        ...

    def is_connected(self) -> bool:
        """Return True if connection is currently active."""
        ...

    def stream_raw_data(
        self,
        symbol: str,
        start_utc: datetime,
        end_utc: datetime,
    ) -> AsyncIterator[RawTransportChunk]:
        """Stream raw transport byte chunks directly to caller without local storage."""
        ...

    async def get_health(self) -> ConnectionHealth:
        """Observe current connection latency and status."""
        ...


class BrokerTradingAdapter(Protocol):
    """Protocol for live/demo trading platform execution adapters.

    Errors raised:
        * BrokerConnectionError: Transport disconnect, timeout, or host unreachable.
        * BrokerAuthenticationError: Unauthenticated live profile or invalid
          credentials.
        * UnsupportedCapabilityError: Unsupported order type or execution
          parameters.
        * BrokerFencedError: Attempting order submission while provider is fenced.
    """

    @property
    def provider_name(self) -> str:
        """Identifier of the trading platform."""
        ...

    async def connect(self, config: BrokerConnectionConfig) -> None:
        """Establish session with the trading terminal or gateway."""
        ...

    async def disconnect(self) -> None:
        """Close session with the trading platform."""
        ...

    def is_connected(self) -> bool:
        """Return True if connection is ready to execute."""
        ...

    async def submit_order(self, intent: BrokerOrderIntent) -> BrokerExecutionAck:
        """Submit a trading command idempotently."""
        ...

    async def cancel_order(self, provider_ticket: str) -> bool:
        """Cancel an open order on the provider platform."""
        ...

    async def get_open_orders(self) -> list[BrokerExecutionAck]:
        """Query currently active orders from the provider."""
        ...

    async def get_positions(self) -> list[dict[str, Any]]:
        """Query currently active positions from the provider."""
        ...

    async def get_health(self) -> ConnectionHealth:
        """Observe connection latency and status."""
        ...


class BrokerReconciliationService(Protocol):
    """Protocol for validating provider state after reconnect."""

    async def reconcile(
        self,
        provider_name: str,
        active_intents: Sequence[BrokerOrderIntent],
        provider_orders: Sequence[BrokerExecutionAck] = (),
    ) -> ReconciliationReport:
        """Compare local intent states against provider order/position snapshots."""
        ...


class BrokerFencingService(Protocol):
    """Protocol for fail-closed disconnect and uncertainty fencing."""

    def is_fenced(self, provider_name: str) -> bool:
        """Return True if the provider is currently locked in fail-closed mode."""
        ...

    def trip_fence(self, provider_name: str, reason: str) -> None:
        """Manually or automatically engage fail-closed circuit breaker."""
        ...

    def reset_fence(self, provider_name: str) -> None:
        """Clear fence lock after verified reconciliation."""
        ...

    def assert_safe_to_submit(self, provider_name: str) -> None:
        """Raise BrokerFencedError if provider is fenced."""
        ...


class BrokerPersistenceService(Protocol):
    """Protocol for SQLite storage of broker metadata under namespace brokers.v1."""

    async def list_profiles(self) -> list[BrokerProfile]:
        """Fetch all stored broker profiles."""
        ...

    async def get_profile(self, broker_id: int) -> BrokerProfile | None:
        """Fetch a single broker profile by ID."""
        ...

    async def get_profile_by_name(self, name: str) -> BrokerProfile | None:
        """Fetch a single broker profile by name."""
        ...

    async def save_profile(self, profile: BrokerProfile) -> BrokerProfile:
        """Insert or update a broker profile."""
        ...

    async def delete_profile(self, broker_id: int) -> bool:
        """Delete a profile if not protected as a system profile."""
        ...

    async def save_connection_config(self, config: BrokerConnectionConfig) -> None:
        """Save connection configuration metadata (credentials referenced by key)."""
        ...

    async def get_connection_config(
        self,
        connection_id: str,
    ) -> BrokerConnectionConfig | None:
        """Retrieve connection configuration metadata."""
        ...


# ---------------------------------------------------------------------------
# Capability Tokens
# ---------------------------------------------------------------------------

BROKER_CATALOG: Capability[BrokerCatalogService] = Capability("brokers.catalog@1")
BROKER_MT5: Capability[BrokerTradingAdapter] = Capability("brokers.mt5@1")
BROKER_CTRADER: Capability[BrokerTradingAdapter] = Capability("brokers.ctrader@1")
BROKER_DUKASCOPY: Capability[BrokerFeedConnector] = Capability("brokers.dukascopy@1")
BROKER_EQUITY: Capability[BrokerFeedConnector] = Capability("brokers.equity@1")
BROKER_FUTURES: Capability[BrokerFeedConnector] = Capability("brokers.futures@1")
BROKER_DARWINEX: Capability[BrokerFeedConnector] = Capability("brokers.darwinex@1")
BROKER_CRYPTO: Capability[BrokerFeedConnector] = Capability("brokers.crypto@1")
BROKER_YAHOO: Capability[BrokerFeedConnector] = Capability("brokers.yahoo@1")
BROKER_RECONCILIATION: Capability[BrokerReconciliationService] = Capability(
    "brokers.reconciliation@1"
)
BROKER_FENCING: Capability[BrokerFencingService] = Capability("brokers.fencing@1")
BROKER_PERSISTENCE: Capability[BrokerPersistenceService] = Capability(
    "persistence.brokers@1"
)
