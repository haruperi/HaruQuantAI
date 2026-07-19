"""Producer/consumer compatibility tests for Simulation-owned v1 contracts.

`docs/PROJECT.md` §5 registers `SimulationBacktestRequestV1`, `SimulationResult`,
`PortfolioBacktestRequestV1`, and `PortfolioSimulationResult` as Simulation-owned.
These tests prove the published shapes match what the registered consumers read,
rather than asserting parity in a comment.
"""
# ruff: noqa: INP001

import dataclasses
from decimal import Decimal

from app.services.analytics.contracts.models import ClosedTrade
from app.services.simulator.reporting import (
    ClosedTradeRecord,
    PortfolioSimulationResult,
    SimulationResult,
)
from app.services.simulator.run import (
    PortfolioBacktestRequestV1,
    SimulationBacktestRequestV1,
)
from app.utils import logger
from tests.simulator.unit.test_reporting_contracts import _result


def test_closed_trade_record_matches_analytics_ledger_schema() -> None:
    """Prove `FR-SIM-040` parity with the Analytics `FR-ANLT-049` field set."""
    logger.info("Testing Simulation/Analytics closed-trade contract parity")
    producer = set(ClosedTradeRecord.model_fields)
    consumer = {field.name for field in dataclasses.fields(ClosedTrade)}
    assert producer == consumer


def test_closed_trade_record_is_directly_consumable_by_analytics() -> None:
    """Construct the Analytics record straight from the Simulation projection."""
    logger.info("Testing Simulation closed-trade consumption by Analytics")
    record = _result().closed_trades[0]
    consumed = ClosedTrade(**record.model_dump(mode="python", warnings=False))
    assert consumed.ticket == record.ticket
    assert consumed.profit == record.profit
    assert consumed.mae == record.mae
    assert consumed.mfe == record.mfe


def test_closed_trade_profit_excludes_costs_for_both_domains() -> None:
    """Prove both sides treat `profit` as gross and costs as non-positive."""
    logger.info("Testing gross-profit convention across the Analytics seam")
    record = _result().closed_trades[0]
    assert record.commission <= Decimal(0)
    assert record.swap <= Decimal(0)
    consumed = ClosedTrade(**record.model_dump(mode="python", warnings=False))
    assert consumed.profit == record.profit


def test_owned_contracts_expose_separate_version_and_schema_identity() -> None:
    """Prove compatibility is evaluated from `contract_version` alone."""
    logger.info("Testing Simulation contract version and schema identity")
    for contract, schema_id in (
        (SimulationBacktestRequestV1, "simulation.backtest_request.v1"),
        (SimulationResult, "simulation.result.v1"),
        (PortfolioBacktestRequestV1, "simulation.portfolio_backtest_request.v1"),
        (PortfolioSimulationResult, "simulation.portfolio_result.v1"),
    ):
        fields = contract.model_fields
        assert "contract_version" in fields
        assert "schema_id" in fields
        assert fields["contract_version"].default == "v1"
        assert fields["schema_id"].default == schema_id


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
    assert required <= set(SimulationResult.model_fields)
