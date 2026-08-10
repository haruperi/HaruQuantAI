"""Database-backed system Broker composition tests."""

from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from app.services.api.composition import broker_config
from pydantic import SecretStr


def test_system_mt5_config_uses_stored_enablement_and_credentials(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Compose MT5 from enabled database settings and its encrypted slot."""
    monkeypatch.setattr(
        broker_config,
        "get_system_settings",
        Mock(return_value=SimpleNamespace(settings={"MT5_ENABLED": "true"})),
    )
    monkeypatch.setattr(
        broker_config,
        "_resolve_system_credentials",
        Mock(
            return_value={
                "login": SecretStr("account-1"),
                "password": SecretStr("password-1"),
                "server": SecretStr("demo-server"),
            }
        ),
    )
    build = Mock(return_value=object())
    monkeypatch.setattr(broker_config, "_build_broker_config", build)

    broker_config.build_system_broker_connection_config("mt5", request_id="req-system")

    assert build.call_args.kwargs["environment"] == "demo"
    assert build.call_args.kwargs["account_reference"] == "account-1"
    assert build.call_args.kwargs["provider_enabled"] is True


def test_system_broker_config_fails_closed_when_disabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Reject a stored provider whose enablement is absent or false."""
    monkeypatch.setattr(
        broker_config,
        "get_system_settings",
        Mock(return_value=SimpleNamespace(settings={})),
    )
    with pytest.raises(ValueError, match="system provider is disabled"):
        broker_config.build_system_broker_connection_config(
            "ctrader", request_id="req-system"
        )


def test_system_credential_free_provider_skips_secret_resolution(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Compose Yahoo from stored enablement without resolving credentials."""
    monkeypatch.setattr(
        broker_config,
        "get_system_settings",
        Mock(return_value=SimpleNamespace(settings={"YAHOO_ENABLED": "true"})),
    )
    resolve = Mock()
    monkeypatch.setattr(broker_config, "_resolve_system_credentials", resolve)
    build = Mock(return_value=object())
    monkeypatch.setattr(broker_config, "_build_broker_config", build)

    broker_config.build_system_broker_connection_config(
        "yahoo", request_id="req-system"
    )

    resolve.assert_not_called()
    assert build.call_args.kwargs["environment"] == "sandbox"
    assert build.call_args.kwargs["credentials"] is None
    assert build.call_args.kwargs["probe_symbol"] == "AAPL"


def test_system_broker_config_rejects_unknown_provider() -> None:
    """Reject a provider outside the approved non-production composition map."""
    with pytest.raises(ValueError, match="unsupported system broker provider"):
        broker_config.build_system_broker_connection_config(
            "unknown", request_id="req-system"
        )
