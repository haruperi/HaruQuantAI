"""Focused tests for host workers owner: subprocess supervisor and worker_main."""

from __future__ import annotations

import asyncio
from typing import Any

import pytest
from app.host.workers import (
    HOST_WORKERS,
    WorkerBudget,
    WorkersConfig,
    WorkerTask,
    WorkerTimeoutError,
    _SubprocessWorkers,
    _workers_feature,
)
from app.kernel.bootstrapper import Runtime
from app.plugins.algebra import GraphDocument, GraphSpec, NodeSpec, PortRef
from app.plugins.schema import FrozenObject
from app.plugins.spec import PluginRef
from app.plugins.wire import graph_document_to_wire


def _sample_rsi_graph_wire() -> dict[str, Any]:
    """Build wire representation of a valid RSI graph."""
    rsi_ref = PluginRef(id="indicator.rsi", version=(1, 0, 0))
    rsi_node = NodeSpec(
        id="rsi_node",
        plugin_ref=rsi_ref,
        operation_id="compute",
        parameters=FrozenObject.from_mapping({"period": 14}),
    )
    graph_spec = GraphSpec(
        nodes=(rsi_node,),
        designated_roots=(PortRef("rsi_node", "rsi"),),
    )
    return graph_document_to_wire(GraphDocument(spec=graph_spec))


def test_worker_run_task_success() -> None:
    """Test running an isolated evaluation task in a subprocess."""

    async def scenario() -> None:
        workers = _SubprocessWorkers(WorkersConfig(max_concurrent_workers=2))
        try:
            graph_wire = _sample_rsi_graph_wire()
            payload = {
                "graph": graph_wire,
                "inputs": {
                    "rsi_node.values": [
                        44.34,
                        44.09,
                        44.15,
                        43.61,
                        44.33,
                        44.83,
                        45.10,
                        45.42,
                        45.84,
                        46.08,
                        45.89,
                        46.03,
                        45.61,
                        46.28,
                        46.28,
                        46.00,
                    ]
                },
            }

            task = WorkerTask(
                task_id="task_001",
                task_kind="execution.evaluate",
                payload=payload,
            )

            result = await workers.run_task(task)
            assert result.task_id == "task_001"
            assert result.success is True
            assert result.exit_code == 0
            from app.plugins.wire import value_to_wire

            res_dict = value_to_wire(result.result_payload)
            assert "outputs" in res_dict
            assert "rsi_node.rsi" in res_dict["outputs"]
            assert len(res_dict["outputs"]["rsi_node.rsi"]) == 16
        finally:
            await workers.close()

    asyncio.run(scenario())


def test_worker_timeout_enforcement() -> None:
    """Test that worker tasks exceeding timeout are terminated."""

    async def scenario() -> None:
        # A 0.001 second timeout should trigger timeout
        workers = _SubprocessWorkers(WorkersConfig())
        try:
            graph_wire = _sample_rsi_graph_wire()
            task = WorkerTask(
                task_id="task_timeout",
                task_kind="execution.evaluate",
                payload={"graph": graph_wire},
                budget=WorkerBudget(timeout_seconds=0.001, grace_period_seconds=0.1),
            )

            with pytest.raises(WorkerTimeoutError, match="timed out"):
                await workers.run_task(task)
        finally:
            await workers.close()

    asyncio.run(scenario())


def test_worker_invalid_task_kind_structured_error() -> None:
    """Test that unsupported worker task kind returns structured error."""

    async def scenario() -> None:
        workers = _SubprocessWorkers(WorkersConfig())
        try:
            task = WorkerTask(
                task_id="task_unsupported",
                task_kind="unsupported.kind",
                payload={},
            )
            result = await workers.run_task(task)
            assert result.success is False
            assert result.error_code == "UNSUPPORTED_TASK_KIND"
        finally:
            await workers.close()

    asyncio.run(scenario())


def test_workers_feature_lifecycle() -> None:
    """Test feature registration and context publication for HOST_WORKERS."""

    async def scenario() -> None:
        feature = _workers_feature(WorkersConfig())
        runtime = Runtime(
            (lambda: feature,),
        )
        async with runtime:
            assert "host.workers" in runtime.active_features
            workers = runtime.require(HOST_WORKERS)
            assert hasattr(workers, "run_task")

    asyncio.run(scenario())
