"""Host admission keeps reservations consistent on every terminal path."""

import asyncio

import pytest
from app.host.jobs import Budget, JobManager


def test_capacity_cancellation_and_peer_denial():
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


def test_success_failure_timeout_release():
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
def test_unbounded_invalid_budgets(budget):
    with pytest.raises(ValueError):
        budget.validate()
