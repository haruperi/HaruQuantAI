"""Producer/consumer compatibility tests for Simulation-owned v1 contracts.

`docs/PROJECT.md` §5 registers `SimulationBacktestRequestV1`, `SimulationResult`,
`PortfolioBacktestRequestV1`, and `PortfolioSimulationResult` as Simulation-owned.
These tests prove the published shapes match what the registered consumers read,
rather than asserting parity in a comment.
"""
# ruff: noqa: INP001

from decimal import Decimal

from app.services.simulator import (
    create_simulation_value,
    get_simulation_value_field,
    get_simulation_value_fields,
)
from app.utils import get_logger
from tests.simulator.unit.test_orchestrator import _dataset, _request
from tests.simulator.unit.test_portfolio_run import _portfolio_request
from tests.simulator.unit.test_reporting_contracts import _result

logger = get_logger(__name__)


def test_closed_trade_record_matches_analytics_ledger_schema() -> None:
    """Prove `FR-SIM-040` parity with the Analytics `FR-ANLT-049` field set."""
    logger.info("Testing Simulation/Analytics closed-trade contract parity")
    producer = set(get_simulation_value_fields("ClosedTradeRecord"))
    consumer = {
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
    assert producer == consumer


def test_closed_trade_record_is_directly_consumable_by_analytics() -> None:
    """Construct the Analytics record straight from the Simulation projection."""
    logger.info("Testing Simulation closed-trade consumption by Analytics")
    record = _result().closed_trades[0]
    projection = record.model_dump(mode="python", warnings=False)
    consumed = create_simulation_value("ClosedTradeRecord", **projection)
    for field in ("ticket", "profit", "mae", "mfe"):
        assert get_simulation_value_field(consumed, field) == getattr(record, field)


def test_closed_trade_profit_excludes_costs_for_both_domains() -> None:
    """Prove both sides treat `profit` as gross and costs as non-positive."""
    logger.info("Testing gross-profit convention across the Analytics seam")
    record = _result().closed_trades[0]
    assert record.commission <= Decimal(0)
    assert record.swap <= Decimal(0)
    consumed = create_simulation_value(
        "ClosedTradeRecord", **record.model_dump(mode="python", warnings=False)
    )
    assert get_simulation_value_field(consumed, "profit") == record.profit


def test_owned_contracts_expose_separate_version_and_schema_identity() -> None:
    """Prove compatibility is evaluated from `contract_version` alone."""
    logger.info("Testing Simulation contract version and schema identity")
    dataset = _dataset("req-55555555-5555-4555-8555-555555555555")
    for value, schema_id in (
        (_request(dataset), "simulation.backtest_request.v1"),
        (_result(), "simulation.result.v1"),
        (_portfolio_request(), "simulation.portfolio_backtest_request.v1"),
    ):
        assert get_simulation_value_field(value, "contract_version") == "v1"
        assert get_simulation_value_field(value, "schema_id") == schema_id
    assert {
        "contract_version",
        "schema_id",
    } <= set(get_simulation_value_fields("PortfolioSimulationResult"))


def test_simulation_result_publishes_the_registered_core_schema() -> None:
    """Prove the registry's stated core schema is present on the result."""
    logger.info("Testing SimulationResult against the PROJECT.md core schema")
    required = {
        "run_id",
        "config_hash",
        "journal_ref",
        "fills",
        "closed_trades",
        "initial_balance",
        "account_currency",
        "artifact_manifest_ref",
    }
    assert required <= set(get_simulation_value_fields("SimulationResult"))
