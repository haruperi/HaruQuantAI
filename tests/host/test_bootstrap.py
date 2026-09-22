"""Composition and import-purity evidence for the initial host."""

import asyncio
import subprocess
import sys
from pathlib import Path

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
import app.host.storage
import app.host.artifacts
import app.host.workers
import app.host.jobs
import app.host.gateway
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


def test_create_runtime_with_durable_s5_features(tmp_path: Path) -> None:
    from app.host.artifacts import HOST_ARTIFACTS, ArtifactsConfig
    from app.host.jobs import HOST_JOBS, JobsConfig
    from app.host.storage import HOST_STORAGE, StorageConfig
    from app.host.workers import HOST_WORKERS, WorkersConfig

    async def scenario() -> None:
        runtime = create_runtime(
            storage_config=StorageConfig(database_path=tmp_path / "storage.db"),
            artifacts_config=ArtifactsConfig(root_dir=tmp_path / "artifacts"),
            workers_config=WorkersConfig(max_concurrent_workers=2),
            jobs_config=JobsConfig(poll_interval_seconds=1.0),
        )
        async with runtime:
            assert "host.storage" in runtime.active_features
            assert "host.artifacts" in runtime.active_features
            assert "host.workers" in runtime.active_features
            assert "host.jobs" in runtime.active_features

            storage = runtime.require(HOST_STORAGE)
            assert storage.scan_records("test").total_count == 0

            artifacts = runtime.require(HOST_ARTIFACTS)
            assert not artifacts.has_artifact("0" * 64)

            workers = runtime.require(HOST_WORKERS)
            assert hasattr(workers, "run_task")

            jobs = runtime.require(HOST_JOBS)
            page = await jobs.list_jobs()
            assert page.total_count == 0

    asyncio.run(scenario())


def test_worker_main_cli_dispatch() -> None:
    """Test worker_main CLI invocation via subprocess."""
    import json

    from app.plugins.algebra import GraphDocument, GraphSpec, NodeSpec, PortRef
    from app.plugins.schema import FrozenObject
    from app.plugins.spec import PluginRef
    from app.plugins.wire import graph_document_to_wire

    doc = GraphDocument(
        spec=GraphSpec(
            nodes=(
                NodeSpec(
                    id="rsi_1",
                    plugin_ref=PluginRef("indicator.rsi", (1, 0, 0)),
                    operation_id="compute",
                    parameters=FrozenObject.from_mapping({"period": 2}),
                ),
            ),
            designated_roots=(PortRef("rsi_1", "rsi"),),
        )
    )

    req = {
        "version": 1,
        "task_id": "test_worker_cli",
        "task_kind": "execution.evaluate",
        "payload": {
            "graph": graph_document_to_wire(doc),
            "inputs": {"rsi_1.values": [10.0, 11.0, 12.0]},
            "seed": None,
            "budget": {
                "max_nodes": 100,
                "max_samples": 1000,
                "max_output_values": 1000,
                "max_trials": 10,
                "max_elapsed_seconds": 10.0,
            },
        },
    }

    completed = subprocess.run(
        [sys.executable, "-m", "app.host.bootstrap", "--worker"],
        input=json.dumps(req).encode("utf-8"),
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0
    resp = json.loads(completed.stdout.decode("utf-8"))
    assert resp["version"] == 1
    assert resp["task_id"] == "test_worker_cli"
    assert resp["success"] is True
    assert "outputs" in resp["result"]
    assert "rsi_1.rsi" in resp["result"]["outputs"]
