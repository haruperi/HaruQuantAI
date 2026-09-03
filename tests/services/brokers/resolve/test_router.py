"""Unit tests for resolve router and service."""

from __future__ import annotations

from pathlib import Path

import pytest
from app.services.brokers.resolve.config import ResolveConfig
from app.services.brokers.resolve.router import (
    ResolveService,
    fr_brk_resolve_broker,
    get_broker_client,
    get_broker_module,
    init_broker_table,
    list_brokers,
    register_broker,
    set_active_broker,
)


@pytest.fixture
def test_db(tmp_path: Path) -> Path:
    """Create a temporary initialized database for testing router."""
    db_file = tmp_path / "router_test.db"
    init_broker_table(db_file)
    return db_file


def test_get_broker_module_default_active(test_db: Path) -> None:
    """Verify get_broker_module returns the active broker (MetaTrader 5)."""
    module = get_broker_module(db_path=test_db)
    assert isinstance(module, dict)
    assert module["name"] == "MetaTrader 5"
    assert module["platform"] == "mt5"
    assert module["active"] is True
    assert module["timezone"] == "UTC+3"
    assert "desc" in module


def test_set_active_broker_and_resolution(test_db: Path) -> None:
    """Verify setting active broker changes resolution outcome."""
    updated = set_active_broker("ctrader", db_path=test_db)
    assert updated["platform"] == "ctrader"
    assert updated["active"] is True

    resolved = get_broker_module(db_path=test_db)
    assert resolved["platform"] == "ctrader"
    assert resolved["name"] == "cTrader"
    assert resolved["active"] is True


def test_set_active_broker_nonexistent_fails(test_db: Path) -> None:
    """Verify setting a non-existent broker raises ValueError."""
    with pytest.raises(ValueError, match="not found in database"):
        set_active_broker("non_existent_broker", db_path=test_db)


def test_list_brokers(test_db: Path) -> None:
    """Verify listing all configured brokers."""
    brokers = list_brokers(db_path=test_db)
    assert len(brokers) == 5
    platforms = [b["platform"] for b in brokers]
    assert "mt5" in platforms
    assert "ctrader" in platforms
    assert "binance" in platforms


def test_register_new_broker(test_db: Path) -> None:
    """Verify registering a custom broker and activating it."""
    new_brk = register_broker(
        name="Interactive Brokers",
        platform="ibkr",
        desc="Interactive Brokers Gateway",
        active=True,
        timezone="America/New_York",
        db_path=test_db,
    )
    assert new_brk["name"] == "Interactive Brokers"
    assert new_brk["platform"] == "ibkr"
    assert new_brk["active"] is True

    active = get_broker_module(db_path=test_db)
    assert active["name"] == "Interactive Brokers"
    assert active["platform"] == "ibkr"
    assert active["timezone"] == "America/New_York"


def test_fr_brk_resolve_broker_trace(test_db: Path) -> None:
    """Verify requirement function fr_brk_resolve_broker trace."""
    cfg = ResolveConfig(database_path=test_db)
    res = fr_brk_resolve_broker(cfg)
    assert res["name"] == "MetaTrader 5"
    assert res["platform"] == "mt5"


def test_resolve_service(test_db: Path) -> None:
    """Verify ResolveService capability implementation."""
    cfg = ResolveConfig(database_path=test_db)
    service = ResolveService(cfg)
    active = service.get_broker_module()
    assert active["name"] == "MetaTrader 5"
    assert active["platform"] == "mt5"

    client = service.get_broker_client()
    assert client is not None
    assert client.is_available() is True


def test_get_broker_client_active_and_switch(test_db: Path) -> None:
    """Verify get_broker_client returns active broker client and tracks DB switches."""
    from app.services.brokers.binance.client import BinanceClient
    from app.services.brokers.metatrader.client import MT5Client

    # Default active broker is mt5
    client = get_broker_client(db_path=test_db)
    assert isinstance(client, MT5Client)

    # Switch active broker to binance
    set_active_broker("binance", db_path=test_db)
    binance_client = get_broker_client(db_path=test_db)
    assert isinstance(binance_client, BinanceClient)


def test_get_broker_client_explicit_platforms() -> None:
    """Verify get_broker_client resolves each platform when specified explicitly."""
    from app.services.brokers.binance.client import BinanceClient
    from app.services.brokers.ctrader.client import CTraderClient
    from app.services.brokers.dukascopy.client import DukascopyClient
    from app.services.brokers.metatrader.client import MT5Client
    from app.services.brokers.yahoo.client import YahooService

    assert isinstance(get_broker_client("mt5"), MT5Client)
    assert isinstance(get_broker_client("metatrader 5"), MT5Client)
    assert isinstance(get_broker_client("binance"), BinanceClient)
    assert isinstance(get_broker_client("ctrader"), CTraderClient)
    assert isinstance(get_broker_client("dukascopy"), DukascopyClient)
    assert isinstance(get_broker_client("yahoo"), YahooService)


def test_get_broker_client_polymorphic_execution() -> None:
    """Verify polymorphic execution across multiple broker clients."""
    for platform in ("binance", "ctrader", "dukascopy"):
        client = get_broker_client(platform)
        assert client.is_available() is True
        assert client.is_connected() is False

        # All implement identical standard signatures
        syms = client.get_symbols()
        assert syms.status == "success"
        assert len(syms.data) > 0

        num_syms = client.get_num_of_symbols()
        assert num_syms.status == "success"
        assert num_syms.data > 0


def test_get_broker_client_unsupported() -> None:
    """Verify ValueError is raised for an unsupported broker platform."""
    with pytest.raises(ValueError, match="Unsupported broker platform"):
        get_broker_client("unknown_crypto_exchange_xyz")
