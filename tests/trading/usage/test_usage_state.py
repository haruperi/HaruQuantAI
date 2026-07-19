"""Runnable usage evidence for the public Trading state API."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.services.trading.contracts import TradingRequest, TradingRoute
from app.services.trading.state import (
    TRADING_SCHEMA_VERSION,
    IdempotencyReservation,
    TradingEvent,
    TradingProjection,
    TradingStateStore,
    apply_execution_event,
    get_trading_migrations,
    reserve_idempotency,
)

NOW = datetime(2026, 7, 19, 8, 0, tzinfo=UTC)
type Scope = tuple[TradingRoute, str, str]


class _UsageStore:
    """Bounded in-memory implementation demonstrating the injected port."""

    def __init__(self) -> None:
        """Initialize isolated usage state."""
        self.reservations: dict[str, IdempotencyReservation] = {}
        self.events: list[TradingEvent] = []
        self.projections: dict[Scope, TradingProjection] = {}

    def reserve_idempotency(
        self,
        key: str,
        material_hash: str,
        material_version: str,
        reserved_at: datetime,
        expires_at: datetime,
    ) -> IdempotencyReservation:
        """Reserve one caller key or return its active duplicate."""
        existing = self.reservations.get(key)
        if existing is not None:
            status = (
                "duplicate_active"
                if existing.material_hash == material_hash
                else "conflict"
            )
            return IdempotencyReservation.model_validate(
                {**existing.model_dump(mode="python"), "status": status}
            )
        reservation = IdempotencyReservation(
            key=key,
            material_hash=material_hash,
            material_version=material_version,
            status="new",
            reserved_at=reserved_at,
            expires_at=expires_at,
        )
        self.reservations[key] = reservation
        return reservation

    def append_event(self, event: TradingEvent) -> None:
        """Append one immutable event."""
        self.events.append(event)

    def load_projection(self, scope: Scope) -> TradingProjection | None:
        """Load the projection for one exact scope."""
        return self.projections.get(scope)

    def save_projection(
        self,
        projection: TradingProjection,
        expected_version: int,
    ) -> None:
        """Save a projection when optimistic version matches."""
        scope = (projection.route, projection.tenant_id, projection.authority_id)
        current = self.projections.get(scope)
        current_version = 0 if current is None else current.version
        if current_version != expected_version:
            raise RuntimeError("stale usage projection")
        self.projections[scope] = projection

    def load_unresolved_attempts(self, scope: Scope) -> tuple[TradingEvent, ...]:
        """Return scoped send attempts without authority resolution."""
        route, tenant_id, authority_id = scope
        return tuple(
            event
            for event in self.events
            if event.event_type == "send_attempted"
            and (event.route, event.tenant_id, event.authority_id)
            == (route, tenant_id, authority_id)
        )

    def load_report_evidence(self, scope: Scope) -> dict[str, object]:
        """Return bounded empty report evidence for one exact scope."""
        del scope
        return {}


def _request() -> TradingRequest:
    """Build one governed request for idempotency usage."""
    return TradingRequest(
        request_id="usage-request-001",
        workflow_id="usage-workflow-001",
        correlation_id="usage-correlation-001",
        route="sim",
        action="submit_order",
        account_id="usage-account-001",
        strategy_id="usage-strategy-001",
        strategy_version="v1",
        intent_id="usage-intent-001",
        symbol="EURUSD",
        side="BUY",
        order_type="MARKET",
        quantity_unit="units",
        quantity="1.00",
        risk_decision_id="usage-risk-001",
        action_policy_verdict_id="usage-verdict-001",
        approval_token_ref="usage-approval-001",
        idempotency_key="usage-key-001",
        canonical_material_version="v1",
        system_time=NOW,
        valid_until=NOW + timedelta(minutes=5),
    )


def _event(event_id: str = "usage-event-001") -> TradingEvent:
    """Build one scoped usage event."""
    return TradingEvent(
        event_id=event_id,
        event_type="send_attempted",
        aggregate_version=0,
        route="sim",
        tenant_id="usage-tenant-001",
        authority_id="simulator",
        occurred_at=NOW,
        request_id="usage-request-001",
        workflow_id="usage-workflow-001",
        correlation_id="usage-correlation-001",
        payload={"order_id": "usage-order-001"},
    )


def _projection(version: int = 1) -> TradingProjection:
    """Build one exact-scope projection."""
    return TradingProjection(
        route="sim",
        tenant_id="usage-tenant-001",
        authority_id="simulator",
        version=version,
        orders={},
        positions={},
        fills={},
        receipts={},
        authority_state={},
        updated_at=NOW,
    )


def test_usage_events_trading_event() -> None:
    """Create a versioned redacted Trading execution event."""
    assert _event().event_version == "v1"


def test_usage_stores_trading_state_store() -> None:
    """Inject an implementation satisfying the minimal state port."""
    store: TradingStateStore = _UsageStore()
    assert store.load_projection((TradingRoute.SIM, "tenant", "simulator")) is None


def test_usage_idempotency_reserve() -> None:
    """Reserve canonical material before authority dispatch."""
    assert (
        reserve_idempotency(
            _request(),
            _UsageStore(),
            reservation_time=NOW,
            retention_seconds=300,
            concurrency_lock_timeout_seconds=Decimal(30),
        ).status
        == "new"
    )


def test_usage_projections_apply_event() -> None:
    """Apply one ordered event to an optimistic projection."""
    assert apply_execution_event(_event(), _UsageStore()).version == 1


def test_usage_migrations_schema_version() -> None:
    """Read the current Trading-owned schema version."""
    assert TRADING_SCHEMA_VERSION == "v1"


def test_usage_migrations_get_migrations() -> None:
    """Pass additive definitions to Data without opening a database."""
    assert get_trading_migrations()[0].domain == "trading"


def test_usage_stores_reserve_idempotency() -> None:
    """Call the store's atomic caller-key reservation operation."""
    result = _UsageStore().reserve_idempotency(
        "usage-key", "a" * 64, "v1", NOW, NOW + timedelta(minutes=5)
    )
    assert result.status == "new"


def test_usage_stores_append_event() -> None:
    """Append one immutable event through the store port."""
    store = _UsageStore()
    store.append_event(_event())
    assert len(store.events) == 1


def test_usage_stores_load_projection() -> None:
    """Load a projection using exact route/tenant/authority scope."""
    store = _UsageStore()
    projection = _projection()
    store.projections[
        (projection.route, projection.tenant_id, projection.authority_id)
    ] = projection
    assert store.load_projection((TradingRoute.SIM, "usage-tenant-001", "simulator"))


def test_usage_stores_save_projection() -> None:
    """Save a projection with optimistic version evidence."""
    store = _UsageStore()
    store.save_projection(_projection(), 0)
    assert len(store.projections) == 1


def test_usage_stores_load_unresolved_attempts() -> None:
    """Read unresolved attempts within one exact conflict scope."""
    store = _UsageStore()
    store.append_event(_event())
    scope = (TradingRoute.SIM, "usage-tenant-001", "simulator")
    assert len(store.load_unresolved_attempts(scope)) == 1


def test_usage_stores_load_report_evidence() -> None:
    """Load exact stored report facts without deriving Analytics metrics."""
    store = _UsageStore()
    scope = (TradingRoute.SIM, "usage-tenant-001", "simulator")
    assert store.load_report_evidence(scope) == {}


def test_usage_idempotency_reservation() -> None:
    """Inspect a finite immutable reservation decision."""
    reservation = _UsageStore().reserve_idempotency(
        "usage-key", "b" * 64, "v1", NOW, NOW + timedelta(minutes=5)
    )
    assert reservation.status == "new"


def test_usage_projections_trading_projection() -> None:
    """Inspect a route/tenant/authority-scoped projection."""
    assert _projection().authority_id == "simulator"
