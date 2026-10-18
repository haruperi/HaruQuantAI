"""Unit tests for execution preservation and read-only lease isolation.

Description:
    Verifies that Stage 2C historical market data changes strictly preserve legacy
    execution backends (MT5Backend, Bridge, SimulationBackend) without breaking or
    mutating trading contracts, order routing, arming mechanics, or receipt tracking.
    Validates that HistoricalProviderView enforces read-only access and rejects
    trading execution calls, ensuring that data acquisition workflows can never
    trigger accidental trade actions.

Purpose:
    FEAT-BROKER-EXECUTION-TEST: Verification of execution preservation and read isolation.

Key Capabilities:
    - FR-TEST-EXEC-PRESERVATION: Assert MT5 and simulation trading methods are intact.
      Associated: `test_mt5_backend_execution_preservation()`, `test_simulation_backend_intact()`
      Logging: Validates trading state snapshots and disarmed execution guards.
    - FR-TEST-EXEC-ISOLATION: Assert BrokerClient rejects trade dispatch.
      Associated: `test_data_broker_client_blocks_execution_mutations()`
      Logging: Validates data-only client boundaries.

Python API Usage:
    ```bash
    uv run pytest tests/unit/services/brokers/test_brokers_execution_preservation.py --no-cov
    ```

CLI Usage:
    ```bash
    uv run pytest tests/unit/services/brokers/test_brokers_execution_preservation.py --no-cov
    ```
"""

import pytest
from app.services.brokers.base import BrokerClient, TradingClient
from app.services.brokers.metatrader import (
    Bridge,
    MetaTraderClient,
    decode_frame,
    encode_frame,
)
from app.services.brokers.simulator import SimulatorClient
from app.services.brokers.yahoo import YahooClient
from app.services.include.contracts import SymbolInfo
from app.services.include.trading import (
    MarginMode,
)

# ============================================================================
# MT5Backend & Bridge Preservation Tests
# ============================================================================


def test_mt5_backend_execution_preservation() -> None:
    """Verify MT5Backend trading protocol methods and offline behavior."""
    token = Bridge.generate_auth_token()
    assert len(token) >= 32

    backend = MetaTraderClient(auth_token=token)
    assert backend.bridge.auth_token == token
    assert backend.bridge.host == "127.0.0.1"
    assert not backend.bridge.connected
    assert not backend.bridge.armed

    # Verify arming guards (cannot arm when disconnected)
    from app.services.brokers.base import BridgeError

    with pytest.raises(BridgeError, match="cannot arm while the EA is disconnected"):
        backend.arm()


def test_legacy_bridge_frame_codec() -> None:
    """Verify legacy Bridge frame encoding and decoding preserves integers."""
    frame = encode_frame({"v": 1, "kind": "call", "id": 1234567890123456})
    assert frame.endswith(b"\n")

    message = decode_frame(frame.rstrip(b"\n"))
    assert message["v"] == 1
    assert message["kind"] == "call"
    assert message["id"] == 1234567890123456


def test_metatrader_data_broker_coexistence() -> None:
    """Verify MetaTraderDataBroker coexists without impacting execution."""
    data_broker = MetaTraderClient()
    assert data_broker.name == "MetaTrader"
    assert isinstance(data_broker, TradingClient)
    assert isinstance(data_broker, BrokerClient)
    assert hasattr(data_broker, "get_bars")
    assert hasattr(data_broker, "get_ticks")
    assert hasattr(data_broker, "order_send")


def test_metatrader_client_terminal_bars_awaitable() -> None:
    """Verify MetaTraderClient returns awaitable coroutines for bars and ticks when connected."""
    import asyncio
    import inspect
    from unittest.mock import AsyncMock

    async def _test() -> None:
        client = MetaTraderClient()
        client.bridge._connected.set()
        client.bridge._authenticated = True

        mock_bar = {
            "time": 1700000000,
            "open": 1.1,
            "high": 1.2,
            "low": 1.0,
            "close": 1.15,
            "tick_volume": 100,
            "spread": 10,
            "real_volume": 50,
        }
        client.call = AsyncMock(return_value=[mock_bar])  # type: ignore[method-assign]

        coro = client.get_bars("EURUSD", "M1", count=1)
        assert inspect.isawaitable(coro)
        bars = await coro
        assert len(bars) == 1
        assert bars[0].time == 1700000000
        assert bars[0].open == 1.1

        mock_tick = {
            "time_msc": 1700000000000,
            "bid": 1.1,
            "ask": 1.1002,
            "last": 1.1001,
            "volume": 10,
            "flags": 6,
            "volume_real": 10.0,
        }
        client.call = AsyncMock(return_value=[mock_tick])  # type: ignore[method-assign]
        tick_coro = client.get_ticks("EURUSD", count=1)
        assert inspect.isawaitable(tick_coro)
        ticks = await tick_coro
        assert len(ticks) == 1
        assert ticks[0].time_msc == 1700000000000

    asyncio.run(_test())


def test_metatrader_disconnected_hard_failure() -> None:
    """Verify MetaTraderClient get_bars and get_ticks hard-fail with BridgeError when disconnected."""
    from app.services.brokers.base import BridgeError

    client = MetaTraderClient()
    assert not client.bridge.connected

    with pytest.raises(BridgeError) as exc_bars:
        client.get_bars("EURUSD", "M1", count=1)
    assert exc_bars.value.code == "NOT_CONNECTED"

    with pytest.raises(BridgeError) as exc_ticks:
        client.get_ticks("EURUSD", count=1)
    assert exc_ticks.value.code == "NOT_CONNECTED"


# ============================================================================
# SimulationBackend Preservation Tests
# ============================================================================


def test_simulation_backend_intact() -> None:
    """Verify SimulationBackend execution, balance, and symbol snapshot registration."""
    sim = SimulatorClient(
        initial_balance=10000.0,
        leverage=100,
        margin_mode=MarginMode.RETAIL_HEDGING,
        currency="USD",
    )
    assert sim.connect()
    sim.arm()

    account = sim.account()
    assert account.balance == 10000.0
    assert account.equity == 10000.0

    terminal = sim.terminal()
    assert terminal.trade_allowed is True

    # Register and query symbol info
    sim.add_symbol(
        SymbolInfo(
            name="EURUSD",
            point=0.00001,
            digits=5,
            trade_contract_size=100000.0,
        )
    )
    sym = sim.symbol("EURUSD")
    assert sym is not None
    assert sym.name == "EURUSD"
    assert sym.digits == 5

    sim.disconnect()


# ============================================================================
# BrokerClient vs TradingClient Execution Isolation Tests
# ============================================================================


def test_data_broker_client_blocks_execution_mutations() -> None:
    """Verify BrokerClient data classes only allow data reads and do not expose trading methods."""
    data_client = YahooClient()
    assert isinstance(data_client, BrokerClient)
    assert not isinstance(data_client, TradingClient)

    # Allowed read operations
    assert hasattr(data_client, "get_bars")
    assert hasattr(data_client, "get_ticks")
    assert hasattr(data_client, "get_symbol_info")
    assert hasattr(data_client, "get_symbols")

    # Execution methods must NOT be present on BrokerClient data clients
    for forbidden_attr in (
        "arm",
        "disarm",
        "order_send",
        "order_check",
        "order_calc_margin",
        "order_calc_profit",
        "positions",
        "orders",
        "history_orders",
        "deals",
    ):
        assert not hasattr(data_client, forbidden_attr), (
            f"BrokerClient must not expose {forbidden_attr}!"
        )


def test_trading_client_exposes_execution_methods() -> None:
    """Verify TradingClient classes implement trading execution methods."""
    sim = SimulatorClient()
    assert isinstance(sim, BrokerClient)
    assert isinstance(sim, TradingClient)

    for required_attr in (
        "arm",
        "disarm",
        "order_send",
        "order_check",
        "order_calc_margin",
        "order_calc_profit",
        "positions",
        "orders",
        "history_orders",
        "deals",
    ):
        assert hasattr(sim, required_attr), (
            f"TradingClient must expose {required_attr}!"
        )
