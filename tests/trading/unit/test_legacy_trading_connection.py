"""Verify legacy Trading connection composition for explicit routes."""

from __future__ import annotations

import importlib.util
import sys
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
