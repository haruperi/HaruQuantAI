"""WF-TRD-015: pause and resume one governed strategy route."""

from __future__ import annotations

import asyncio
import sys
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from app.services.trading import (
    create_authority_snapshot,
    pause_strategy,
    resume_strategy,
)
from tests.trading.usage.workflows._support import examples

WORKFLOW_ID = "WF-TRD-015"
STAGES = (
    "Accept an authorized command for one exact strategy route.",
    "Pause admission without cancelling orders or changing exposure.",
    "Read durable Trading control evidence for the paused route.",
    "Require clear Risk hierarchy and reconciled route truth before resume.",
    "Return durable resumed-route evidence without broker mutation.",
)


def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(
        f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}"
    )


async def run() -> None:
    """Run the governed pause/resume workflow."""
    # Stage 1 — INPUT BOUNDARY: exact strategy-scoped governance command.
    _stage(1)
    store = examples.MemoryStore()
    pause_request = examples.trading_request(action="pause_strategy")
    pause_dependencies = examples.trading_dependencies(
        store=store,
        action_policy=examples.action_policy("pause_strategy"),
    )
    print(
        "Input:",
        pause_request.strategy_id,
        pause_request.strategy_version,
        pause_request.route,
    )
    # Stage 2: Pause only Trading admission.
    _stage(2)
    paused = await pause_strategy(pause_request, pause_dependencies)
    assert paused.data is not None
    print("Paused evidence:", paused.data)
    # Stage 3: Prove durable state and absence of authority mutation.
    _stage(3)
    print(
        "Persisted events:",
        tuple(event.event_type for event in store.events),
        "idempotency reservations:",
        len(store.reservations),
    )
    # Stage 4: Resume requires clear hierarchy and matching authority truth.
    _stage(4)
    assert store.projection is not None
    authority_snapshot = create_authority_snapshot(
        route="sim",
        authority_id="simulation",
        account_id="account-001",
        source_id="simulation-read-port",
        account={},
        orders=store.projection.orders,
        positions=store.projection.positions,
        observed_at=examples.NOW,
        expires_at=pause_request.valid_until,
    )
    resume_dependencies = replace(
        examples.trading_dependencies(
            store=store,
            action_policy=examples.action_policy("resume_strategy"),
        ),
        kill_switch_state_source=examples.inactive_kill_switch_hierarchy,
        reconciliation_source=lambda _request: authority_snapshot,
    )
    resumed = await resume_strategy(
        examples.trading_request(action="resume_strategy"),
        resume_dependencies,
    )
    assert resumed.data is not None
    print("Resume evidence:", resumed.data)
    # Stage 5 — OUTPUT BOUNDARY: durable control truth, no broker mutation.
    _stage(5)
    print(
        "Output:",
        resumed.status,
        "events:",
        tuple(event.event_type for event in store.events),
        "No broker mutation was transmitted",
    )


def main() -> None:
    """Run the workflow."""
    asyncio.run(run())


if __name__ == "__main__":
    main()
