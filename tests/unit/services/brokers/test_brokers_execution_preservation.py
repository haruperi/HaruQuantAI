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
    - FR-TEST-EXEC-ISOLATION: Assert HistoricalProviderView rejects trade dispatch.
      Associated: `test_historical_view_blocks_execution_mutations()`
      Logging: Validates read-only lease boundaries.

Python API Usage:
    ```bash
    uv run pytest tests/unit/services/brokers/test_brokers_execution_preservation.py --no-cov
    ```

CLI Usage:
    ```bash
    uv run pytest tests/unit/services/brokers/test_brokers_execution_preservation.py --no-cov
    ```
"""

from __future__ import annotations

import pytest
from app.services.brokers.metatrader import (
    Bridge,
    MetaTraderDataBroker,
    MT5Backend,
    decode_frame,
    encode_frame,
)
from app.services.brokers.registry import (
    BrokerKey,
    BrokerRegistry,
    HistoricalProviderView,
)
from app.services.brokers.simulator import SimulationBackend
from app.services.libs.contracts import SymbolInfo
from app.services.trading import (
    MarginMode,
)

# ============================================================================
# MT5Backend & Bridge Preservation Tests
# ============================================================================


def test_mt5_backend_execution_preservation() -> None:
    """Verify MT5Backend trading protocol methods and offline behavior."""
    token = Bridge.generate_auth_token()
    assert len(token) >= 32

    backend = MT5Backend(auth_token=token)
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
    data_broker = MetaTraderDataBroker()
    assert data_broker.name == "MetaTrader"
    assert data_broker.capabilities.provider_id == "metatrader"
    health = data_broker.check_health()
    assert health.provider_id == "metatrader"


# ============================================================================
# SimulationBackend Preservation Tests
# ============================================================================


def test_simulation_backend_intact() -> None:
    """Verify SimulationBackend execution, balance, and symbol snapshot registration."""
    sim = SimulationBackend(
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
# HistoricalProviderView Read-Only Lease Protection
# ============================================================================


def test_historical_view_blocks_execution_mutations() -> None:
    """Verify HistoricalProviderView only allows reads and blocks trading methods."""
    token = Bridge.generate_auth_token()
    backend = MT5Backend(auth_token=token)
    key = BrokerKey(provider="metatrader")
    view = HistoricalProviderView(backend, key)

    assert view.provider_id == "metatrader"
    assert view.key == key

    # Allowed read operations
    health = view.check_health()
    assert health.provider_id == "metatrader"

    # Disallowed execution methods must NOT be present on HistoricalProviderView
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
        "history_deals",
    ):
        assert not hasattr(view, forbidden_attr), (
            f"HistoricalProviderView must not expose {forbidden_attr}!"
        )


def test_registry_historical_views_are_isolated() -> None:
    """Verify registry.list_historical_providers returns read-only views."""
    registry = BrokerRegistry()
    views = registry.list_historical_providers()

    assert len(views) == 9
    for v in views:
        assert isinstance(v, HistoricalProviderView)
        assert hasattr(v, "fetch_bars")
        assert hasattr(v, "fetch_ticks")
        assert hasattr(v, "check_health")
        # Trading mutations must never be exposed on historical views
        assert not hasattr(v, "order_send")
        assert not hasattr(v, "arm")

    registry.close()
