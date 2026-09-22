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

            task = WorkerTask.from_payload(
                "task_001", payload, task_kind="execution.evaluate"
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
            task = WorkerTask.from_payload(
                "task_timeout",
                {"graph": graph_wire},
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
            task = WorkerTask.from_payload(
                "task_unsupported", {}, task_kind="unsupported.kind"
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


def _spawn_helper(script: str) -> asyncio.subprocess.Process:
    """Spawn an ad-hoc python child for supervisor-level behavior tests."""
    import sys as _sys

    return asyncio.run(
        asyncio.create_subprocess_exec(
            _sys.executable,
            "-c",
            script,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
    )


def test_worker_values_are_immutable() -> None:
    budget = WorkerBudget()
    with pytest.raises(AttributeError, match="cannot assign"):
        budget.timeout_seconds = 5  # type: ignore[misc]
    task = WorkerTask.from_payload("t", {"k": 1})
    with pytest.raises(AttributeError, match="cannot assign"):
        task.task_id = "other"  # type: ignore[misc]
    result = task_budget_result()
    with pytest.raises(AttributeError, match="cannot assign"):
        result.success = False


def task_budget_result() -> Any:
    from app.host.workers import WorkerResult

    return WorkerResult(task_id="t", success=True)


def test_escalation_closes_stdin_first_for_graceful_exit() -> None:
    """Phase 1 (stdin close) lets a well-formed child exit without signals."""

    async def scenario() -> None:
        workers = _SubprocessWorkers(WorkersConfig())
        proc = await asyncio.create_subprocess_exec(
            "python",
            "-c",
            "import sys; sys.stdin.buffer.read(); sys.stdout.buffer.write(b'{}');",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await workers._escalate_termination(proc, grace_period=2.0)
        assert proc.returncode is not None
        await workers.close()

    asyncio.run(scenario())


def test_escalation_reaps_stubborn_process() -> None:
    """Terminate/kill fallback reaps a child that ignores stdin EOF."""

    async def scenario() -> None:
        workers = _SubprocessWorkers(WorkersConfig())
        proc = await asyncio.create_subprocess_exec(
            "python",
            "-c",
            "import time, sys\nsys.stdin.buffer.read()\ntime.sleep(30)",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await workers._escalate_termination(proc, grace_period=0.1)
        assert proc.returncode is not None
        assert workers._active_processes == {}
        await workers.close()

    asyncio.run(scenario())


def test_exchange_rejects_oversized_output_mid_read() -> None:
    """stdout beyond the cap aborts during the read, not post-hoc."""

    async def scenario() -> None:
        from app.host.workers import WorkerOversizedOutputError

        workers = _SubprocessWorkers(WorkersConfig())
        proc = await asyncio.create_subprocess_exec(
            "python",
            "-c",
            "import sys; sys.stdin.buffer.read();"
            "sys.stdout.buffer.write(b'x' * 5000); sys.stdout.flush()",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        budget = WorkerBudget(max_output_bytes=1000, idle_timeout_seconds=5.0)
        with pytest.raises(WorkerOversizedOutputError, match="mid-read"):
            await workers._exchange(proc, b"", budget)
        await workers._escalate_termination(proc, 1.0)
        assert proc.returncode is not None
        await workers.close()

    asyncio.run(scenario())


def test_startup_timeout_raises_worker_startup_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.host.workers import WorkerStartupError

    async def slow_spawn(*args: Any, **kwargs: Any) -> Any:
        await asyncio.sleep(5.0)
        raise AssertionError("should not reach")

    monkeypatch.setattr(asyncio, "create_subprocess_exec", slow_spawn)
    workers = _SubprocessWorkers(WorkersConfig())
    task = WorkerTask.from_payload(
        "t_startup",
        {"graph": _sample_rsi_graph_wire()},
        budget=WorkerBudget(startup_timeout_seconds=0.05),
    )

    async def scenario() -> None:
        with pytest.raises(WorkerStartupError, match="did not start"):
            await workers.run_task(task)
        await workers.close()

    asyncio.run(scenario())


def test_finalize_result_crash_and_malformed_output() -> None:
    from app.host.workers import WorkerCrashError, WorkerProtocolError

    workers = _SubprocessWorkers(WorkersConfig())
    task = WorkerTask.from_payload("t_parse", {})

    with pytest.raises(WorkerCrashError, match="exited with code 3"):
        workers._finalize_result(task, b"", b"boom", 3, 0.1)

    with pytest.raises(WorkerProtocolError, match="invalid JSON"):
        workers._finalize_result(task, b"this is not json", b"", 0, 0.1)

    bad_envelope = b'{"version": 1, "task_id": "other"}'
    with pytest.raises(WorkerProtocolError, match="protocol validation"):
        workers._finalize_result(task, bad_envelope, b"", 0, 0.1)

    asyncio.run(workers.close())


def test_worker_verifies_entry_fingerprints_end_to_end() -> None:
    """Wrong pinned entry fingerprint fails; exact fingerprint succeeds."""

    async def scenario() -> None:
        from app.host.bootstrap import approved_catalog_roots, create_runtime
        from app.host.catalog import HOST_CATALOG
        from app.plugins.spec import PluginRef

        runtime = create_runtime(catalog_roots=approved_catalog_roots())
        async with runtime:
            catalog = runtime.require(HOST_CATALOG)
            admitted = catalog.admit(
                PluginRef(id="indicator.rsi", version=(1, 0, 0)), "compute"
            )

        workers = _SubprocessWorkers(WorkersConfig())
        try:
            payload = {
                "graph": _sample_rsi_graph_wire(),
                "inputs": {"rsi_node.values": [10.0, 11.0, 12.0, 13.0, 14.0]},
                "entry_fingerprints": {
                    "indicator.rsi@1.0.0#compute": "0" * 64,
                },
                "dependency_fingerprint": "1" * 64,
            }
            mismatch = await workers.run_task(
                WorkerTask.from_payload("fp_bad", payload)
            )
            assert mismatch.success is False
            assert mismatch.error_code == "ENTRY_FINGERPRINT_MISMATCH"

            payload["entry_fingerprints"] = {
                "indicator.rsi@1.0.0#compute": admitted.entry_fingerprint,
            }
            payload["dependency_fingerprint"] = admitted.dependency_fingerprint
            ok = await workers.run_task(WorkerTask.from_payload("fp_good", payload))
            assert ok.success is True, ok.error_message
        finally:
            await workers.close()

    asyncio.run(scenario())


def test_worker_rejects_missing_pinned_dependency() -> None:
    async def scenario() -> None:
        workers = _SubprocessWorkers(WorkersConfig())
        try:
            payload = {
                "graph": _sample_rsi_graph_wire(),
                "entry_fingerprints": {
                    "indicator.nonexistent@9.0.0#compute": "0" * 64,
                },
            }
            result = await workers.run_task(
                WorkerTask.from_payload("fp_missing", payload)
            )
            assert result.success is False
            assert result.error_code == "DEPENDENCY_MISSING"
        finally:
            await workers.close()

    asyncio.run(scenario())
