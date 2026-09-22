"""Composition and import-purity evidence for the initial host."""

import asyncio
import subprocess
import sys

import pytest
from app.host.bootstrap import create_runtime
from app.host.catalog import HOST_CATALOG
from app.host.execution import HOST_EXECUTION
from app.host.telemetry import HOST_TELEMETRY
from app.kernel.capability import CapabilityUnavailableError


def test_contract_import_does_not_start_effects_or_read_environment() -> None:
    script = r"""
import asyncio
import logging
import os
import threading

def forbidden(*args, **kwargs):
    raise AssertionError("import performed an effect")

asyncio.create_task = forbidden
logging.basicConfig = forbidden
os.getenv = forbidden
threading.Thread.start = forbidden
import app.host.telemetry
import app.host.catalog
import app.host.execution
import app.host.bootstrap
"""
    completed = subprocess.run(
        [sys.executable, "-c", script],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr


def test_create_runtime_is_inactive_until_entered_and_single_use() -> None:
    async def scenario() -> None:
        runtime = create_runtime()
        with pytest.raises(CapabilityUnavailableError):
            runtime.require(HOST_TELEMETRY)
        with pytest.raises(CapabilityUnavailableError):
            runtime.require(HOST_CATALOG)
        with pytest.raises(CapabilityUnavailableError):
            runtime.require(HOST_EXECUTION)
        async with runtime:
            assert set(runtime.active_features) == {
                "host.catalog",
                "host.execution",
                "host.telemetry",
            }
            assert runtime.require(HOST_TELEMETRY).diagnostics == ()
            catalog = runtime.require(HOST_CATALOG)
            assert catalog.is_ready()
            assert catalog.snapshot().view.entries == ()
            execution = runtime.require(HOST_EXECUTION)
            assert execution is runtime.require(HOST_EXECUTION)
        with pytest.raises(RuntimeError, match="single-use"):
            async with runtime:
                pass

    asyncio.run(scenario())


@pytest.mark.parametrize(
    ("subscribers", "diagnostics"),
    [(0, 1), (1, 0)],
)
def test_invalid_host_bounds_fail_at_explicit_construction(
    subscribers: int, diagnostics: int
) -> None:
    with pytest.raises(ValueError, match="positive"):
        create_runtime(
            telemetry_max_subscribers=subscribers,
            diagnostic_capacity=diagnostics,
        )


def test_approved_catalog_roots_includes_workspaces() -> None:
    from app.host.bootstrap import approved_catalog_roots

    roots = approved_catalog_roots()
    families = {r.logical_family for r in roots}
    assert "indicators" in families
    assert "comparisons" in families
    assert "exporters" in families
    assert "workspaces" in families


def test_create_runtime_with_gateway() -> None:
    from app.host.gateway import HOST_GATEWAY, GatewayConfig

    async def scenario() -> None:
        runtime = create_runtime(
            gateway_config=GatewayConfig(port=0),
            gateway_auto_start=False,
        )
        async with runtime:
            assert "host.gateway" in runtime.active_features
            gw = runtime.require(HOST_GATEWAY)
            assert gw.config.port == 0

    asyncio.run(scenario())
