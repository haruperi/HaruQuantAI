"""Unit tests for the state reconciliation submodule."""

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import pytest
from app.services.trading.config.models import (
    ReconciliationSettings,
    RouteSettings,
    SecretReference,
    StoreConnectionTargets,
    TradingRuntimeConfig,
)
from app.services.trading.contracts import (
    JsonObject,
    TradingRoute,
)
from app.services.trading.execution.reporting import ReconciliationDiscrepancyEntry
from app.services.trading.execution.state_machine import LifecycleKind
from app.services.trading.gates._common import GateStepStatus
from app.services.trading.reconciliation.authority_and_retry_guard import (
    AuthorityAndRetryGuard,
    evaluate_reconciliation_authority_gate,
)
from app.services.trading.reconciliation.service import (
    ReconciliationService,
)
from app.services.trading.reconciliation.snapshots_and_compare import (
    _compare_balance,
    _compare_margin,
    _map_broker_order_state,
    compare_snapshots,
)


class MockClock:
    """Mock clock for deterministic test execution."""

    def now_utc(self) -> datetime:
        return datetime(2026, 7, 9, 12, 0, 0, tzinfo=UTC)

    def monotonic(self) -> float:
        return 123.456


class MockEventJournal:
    """Mock event journal to record events."""

    def __init__(self) -> None:
        self.events: list[JsonObject] = []

    def append_event(
        self,
        *,
        event_type: str,
        request_id: str,
        correlation_id: str,
        route: TradingRoute,
        account_id: str,
        symbol: str,
        actor: str,
        payload: JsonObject,
    ) -> JsonObject:
        event = {
            "event_type": event_type,
            "request_id": request_id,
            "correlation_id": correlation_id,
            "route": route.value,
            "account_id": account_id,
            "symbol": symbol,
            "actor": actor,
            "payload": payload,
        }
        self.events.append(event)
        return event


class MockStateStore:
    """Mock state store snapshot manager."""

    def __init__(self) -> None:
        self.state: dict[str, JsonObject] = {}

    def load_state(
        self, *, route: TradingRoute, tenant_id: str, snapshot_id: str
    ) -> JsonObject | None:
        return self.state.get(f"{route.value}:{tenant_id}:{snapshot_id}")

    def save_state(
        self,
        *,
        route: TradingRoute,
        tenant_id: str,
        snapshot: JsonObject,
        expected_version: int | None,
    ) -> str:
        key = f"{route.value}:{tenant_id}:{snapshot.get('id', 'latest')}"
        self.state[key] = snapshot
        return key


class MockTradeStore:
    """Mock trade store port."""

    def __init__(self) -> None:
        self.orders: list[JsonObject] = []
        self.positions: list[JsonObject] = []
        self.saved_positions: list[JsonObject] = []

    def list_order_states(
        self, *, route: TradingRoute, tenant_id: str
    ) -> list[JsonObject]:
        return self.orders

    def list_position_states(
        self, *, route: TradingRoute, tenant_id: str
    ) -> list[JsonObject]:
        return self.positions

    def save_position_state(
        self,
        *,
        route: TradingRoute,
        tenant_id: str,
        position_state: JsonObject,
        expected_version: int | None,
    ) -> str:
        self.saved_positions.append(position_state)
        return "pos-ref"


# ---------------------------------------------------------------------------
# Snapshots and Compare Tests
# ---------------------------------------------------------------------------


def test_map_broker_order_state() -> None:
    # String mapping
    assert _map_broker_order_state("NEW") == "NEW"
    assert _map_broker_order_state("SUBMITTED") == "NEW"
    assert _map_broker_order_state("STARTED") == "NEW"
    assert _map_broker_order_state("placed") == "NEW"
    assert _map_broker_order_state("REQUEST SENT") == "NEW"
    assert _map_broker_order_state("PARTIAL") == "PARTIALLY_FILLED"
    assert _map_broker_order_state("PARTIALLY_FILLED") == "PARTIALLY_FILLED"
    assert _map_broker_order_state("FILLED") == "FILLED"
    assert _map_broker_order_state("canceled") == "CANCELLED"
    assert _map_broker_order_state("CANCELLED") == "CANCELLED"
    assert _map_broker_order_state("REQUEST CANCELLED") == "CANCELLED"
    assert _map_broker_order_state("REJECTED") == "REJECTED"
    assert _map_broker_order_state("EXPIRED") == "EXPIRED"
    assert _map_broker_order_state("SOMETHING_ELSE") == "UNKNOWN"

    # Integer mapping
    assert _map_broker_order_state(0) == "NEW"
    assert _map_broker_order_state(1) == "NEW"
    assert _map_broker_order_state(7) == "NEW"
    assert _map_broker_order_state(3) == "PARTIALLY_FILLED"
    assert _map_broker_order_state(4) == "FILLED"
    assert _map_broker_order_state(2) == "CANCELLED"
    assert _map_broker_order_state(8) == "CANCELLED"
    assert _map_broker_order_state(5) == "REJECTED"
    assert _map_broker_order_state(6) == "EXPIRED"
    assert _map_broker_order_state(999) == "UNKNOWN"

    # Incompatible types
    assert _map_broker_order_state(None) == "UNKNOWN"
    assert _map_broker_order_state([]) == "UNKNOWN"
    assert _map_broker_order_state("INVALID_INT") == "UNKNOWN"


def test_compare_balance() -> None:
    det = "2026-07-09T12:00:00"
    disc = _compare_balance(
        local_balance=Decimal("1000.00"),
        broker_balance=Decimal("1000.00"),
        balance_drift_threshold=Decimal("0.05"),
        detected_at=det,
    )
    assert disc is None

    disc = _compare_balance(
        local_balance=Decimal("1000.00"),
        broker_balance=Decimal("1000.10"),
        balance_drift_threshold=Decimal("0.05"),
        detected_at=det,
    )
    assert disc is not None
    assert disc.discrepancy_type == "balance_mismatch"
    assert disc.local_value == "1000.00"
    assert disc.broker_value == "1000.10"


def test_compare_margin() -> None:
    det = "2026-07-09T12:00:00"
    disc = _compare_margin(
        local_margin=Decimal("200.00"),
        broker_margin=Decimal("200.00"),
        margin_drift_threshold=Decimal("0.05"),
        detected_at=det,
    )
    assert disc is None

    disc = _compare_margin(
        local_margin=Decimal("200.00"),
        broker_margin=Decimal("200.10"),
        margin_drift_threshold=Decimal("0.05"),
        detected_at=det,
    )
    assert disc is not None
    assert disc.discrepancy_type == "margin_mismatch"
    assert disc.local_value == "200.00"
    assert disc.broker_value == "200.10"


def test_compare_snapshots_order_cases() -> None:
    clock = MockClock()

    # Skip terminal order local states
    local_orders = [
        {"order_id": "1", "symbol": "EURUSD", "state": "FILLED"},
        {
            "order_id": "2",
            "symbol": "EURUSD",
            "state": "NEW",
            "remaining_volume": "1.0",
            "vwap": "1.10",
        },
        {
            "order_id": "3",
            "symbol": "EURUSD",
            "state": "NEW",
            "remaining_volume": "1.0",
        },  # None price case
    ]
    broker_orders = [
        {
            "ticket": "2",
            "symbol": "EURUSD",
            "state": "NEW",
            "volume_current": "1.0001",
            "price": "1.10",
        },
        {
            "ticket": "3",
            "symbol": "EURUSD",
            "state": "NEW",
            "volume_current": "1.0",
            "price": "1.10",
        },  # None price locally
    ]

    # Thresholds: volume threshold is 0.00005, price threshold is 0.001
    discs = compare_snapshots(
        local_orders=local_orders,
        broker_orders=broker_orders,
        local_positions=[],
        broker_positions=[],
        local_balance=Decimal(100),
        broker_balance=Decimal(100),
        local_margin=Decimal(50),
        broker_margin=Decimal(50),
        price_drift_threshold=Decimal("0.001"),
        volume_drift_threshold=Decimal("0.00005"),
        balance_drift_threshold=Decimal("0.1"),
        margin_drift_threshold=Decimal("0.1"),
        clock=clock,
    )
    assert len(discs) == 1
    assert discs[0].discrepancy_type == "volume_mismatch"

    # Price drift case
    broker_orders[0]["price"] = "1.102"
    discs = compare_snapshots(
        local_orders=local_orders,
        broker_orders=broker_orders,
        local_positions=[],
        broker_positions=[],
        local_balance=Decimal(100),
        broker_balance=Decimal(100),
        local_margin=Decimal(50),
        broker_margin=Decimal(50),
        price_drift_threshold=Decimal("0.001"),
        volume_drift_threshold=Decimal("0.01"),
        balance_drift_threshold=Decimal("0.1"),
        margin_drift_threshold=Decimal("0.1"),
        clock=clock,
    )
    assert len(discs) == 1
    assert discs[0].discrepancy_type == "price_mismatch"

    # State mismatch case
    broker_orders[0]["price"] = "1.10"
    broker_orders[0]["state"] = "PARTIAL"
    discs = compare_snapshots(
        local_orders=local_orders,
        broker_orders=broker_orders,
        local_positions=[],
        broker_positions=[],
        local_balance=Decimal(100),
        broker_balance=Decimal(100),
        local_margin=Decimal(50),
        broker_margin=Decimal(50),
        price_drift_threshold=Decimal("0.001"),
        volume_drift_threshold=Decimal("0.01"),
        balance_drift_threshold=Decimal("0.1"),
        margin_drift_threshold=Decimal("0.1"),
        clock=clock,
    )
    assert len(discs) == 1
    assert discs[0].discrepancy_type == "state_mismatch"

    # Order missing at broker
    discs = compare_snapshots(
        local_orders=local_orders,
        broker_orders=[],
        local_positions=[],
        broker_positions=[],
        local_balance=Decimal(100),
        broker_balance=Decimal(100),
        local_margin=Decimal(50),
        broker_margin=Decimal(50),
        price_drift_threshold=Decimal("0.001"),
        volume_drift_threshold=Decimal("0.01"),
        balance_drift_threshold=Decimal("0.1"),
        margin_drift_threshold=Decimal("0.1"),
        clock=clock,
    )
    # Order 1 is FILLED (skipped), order 2 and 3 are NEW (missing at broker)
    assert len(discs) == 2
    assert discs[0].discrepancy_type == "missing_at_broker"


def test_compare_snapshots_position_cases() -> None:
    clock = MockClock()

    local_positions = [
        {"position_id": "pos-1", "symbol": "EURUSD", "volume": "1.0", "vwap": "1.10"},
        {"position_id": "pos-2", "symbol": "EURUSD", "volume": "1.0"},  # None VWAP case
        {
            "position_id": "pos-3",
            "symbol": "EURUSD",
            "volume": "1.0",
            "vwap": "1.10",
        },  # Missing at broker case
    ]
    broker_positions = [
        {
            "position_id": "pos-1",
            "symbol": "EURUSD",
            "volume": "1.002",
            "price_open": "1.10",
        },
        {
            "position_id": "pos-2",
            "symbol": "EURUSD",
            "volume": "1.0",
            "price_open": "1.10",
        },  # None VWAP locally
    ]

    # Volume mismatch and missing at broker for pos-3
    discs = compare_snapshots(
        local_orders=[],
        broker_orders=[],
        local_positions=local_positions,
        broker_positions=broker_positions,
        local_balance=Decimal(100),
        broker_balance=Decimal(100),
        local_margin=Decimal(50),
        broker_margin=Decimal(60),
        price_drift_threshold=Decimal("0.001"),
        volume_drift_threshold=Decimal("0.001"),
        balance_drift_threshold=Decimal("0.1"),
        margin_drift_threshold=Decimal("0.1"),
        clock=clock,
    )
    # pos-1 has volume mismatch, pos-3 missing at broker, and margin mismatch
    assert len(discs) == 3
    assert {d.discrepancy_type for d in discs} == {
        "volume_mismatch",
        "missing_at_broker",
        "margin_mismatch",
    }

    # VWAP mismatch
    broker_positions[0]["volume"] = "1.0"
    broker_positions[0]["price_open"] = "1.105"
    discs = compare_snapshots(
        local_orders=[],
        broker_orders=[],
        local_positions=[local_positions[0]],
        broker_positions=[broker_positions[0]],
        local_balance=Decimal(100),
        broker_balance=Decimal(100),
        local_margin=Decimal(50),
        broker_margin=Decimal(50),
        price_drift_threshold=Decimal("0.001"),
        volume_drift_threshold=Decimal("0.01"),
        balance_drift_threshold=Decimal("0.1"),
        margin_drift_threshold=Decimal("0.1"),
        clock=clock,
    )
    assert len(discs) == 1
    assert discs[0].discrepancy_type == "vwap_mismatch"


def test_snapshots_and_compare_empty_keys_coverage() -> None:
    # Coverage for empty ID checks in loop builds
    local_orders = [
        {"state": "NEW", "remaining_volume": "1.0"},  # empty ticket/order_id
    ]
    broker_orders = [
        {"symbol": "EURUSD"},  # empty ticket
    ]
    local_positions = [
        {"volume": "1.0"},  # empty position_id/ticket/symbol
    ]
    broker_positions = [
        {"volume": "1.0"},  # empty position_id/ticket/symbol
    ]

    discs = compare_snapshots(
        local_orders=local_orders,
        broker_orders=broker_orders,
        local_positions=local_positions,
        broker_positions=broker_positions,
        local_balance=Decimal(100),
        broker_balance=Decimal(100),
        local_margin=Decimal(50),
        broker_margin=Decimal(50),
        price_drift_threshold=Decimal("0.01"),
        volume_drift_threshold=Decimal("0.01"),
        balance_drift_threshold=Decimal("0.1"),
        margin_drift_threshold=Decimal("0.1"),
        clock=MockClock(),
    )
    # The empty ticket orders and positions should be ignored in the dict keys and not compared
    assert len(discs) == 0


# ---------------------------------------------------------------------------
# Authority Guard Tests
# ---------------------------------------------------------------------------


def test_authority_guard_blocks_and_resolves() -> None:
    guard = AuthorityAndRetryGuard()

    # Default: unblocked
    assert not guard.is_blocked("acct-1", "EURUSD")

    # Transition to unresolved: symbol-specific
    guard.transition_to_unresolved("acct-1", "EURUSD", "req-1")
    assert guard.is_blocked("acct-1", "EURUSD")
    assert not guard.is_blocked("acct-1", "GBPUSD")

    # Resolve symbol-specific
    guard.resolve_scope("acct-1", "EURUSD")
    assert not guard.is_blocked("acct-1", "EURUSD")

    # Transition to unresolved: account-wide
    guard.transition_to_unresolved("acct-1", None, "req-2")
    assert guard.is_blocked("acct-1", "EURUSD")
    assert guard.is_blocked("acct-1", "GBPUSD")

    # Resolve account-wide
    guard.resolve_scope("acct-1", None)
    assert not guard.is_blocked("acct-1", "EURUSD")

    # Stream gap: symbol-specific
    guard.report_stream_gap("acct-1", "EURUSD")
    assert guard.is_blocked("acct-1", "EURUSD")
    assert not guard.is_blocked("acct-1", "GBPUSD")

    # Stream gap: account-wide
    guard.report_stream_gap("acct-1", None)
    assert guard.is_blocked("acct-1", "GBPUSD")

    # Resolve account-wide checks cleanups with active symbol blocks
    guard.transition_to_unresolved("acct-1", "EURUSD", "req-3")
    guard.report_stream_gap("acct-1", "GBPUSD")
    guard.resolve_scope("acct-1", None)
    assert not guard.is_blocked("acct-1", "EURUSD")
    assert not guard.is_blocked("acct-1", "GBPUSD")


def test_authority_guard_duplicates() -> None:
    guard = AuthorityAndRetryGuard()

    # Empty event ID is ignored
    assert not guard.process_event_id("")

    # First view returns False
    assert not guard.process_event_id("evt-1")

    # Second view returns True (duplicate) and increments count
    assert guard.process_event_id("evt-1")
    assert guard.duplicate_count == 1


def test_reconciliation_authority_gate() -> None:
    guard = AuthorityAndRetryGuard()

    # Pass case
    result = evaluate_reconciliation_authority_gate(
        guard=guard, account_id="acct-1", symbol="EURUSD"
    )
    assert result.status is GateStepStatus.PASSED

    # Block case
    guard.transition_to_unresolved("acct-1", "EURUSD", "req-1")
    result = evaluate_reconciliation_authority_gate(
        guard=guard, account_id="acct-1", symbol="EURUSD"
    )
    assert result.status is GateStepStatus.BLOCKED
    assert result.reason_code == "RECONCILIATION_REQUIRED"


# ---------------------------------------------------------------------------
# Reconciliation Service Tests
# ---------------------------------------------------------------------------


class DummyBrokerRecord:
    """Mock broker record."""

    def __init__(self, **kwargs: Any) -> None:
        for k, v in kwargs.items():
            setattr(self, k, v)


@pytest.fixture
def base_config() -> TradingRuntimeConfig:
    return TradingRuntimeConfig(
        active_broker="test_broker",
        store_targets=StoreConnectionTargets(
            trade_store_ref="t_store",
            state_store_ref="s_store",
            audit_sink_ref="audit",
            idempotency_store_ref="idem",
            event_journal_ref="journal",
        ),
        route_settings=RouteSettings(
            enabled_routes=frozenset(
                {
                    TradingRoute.SIM,
                    TradingRoute.PAPER,
                    TradingRoute.SHADOW,
                    TradingRoute.LIVE,
                }
            ),
            allow_live_mutations=True,
        ),
        reconciliation=ReconciliationSettings(
            price_drift_threshold=Decimal("0.01"),
            volume_drift_threshold=Decimal("0.001"),
            balance_drift_threshold=Decimal("0.10"),
            margin_drift_threshold=Decimal("0.10"),
            orphan_deal_policy="block",
        ),
        secret_references={
            "broker_credentials": SecretReference(reference="vault://broker"),
            "database_credentials": SecretReference(reference="vault://db"),
        },
    )


def test_reconciliation_settings_validator() -> None:
    with pytest.raises(ValueError, match="orphan_deal_policy"):
        ReconciliationSettings(orphan_deal_policy="invalid_policy")


def test_reconciliation_service_success(
    base_config: TradingRuntimeConfig, monkeypatch: pytest.MonkeyPatch
) -> None:
    trade_store = MockTradeStore()
    state_store = MockStateStore()
    journal = MockEventJournal()
    guard = AuthorityAndRetryGuard()
    clock = MockClock()

    service = ReconciliationService(
        trade_store=trade_store,
        state_store=state_store,
        journal=journal,
        authority_guard=guard,
        clock=clock,
        config=base_config,
    )

    # Mock broker responses with no discrepancies (globally in both imports namespaces)
    def mock_broker_call(name: str, *args: Any, **kwargs: Any) -> Any:
        if name == "get_order_info":
            return [
                DummyBrokerRecord(
                    ticket=123, symbol="EURUSD", volume_current=1.0, price=1.10, state=0
                )
            ]
        if name == "get_position_info":
            return [
                DummyBrokerRecord(
                    position_id="pos-1", symbol="EURUSD", volume=1.5, price_open=1.10
                )
            ]
        return DummyBrokerRecord(balance=1000.0, margin=200.0)

    monkeypatch.setattr(
        "app.services.trading.reconciliation.service.broker_call",
        mock_broker_call,
    )
    monkeypatch.setattr(
        "app.services.trading.info.account.broker_call",
        mock_broker_call,
    )

    trade_store.orders = [
        {
            "order_id": "123",
            "symbol": "EURUSD",
            "state": "NEW",
            "remaining_volume": "1.0",
            "vwap": "1.10",
        }
    ]
    trade_store.positions = [
        {"position_id": "pos-1", "symbol": "EURUSD", "volume": "1.5", "vwap": "1.10"}
    ]

    state_store.save_state(
        route=TradingRoute.LIVE,
        tenant_id="tenant-1",
        snapshot={"id": "latest", "balance": "1000.00", "margin": "200.00"},
        expected_version=None,
    )

    report = service.run_reconciliation(
        route=TradingRoute.LIVE,
        tenant_id="tenant-1",
        account_id="acct-1",
        run_type="periodic",
    )

    assert report.status == "success"
    assert len(report.discrepancies) == 0
    assert not guard.is_blocked("acct-1", "EURUSD")


def test_reconciliation_service_mismatch_startup(
    base_config: TradingRuntimeConfig, monkeypatch: pytest.MonkeyPatch
) -> None:
    trade_store = MockTradeStore()
    state_store = MockStateStore()
    journal = MockEventJournal()
    guard = AuthorityAndRetryGuard()
    clock = MockClock()

    service = ReconciliationService(
        trade_store=trade_store,
        state_store=state_store,
        journal=journal,
        authority_guard=guard,
        clock=clock,
        config=base_config,
    )

    # Mock broker mismatch: balance differs
    def mock_broker_call(name: str, *args: Any, **kwargs: Any) -> Any:
        if name == "get_order_info" or name == "get_position_info":
            return []
        return DummyBrokerRecord(balance=950.0, margin=200.0)

    monkeypatch.setattr(
        "app.services.trading.reconciliation.service.broker_call",
        mock_broker_call,
    )
    monkeypatch.setattr(
        "app.services.trading.info.account.broker_call",
        mock_broker_call,
    )

    state_store.save_state(
        route=TradingRoute.LIVE,
        tenant_id="tenant-1",
        snapshot={"id": "latest", "balance": "1000.00", "margin": "200.00"},
        expected_version=None,
    )

    # Mismatch under 'startup' triggers global lockout
    report = service.run_reconciliation(
        route=TradingRoute.LIVE,
        tenant_id="tenant-1",
        account_id="acct-1",
        run_type="startup",
    )

    assert report.status == "mismatch"
    assert len(report.discrepancies) == 1
    assert report.discrepancies[0].discrepancy_type == "balance_mismatch"
    assert guard.is_blocked("acct-1", "*")


def test_reconciliation_service_orphan_block(
    base_config: TradingRuntimeConfig, monkeypatch: pytest.MonkeyPatch
) -> None:
    trade_store = MockTradeStore()
    state_store = MockStateStore()
    journal = MockEventJournal()
    guard = AuthorityAndRetryGuard()
    clock = MockClock()

    service = ReconciliationService(
        trade_store=trade_store,
        state_store=state_store,
        journal=journal,
        authority_guard=guard,
        clock=clock,
        config=base_config,
    )

    # Broker has a position that local store does not (orphan deal)
    def mock_broker_call(name: str, *args: Any, **kwargs: Any) -> Any:
        if name == "get_order_info":
            return []
        if name == "get_position_info":
            return [
                DummyBrokerRecord(
                    position_id="pos-orphan",
                    symbol="EURUSD",
                    volume=1.0,
                    price_open=1.10,
                )
            ]
        return DummyBrokerRecord(balance=1000.0, margin=200.0)

    monkeypatch.setattr(
        "app.services.trading.reconciliation.service.broker_call",
        mock_broker_call,
    )
    monkeypatch.setattr(
        "app.services.trading.info.account.broker_call",
        mock_broker_call,
    )

    # Policy is "block" by default (from base_config)
    report = service.run_reconciliation(
        route=TradingRoute.LIVE,
        tenant_id="tenant-1",
        account_id="acct-1",
        run_type="periodic",
    )

    assert report.status == "mismatch"
    assert len(report.discrepancies) == 1
    assert report.discrepancies[0].discrepancy_type == "missing_locally"
    # EURUSD scope should be blocked
    assert guard.is_blocked("acct-1", "EURUSD")


def test_reconciliation_service_orphan_adopt(
    base_config: TradingRuntimeConfig, monkeypatch: pytest.MonkeyPatch
) -> None:
    trade_store = MockTradeStore()
    state_store = MockStateStore()
    journal = MockEventJournal()
    guard = AuthorityAndRetryGuard()
    clock = MockClock()

    # Modify policy to adopt-quarantine
    config_adopt = base_config.model_copy(
        update={
            "reconciliation": ReconciliationSettings(
                orphan_deal_policy="adopt-quarantine",
            )
        }
    )

    service = ReconciliationService(
        trade_store=trade_store,
        state_store=state_store,
        journal=journal,
        authority_guard=guard,
        clock=clock,
        config=config_adopt,
    )

    # Broker has a position that local store does not (orphan deal)
    def mock_broker_call(name: str, *args: Any, **kwargs: Any) -> Any:
        if name == "get_order_info":
            return []
        if name == "get_position_info":
            return [
                DummyBrokerRecord(
                    position_id="pos-orphan",
                    symbol="EURUSD",
                    volume=1.0,
                    price_open=1.10,
                )
            ]
        return DummyBrokerRecord(balance=1000.0, margin=200.0)

    monkeypatch.setattr(
        "app.services.trading.reconciliation.service.broker_call",
        mock_broker_call,
    )
    monkeypatch.setattr(
        "app.services.trading.info.account.broker_call",
        mock_broker_call,
    )

    report = service.run_reconciliation(
        route=TradingRoute.LIVE,
        tenant_id="tenant-1",
        account_id="acct-1",
        run_type="periodic",
    )

    assert report.status == "mismatch"
    assert len(report.discrepancies) == 1
    assert report.discrepancies[0].discrepancy_type == "missing_locally"
    # EURUSD scope should NOT be blocked
    assert not guard.is_blocked("acct-1", "EURUSD")
    # Position should be saved locally with quarantine owner tag
    assert len(trade_store.saved_positions) == 1
    saved = trade_store.saved_positions[0]
    assert saved["position_id"] == "pos-orphan"
    assert saved["regulatory_tags"]["tags"]["owner"] == "external"


def test_reconciliation_service_orphan_order_block(
    base_config: TradingRuntimeConfig, monkeypatch: pytest.MonkeyPatch
) -> None:
    trade_store = MockTradeStore()
    state_store = MockStateStore()
    journal = MockEventJournal()
    guard = AuthorityAndRetryGuard()
    clock = MockClock()

    service = ReconciliationService(
        trade_store=trade_store,
        state_store=state_store,
        journal=journal,
        authority_guard=guard,
        clock=clock,
        config=base_config,
    )

    # Broker has an order that local store does not (orphan order)
    def mock_broker_call(name: str, *args: Any, **kwargs: Any) -> Any:
        if name == "get_order_info":
            return [
                DummyBrokerRecord(
                    ticket=999, symbol="GBPUSD", volume_current=1.0, price=1.20, state=0
                )
            ]
        if name == "get_position_info":
            return []
        return DummyBrokerRecord(balance=1000.0, margin=200.0)

    monkeypatch.setattr(
        "app.services.trading.reconciliation.service.broker_call",
        mock_broker_call,
    )
    monkeypatch.setattr(
        "app.services.trading.info.account.broker_call",
        mock_broker_call,
    )

    # Policy is "block" by default (from base_config)
    report = service.run_reconciliation(
        route=TradingRoute.LIVE,
        tenant_id="tenant-1",
        account_id="acct-1",
        run_type="periodic",
    )

    assert report.status == "mismatch"
    assert len(report.discrepancies) == 1
    assert report.discrepancies[0].discrepancy_type == "missing_locally"
    assert report.discrepancies[0].kind == LifecycleKind.ORDER
    # Since it's an order, symbol is '*' for block
    assert guard.is_blocked("acct-1", "GBPUSD")


def test_service_coverage_branches(
    base_config: TradingRuntimeConfig, monkeypatch: pytest.MonkeyPatch
) -> None:
    trade_store = MockTradeStore()
    state_store = MockStateStore()
    journal = MockEventJournal()
    guard = AuthorityAndRetryGuard()
    clock = MockClock()

    # Create service under adopt-quarantine policy
    config_adopt = base_config.model_copy(
        update={
            "reconciliation": ReconciliationSettings(
                orphan_deal_policy="adopt-quarantine",
            )
        }
    )

    service = ReconciliationService(
        trade_store=trade_store,
        state_store=state_store,
        journal=journal,
        authority_guard=guard,
        clock=clock,
        config=config_adopt,
    )

    # 1. Branch: policy = 'adopt-quarantine' but kind = ORDER (so it exits without action)
    disc_order = ReconciliationDiscrepancyEntry(
        entity_id="999",
        kind=LifecycleKind.ORDER,
        discrepancy_type="missing_locally",
        local_value="",
        broker_value="order-data",
        detected_at="2026-07-09T12:00:00",
    )
    service._handle_discrepancies(
        route=TradingRoute.LIVE,
        tenant_id="tenant-1",
        account_id="acct-1",
        run_type="periodic",
        discrepancies=[disc_order],
        broker_positions=[],
    )
    assert not guard.is_blocked("acct-1", "GBPUSD")
    assert len(trade_store.saved_positions) == 0

    # 2. Branch: policy = 'adopt-quarantine', kind = POSITION, but position is not in broker_positions list
    # (Evaluates if broker_p is None, exits without action)
    disc_pos = ReconciliationDiscrepancyEntry(
        entity_id="pos-ghost",
        kind=LifecycleKind.POSITION,
        discrepancy_type="missing_locally",
        local_value="",
        broker_value="pos-data",
        detected_at="2026-07-09T12:00:00",
    )
    service._handle_discrepancies(
        route=TradingRoute.LIVE,
        tenant_id="tenant-1",
        account_id="acct-1",
        run_type="periodic",
        discrepancies=[disc_pos],
        broker_positions=[],
    )
    assert len(trade_store.saved_positions) == 0

    # 3. Branch: policy = 'block', kind = POSITION, but position not in broker_positions list
    # (Evaluates if broker_p is None, sets symbol to '*')
    service_block = ReconciliationService(
        trade_store=trade_store,
        state_store=state_store,
        journal=journal,
        authority_guard=guard,
        clock=clock,
        config=base_config,
    )
    service_block._handle_discrepancies(
        route=TradingRoute.LIVE,
        tenant_id="tenant-1",
        account_id="acct-1",
        run_type="periodic",
        discrepancies=[disc_pos],
        broker_positions=[],
    )
    # Entire account scope should be blocked since symbol fell back to '*'
    assert guard.is_blocked("acct-1", "*")
