"""Safety contract for genuine non-production Brokers usage programs."""

import ast
import asyncio
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from app.services.brokers import resolve_provider_connection_config
from app.services.brokers._shared import connections
from app.services.brokers.canonical_contracts import BrokerEnvironment, BrokerId
from pydantic import SecretStr

from tests.brokers.usage.features import _support

_USAGE_DIR = Path("tests/brokers/usage/features")
_PROVIDER_PROGRAMS = (
    "02_metatrader.py",
    "03_ctrader.py",
    "04_binance.py",
    "05_dukascopy.py",
    "06_yahoo.py",
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
    environments = {
        "mt5": BrokerEnvironment.DEMO,
        "ctrader": BrokerEnvironment.DEMO,
        "binance_spot": BrokerEnvironment.TESTNET,
        "dukascopy": BrokerEnvironment.SANDBOX,
        "yahoo": BrokerEnvironment.SANDBOX,
    }
    monkeypatch.setattr(
        _support,
        "build_system_broker_connection_config",
        lambda broker_id, **_values: SimpleNamespace(
            environment=environments[broker_id]
        ),
    )
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

    def _reject_live(*_args: object, **_kwargs: object) -> object:
        raise ValueError("production broker environments are excluded")

    monkeypatch.setattr(_support, "build_system_broker_connection_config", _reject_live)
    with pytest.raises(_support.UsageEvidenceError, match="production"):
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


def test_every_enabled_provider_resolves_a_bounded_configuration() -> None:
    """Exercise every credentialed and credential-free configuration branch."""
    expected = {
        BrokerId.MT5: BrokerEnvironment.DEMO,
        BrokerId.CTRADER: BrokerEnvironment.DEMO,
        BrokerId.BINANCE_SPOT: BrokerEnvironment.TESTNET,
        BrokerId.DUKASCOPY: BrokerEnvironment.SANDBOX,
        BrokerId.YAHOO: BrokerEnvironment.SANDBOX,
    }
    for broker_id, environment in expected.items():
        config = resolve_provider_connection_config(broker_id, settings=_settings())
        assert config.broker_id is broker_id
        assert config.environment is environment


def test_provider_resolution_rejects_live_and_unsupported_routes() -> None:
    """Reject production and non-provider adapter profiles before construction."""
    with pytest.raises(ValueError, match="reject live"):
        resolve_provider_connection_config(
            BrokerId.MT5,
            settings=_settings(mt5_environment="live"),
        )
    with pytest.raises(ValueError, match="not a valid BrokerId"):
        resolve_provider_connection_config("unsupported", settings=_settings())


def test_connected_broker_construction_and_connection_failures(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Cover deferred connection, construction failure, and connection failure."""

    async def _exercise() -> None:
        """Run construction branches on one event loop."""
        adapter = object()
        config = SimpleNamespace(broker_id=BrokerId.MT5)
        monkeypatch.setattr(
            connections, "resolve_provider_connection_config", Mock(return_value=config)
        )
        monkeypatch.setattr(
            connections,
            "create_broker_adapter",
            Mock(return_value=SimpleNamespace(data=adapter, error=None)),
        )
        assert (
            await connections.create_connected_broker(BrokerId.MT5, connect=False)
            is adapter
        )
        monkeypatch.setattr(
            connections,
            "create_broker_adapter",
            Mock(return_value=SimpleNamespace(data=None, error=object())),
        )
        with pytest.raises(ValueError, match="construction failed"):
            await connections.create_connected_broker(BrokerId.MT5, connect=False)
        monkeypatch.setattr(
            connections,
            "create_broker_adapter",
            Mock(return_value=SimpleNamespace(data=adapter, error=None)),
        )

        async def _failed_connect(_adapter: object) -> object:
            """Return one canonical-looking failed connection result."""
            return SimpleNamespace(error=object())

        monkeypatch.setattr(connections, "connect_broker", _failed_connect)
        with pytest.raises(ValueError, match="connection failed"):
            await connections.create_connected_broker(BrokerId.MT5)

    asyncio.run(_exercise())


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


def test_provider_channels_never_mutate_inside_usage_sessions() -> None:
    """No consolidated provider usage program transmits a broker mutation."""
    for filename in _PROVIDER_PROGRAMS:
        tree = ast.parse((_USAGE_DIR / filename).read_text(encoding="utf-8"))
        connected_calls = {
            node.attr
            for context in ast.walk(tree)
            if isinstance(context, ast.AsyncWith)
            for node in ast.walk(context)
            if isinstance(node, ast.Attribute)
        }
        assert not connected_calls & _MUTATION_METHODS, filename
