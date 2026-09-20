"""Unit tests for the sandboxed plugin host feature (FR-WORKSPACE-007)."""

from __future__ import annotations

import asyncio

import pytest
from app.contracts.workspace import (
    WORKSPACE_PLUGINS,
    PluginError,
    PluginManifest,
    PluginSecurityError,
)
from app.kernel.bootstrapper import Runtime
from app.services.workspace.plugin_host import (
    SPEC,
    PluginHostConfig,
    PluginHostService,
    feature,
)


def test_valid_plugin_load_and_hook_execution() -> None:
    """Verify loading and executing a valid sandboxed plugin."""
    host = PluginHostService(PluginHostConfig())

    manifest = PluginManifest(
        plugin_id="indicator.rsi.custom",
        name="Custom RSI",
        version="1.0.0",
        author="QuantLab",
        entry_point="calculate",
        permissions=("compute", "custom_indicator"),
        is_sandboxed=True,
    )

    code = """
def calculate(payload):
    prices = payload.get("prices", [])
    factor = payload.get("factor", 1.0)
    avg = sum(prices) / max(1, len(prices))
    return {"avg_price": round(avg * factor, 2)}
"""

    inst = host.load_plugin(manifest, code)
    assert inst.manifest.plugin_id == "indicator.rsi.custom"
    assert inst.active is True

    # List plugins
    all_plugins = host.list_plugins()
    assert len(all_plugins) == 1
    assert all_plugins[0].manifest.name == "Custom RSI"

    # Execute hook
    out = host.execute_plugin_hook(
        "indicator.rsi.custom",
        "calculate",
        {"prices": [10.0, 20.0, 30.0], "factor": 2.0},
    )
    assert out == {"avg_price": 40.0}

    # Unload plugin
    assert host.unload_plugin("indicator.rsi.custom") is True
    assert len(host.list_plugins()) == 0
    assert host.unload_plugin("indicator.rsi.custom") is False


def test_sandboxing_blocks_imports_and_dangerous_builtins() -> None:
    """Verify AST inspects and rejects direct imports or dangerous builtins."""
    host = PluginHostService(PluginHostConfig())

    manifest = PluginManifest(
        plugin_id="malicious.plugin",
        name="Malicious Plugin",
        version="1.0.0",
        author="Attacker",
        entry_point="run",
        permissions=("compute",),
        is_sandboxed=True,
    )

    import_code = """
import os
def run(payload):
    return {}
"""
    with pytest.raises(
        PluginSecurityError, match="Direct module imports are forbidden"
    ):
        host.load_plugin(manifest, import_code)

    eval_code = """
def run(payload):
    cmd = eval("1 + 1")
    return {"val": cmd}
"""
    with pytest.raises(PluginSecurityError, match="Forbidden symbol 'eval'"):
        host.load_plugin(manifest, eval_code)


def test_unapproved_permissions_rejected() -> None:
    """Verify manifest requesting unauthorized permissions is rejected."""
    host = PluginHostService(PluginHostConfig(allowed_permissions=("compute",)))

    manifest = PluginManifest(
        plugin_id="network.plugin",
        name="Network Plugin",
        version="1.0.0",
        author="Dev",
        entry_point="run",
        permissions=("compute", "network:outbound"),
    )
    code = "def run(payload): return {}"

    with pytest.raises(
        PluginSecurityError, match="Permission 'network:outbound' is not allowed"
    ):
        host.load_plugin(manifest, code)


def test_missing_entry_point_error() -> None:
    """Verify loading fails if entry point is missing from code."""
    host = PluginHostService(PluginHostConfig())

    manifest = PluginManifest(
        plugin_id="incomplete.plugin",
        name="Incomplete Plugin",
        version="1.0.0",
        author="Dev",
        entry_point="missing_fn",
        permissions=("compute",),
    )
    code = "def existing_fn(payload): return {}"

    with pytest.raises(PluginError, match="Entry point 'missing_fn' not defined"):
        host.load_plugin(manifest, code)


def test_plugin_host_lifecycle_within_runtime() -> None:
    """Verify feature mounts inside Runtime and publishes WORKSPACE_PLUGINS."""
    feat = feature()
    assert feat.spec == SPEC

    async def _test() -> None:
        async with Runtime((feature,)) as runtime:
            ph = runtime.require(WORKSPACE_PLUGINS)
            assert len(ph.list_plugins()) == 0

    asyncio.run(_test())


def test_sandboxing_blocks_dunder_attribute_access() -> None:
    """Verify accessing dunder attributes like __class__ or __subclasses__ is rejected."""
    host = PluginHostService(PluginHostConfig())
    manifest = PluginManifest(
        plugin_id="dunder.plugin",
        name="Dunder Exploit Plugin",
        version="1.0.0",
        author="Attacker",
        entry_point="run",
        permissions=("compute",),
    )
    dunder_code = """
def run(payload):
    cls = ().__class__.__bases__[0].__subclasses__()
    return {"classes": len(cls)}
"""
    with pytest.raises(
        PluginSecurityError, match=r"Dunder attribute access '.*' is forbidden"
    ):
        host.load_plugin(manifest, dunder_code)


def test_plugin_host_config_validation() -> None:
    """Verify bounds enforcement on PluginHostConfig."""
    with pytest.raises(ValueError, match="execution_timeout_s"):
        PluginHostConfig(execution_timeout_s=0.0)

    valid = PluginHostConfig(execution_timeout_s=10.0)
    assert valid.execution_timeout_s == 10.0
