"""Integration tests for route-neutral Trading evaluation deadlines."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import replace

import pytest
from app.services.trading import run_live_evaluation_cycle

from tests.trading.unit.actions.test_runtime import (
    evaluation_dependencies,
    evidence,
)


def _deadline(*, timeout_on_exit: bool = False):
    """Return a scheduler-compatible fake deadline without sleeping."""

    @asynccontextmanager
    async def context(timeout_seconds, supplied_evidence) -> AsyncIterator[None]:
        del timeout_seconds, supplied_evidence
        yield
        if timeout_on_exit:
            raise TimeoutError

    return context


@pytest.mark.anyio
async def test_neutral_result_is_identical_with_injected_deadline() -> None:
    """A scheduler deadline preserves the normal neutral response semantics."""
    deps, _ = evaluation_dependencies(None)
    outcome = await run_live_evaluation_cycle(
        replace(deps, evaluation_deadline_factory=_deadline()), evidence()
    )
    assert outcome.status == "success"
    assert outcome.data == {"mutation_performed": False}


@pytest.mark.anyio
async def test_timeout_after_neutral_has_canonical_evidence_shape() -> None:
    """A scheduler timeout maps through the same canonical public error contract."""
    deps, _ = evaluation_dependencies(None)
    events = []
    outcome = await run_live_evaluation_cycle(
        replace(
            deps,
            evaluation_deadline_factory=_deadline(timeout_on_exit=True),
            event_sink=events.append,
        ),
        evidence(),
    )
    assert outcome.status == "error"
    assert events[0].event_type == "WORKFLOW_TIMEOUT"
    assert events[0].request_id == evidence()["request_id"]
    assert events[0].workflow_id == evidence()["workflow_id"]
    assert events[0].correlation_id == evidence()["correlation_id"]


@pytest.mark.anyio
async def test_upstream_error_and_cancellation_are_not_reclassified() -> None:
    """Only deadline TimeoutError is mapped; cancellation remains cooperative."""
    deps, _ = evaluation_dependencies(None)

    async def cancel(_evidence):
        raise asyncio.CancelledError

    with pytest.raises(asyncio.CancelledError):
        await run_live_evaluation_cycle(
            replace(
                deps,
                evaluation_deadline_factory=_deadline(),
                market_data_source=cancel,
            ),
            evidence(),
        )

    async def fail(_evidence):
        raise ValueError("upstream failed")

    outcome = await run_live_evaluation_cycle(
        replace(
            deps,
            evaluation_deadline_factory=_deadline(),
            market_data_source=fail,
        ),
        evidence(),
    )
    assert outcome.status == "error"
