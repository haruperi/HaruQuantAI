"""Safety contract for genuine non-production Brokers usage programs."""

import ast
from pathlib import Path
from types import SimpleNamespace

import pytest
from app.services.brokers import resolve_provider_connection_config
from app.services.brokers.contracts import BrokerEnvironment, BrokerId
from pydantic import SecretStr

from tests.brokers.usage.features import _support

_USAGE_DIR = Path("tests/brokers/usage/features")
_PROVIDER_PROGRAMS = (
    "02_mt5_account.py",
    "03_ctrader_lifecycle.py",
    "04_binance_lifecycle.py",
    "05_dukascopy_lifecycle.py",
    "06_yahoo_lifecycle.py",
    "07_mt5_mutations.py",
    "08_ctrader_mutations.py",
    "09_history_reads.py",
    "10_calculations.py",
    "11_price_streams.py",
    "12_ctrader_market_data.py",
    "13_dukascopy_bars.py",
    "15_adapter_runtime.py",
)
_MUTATION_METHODS = {
    "check_order",
    "place_order",
    "modify_order",
    "cancel_order",
    "modify_position",
    "close_position",
    "replace_order",
}


def _settings(**overrides: object) -> SimpleNamespace:
    """Return complete bounded provider settings for config tests."""
    values: dict[str, object] = {
        "mt5_enabled": True,
        "mt5_environment": "demo",
        "mt5_login": SecretStr("100001"),
        "mt5_password": SecretStr("secret"),
        "mt5_server": SecretStr("Demo"),
        "mt5_terminal_path": None,
        "ctrader_enabled": True,
        "ctrader_environment": "demo",
        "ctrader_client_id": SecretStr("client"),
        "ctrader_client_secret": SecretStr("secret"),
        "ctrader_access_token": SecretStr("token"),
        "ctrader_account_id": SecretStr("100001"),
        "binance_enabled": True,
        "binance_environment": "testnet",
        "dukascopy_enabled": True,
        "yahoo_enabled": True,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_real_usage_configs_are_non_production(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Every provider usage profile resolves only to approved non-production."""
    monkeypatch.setattr(_support, "load_broker_provider_settings", _settings)
    expected = {
        BrokerId.MT5: BrokerEnvironment.DEMO,
        BrokerId.CTRADER: BrokerEnvironment.DEMO,
        BrokerId.BINANCE_SPOT: BrokerEnvironment.TESTNET,
        BrokerId.DUKASCOPY: BrokerEnvironment.SANDBOX,
        BrokerId.YAHOO: BrokerEnvironment.SANDBOX,
    }
    for broker_id, environment in expected.items():
        assert _support.config(broker_id).environment is environment


def test_real_usage_rejects_live_before_adapter_creation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A live setting cannot enter a standalone usage adapter."""
    monkeypatch.setattr(
        _support,
        "load_broker_provider_settings",
        lambda: _settings(mt5_environment="live"),
    )
    with pytest.raises(_support.UsageEvidenceError, match="reject live"):
        _support.config(BrokerId.MT5)


@pytest.mark.parametrize(
    ("broker_id", "overrides", "message"),
    [
        ("mt5", {"mt5_password": None}, "credentials missing"),
        ("ctrader", {"ctrader_enabled": False}, "provider enablement"),
        ("binance_spot", {"binance_enabled": False}, "provider enablement"),
        ("dukascopy", {"dukascopy_enabled": False}, "provider enablement"),
        ("yahoo", {"yahoo_enabled": False}, "provider enablement"),
    ],
)
def test_provider_resolution_fails_closed_for_incomplete_settings(
    broker_id: str,
    overrides: dict[str, object],
    message: str,
) -> None:
    """Provider resolution rejects missing credentials and disabled routes."""
    with pytest.raises(ValueError, match=message):
        resolve_provider_connection_config(
            broker_id,
            settings=_settings(**overrides),
        )


def test_provider_usage_programs_use_real_session_helper() -> None:
    """Every provider-backed feature uses the genuine lifecycle boundary."""
    for filename in _PROVIDER_PROGRAMS:
        content = (_USAGE_DIR / filename).read_text(encoding="utf-8")
        assert "real_session(" in content, filename
        assert "Offline" not in content, filename
        assert "offline-" not in content, filename


def test_support_has_one_deterministic_disconnect_boundary() -> None:
    """The real-session context always awaits adapter disconnect."""
    tree = ast.parse((_USAGE_DIR / "_support.py").read_text(encoding="utf-8"))
    real_session = next(
        node
        for node in tree.body
        if isinstance(node, ast.AsyncFunctionDef) and node.name == "real_session"
    )
    finalizers = [node for node in ast.walk(real_session) if isinstance(node, ast.Try)]
    assert len(finalizers) == 1
    assert any(
        (isinstance(node, ast.Attribute) and node.attr == "disconnect")
        or (isinstance(node, ast.Name) and node.id == "disconnect_broker")
        for node in ast.walk(finalizers[0].finalbody[0])
    )


def test_mt5_mutations_are_outside_connected_context() -> None:
    """The standalone MT5 mutation program never transmits while connected."""
    tree = ast.parse((_USAGE_DIR / "07_mt5_mutations.py").read_text(encoding="utf-8"))
    run = next(
        node
        for node in tree.body
        if isinstance(node, ast.AsyncFunctionDef) and node.name == "_run"
    )
    connected_calls = {
        node.attr
        for context in run.body
        if isinstance(context, ast.AsyncWith)
        for node in ast.walk(context)
        if isinstance(node, ast.Attribute)
    }
    assert not connected_calls & _MUTATION_METHODS
