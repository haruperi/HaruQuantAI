"""Workflow integration test for deterministic official-journal replay."""

from pathlib import Path

from app.services.simulator import (
    get_simulation_value_field,
    replay_journal,
    run_backtest,
    unwrap_simulation_response,
)
from app.utils import get_logger

from tests.simulator.unit.test_orchestrator import (
    FakeDependencies,
    _auth,
    _dataset,
    _request,
)

logger = get_logger(__name__)


def _count_events(state: object, event: object) -> dict[str, object]:
    """Reduce replay evidence to its deterministic event count."""
    logger.debug("Reducing one official journal event during replay")
    del state
    sequence = get_simulation_value_field(event, "sequence")
    assert isinstance(sequence, int)
    return {
        "events": sequence + 1,
        "last_type": get_simulation_value_field(event, "event_type"),
    }


def test_completed_run_replays_to_terminal_state(tmp_path: Path) -> None:
    """Validate the hash chain and reconstruct the terminal run event."""
    logger.info("Testing WF-SIM-005 deterministic replay")
    dataset = _dataset("req-ffffffff-ffff-4fff-8fff-ffffffffffff")
    request = _request(dataset, suffix="f")
    dependencies = FakeDependencies(tmp_path, dataset)
    result = unwrap_simulation_response(
        run_backtest(request, _auth(request), dependencies),
        operation="test.replay.run_backtest",
    )
    state = unwrap_simulation_response(
        replay_journal(
            dependencies.artifact_root / result.journal_ref,
            _count_events,
        ),
        operation="test.replay.replay_journal",
    )
    assert state["events"] >= 3  # type: ignore[operator]
    assert state["last_type"] == "run_completed"
