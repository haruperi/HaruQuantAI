"""Unit tests for LiveTest and LiveTestCLI in app.services.brokers.registry.

Description:
    Validates live broker credential validation and secret redaction, readonly
    research profile enforcement and authorized order-check latency probing,
    account trading permissions and margin currency verification, and CLI
    execution for FEAT-BROKER-LIVETEST.

Purpose:
    FEAT-BROKER-LIVETEST: Unit test suite for LiveTest and LiveTestCLI.

Key Capabilities:
    - FR-BROKER-LIVETEST-CREDENTIALS: Verify credential validation and secret redaction.
    - FR-BROKER-LIVETEST-LATENCY: Verify quote and order latency probes and readonly safety.
    - FR-BROKER-LIVETEST-PERMISSIONS: Verify account trading permissions and margin currency.

Python API Usage:
    ```bash
    uv run pytest tests/unit/services/brokers/test_registry.py --no-cov
    ```
"""

from __future__ import annotations

from json import loads
from typing import Any

import app.services.brokers as brokers_pkg
import pytest
from app.services.brokers.base import BrokerClient, get_broker
from app.services.brokers.registry import LiveTest, LiveTestCLI, _Config


class TestLiveTest:
    """Unit tests for LiveTest (FEAT-BROKER-LIVETEST)."""

    def test_inherits_from_broker_client_and_lazy_package_export(self) -> None:
        """Verify LiveTest inherits from BrokerClient and resolves via brokers package."""
        svc = LiveTest()
        assert isinstance(svc, BrokerClient)
        assert svc.name == "live_test"
        assert svc.connect() is True
        assert bool(svc.is_connected) is True
        svc.disconnect()
        assert bool(svc.is_connected) is False

        assert brokers_pkg.LiveTest is LiveTest
        assert brokers_pkg.LiveTestCLI is LiveTestCLI
        singleton = get_broker("live_test")
        assert isinstance(singleton, LiveTest)

    def test_validate_credentials_redacts_secrets_and_checks_required_fields(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Verify FR-BROKER-LIVETEST-CREDENTIALS across valid, missing, and unknown providers."""
        svc = LiveTest()

        with caplog.at_level("INFO"):
            ok_ct = svc.validate_credentials(
                "ctrader",
                {
                    "client_id": "cid-1",
                    "client_secret": "super-secret-ct",
                    "access_token": "tok-ct-123",
                    "account_id": "891044",
                },
            )
        assert ok_ct["provider"] == "ctrader"
        assert ok_ct["valid"] is True
        assert ok_ct["authenticated"] is True
        assert ok_ct["status"] == "VALID"
        assert ok_ct["missing_fields"] == []
        red_ct = ok_ct["redacted_credentials"]
        assert red_ct["client_secret"] != "super-secret-ct"
        assert "REDACTED" in str(red_ct["client_secret"])
        assert "REDACTED" in str(red_ct["access_token"])
        assert any(
            getattr(r, "fr_id", None) == "FR-BROKER-LIVETEST-CREDENTIALS"
            for r in caplog.records
        )

        # MetaTrader accepts either auth_token or login+server
        mt_login = svc.validate_credentials(
            "mt5", {"login": "50184201", "server": "MetaQuotes-Demo"}
        )
        assert mt_login["provider"] == "metatrader"
        assert mt_login["valid"] is True

        # Missing required fields on binance
        bad_bn = svc.validate_credentials("binance", {"api_key": "k-only"})
        assert bad_bn["valid"] is False
        assert bad_bn["status"] == "INVALID_CREDENTIALS"
        assert bad_bn["missing_fields"] == ["api_secret"]

        # Unknown provider
        unk = svc.validate_credentials("nonexistent_broker", {"api_key": "abc"})
        assert unk["valid"] is False
        assert unk["status"] == "UNKNOWN_PROVIDER"

    def test_measure_trading_latency_readonly_profile_and_authorized_probe(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Verify FR-BROKER-LIVETEST-LATENCY enforces readonly profile by default."""
        readonly_svc = LiveTest()
        with caplog.at_level("INFO"):
            lat_ro = readonly_svc.measure_trading_latency("simulator", "EURUSD")

        assert lat_ro["provider"] == "simulator"
        assert lat_ro["symbol"] == "EURUSD"
        assert lat_ro["readonly_profile"] is True
        assert lat_ro["execution_authorized"] is False
        assert lat_ro["order_probe_status"] == "DISABLED_READONLY_PROFILE"
        assert float(lat_ro["quote_latency_ms"]) >= 0.01
        assert float(lat_ro["order_latency_ms"]) == 0.0
        assert float(lat_ro["round_trip_latency_ms"]) == float(
            lat_ro["quote_latency_ms"]
        )
        assert any(
            getattr(r, "fr_id", None) == "FR-BROKER-LIVETEST-LATENCY"
            for r in caplog.records
        )

        # Authorized execution probe runs local order_check latency measurement
        auth_svc = LiveTest(_Config(allow_live_execution=True))
        lat_auth = auth_svc.measure_trading_latency("simulator", "gbpusd")
        assert lat_auth["symbol"] == "GBPUSD"
        assert lat_auth["readonly_profile"] is False
        assert lat_auth["execution_authorized"] is True
        assert lat_auth["order_probe_status"] == "AUTHORIZED_ORDER_CHECK"
        assert float(lat_auth["order_latency_ms"]) >= 0.01
        assert float(lat_auth["round_trip_latency_ms"]) > float(
            lat_auth["quote_latency_ms"]
        )

        # Fallback to self when provider is live_test
        lat_self = readonly_svc.measure_trading_latency("live_test", "")
        assert lat_self["provider"] == "live_test"
        assert lat_self["symbol"] == "EURUSD"

    def test_verify_trading_permissions_across_providers(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Verify FR-BROKER-LIVETEST-PERMISSIONS inspects account permissions and currency."""
        svc = LiveTest()
        with caplog.at_level("INFO"):
            sim_perm = svc.verify_trading_permissions("simulator", "sim-acc-01")
        assert sim_perm["provider"] == "simulator"
        assert sim_perm["account_id"] == "sim-acc-01"
        assert sim_perm["verified"] is True
        assert sim_perm["trade_allowed"] is True
        assert sim_perm["margin_currency"] == "USD"
        assert "order_check" in sim_perm["permissions"]
        assert "order_execution" not in sim_perm["permissions"]
        assert any(
            getattr(r, "fr_id", None) == "FR-BROKER-LIVETEST-PERMISSIONS"
            for r in caplog.records
        )

        # Authorized execution includes order_execution permission
        auth_svc = LiveTest(_Config(allow_live_execution=True))
        bn_perm = auth_svc.verify_trading_permissions("binance", "BN-882190")
        assert bn_perm["verified"] is True
        assert bn_perm["margin_currency"] == "USDT"
        assert "order_execution" in bn_perm["permissions"]

        # Data-only provider has market_data + account_read but trade_allowed=False
        duk_perm = svc.verify_trading_permissions("dukascopy", "duk-read")
        assert duk_perm["verified"] is True
        assert duk_perm["trade_allowed"] is False
        assert duk_perm["permissions"] == ["market_data", "account_read"]

        # Invalid/empty account or unknown provider fails verification
        bad_perm = svc.verify_trading_permissions("unknown_xyz", "")
        assert bad_perm["verified"] is False
        assert bad_perm["trade_allowed"] is False
        assert bad_perm["permissions"] == []

    def test_cli_format_output_and_run(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Verify LiveTestCLI.format_output and LiveTestCLI.run."""
        code = LiveTestCLI.run(
            ["--provider", "simulator", "--symbol", "EURUSD", "--account-id", "sim-99"]
        )
        assert code == 0
        captured: Any = loads(capsys.readouterr().out)
        assert captured["credentials"]["provider"] == "simulator"
        assert captured["credentials"]["valid"] is True
        assert captured["latency"]["symbol"] == "EURUSD"
        assert captured["permissions"]["account_id"] == "sim-99"
