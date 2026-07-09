"""Shared test fixtures for trading action primitive tests."""
# ruff: noqa: ARG002

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import TypedDict

from app.services.trading.actions._common import TradingActionDependencies
from app.services.trading.actions.validation import (
    AccountMarginContext,
    DailyRailState,
    DefenseInDepthRailLimits,
    OrderValidationContext,
    SymbolTradingConstraints,
)
from app.services.trading.contracts import (
    JsonObject,
    JsonValue,
    MutationCapability,
    PromotionStage,
    TradingRoute,
)


class RouteKwargs(TypedDict):
    """Common route/promotion/mutation-capability keyword bundle."""

    route: TradingRoute
    promotion_stage: PromotionStage
    mutation_capability: MutationCapability


ROUTE_KWARGS: RouteKwargs = {
    "route": TradingRoute.SIM,
    "promotion_stage": PromotionStage.SIMULATION,
    "mutation_capability": MutationCapability.PACKAGED_ONLY,
}


def as_dict(value: JsonValue) -> JsonObject:
    """Narrow a JSON value to a JSON object for test assertions.

    Args:
        value: JSON value expected to be a JSON object.

    Returns:
        JsonObject: The same value, narrowed to a JSON object.
    """
    assert isinstance(value, dict)  # noqa: S101
    return value


class FixedClock:
    """Deterministic test clock."""

    def __init__(self, moment: datetime | None = None) -> None:
        """Initialize the fixed clock.

        Args:
            moment: Optional fixed UTC timestamp.
        """
        self._moment = moment or datetime(2026, 7, 9, 10, 0, tzinfo=UTC)

    def now_utc(self) -> datetime:
        """Return the fixed UTC timestamp."""
        return self._moment

    def now_ptp(self) -> datetime:
        """Return the fixed PTP timestamp."""
        return self._moment

    def monotonic(self) -> float:
        """Return a fixed monotonic value."""
        return 10.0


class FixedRNG:
    """Deterministic test pseudo-random generator."""

    def random(self) -> float:
        """Return a fixed pseudo-random draw."""
        return 0.5

    def randint(self, lower_inclusive: int, upper_inclusive: int) -> int:
        """Return the midpoint of the requested inclusive range."""
        return lower_inclusive + (upper_inclusive - lower_inclusive) // 2


class FakeIdempotencyStore:
    """In-memory idempotency store port double."""

    def __init__(self) -> None:
        """Initialize the empty in-memory reservation table."""
        self._seen: set[str] = set()

    def reserve(
        self,
        *,
        route: TradingRoute,
        tenant_id: str,
        key: str,
        material_hash: str,
        expires_at: datetime,
    ) -> JsonObject:
        """Reserve a key, reporting whether it was already seen."""
        first = key not in self._seen
        self._seen.add(key)
        return {"decision": "reserved" if first else "duplicate", "route": route.value}

    def resolve(self, **_: object) -> JsonObject | None:
        """Return no cached resolution for this double."""
        return None

    def complete(self, **_: object) -> None:
        """No-op completion for this double."""
        return


class FakeEventJournal:
    """In-memory append-only event journal port double."""

    def __init__(self) -> None:
        """Initialize the empty in-memory event list."""
        self.events: list[JsonObject] = []

    def append(self, *, event: JsonObject, recorded_at: datetime) -> str:
        """Append an event and return a synthetic reference."""
        self.events.append(event)
        return f"journal-{len(self.events)}"

    def scan_unresolved(self, **_: object) -> tuple[JsonObject, ...]:
        """Return no unresolved entries for this double."""
        return ()


class FakeTradeStore:
    """In-memory trade projection store port double."""

    def __init__(self) -> None:
        """Initialize empty in-memory projection lists."""
        self.positions: list[JsonObject] = []
        self.orders: list[JsonObject] = []

    def save_order_state(self, *, order_state: JsonObject, **_: object) -> str:
        """Persist an order state projection in memory."""
        self.orders.append(order_state)
        return f"order-ref-{len(self.orders)}"

    def save_position_state(self, *, position_state: JsonObject, **_: object) -> str:
        """Persist a position state projection in memory."""
        self.positions.append(position_state)
        return f"position-ref-{len(self.positions)}"

    def record_execution_fill(self, **_: object) -> JsonObject:
        """Return an empty fill projection for this double."""
        return {}

    def apply_corporate_action(self, **_: object) -> JsonObject:
        """Return an empty adjustment projection for this double."""
        return {}


def build_constraints(**overrides: object) -> SymbolTradingConstraints:
    """Build symbol trading constraints with sane EURUSD-like defaults."""
    defaults: dict[str, object] = {
        "symbol": "EURUSD",
        "digits": 5,
        "volume_min": Decimal("0.01"),
        "volume_max": Decimal(100),
        "volume_step": Decimal("0.01"),
        "tick_size": Decimal("0.00001"),
        "min_stop_distance": Decimal("0.0005"),
        "contract_size": Decimal(100000),
        "quote_currency": "USD",
        "price_collar_bps": Decimal(50),
    }
    defaults.update(overrides)
    return SymbolTradingConstraints(**defaults)  # type: ignore[arg-type]


def build_account(**overrides: object) -> AccountMarginContext:
    """Build account margin context with sane defaults."""
    defaults: dict[str, object] = {
        "account_currency": "USD",
        "leverage": 100,
        "free_margin": Decimal(10000),
    }
    defaults.update(overrides)
    return AccountMarginContext(**defaults)  # type: ignore[arg-type]


def build_rail_limits(**overrides: object) -> DefenseInDepthRailLimits:
    """Build defense-in-depth rail limits with permissive defaults."""
    defaults: dict[str, object] = {
        "max_mutation_attempts_per_window": 10,
        "window_seconds": 60,
        "max_open_positions": 5,
        "daily_notional_ceiling": Decimal(1000000),
    }
    defaults.update(overrides)
    return DefenseInDepthRailLimits(**defaults)  # type: ignore[arg-type]


def build_rail_state(**overrides: object) -> DailyRailState:
    """Build daily rail counters starting from zero."""
    defaults: dict[str, object] = {
        "mutation_attempts_in_window": 0,
        "open_positions_count": 0,
        "cumulative_daily_notional": Decimal(0),
    }
    defaults.update(overrides)
    return DailyRailState(**defaults)  # type: ignore[arg-type]


def build_context(**overrides: object) -> OrderValidationContext:
    """Build a permissive order validation context for EURUSD at 1.10000."""
    defaults: dict[str, object] = {
        "route": TradingRoute.SIM,
        "reference_price": Decimal("1.10000"),
        "constraints": build_constraints(),
        "account_margin": build_account(),
        "fat_finger_ceiling": Decimal(50000),
        "rail_limits": build_rail_limits(),
        "rail_state": build_rail_state(),
    }
    defaults.update(overrides)
    return OrderValidationContext(**defaults)  # type: ignore[arg-type]


def build_deps(**overrides: object) -> TradingActionDependencies:
    """Build shared trading action dependencies with in-memory doubles."""
    defaults: dict[str, object] = {
        "clock": FixedClock(),
        "rng": FixedRNG(),
        "tenant_id": "tenant-1",
        "idempotency_store": FakeIdempotencyStore(),
        "event_journal": FakeEventJournal(),
        "trade_store": FakeTradeStore(),
    }
    defaults.update(overrides)
    return TradingActionDependencies(**defaults)  # type: ignore[arg-type]
