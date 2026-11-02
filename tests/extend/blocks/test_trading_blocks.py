"""Canonical trading blocks own strategy behavior independently of workspace APIs."""

from __future__ import annotations

import asyncio
import inspect
import json
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from app.core.data.contracts import (
    AccountInfo,
    SymbolInfo,
    SymbolPrice,
    TradeCheckResult,
    TradeRequest,
    TradeResult,
)
from app.core.enums import OrderType, TradeRetcode
from app.extend.blocks.metadata import ExecutionKind
from app.extend.blocks.order.types import TradeFilter
from app.extend.blocks.registry import BlockRegistry, BlockRegistryError
from app.workspace.brokers.simulator import SimulatorClient
from app.workspace.trading import (
    AccountProxy,
    HistoryOrderProxy,
    OrderProxy,
    PositionProxy,
    Trade,
    Trading,
)

ROOT = Path(__file__).resolve().parents[3]
MANIFEST = json.loads(
    (ROOT / "docs/dev/fixtures/trading-block-migration-manifest.json").read_text()
)


def registry() -> BlockRegistry:
    result = BlockRegistry()
    result.discover(ROOT / "app/extend/blocks/order")
    result.discover(ROOT / "app/extend/blocks/strategy_control")
    assert not result.diagnostics
    return result


def test_complete_donor_manifest_and_catalog_ownership() -> None:
    catalog = registry().snapshot()
    assert len(MANIFEST) == 37
    assert len({m["donor"] for m in MANIFEST}) == 37
    assert set(catalog.blocks) == {m["id"] for m in MANIFEST}
    for entry in MANIFEST:
        descriptor = catalog.blocks[entry["id"]]
        assert (
            Path(descriptor.source_file).resolve() == (ROOT / entry["source"]).resolve()
        )
        assert inspect.iscoroutinefunction(descriptor.target)
        properties = descriptor.parameter_schema["properties"]
        assert "context" not in properties
        assert "scope" not in properties
        assert not descriptor.spec.is_generation_eligible
        if entry["id"].startswith("order."):
            assert descriptor.spec.execution_kind == ExecutionKind.ORDER


def test_discovery_and_configuration_never_execute_orders() -> None:
    client = SimulatorClient()
    trading = Trading(client)
    trading.trade.OrderSend = AsyncMock(
        side_effect=AssertionError("Discovery sent an order")
    )
    result = registry()
    for entry in MANIFEST:
        descriptor = result.snapshot().blocks[entry["id"]]
        descriptor.instantiate()
    trading.trade.OrderSend.assert_not_awaited()
    with pytest.raises(BlockRegistryError):
        result.snapshot().blocks["order.enter_at_market"].instantiate(
            allow_duplicate_trades="yes"
        )
    with pytest.raises(BlockRegistryError):
        result.snapshot().blocks["strategy_control.closed_pl_in_money"].instantiate(
            trades_ago="1"
        )


def test_every_registered_block_runs_through_an_independent_runtime() -> None:
    async def prepare(symbol, direction, volume, buy_type, **kwargs):
        return TradeRequest(
            symbol=symbol,
            volume=volume,
            order_type=buy_type if direction == 1 else OrderType(int(buy_type) + 1),
            magic=kwargs["magic"] or 0,
            comment=kwargs["comment"],
        )

    execution = SimpleNamespace(
        operation_lock=asyncio.Lock(),
        prepare_entry_request=prepare,
        OrderCheck=AsyncMock(return_value=TradeCheckResult(retcode=0)),
        send_checked=AsyncMock(return_value=TradeResult(retcode=TradeRetcode.DONE)),
        close=AsyncMock(),
        cancel=AsyncMock(),
        modify_protection=AsyncMock(),
    )
    context = SimpleNamespace(
        trade=execution,
        position=SimpleNamespace(PositionsGet=AsyncMock(return_value=[])),
        order=SimpleNamespace(OrdersGet=AsyncMock(return_value=[])),
        account=SimpleNamespace(AccountInfo=AsyncMock(return_value=AccountInfo())),
        symbol=SimpleNamespace(
            SymbolInfo=AsyncMock(
                return_value=SymbolInfo(price=SymbolPrice(bid=1.1, ask=1.1002))
            )
        ),
        deal=SimpleNamespace(HistoryDealsGet=AsyncMock(return_value=[])),
    )
    stamp = datetime(2026, 10, 28, tzinfo=UTC)
    runtime_inputs = {
        "context": context,
        "scope": TradeFilter("EURUSD"),
        "symbol": "EURUSD",
        "direction": 1,
        "volume": 0.01,
        "price": 1.1,
        "bar_times": [stamp],
        "as_of": stamp,
        "bar_start": stamp,
    }

    async def scenario():
        for descriptor in registry().snapshot().blocks.values():
            configured = descriptor.instantiate()
            kwargs = {
                p.name: runtime_inputs[p.name]
                for p in descriptor.spec.inputs
                if p.name in runtime_inputs
            }
            await configured(**kwargs)
        assert execution.send_checked.await_count == 4
        execution.close.assert_not_awaited()
        execution.cancel.assert_not_awaited()
        execution.modify_protection.assert_not_awaited()

    asyncio.run(scenario())


@pytest.mark.parametrize(
    ("cls", "names"),
    [
        (
            Trade,
            [
                "enter_at_market",
                "enter_at_limit",
                "enter_at_stop",
                "enter_reverse_at_market",
                "close_position",
                "close_all_positions",
                "close_best_position",
                "close_worst_position",
                "cancel_pending_order",
                "cancel_all_pending_orders",
                "set_stop_loss",
                "set_profit_target",
            ],
        ),
        (
            PositionProxy,
            [
                "market_position",
                "market_position_is_flat",
                "market_position_is_long",
                "market_position_is_short",
                "market_position_is_not_long",
                "market_position_is_not_short",
                "market_positions_count",
                "market_position_size",
                "open_pl_in_money",
                "open_pl_in_pips",
                "bars_since_order_open",
                "order_open_price",
                "order_sl",
                "order_pt",
            ],
        ),
        (
            OrderProxy,
            [
                "pending_order_exists",
                "pending_order_doesnt_exist",
                "order_open_price",
                "order_sl",
                "order_pt",
            ],
        ),
        (
            HistoryOrderProxy,
            [
                "closed_trades",
                "closed_pl_in_money",
                "closed_pl_in_pips",
                "last_order_was",
                "last_order_was_not",
                "bars_since_order_closed",
                "trade_recently_closed",
                "no_trade_recently_closed",
            ],
        ),
        (AccountProxy, ["account_balance", "account_equity"]),
    ],
)
def test_workspace_has_no_obsolete_helpers_or_forwarders(
    cls: type, names: list[str]
) -> None:
    assert all(not hasattr(cls, name) for name in names)


def test_execution_primitives_remain_and_catalog_can_execute_simulated_orders() -> None:
    client = SimulatorClient()
    client.add_symbol(SymbolInfo(name="EURUSD"))
    client.feed_tick("EURUSD", bid=1.1, ask=1.1002)
    trading = Trading(client)
    trading.arm()
    catalog = registry().snapshot()

    async def scenario():
        entry = catalog.blocks["order.enter_at_market"].instantiate(magic=51)
        result = await entry(trading, "EURUSD", 1, 0.01)
        assert result.retcode == TradeRetcode.DONE
        count = catalog.blocks["strategy_control.market_positions_count"].instantiate()
        assert await count(trading, TradeFilter("EURUSD", magic=51)) == 1
        close = catalog.blocks["order.close_best_position"].instantiate()
        assert (
            await close(trading, TradeFilter("EURUSD", magic=51))
        ).retcode == TradeRetcode.DONE
        assert not client.positions()

    asyncio.run(scenario())
