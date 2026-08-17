"""MetaTrader 5 live-environment election tests.

``AGENTS.md`` section 3 permits exactly one live-environment exception: MT5,
and only when the operator has explicitly elected live execution. These tests
pin both halves of that rule - the exception exists, and it is narrow.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from app.services.brokers import resolve_provider_connection_config
from pydantic import SecretStr


def _settings(environment: str) -> SimpleNamespace:
    """Build provider settings naming one MT5 environment.

    Args:
        environment: MT5 environment to resolve.

    Returns:
        Structural provider-settings stand-in with MT5 enabled.
    """
    return SimpleNamespace(
        mt5_enabled=True,
        mt5_login=SecretStr("1234567"),
        mt5_password=SecretStr("not-a-real-password"),  # pragma: allowlist secret
        mt5_server=SecretStr("Broker-Server"),
        mt5_environment=environment,
        mt5_terminal_path=None,
        ctrader_enabled=False,
        binance_enabled=False,
        dukascopy_enabled=False,
        yahoo_enabled=False,
    )


def test_live_mt5_is_refused_without_an_explicit_election() -> None:
    """Live stays closed by default, exactly as before the exception."""
    with pytest.raises(ValueError, match="reject live environments"):
        resolve_provider_connection_config("mt5", settings=_settings("live"))


def test_live_mt5_resolves_when_live_is_explicitly_elected() -> None:
    """An explicit election opens the one documented live path."""
    config = resolve_provider_connection_config(
        "mt5", settings=_settings("live"), allow_live=True
    )
    assert str(config.environment) == "live"


def test_demo_mt5_resolves_regardless_of_the_election_flag() -> None:
    """The flag widens what live may do; it never narrows demo."""
    for allow_live in (False, True):
        config = resolve_provider_connection_config(
            "mt5", settings=_settings("demo"), allow_live=allow_live
        )
        assert str(config.environment) == "demo"


def test_the_election_never_generalizes_to_another_provider() -> None:
    """Only MT5 carries the exception; every other provider stays closed.

    cTrader is credential-bearing like MT5, so it is the provider most likely
    to be assumed to share the exception. It does not.
    """
    settings = SimpleNamespace(
        ctrader_enabled=True,
        ctrader_environment="live",
        ctrader_account_id=SecretStr("1"),
        ctrader_client_id=SecretStr("id"),
        ctrader_client_secret=SecretStr("secret"),  # pragma: allowlist secret
        ctrader_access_token=SecretStr("token"),  # pragma: allowlist secret
        ctrader_refresh_token=SecretStr("refresh"),  # pragma: allowlist secret
    )
    with pytest.raises(ValueError, match="reject live environments"):
        resolve_provider_connection_config(
            "ctrader", settings=settings, allow_live=True
        )
