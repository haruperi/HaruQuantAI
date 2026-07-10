"""Tests for the concrete TradeStore implementations (BF-TRD-002)."""

from __future__ import annotations

from decimal import Decimal

import pytest
from app.services.trading.contracts import TradingRoute
from app.services.trading.security.error_mapping import TradingMappedError
from app.services.trading.state.trade_store import InMemoryTradeStore, JsonlTradeStore

TENANT = "tenant-1"


@pytest.fixture(params=["memory", "jsonl"])
def store(request, tmp_path):
    """Yield each TradeStore backend so both satisfy the same contract."""
    if request.param == "memory":
        return InMemoryTradeStore()
    return JsonlTradeStore(path=tmp_path / "trade_store.jsonl")


def _order(order_id: str = "ord-1", total: str = "1.0") -> dict:
    return {
        "order_id": order_id,
        "symbol": "EURUSD",
        "total_volume": total,
        "filled_volume": "0",
        "remaining_volume": total,
        "vwap": "0",
    }


def test_save_and_get_order_state(store) -> None:
    ref = store.save_order_state(
        route=TradingRoute.LIVE,
        tenant_id=TENANT,
        order_state=_order(),
        expected_version=None,
    )
    assert ref.endswith("@1")

    state = store.get_order_state(
        route=TradingRoute.LIVE, tenant_id=TENANT, order_id="ord-1"
    )
    assert state is not None
    assert state["version"] == 1
    assert state["symbol"] == "EURUSD"


def test_get_returns_none_for_unknown_entity(store) -> None:
    assert (
        store.get_order_state(
            route=TradingRoute.LIVE, tenant_id=TENANT, order_id="nope"
        )
        is None
    )


def test_version_increments_on_each_save(store) -> None:
    for expected in (None, 1, 2):
        store.save_order_state(
            route=TradingRoute.LIVE,
            tenant_id=TENANT,
            order_state=_order(),
            expected_version=expected,
        )
    state = store.get_order_state(
        route=TradingRoute.LIVE, tenant_id=TENANT, order_id="ord-1"
    )
    assert state["version"] == 3


def test_stale_expected_version_raises_conflict(store) -> None:
    store.save_order_state(
        route=TradingRoute.LIVE,
        tenant_id=TENANT,
        order_state=_order(),
        expected_version=None,
    )
    with pytest.raises(TradingMappedError) as exc:
        store.save_order_state(
            route=TradingRoute.LIVE,
            tenant_id=TENANT,
            order_state=_order(),
            expected_version=0,
        )
    assert exc.value.code == "LIVE_STATE_VERSION_CONFLICT"


def test_routes_are_isolated_from_each_other(store) -> None:
    store.save_order_state(
        route=TradingRoute.LIVE,
        tenant_id=TENANT,
        order_state=_order(),
        expected_version=None,
    )
    assert (
        store.get_order_state(
            route=TradingRoute.SIM, tenant_id=TENANT, order_id="ord-1"
        )
        is None
    )
    assert store.list_order_states(route=TradingRoute.SIM, tenant_id=TENANT) == []
    assert len(store.list_order_states(route=TradingRoute.LIVE, tenant_id=TENANT)) == 1


def test_tenants_are_isolated_from_each_other(store) -> None:
    store.save_order_state(
        route=TradingRoute.LIVE,
        tenant_id=TENANT,
        order_state=_order(),
        expected_version=None,
    )
    assert (
        store.get_order_state(
            route=TradingRoute.LIVE, tenant_id="other", order_id="ord-1"
        )
        is None
    )


def test_blank_tenant_rejected(store) -> None:
    with pytest.raises(TradingMappedError) as exc:
        store.save_order_state(
            route=TradingRoute.LIVE,
            tenant_id="   ",
            order_state=_order(),
            expected_version=None,
        )
    assert exc.value.code == "INVALID_INPUT"


def test_missing_identifier_rejected(store) -> None:
    with pytest.raises(TradingMappedError) as exc:
        store.save_order_state(
            route=TradingRoute.LIVE,
            tenant_id=TENANT,
            order_state={"symbol": "EURUSD"},
            expected_version=None,
        )
    assert exc.value.code == "INVALID_INPUT"


def test_orders_and_positions_share_id_without_collision(store) -> None:
    store.save_order_state(
        route=TradingRoute.LIVE,
        tenant_id=TENANT,
        order_state={"order_id": "x-1", "symbol": "EURUSD"},
        expected_version=None,
    )
    store.save_position_state(
        route=TradingRoute.LIVE,
        tenant_id=TENANT,
        position_state={"position_id": "x-1", "symbol": "GBPUSD"},
        expected_version=None,
    )
    order = store.get_order_state(
        route=TradingRoute.LIVE, tenant_id=TENANT, order_id="x-1"
    )
    position = store.get_position_state(
        route=TradingRoute.LIVE, tenant_id=TENANT, position_id="x-1"
    )
    assert order["symbol"] == "EURUSD"
    assert position["symbol"] == "GBPUSD"


def test_vwap_accumulates_across_partial_fills(store) -> None:
    store.save_order_state(
        route=TradingRoute.LIVE,
        tenant_id=TENANT,
        order_state=_order(total="1.0"),
        expected_version=None,
    )
    store.record_execution_fill(
        route=TradingRoute.LIVE,
        tenant_id=TENANT,
        order_id="ord-1",
        filled_volume=Decimal("0.4"),
        fill_price=Decimal("1.10000"),
        broker_event_id="evt-1",
    )
    summary = store.record_execution_fill(
        route=TradingRoute.LIVE,
        tenant_id=TENANT,
        order_id="ord-1",
        filled_volume=Decimal("0.6"),
        fill_price=Decimal("1.20000"),
        broker_event_id="evt-2",
    )
    # (0.4*1.1 + 0.6*1.2) / 1.0 == 1.16
    assert Decimal(summary["vwap"]) == Decimal("1.16")
    assert Decimal(summary["filled_volume"]) == Decimal("1.0")
    assert Decimal(summary["remaining_volume"]) == Decimal(0)


def test_duplicate_broker_event_does_not_double_count(store) -> None:
    store.save_order_state(
        route=TradingRoute.LIVE,
        tenant_id=TENANT,
        order_state=_order(total="1.0"),
        expected_version=None,
    )
    first = store.record_execution_fill(
        route=TradingRoute.LIVE,
        tenant_id=TENANT,
        order_id="ord-1",
        filled_volume=Decimal("0.4"),
        fill_price=Decimal("1.10000"),
        broker_event_id="evt-1",
    )
    replay = store.record_execution_fill(
        route=TradingRoute.LIVE,
        tenant_id=TENANT,
        order_id="ord-1",
        filled_volume=Decimal("0.4"),
        fill_price=Decimal("1.10000"),
        broker_event_id="evt-1",
    )
    assert Decimal(replay["filled_volume"]) == Decimal("0.4")
    assert replay["version"] == first["version"]


def test_fill_against_unknown_order_raises(store) -> None:
    with pytest.raises(TradingMappedError) as exc:
        store.record_execution_fill(
            route=TradingRoute.LIVE,
            tenant_id=TENANT,
            order_id="ghost",
            filled_volume=Decimal(1),
            fill_price=Decimal("1.1"),
            broker_event_id="evt-1",
        )
    assert exc.value.code == "DATA_NOT_FOUND"


def test_non_positive_fill_volume_rejected(store) -> None:
    store.save_order_state(
        route=TradingRoute.LIVE,
        tenant_id=TENANT,
        order_state=_order(),
        expected_version=None,
    )
    with pytest.raises(TradingMappedError) as exc:
        store.record_execution_fill(
            route=TradingRoute.LIVE,
            tenant_id=TENANT,
            order_id="ord-1",
            filled_volume=Decimal(0),
            fill_price=Decimal("1.1"),
            broker_event_id="evt-1",
        )
    assert exc.value.code == "INVALID_INPUT"


def test_overfill_beyond_total_volume_rejected(store) -> None:
    store.save_order_state(
        route=TradingRoute.LIVE,
        tenant_id=TENANT,
        order_state=_order(total="1.0"),
        expected_version=None,
    )
    with pytest.raises(TradingMappedError) as exc:
        store.record_execution_fill(
            route=TradingRoute.LIVE,
            tenant_id=TENANT,
            order_id="ord-1",
            filled_volume=Decimal("1.5"),
            fill_price=Decimal("1.1"),
            broker_event_id="evt-1",
        )
    assert exc.value.code == "VALIDATION_FAILED"


def test_split_rescales_position_volume_and_vwap(store) -> None:
    store.save_position_state(
        route=TradingRoute.LIVE,
        tenant_id=TENANT,
        position_state={
            "position_id": "pos-1",
            "symbol": "AAPL",
            "volume": "10",
            "vwap": "200",
        },
        expected_version=None,
    )
    summary = store.apply_corporate_action(
        route=TradingRoute.LIVE,
        tenant_id=TENANT,
        corporate_action={"kind": "split", "symbol": "AAPL", "ratio": "2"},
        audit_ref="audit-1",
    )
    assert summary["adjusted_position_ids"] == ["pos-1"]

    state = store.get_position_state(
        route=TradingRoute.LIVE, tenant_id=TENANT, position_id="pos-1"
    )
    assert Decimal(state["volume"]) == Decimal(20)
    assert Decimal(state["vwap"]) == Decimal(100)
    assert state["corporate_action_audit_ref"] == "audit-1"


def test_reverse_split_rescales_inversely(store) -> None:
    store.save_position_state(
        route=TradingRoute.LIVE,
        tenant_id=TENANT,
        position_state={
            "position_id": "pos-1",
            "symbol": "AAPL",
            "volume": "20",
            "vwap": "100",
        },
        expected_version=None,
    )
    store.apply_corporate_action(
        route=TradingRoute.LIVE,
        tenant_id=TENANT,
        corporate_action={"kind": "reverse_split", "symbol": "AAPL", "ratio": "2"},
        audit_ref="audit-1",
    )
    state = store.get_position_state(
        route=TradingRoute.LIVE, tenant_id=TENANT, position_id="pos-1"
    )
    assert Decimal(state["volume"]) == Decimal(10)
    assert Decimal(state["vwap"]) == Decimal(200)


def test_symbol_change_rewrites_symbol(store) -> None:
    store.save_position_state(
        route=TradingRoute.LIVE,
        tenant_id=TENANT,
        position_state={"position_id": "pos-1", "symbol": "OLD", "volume": "1"},
        expected_version=None,
    )
    store.apply_corporate_action(
        route=TradingRoute.LIVE,
        tenant_id=TENANT,
        corporate_action={
            "kind": "symbol_change",
            "symbol": "OLD",
            "new_symbol": "NEW",
        },
        audit_ref="audit-1",
    )
    state = store.get_position_state(
        route=TradingRoute.LIVE, tenant_id=TENANT, position_id="pos-1"
    )
    assert state["symbol"] == "NEW"


def test_corporate_action_skips_unrelated_symbols(store) -> None:
    store.save_position_state(
        route=TradingRoute.LIVE,
        tenant_id=TENANT,
        position_state={"position_id": "pos-1", "symbol": "AAPL", "volume": "10"},
        expected_version=None,
    )
    store.save_position_state(
        route=TradingRoute.LIVE,
        tenant_id=TENANT,
        position_state={"position_id": "pos-2", "symbol": "MSFT", "volume": "10"},
        expected_version=None,
    )
    summary = store.apply_corporate_action(
        route=TradingRoute.LIVE,
        tenant_id=TENANT,
        corporate_action={"kind": "split", "symbol": "AAPL", "ratio": "2"},
        audit_ref="audit-1",
    )
    assert summary["adjusted_position_ids"] == ["pos-1"]
    msft = store.get_position_state(
        route=TradingRoute.LIVE, tenant_id=TENANT, position_id="pos-2"
    )
    assert Decimal(msft["volume"]) == Decimal(10)


def test_corporate_action_requires_audit_ref(store) -> None:
    with pytest.raises(TradingMappedError) as exc:
        store.apply_corporate_action(
            route=TradingRoute.LIVE,
            tenant_id=TENANT,
            corporate_action={"kind": "split", "symbol": "AAPL", "ratio": "2"},
            audit_ref="  ",
        )
    assert exc.value.code == "INVALID_INPUT"


def test_jsonl_store_survives_restart(tmp_path) -> None:
    path = tmp_path / "durable.jsonl"
    first = JsonlTradeStore(path=path)
    first.save_order_state(
        route=TradingRoute.LIVE,
        tenant_id=TENANT,
        order_state=_order(total="1.0"),
        expected_version=None,
    )
    first.record_execution_fill(
        route=TradingRoute.LIVE,
        tenant_id=TENANT,
        order_id="ord-1",
        filled_volume=Decimal("0.5"),
        fill_price=Decimal("1.10000"),
        broker_event_id="evt-1",
    )

    # A fresh instance over the same path models a process restart.
    reopened = JsonlTradeStore(path=path)
    state = reopened.get_order_state(
        route=TradingRoute.LIVE, tenant_id=TENANT, order_id="ord-1"
    )
    assert state is not None
    assert Decimal(state["filled_volume"]) == Decimal("0.5")
    assert Decimal(state["vwap"]) == Decimal("1.10000")
    assert state["processed_event_ids"] == ["evt-1"]


def test_jsonl_store_dedupes_fill_after_restart(tmp_path) -> None:
    path = tmp_path / "durable.jsonl"
    first = JsonlTradeStore(path=path)
    first.save_order_state(
        route=TradingRoute.LIVE,
        tenant_id=TENANT,
        order_state=_order(total="1.0"),
        expected_version=None,
    )
    first.record_execution_fill(
        route=TradingRoute.LIVE,
        tenant_id=TENANT,
        order_id="ord-1",
        filled_volume=Decimal("0.5"),
        fill_price=Decimal("1.1"),
        broker_event_id="evt-1",
    )
    reopened = JsonlTradeStore(path=path)
    summary = reopened.record_execution_fill(
        route=TradingRoute.LIVE,
        tenant_id=TENANT,
        order_id="ord-1",
        filled_volume=Decimal("0.5"),
        fill_price=Decimal("1.1"),
        broker_event_id="evt-1",
    )
    assert Decimal(summary["filled_volume"]) == Decimal("0.5")


def test_jsonl_store_isolates_routes_on_disk(tmp_path) -> None:
    path = tmp_path / "durable.jsonl"
    store = JsonlTradeStore(path=path)
    store.save_order_state(
        route=TradingRoute.LIVE,
        tenant_id=TENANT,
        order_state=_order("ord-live"),
        expected_version=None,
    )
    store.save_order_state(
        route=TradingRoute.SIM,
        tenant_id=TENANT,
        order_state=_order("ord-sim"),
        expected_version=None,
    )
    reopened = JsonlTradeStore(path=path)
    live = reopened.list_order_states(route=TradingRoute.LIVE, tenant_id=TENANT)
    sim = reopened.list_order_states(route=TradingRoute.SIM, tenant_id=TENANT)
    assert [o["order_id"] for o in live] == ["ord-live"]
    assert [o["order_id"] for o in sim] == ["ord-sim"]
