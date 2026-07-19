"""Producer README fixture-parity checks for Analytics inputs."""

# ruff: noqa: INP001

import json
from pathlib import Path

from app.utils import logger

_ROOT = Path(__file__).resolve().parents[3]
_TRADE_FIELDS = {
    "ticket",
    "symbol",
    "type",
    "volume",
    "entry_time",
    "entry_price",
    "stop_loss",
    "take_profit",
    "exit_time",
    "exit_price",
    "comment",
    "commission",
    "swap",
    "profit",
    "magic",
    "mae",
    "mfe",
}
_PORTFOLIO_FIELDS = {
    "contract_version",
    "schema_id",
    "result_id",
    "run_id",
    "request_hash",
    "config_hash",
    "data_hash",
    "result_hash",
    "engine_version",
    "status",
    "portfolio_id",
    "construction_result_id",
    "construction_version",
    "measurement_start",
    "measurement_end",
    "base_currency",
    "component_results",
    "component_return_series",
    "aggregate_journal_ref",
    "aggregate_metrics_ref",
    "risk_budget_history",
    "fx_evidence_ids",
    "artifact_manifest",
}
_COMPONENT_FIELDS = {
    "component_id",
    "simulation_result_id",
    "journal_ref",
    "metrics_ref",
    "account_currency",
    "reconciled",
}
_RETURN_FIELDS = {"component_id", "simulation_result_id", "observations"}
_OBSERVATION_FIELDS = {"timestamp", "return_value"}


def _fixture() -> dict[str, object]:
    """Load the canonical producer fixture."""
    logger.debug("Loading Analytics upstream parity fixture")
    path = _ROOT / "tests" / "analytics" / "fixtures" / "canonical_ledger.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _portfolio_fixture() -> dict[str, object]:
    """Load the frozen portfolio producer fixture.

    Returns:
        JSON-decoded PortfolioSimulationResult evidence.
    """
    logger.debug("Loading Analytics portfolio upstream parity fixture")
    path = (
        _ROOT / "tests" / "analytics" / "fixtures" / "portfolio_simulation_result.json"
    )
    return json.loads(path.read_text(encoding="utf-8"))


def test_simulation_result_fixture_matches_documented_schema() -> None:
    """Simulation closed trades match the exact Analytics receiver row."""
    logger.debug("Testing Simulation result fixture parity")
    fixture = _fixture()
    trades = fixture["closed_trades"]
    assert isinstance(trades, list)
    assert set(trades[0]) == _TRADE_FIELDS
    simulator_readme = (_ROOT / "app/services/simulator/README.md").read_text(
        encoding="utf-8"
    )
    assert "FR-SIM-040" in simulator_readme
    assert "closed_trades: tuple[ClosedTradeRecord, ...]" in simulator_readme


def test_portfolio_simulation_result_fixture_matches_documented_schema() -> None:
    """The Simulation portfolio schema is frozen before allocation integration."""
    logger.debug("Testing portfolio Simulation schema parity")
    fixture = _portfolio_fixture()
    components = fixture["component_results"]
    returns = fixture["component_return_series"]
    assert set(fixture) == _PORTFOLIO_FIELDS
    assert isinstance(components, list)
    assert isinstance(returns, list)
    assert all(set(component) == _COMPONENT_FIELDS for component in components)
    assert all(set(row) == _RETURN_FIELDS for row in returns)
    assert all(
        set(observation) == _OBSERVATION_FIELDS
        for row in returns
        for observation in row["observations"]
    )
    simulator_readme = (_ROOT / "app/services/simulator/README.md").read_text(
        encoding="utf-8"
    )
    assert "FR-SIM-033" in simulator_readme
    assert "simulation.portfolio_result.v1" in simulator_readme
    assert "component_results: tuple[Mapping[str, object], ...]" in simulator_readme
    assert (
        "component_return_series: tuple[Mapping[str, object], ...]" in simulator_readme
    )
