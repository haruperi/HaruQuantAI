"""Host workers owner: subprocess-per-job execution and supervisor."""

from __future__ import annotations

import asyncio
import contextlib
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol, override

from app.kernel.capability import Capability
from app.kernel.context import FeatureContext
from app.kernel.feature import FeatureSpec
from app.plugins.schema import (
    EMPTY_FROZEN_OBJECT,
    FrozenObject,
    freeze_value,
)
from app.plugins.wire import (
    parse_strict_json,
    to_canonical_json_bytes,
    value_to_wire,
)


class WorkerError(RuntimeError):
    """Base error for worker failures."""


class WorkerTimeoutError(WorkerError):
    """Raised when worker execution exceeds configured budget timeout."""


class WorkerCrashError(WorkerError):
    """Raised when worker process terminates unexpectedly with non-zero exit code."""


class WorkerCancellationError(WorkerError):
    """Raised when worker execution is cancelled."""


class WorkerOversizedOutputError(WorkerError):
    """Raised when worker stdout exceeds maximum output bytes."""


class WorkerStartupError(WorkerError):
    """Raised when the worker process does not start within its budget."""


class WorkerProtocolError(WorkerError):
    """Raised when worker request or response violates wire protocol."""


@dataclass(frozen=True, slots=True)
class WorkerBudget:
    """Immutable resource limits for one subprocess worker task."""

    timeout_seconds: float = 60.0
    max_output_bytes: int = 10_000_000
    grace_period_seconds: float = 2.0
    startup_timeout_seconds: float = 10.0
    idle_timeout_seconds: float = 30.0

    def __post_init__(self) -> None:
        """Validate budget fields."""
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be > 0")
        if self.max_output_bytes <= 0:
            raise ValueError("max_output_bytes must be > 0")
        if self.grace_period_seconds <= 0:
            raise ValueError("grace_period_seconds must be > 0")
        if self.startup_timeout_seconds <= 0:
            raise ValueError("startup_timeout_seconds must be > 0")
        if self.idle_timeout_seconds <= 0:
            raise ValueError("idle_timeout_seconds must be > 0")


DEFAULT_WORKER_BUDGET = WorkerBudget()

MAX_STDERR_BYTES = 10_000
_READ_CHUNK_BYTES = 65_536


@dataclass(frozen=True, slots=True)
class WorkerTask:
    """Immutable specification for one isolated worker execution task."""

    task_id: str
    task_kind: str = "execution.evaluate"
    payload: FrozenObject = EMPTY_FROZEN_OBJECT
    budget: WorkerBudget = DEFAULT_WORKER_BUDGET

    def __post_init__(self) -> None:
        """Validate and normalize the task specification."""
        if not self.task_id or not isinstance(self.task_id, str):
            raise ValueError("task_id must be a non-empty string")
        if not self.task_kind or not isinstance(self.task_kind, str):
            raise ValueError("task_kind must be a non-empty string")
        if not isinstance(self.budget, WorkerBudget):
            raise TypeError("budget must be a WorkerBudget")

    @classmethod
    def from_payload(
        cls,
        task_id: str,
        payload: FrozenObject | dict[str, Any],
        *,
        task_kind: str = "execution.evaluate",
        budget: WorkerBudget = DEFAULT_WORKER_BUDGET,
    ) -> WorkerTask:
        """Build a task, freezing dict payloads into immutable form."""
        if isinstance(payload, dict):
            frozen = freeze_value(payload)
            if not isinstance(frozen, FrozenObject):
                raise TypeError("payload must freeze to FrozenObject")
            normalized = frozen
        elif isinstance(payload, FrozenObject):
            normalized = payload
        else:
            raise TypeError("payload must be a FrozenObject or dict")
        return cls(
            task_id=task_id,
            task_kind=task_kind,
            payload=normalized,
            budget=budget,
        )


@dataclass(frozen=True, slots=True)
class WorkerResult:
    """Immutable outcome of one subprocess worker task."""

    task_id: str
    success: bool
    result_payload: FrozenObject = EMPTY_FROZEN_OBJECT
    elapsed_seconds: float = 0.0
    exit_code: int = 0
    error_code: str = ""
    error_message: str = ""


class WorkersConfig:
    """Configuration for subprocess worker supervisor."""

    __slots__ = ("default_budget", "max_concurrent_workers", "repo_root")

    def __init__(
        self,
        max_concurrent_workers: int = 4,
        default_budget: WorkerBudget = DEFAULT_WORKER_BUDGET,
        repo_root: Path | None = None,
    ) -> None:
        if max_concurrent_workers <= 0:
            raise ValueError("max_concurrent_workers must be > 0")
        self.max_concurrent_workers = max_concurrent_workers
        self.default_budget = default_budget
        self.repo_root = (
            repo_root or Path(__file__).resolve().parent.parent.parent
        ).resolve()


class Workers(Protocol):
    """Public capability protocol for isolated subprocess execution."""

    async def run_task(self, task: WorkerTask) -> WorkerResult:
        """Run an isolated task in a subprocess and return its result."""
        ...

    async def close(self) -> None:
        """Terminate active workers and release supervisor resources."""
        ...


HOST_WORKERS = Capability[Workers]("host.workers", 1)

_ENV_ALLOWLIST = frozenset(
    {
        "PATH",
        "SYSTEMROOT",
        "SYSTEMDRIVE",
        "TEMP",
        "TMP",
        "USERPROFILE",
        "HOMEDRIVE",
        "HOMEPATH",
        "LANG",
        "LC_ALL",
        "VIRTUAL_ENV",
    }
)


class _SubprocessWorkers(Workers):
    """Private supervisor launching process-per-job workers."""

    def __init__(self, config: WorkersConfig) -> None:
        """Initialize supervisor."""
        self._config = config
        self._semaphore = asyncio.Semaphore(config.max_concurrent_workers)
        self._active_processes: dict[str, asyncio.subprocess.Process] = {}
        self._closed = False

    def _build_sanitized_env(self) -> dict[str, str]:
        """Construct a minimal sanitized environment allowlist."""
        env: dict[str, str] = {}
        for key in _ENV_ALLOWLIST:
            if key in os.environ:
                env[key] = os.environ[key]

        # Explicitly configure PYTHONPATH to repository root
        env["PYTHONPATH"] = str(self._config.repo_root)
        env["PYTHONUNBUFFERED"] = "1"
        return env

    @override
    async def run_task(self, task: WorkerTask) -> WorkerResult:
        """Run task inside a dedicated subprocess with timeout and cancellation."""
        if self._closed:
            raise WorkerError("Workers supervisor is closed")

        async with self._semaphore:
            start_time = time.monotonic()
            cmd = [sys.executable, "-m", "app.host.bootstrap", "--worker"]
            env = self._build_sanitized_env()

            request_envelope = {
                "version": 1,
                "task_id": task.task_id,
                "task_kind": task.task_kind,
                "payload": value_to_wire(task.payload),
            }
            request_bytes = to_canonical_json_bytes(request_envelope)

            stdout_data, stderr_data, exit_code = await self._spawn_and_exchange(
                task, request_bytes, env, cmd
            )

            elapsed = time.monotonic() - start_time
            return self._finalize_result(
                task, stdout_data, stderr_data, exit_code, elapsed
            )

    def _finalize_result(
        self,
        task: WorkerTask,
        stdout_data: bytes,
        stderr_data: bytes,
        exit_code: int,
        elapsed: float,
    ) -> WorkerResult:
        """Validate the raw exchange outcome into a WorkerResult."""
        if exit_code != 0:
            stderr_text = stderr_data.decode("utf-8", errors="replace")[:1000]
            raise WorkerCrashError(
                f"Worker process for task {task.task_id} exited with "
                f"code {exit_code}: {stderr_text}"
            )

        try:
            raw_response = parse_strict_json(stdout_data)
        except Exception as err:
            raise WorkerProtocolError(
                f"Worker for task {task.task_id} returned invalid JSON: {err}"
            ) from err

        if (
            not isinstance(raw_response, dict)
            or raw_response.get("version") != 1
            or raw_response.get("task_id") != task.task_id
        ):
            raise WorkerProtocolError(
                f"Worker response failed protocol validation for task {task.task_id}"
            )

        success = bool(raw_response.get("success", False))
        result_raw = raw_response.get("result", {})
        frozen_result = (
            freeze_value(result_raw)
            if isinstance(result_raw, dict)
            else EMPTY_FROZEN_OBJECT
        )
        if not isinstance(frozen_result, FrozenObject):
            frozen_result = EMPTY_FROZEN_OBJECT

        error_code = str(raw_response.get("error_code") or "")
        error_message = str(raw_response.get("error_message") or "")

        return WorkerResult(
            task_id=task.task_id,
            success=success,
            result_payload=frozen_result,
            elapsed_seconds=elapsed,
            exit_code=exit_code,
            error_code=error_code,
            error_message=error_message,
        )

    async def _spawn_and_exchange(
        self,
        task: WorkerTask,
        request_bytes: bytes,
        env: dict[str, str],
        cmd: list[str],
    ) -> tuple[bytes, bytes, int]:
        """Spawn the worker and run the bounded JSON exchange.

        Raises WorkerTimeoutError / WorkerOversizedOutputError /
        WorkerStartupError according to which budget phase failed.
        """
        try:
            proc = await asyncio.wait_for(
                asyncio.create_subprocess_exec(
                    *cmd,
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    env=env,
                    cwd=str(self._config.repo_root),
                ),
                timeout=task.budget.startup_timeout_seconds,
            )
        except TimeoutError as err:
            raise WorkerStartupError(
                f"Task {task.task_id} worker did not start within "
                f"{task.budget.startup_timeout_seconds}s"
            ) from err

        self._active_processes[task.task_id] = proc
        if proc.stdin is None or proc.stdout is None or proc.stderr is None:
            raise WorkerProtocolError("worker pipes were not created")
        try:
            stdout_data, stderr_data = await asyncio.wait_for(
                self._exchange(proc, request_bytes, task.budget),
                timeout=task.budget.timeout_seconds,
            )
        except TimeoutError:
            await self._escalate_termination(proc, task.budget.grace_period_seconds)
            raise WorkerTimeoutError(
                f"Task {task.task_id} timed out after {task.budget.timeout_seconds}s"
            ) from None
        except asyncio.CancelledError:
            await self._escalate_termination(proc, task.budget.grace_period_seconds)
            raise WorkerCancellationError(
                f"Task {task.task_id} was cancelled"
            ) from None
        except WorkerOversizedOutputError:
            await self._escalate_termination(proc, task.budget.grace_period_seconds)
            raise
        finally:
            self._active_processes.pop(task.task_id, None)

        if len(stdout_data) > task.budget.max_output_bytes:
            await self._escalate_termination(proc, task.budget.grace_period_seconds)
            raise WorkerOversizedOutputError(
                f"Task {task.task_id} produced {len(stdout_data)} bytes, "
                f"exceeding {task.budget.max_output_bytes}"
            )
        return stdout_data, stderr_data, proc.returncode or 0

    async def _exchange(
        self,
        proc: asyncio.subprocess.Process,
        request_bytes: bytes,
        budget: WorkerBudget,
    ) -> tuple[bytes, bytes]:
        """Write one request, then read bounded stdout/stderr concurrently."""
        if proc.stdin is None or proc.stdout is None or proc.stderr is None:
            raise WorkerProtocolError("worker pipes were not created")
        stdin = proc.stdin

        async def write_request() -> None:
            stdin.write(request_bytes)
            await stdin.drain()
            stdin.close()
            # Closing stdin is the graceful shutdown signal: the worker
            # child exits on request EOF.
            await stdin.wait_closed()

        async def read_bounded(stream: asyncio.StreamReader, cap: int) -> bytes:
            chunks: list[bytes] = []
            total = 0
            while True:
                chunk = await asyncio.wait_for(
                    stream.read(_READ_CHUNK_BYTES), timeout=budget.idle_timeout_seconds
                )
                if not chunk:
                    break
                total += len(chunk)
                if total > cap:
                    raise WorkerOversizedOutputError(
                        f"Worker output exceeded {cap} bytes mid-read"
                    )
                chunks.append(chunk)
            return b"".join(chunks)

        await write_request()
        stdout_data, stderr_data = await asyncio.gather(
            read_bounded(proc.stdout, budget.max_output_bytes),
            read_bounded(proc.stderr, MAX_STDERR_BYTES),
        )
        await proc.wait()
        return stdout_data, stderr_data

    async def _escalate_termination(
        self, proc: asyncio.subprocess.Process, grace_period: float
    ) -> None:
        """Full cancellation escalation: stdin close, grace, terminate, kill."""
        # Phase 1: close stdin so a well-formed child exits on request EOF.
        if proc.stdin is not None and not proc.stdin.is_closing():
            proc.stdin.close()
        if await self._await_exit(proc, grace_period):
            self._reap_transport(proc)
            return
        # Phase 2: request OS-level termination.
        with contextlib.suppress(ProcessLookupError):
            proc.terminate()
        if await self._await_exit(proc, grace_period):
            self._reap_transport(proc)
            return
        # Phase 3: unconditional kill, then reap.
        with contextlib.suppress(ProcessLookupError):
            proc.kill()
            await proc.wait()
        self._reap_transport(proc)

    async def _await_exit(
        self, proc: asyncio.subprocess.Process, grace_period: float
    ) -> bool:
        """Wait bounded for exit; False when still live after the grace."""
        try:
            await asyncio.wait_for(proc.wait(), timeout=grace_period)
            return True
        except TimeoutError, ProcessLookupError:
            return False

    def _reap_transport(self, proc: asyncio.subprocess.Process) -> None:
        """Close the subprocess transport so no pipe survives termination."""
        transport = getattr(proc, "_transport", None)
        if transport is not None:
            transport.close()

    @override
    async def close(self) -> None:
        """Terminate all active worker processes with full escalation."""
        self._closed = True
        active = list(self._active_processes.values())
        for proc in active:
            await self._escalate_termination(proc, grace_period=1.0)
        self._active_processes.clear()


class _WorkersFeature:
    """Feature providing HOST_WORKERS."""

    spec = FeatureSpec(
        "host.workers",
        provides=frozenset({HOST_WORKERS}),
        description="Subprocess worker pool for isolated task execution",
    )

    def __init__(self, config: WorkersConfig) -> None:
        self._config = config
        self._service: _SubprocessWorkers | None = None

    async def start(self, context: FeatureContext) -> None:
        self._service = _SubprocessWorkers(self._config)
        context.on_close(self._service.close)
        context.provide(HOST_WORKERS, self._service)


def _workers_feature(config: WorkersConfig) -> _WorkersFeature:
    """Construct the workers owner for the host composition root only."""
    return _WorkersFeature(config)


__all__ = (
    "DEFAULT_WORKER_BUDGET",
    "HOST_WORKERS",
    "MAX_STDERR_BYTES",
    "WorkerBudget",
    "WorkerCancellationError",
    "WorkerCrashError",
    "WorkerError",
    "WorkerOversizedOutputError",
    "WorkerProtocolError",
    "WorkerResult",
    "WorkerStartupError",
    "WorkerTask",
    "WorkerTimeoutError",
    "Workers",
    "WorkersConfig",
    "_workers_feature",
)
