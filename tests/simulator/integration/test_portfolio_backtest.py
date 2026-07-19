"""Workflow integration test for all-or-nothing portfolio simulation."""
# ruff: noqa: INP001

from decimal import Decimal
from pathlib import Path

from app.services.simulator import run_portfolio_backtest
from app.services.simulator.journal import JournalEvent, replay_journal
from app.utils import logger
from tests.simulator.unit.test_orchestrator import FakeDependencies, _dataset
from tests.simulator.unit.test_portfolio_run import (
    _portfolio_auth,
    _portfolio_request,
)


def _last_event(state: object, event: JournalEvent) -> dict[str, object]:
    """Project the latest aggregate journal event."""
    logger.debug("Reducing one portfolio aggregate journal event")
    del state
    return {"last_type": event.event_type}


def test_portfolio_candidate_publishes_reconciled_aggregate(tmp_path: Path) -> None:
    """Complete every component before publishing the aggregate manifest."""
    logger.info("Testing WF-SIM-009 portfolio backtest")
    request = _portfolio_request()
    dataset = _dataset(f"req-{'6' * 64}")
    dependencies = FakeDependencies(tmp_path, dataset)
    result = run_portfolio_backtest(
        request,
        _portfolio_auth(request),
        dependencies,  # type: ignore[arg-type]
    )
    assert result.status == "completed"
    assert all(row.reconciled for row in result.component_results)
    assert len(result.component_return_series[0].observations) == 30
    component_total = sum(
        (item.approved_budget for item in result.risk_budget_history), Decimal(0)
    )
    assert component_total > Decimal(0)
    assert result.component_return_series[0].simulation_result_id == (
        result.component_results[0].simulation_result_id
    )
    assert (dependencies.artifact_root / result.artifact_manifest_ref).is_file()
    replayed = replay_journal(
        dependencies.artifact_root / result.aggregate_journal_ref,
        _last_event,
    )
    assert replayed["last_type"] == "portfolio_completed"
