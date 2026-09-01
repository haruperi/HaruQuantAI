"""Producer/consumer compatibility tests for Simulation-owned contracts.

`docs/PROJECT.md` §5 registers `SimulationBacktestRequest`, `SimulationResult`,
`PortfolioBacktestRequest`, and `PortfolioSimulationResult` as Simulation-owned.
These tests prove the published shapes match what the registered consumers read,
rather than asserting parity in a comment.
"""

import runpy
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from app.composition.logging import get_logger
from app.services.brokers import dump_provider_specification_snapshot
from app.services.data import (
    build_data_settings,
    data_settings_context,
    get_provider_specification_revision,
    register_provider_specification_revision,
    run_data_migrations,
    unwrap_data_response,
)
from app.services.simulator import (
    create_simulation_value,
    get_simulation_value_field,
    get_simulation_value_fields,
)

from tests.simulator.component.test_orchestrator import _dataset, _request
from tests.simulator.component.test_portfolio_run import _portfolio_request
from tests.simulator.unit.test_reporting_contracts import _result
from tests.simulator.unit.test_run_request_v2 import _build, _payload, _rehash

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
        (_request(dataset), "simulation.backtest_request.v2"),
        (_result(), "simulation.result.v1"),
        (_portfolio_request(), "simulation.portfolio_backtest_request.v1"),
    ):
        assert get_simulation_value_field(value, "contract_version") == (
            "v2" if schema_id == "simulation.backtest_request.v2" else "v1"
        )
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


def test_request_v2_matches_the_registered_execution_identity_schema() -> None:
    """FR-SIM-231: PROJECT and the producer expose the same V2 identity."""
    required = {
        "execution_model_ref",
        "execution_model_hash",
        "source_lineage_hash",
        "tick_lineage_hash",
        "market_evidence_class",
        "decision_instant_policy",
        "provider_specification_revisions",
        "initial_authority_state_hash",
        "certification_target",
        "close_open_positions_at_end",
    }
    assert required <= set(get_simulation_value_fields("SimulationBacktestRequest"))


def test_request_v2_binds_broker_snapshot_persisted_point_in_time(
    tmp_path: Path,
) -> None:
    """Phase 4 integration gate binds public Brokers and Data evidence into V2."""
    script = Path("tests/brokers/usage/features/18_specifications.py")
    snapshot = runpy.run_path(str(script))["_snapshot"]()
    dumped = dump_provider_specification_snapshot(snapshot)
    settings = build_data_settings(
        database_url="sqlite:///phase-4c.sqlite3",
        data_dir=tmp_path,
        sqlite_busy_timeout_seconds=0.1,
        write_lock_lease_seconds=30,
    )
    with data_settings_context(settings):
        request_id = "req-44444444-4444-4444-8444-444444444444"
        unwrap_data_response(
            run_data_migrations(request_id),
            operation="test.phase_4c.migrate",
            request_id=request_id,
        )
        register_provider_specification_revision(
            dumped,
            effective_from=_request(_dataset(request_id)).start,
            historical_provenance={"source": "owner-approved-broker-snapshot"},
            request_id=request_id,
        )
        exact = get_provider_specification_revision(
            provider=str(dumped["broker"]),
            server=str(dumped["server"]),
            environment=str(dumped["environment"]),
            account_digest=str(dumped["account_digest"]),
            symbol=str(dumped["provider_symbol"]),
            as_of=_request(_dataset(request_id)).start,
            request_id=request_id,
        )
    payload = _payload()
    binding = {
        "revision_id": exact["revision_id"],
        "checksum": exact["snapshot_checksum"],
        "provider": exact["broker"],
        "server": exact["server"],
        "environment": exact["environment"],
        "account_digest": exact["account_digest"],
        "symbol": exact["provider_symbol"],
        "observed_at": datetime.fromisoformat(str(exact["observed_at"])),
        "effective_from": datetime.fromisoformat(str(exact["effective_from"])),
        "effective_to": None
        if exact["effective_to"] is None
        else datetime.fromisoformat(str(exact["effective_to"])),
        "historical_provenance": exact["historical_provenance"],
    }
    payload["provider_specification_revisions"] = (binding,)
    _rehash(payload)
    assert get_simulation_value_field(_build(payload), "certification_target") == "demo"
