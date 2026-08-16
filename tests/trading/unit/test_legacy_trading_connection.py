"""Verify legacy Trading connection composition for explicit routes."""

from __future__ import annotations

import importlib.util
import sys
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[3]
LEGACY_SCRIPT = ROOT / "tests" / "legacy" / "07_trading.py"


def _load_legacy_script() -> ModuleType:
    """Load the numbered legacy program without executing its main guard.

    Returns:
        Loaded legacy Trading module.

    Raises:
        AssertionError: If Python cannot construct the module specification.
    """
    spec = importlib.util.spec_from_file_location("legacy_trading_07", LEGACY_SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


LEGACY_MODULE = _load_legacy_script()


def test_sim_connection_is_ready_without_provider_resolution(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Require socket-free Simulation readiness before provider composition."""
    module = LEGACY_MODULE
    module.ctx.target = "sim"

    def _unexpected_provider_resolution(*args: object, **kwargs: object) -> object:
        """Fail if Simulation attempts provider or credential resolution."""
        del args, kwargs
        raise AssertionError("sim must not resolve a provider connection")

    monkeypatch.setattr(
        module,
        "resolve_provider_connection_config",
        _unexpected_provider_resolution,
    )

    module.example_01_connect()

    output = capsys.readouterr().out
    assert module.ctx.connected is True
    assert module.ctx.adapter is None
    assert module.ctx.connection is None
    assert "Status:             CONNECTED" in output
    assert "Authority:          Deterministic Simulation" in output
    assert "Environment:        simulation" in output
    assert "Virtual:            Yes" in output


def test_selected_symbol_drives_every_virtual_symbol_identity() -> None:
    """Require one configured symbol to flow through every virtual fixture."""
    module = LEGACY_MODULE
    selected_symbol = "TESTUSD"
    original_symbol = module.ctx.symbol
    module.ctx.symbol = selected_symbol
    try:
        order_page = module._virtual_order_page()
        assert order_page["items"][0]["symbol"] == selected_symbol

        output = StringIO()
        with redirect_stdout(output):
            module.example_04_symbol()
            module.example_05_position()
            module.example_07_history_order()
            module.example_08_history_deal()
            module.example_09_open_position()
            module.example_14_pending_orders()
        rendered = output.getvalue()
        assert selected_symbol in rendered
        assert "EURUSD" not in rendered
        assert "GBPUSD" not in rendered
        assert "BTCUSD" not in rendered
    finally:
        module.ctx.symbol = original_symbol


def test_default_symbol_has_one_declaration_and_no_competing_literal() -> None:
    """Require all legacy symbol identity to originate from ``SYMBOL``."""
    source = LEGACY_SCRIPT.read_text(encoding="utf-8")
    assert 'SYMBOL = "BTCUSD"' in source
    assert source.count('"BTCUSD"') == 1
    assert '"EURUSD"' not in source
    assert '"GBPUSD"' not in source


def test_virtual_simulation_fixtures_do_not_claim_demo_identity(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Require local fallback identity to remain Simulation-scoped."""
    module = LEGACY_MODULE
    module.ctx.target = "sim"
    module.ctx.adapter = None
    module.example_02_terminal()
    module.example_03_account()

    output = capsys.readouterr().out
    assert "Environment:        simulation" in output
    assert "Simulation Account" in output
    assert "Simulation Authority" in output
    assert "demo" not in output.lower()


def test_provider_session_uses_explicit_resolved_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Require provider session configuration to preserve its explicit route."""
    module = LEGACY_MODULE
    module.ctx.target = "mt5"
    connection = type(
        "Connection",
        (),
        {"environment": "demo"},
    )()
    adapter = object()
    captured: dict[str, Any] = {}

    monkeypatch.setattr(module, "_provider_settings", lambda _target: object())
    monkeypatch.setattr(
        module,
        "resolve_provider_connection_config",
        lambda *_args, **_kwargs: connection,
    )
    monkeypatch.setattr(
        module,
        "get_broker_connection_environment",
        lambda _connection: "demo",
    )
    monkeypatch.setattr(
        module,
        "create_broker_adapter",
        lambda *_args, **_kwargs: SimpleNamespace(status="success", data=adapter),
    )

    async def _connect(_adapter: object) -> object:
        """Return one successful provider connection response."""
        return SimpleNamespace(status="success")

    monkeypatch.setattr(module, "connect_broker", _connect)
    monkeypatch.setattr(module, "create_live_session", lambda **_kwargs: object())

    async def _start(
        _session: object,
        config: dict[str, object],
        _evidence: dict[str, object],
    ) -> object:
        """Capture the exact configured route without external effects."""
        captured.update(config)
        return SimpleNamespace(status="success")

    monkeypatch.setattr(module, "start_live_session", _start)

    module.example_01_connect()

    assert captured["RUNTIME_PROFILE"] == "demo"
    assert captured["EXECUTION_ROUTE"] == "demo"
    assert captured["ALLOW_LIVE_MUTATIONS"] is False


def test_provider_resolution_failure_is_fail_closed_and_secret_safe(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Require provider composition failure to remain disconnected and bounded."""
    module = LEGACY_MODULE
    module.ctx.target = "mt5"
    monkeypatch.setattr(module, "_provider_settings", lambda _target: object())
    monkeypatch.setattr(
        module,
        "resolve_provider_connection_config",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            ValueError("provider disabled")
        ),
    )

    module.example_01_connect()

    output = capsys.readouterr().out
    assert module.ctx.connected is False
    assert "provider disabled" in output
    assert "FAILED / DISCONNECTED" in output
    assert "password" not in output.lower()
