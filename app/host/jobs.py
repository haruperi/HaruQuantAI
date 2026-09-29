"""Host-owned finite job admission and cooperative execution lifecycle."""

from __future__ import annotations

import asyncio
import math
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, replace
from typing import Literal
from uuid import uuid4

from app.host.logging import get_logger

logger = get_logger(__name__)

MAX_JOBS = 4096
SHUTDOWN_SECONDS = 5.0


@dataclass(frozen=True)
class Budget:
    """Logical CPU/memory reservation and finite cooperative deadline."""

    workers: int
    memory_bytes: int
    timeout_seconds: float

    def validate(self) -> None:
        """Reject nonpositive, unbounded or nonintegral resource requests."""
        if (
            type(self.workers) is not int
            or type(self.memory_bytes) is not int
            or self.workers < 1
            or self.memory_bytes < 1
            or not math.isfinite(self.timeout_seconds)
            or self.timeout_seconds <= 0
        ):
            raise ValueError("Invalid job budget")


@dataclass(frozen=True)
class Job:
    """Immutable job state without exception text or task-input diagnostics."""

    id: str
    owner: str
    budget: Budget
    state: Literal["queued", "running", "succeeded", "failed", "cancelled", "timed_out"]


class JobManager:
    """One event-loop admission authority shared by all scoped owner capabilities."""

    def __init__(self, workers: int, memory_bytes: int) -> None:
        Budget(workers, memory_bytes, 1).validate()
        self.capacity = (workers, memory_bytes)
        self.reserved = (0, 0)
        self.records: dict[str, Job] = {}
        self.tasks: dict[str, asyncio.Task[None]] = {}
        self.closed = False

    def submit(
        self, owner: str, budget: Budget, operation: Callable[[], Awaitable[None]]
    ) -> Job:
        """Reserve capacity before starting an explicitly supplied local task body.

        Raises:
            ValueError: Invalid budget, owner, capacity or admission lifecycle.
        """
        budget.validate()
        if not owner or self.closed or len(self.records) >= MAX_JOBS:
            raise ValueError("Job admission unavailable")
        workers = self.reserved[0] + budget.workers
        memory = self.reserved[1] + budget.memory_bytes
        if workers > self.capacity[0] or memory > self.capacity[1]:
            raise ValueError("Insufficient host resources")
        loop = asyncio.get_running_loop()
        job = Job(uuid4().hex, owner, budget, "queued")
        self.reserved = (workers, memory)
        self.records[job.id] = job
        self.tasks[job.id] = loop.create_task(self._run(job, operation))
        self.tasks[job.id].add_done_callback(lambda _task: self._finished(job))
        logger.info(
            "Host job submitted: id=%s, owner=%s, budget=(workers=%d, "
            "mem=%dMB, timeout=%.1fs)",
            job.id,
            owner,
            budget.workers,
            budget.memory_bytes // (1024 * 1024),
            budget.timeout_seconds,
        )
        return job

    def _finished(self, job: Job) -> None:
        """Release reservations even for cancellation before a queued task starts."""
        self.tasks.pop(job.id, None)
        self.reserved = (
            self.reserved[0] - job.budget.workers,
            self.reserved[1] - job.budget.memory_bytes,
        )
        if self.records[job.id].state in {"queued", "running"}:
            self.records[job.id] = replace(job, state="cancelled")

    async def _run(self, job: Job, operation: Callable[[], Awaitable[None]]) -> None:
        """Run one trusted cooperative body and record only attributed safe outcomes."""
        self.records[job.id] = replace(job, state="running")
        logger.debug("Host job started: id=%s, owner=%s", job.id, job.owner)
        try:
            async with asyncio.timeout(job.budget.timeout_seconds):
                await operation()
        except TimeoutError:
            self.records[job.id] = replace(job, state="timed_out")
            logger.warning(
                "Host job timed out: id=%s, owner=%s (timeout=%.1fs)",
                job.id,
                job.owner,
                job.budget.timeout_seconds,
            )
        except asyncio.CancelledError:
            self.records[job.id] = replace(job, state="cancelled")
            logger.info("Host job cancelled: id=%s, owner=%s", job.id, job.owner)
            raise
        except Exception:
            self.records[job.id] = replace(job, state="failed")
            logger.exception("Host job failed: id=%s, owner=%s", job.id, job.owner)
        else:
            self.records[job.id] = replace(job, state="succeeded")
            logger.info("Host job succeeded: id=%s, owner=%s", job.id, job.owner)

    def status(self, owner: str, job_id: str) -> Job:
        """Read only the caller's job, without granting peer execution authority."""
        job = self.records[job_id]
        if job.owner != owner:
            raise PermissionError("Job access denied")
        return job

    def cancel(self, owner: str, job_id: str) -> None:
        """Request cooperative cancellation of an owned job."""
        self.status(owner, job_id)
        logger.info("Host job cancel requested: id=%s, owner=%s", job_id, owner)
        task = self.tasks.get(job_id)
        if task is not None:
            task.cancel()

    async def close(self, owner: str | None = None) -> None:
        """Cancel owned/all jobs and report bodies that fail to stop within the bound.

        Reservations are retained until a task actually finishes. This is not OS
        process containment for an uncooperative extension.
        """
        if owner is None:
            self.closed = True
        pending = [
            task
            for key, task in self.tasks.items()
            if owner is None or self.records[key].owner == owner
        ]
        for task in pending:
            task.cancel()
        if pending:
            _, unfinished = await asyncio.wait(pending, timeout=SHUTDOWN_SECONDS)
            if unfinished:
                raise TimeoutError("Owner jobs did not stop")
