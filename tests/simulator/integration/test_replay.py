"""Workflow integration test for deterministic official-journal replay."""
# ruff: noqa: INP001

from pathlib import Path

from app.services.simulator import run_backtest
from app.services.simulator.journal import JournalEvent, replay_journal
from app.utils import logger
from tests.simulator.unit.test_orchestrator import (
    FakeDependencies,
    _auth,
    _dataset,
    _request,
)


def _count_events(state: object, event: JournalEvent) -> dict[str, object]:
    """Reduce replay evidence to its deterministic event count."""
    logger.debug("Reducing one official journal event during replay")
    del state
    return {"events": event.sequence + 1, "last_type": event.event_type}


def test_completed_run_replays_to_terminal_state(tmp_path: Path) -> None:
    """Validate the hash chain and reconstruct the terminal run event."""
    logger.info("Testing WF-SIM-005 deterministic replay")
    dataset = _dataset(f"req-{'f' * 64}")
    request = _request(dataset, suffix="f")
    dependencies = FakeDependencies(tmp_path, dataset)
    result = run_backtest(request, _auth(request), dependencies)  # type: ignore[arg-type]
    state = replay_journal(
        dependencies.artifact_root / result.journal_ref,
        _count_events,
    )
    assert state["events"] >= 3  # type: ignore[operator]
    assert state["last_type"] == "run_completed"
