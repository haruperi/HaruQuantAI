"""Host admission keeps reservations consistent on every terminal path."""

import asyncio
from typing import Any

import pytest
from app.host.jobs import Budget, JobManager


def test_capacity_cancellation_and_peer_denial() -> None:
    async def run() -> None:
        jobs = JobManager(1, 1024)

        async def wait() -> None:
            await asyncio.Event().wait()

        first = jobs.submit("one", Budget(1, 512, 10), wait)
        with pytest.raises(ValueError, match="Insufficient"):
            jobs.submit("two", Budget(1, 512, 10), wait)
        with pytest.raises(PermissionError):
            jobs.cancel("two", first.id)
        await jobs.close()
        await asyncio.sleep(0)
        assert jobs.status("one", first.id).state == "cancelled"
        assert jobs.reserved == (0, 0)
        with pytest.raises(ValueError, match="unavailable"):
            jobs.submit("one", Budget(1, 1, 1), wait)

    asyncio.run(run())


def test_success_failure_timeout_release() -> None:
    async def run() -> None:
        jobs = JobManager(3, 1024)

        async def good() -> None:
            await asyncio.sleep(0)

        async def bad() -> None:
            raise RuntimeError("sensitive contents never enter status")

        async def slow() -> None:
            await asyncio.sleep(10)

        values = [jobs.submit("one", Budget(1, 1, 0.01), f) for f in (good, bad, slow)]
        await asyncio.gather(*tuple(jobs.tasks.values()))
        await asyncio.sleep(0)
        assert [jobs.status("one", v.id).state for v in values] == [
            "succeeded",
            "failed",
            "timed_out",
        ]
        assert jobs.reserved == (0, 0)
        await jobs.close()

    asyncio.run(run())


@pytest.mark.parametrize(
    "budget",
    [Budget(0, 1, 1), Budget(1, 0, 1), Budget(1, 1, float("inf")), Budget(1, 1, -1)],
)
def test_unbounded_invalid_budgets(budget: Any) -> None:
    with pytest.raises(ValueError):
        budget.validate()


def test_observed_terminal_state_has_released_admission_capacity() -> None:
    async def run() -> None:
        jobs = JobManager(1, 1024)

        async def finish() -> Any:
            return

        first = jobs.submit("one", Budget(1, 512, 10), finish)
        await asyncio.sleep(0)
        assert jobs.status("one", first.id).state == "succeeded"
        second = jobs.submit("one", Budget(1, 512, 10), finish)
        await asyncio.sleep(0)
        assert jobs.status("one", second.id).state == "succeeded"
        await asyncio.sleep(0)
        assert jobs.reserved == (0, 0)
        await jobs.close()

    asyncio.run(run())


def test_compute_retains_admission_until_cancelled_worker_finishes() -> None:
    import threading

    entered = threading.Event()
    release = threading.Event()

    def compute() -> int:
        entered.set()
        assert release.wait(2)
        return 42

    async def run() -> None:
        manager = JobManager(1, 100)
        with pytest.raises(PermissionError, match="admitted"):
            await manager.offload("owner", compute)

        async def body() -> None:
            await manager.offload("owner", compute)

        started = manager.submit("owner", Budget(1, 100, 3), body)
        await asyncio.to_thread(entered.wait, 1)
        manager.cancel("owner", started.id)
        await asyncio.sleep(0.01)
        assert manager.reserved == (1, 100)
        with pytest.raises(ValueError, match="resources"):
            manager.submit("another", Budget(1, 1, 1), body)
        task = manager.tasks[started.id]
        release.set()
        await asyncio.gather(task, return_exceptions=True)
        assert manager.status("owner", started.id).state == "cancelled"
        assert manager.reserved == (0, 0)
        await manager.close()

    asyncio.run(run())
