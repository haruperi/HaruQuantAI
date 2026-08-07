"""Workflow integration test for all-or-nothing portfolio simulation."""

from decimal import Decimal
from pathlib import Path

from app.services.simulator import (
    get_simulation_value_field,
    replay_journal,
    run_portfolio_backtest,
    unwrap_simulation_response,
)
from app.utils import get_logger

from tests.simulator.component.test_orchestrator import FakeDependencies, _dataset
from tests.simulator.component.test_portfolio_run import (
    _portfolio_auth,
    _portfolio_request,
)

logger = get_logger(__name__)


def _last_event(state: object, event: object) -> dict[str, object]:
    """Project the latest aggregate journal event."""
    logger.debug("Reducing one portfolio aggregate journal event")
    del state
    return {"last_type": get_simulation_value_field(event, "event_type")}


def test_portfolio_candidate_publishes_reconciled_aggregate(tmp_path: Path) -> None:
    """Complete every component before publishing the aggregate manifest."""
    logger.info("Testing WF-SIM-009 portfolio backtest")
    request = _portfolio_request()
    dataset = _dataset("req-66666666-6666-4666-8666-666666666666")
    dependencies = FakeDependencies(tmp_path, dataset)
    result = unwrap_simulation_response(
        run_portfolio_backtest(request, _portfolio_auth(request), dependencies),
        operation="test.portfolio.run_portfolio_backtest",
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
    replayed = unwrap_simulation_response(
        replay_journal(
            dependencies.artifact_root / result.aggregate_journal_ref,
            _last_event,
        ),
        operation="test.portfolio.replay_journal",
    )
    assert replayed["last_type"] == "portfolio_completed"
