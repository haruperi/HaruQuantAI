"""FEAT-BRK-18: Provider specification snapshots."""

import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import NamedTuple

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.brokers import (
    build_provider_specification_snapshot,
    dump_provider_specification_snapshot,
    get_provider_specification_snapshot_field,
    parse_provider_specification_snapshot,
    verify_provider_specification_snapshot,
)


class _SI(NamedTuple):
    name: object
    digits: object
    point: object
    filling_mode: object
    order_mode: object
    expiration_mode: object
    order_gtc_mode: object
    trade_exemode: object
    trade_mode: object
    trade_calc_mode: object
    swap_mode: object
    swap_rollover3days: object
    trade_stops_level: object
    trade_freeze_level: object
    volume_min: object
    volume_max: object
    volume_step: object
    volume_limit: object
    trade_tick_size: object
    trade_tick_value: object
    trade_tick_value_profit: object
    trade_tick_value_loss: object
    trade_contract_size: object
    currency_base: object
    currency_profit: object
    currency_margin: object
    margin_initial: object
    margin_maintenance: object
    margin_hedged: object
    margin_hedged_use_leg: object
    swap_long: object
    swap_short: object


class _Account(NamedTuple):
    login: object
    margin_mode: object


def _symbol_info() -> _SI:
    """Return one bounded sanitized MT5-shaped symbol observation."""
    return _SI(
        name="EURUSD",
        digits=5,
        point=0.00001,
        filling_mode=3,
        order_mode=127,
        expiration_mode=7,
        order_gtc_mode=0,
        trade_exemode=2,
        trade_mode=4,
        trade_calc_mode=0,
        swap_mode=1,
        swap_rollover3days=3,
        trade_stops_level=10,
        trade_freeze_level=5,
        volume_min=0.01,
        volume_max=500.0,
        volume_step=0.01,
        volume_limit=300.0,
        trade_tick_size=0.00001,
        trade_tick_value=1.0,
        trade_tick_value_profit=1.0,
        trade_tick_value_loss=1.0,
        trade_contract_size=100000.0,
        currency_base="EUR",
        currency_profit="USD",
        currency_margin="USD",
        margin_initial=0.0,
        margin_maintenance=0.0,
        margin_hedged=100000.0,
        margin_hedged_use_leg=False,
        swap_long=-0.2,
        swap_short=-1.2,
    )


def _snapshot() -> object:
    """Build one canonical snapshot from the bounded fixture."""
    return build_provider_specification_snapshot(
        symbol_info=_symbol_info(),
        broker="mt5",
        server="Demo-Server",
        account_id="12345",
        environment="demo",
        terminal_build="4570",
        source_revision="mt5:4570",
        observed_at=datetime(2026, 8, 20, 12, 0, 0, tzinfo=UTC),
        retrieval_provenance="metatrader.symbol_info+account_info+terminal_info",
        account_info=_Account(12345, 2),
        cost_evidence_id="cost-evidence/demo/4570/EURUSD",
        cost_evidence_checksum="a" * 64,
    )


def fr_brokers_159() -> None:
    """FR-BRK-159: typed current snapshot covering every admitted mode block."""
    dumped = dump_provider_specification_snapshot(_snapshot())
    assert dumped["filling_modes"] == ["FOK", "IOC"]
    assert dumped["calculation_mode"] == "FOREX"
    assert dumped["swap_mode"] == "POINTS"
    assert dumped["execution_mode"] == "MARKET"
    print("SUCCESS: FR-BRK-159 typed snapshot built with all mode blocks")


def fr_brokers_160() -> None:
    """FR-BRK-160: source and observation identity bound with checksum."""
    snapshot = _snapshot()
    dumped = dump_provider_specification_snapshot(snapshot)
    assert dumped["terminal_build"] == "4570"
    assert len(dumped["account_digest"]) == 64
    assert "12345" not in str(dumped)
    assert verify_provider_specification_snapshot(snapshot) is True
    print("SUCCESS: FR-BRK-160 identity, provenance, and checksum bound")


def fr_brokers_161() -> None:
    """FR-BRK-161: missing required fields fail closed at build time."""
    incomplete = _symbol_info()._replace(trade_calc_mode=None)
    message = ""
    try:
        build_provider_specification_snapshot(
            symbol_info=incomplete,
            broker="mt5",
            server="Demo-Server",
            account_id="12345",
            environment="demo",
            terminal_build="4570",
            source_revision="mt5:4570",
            observed_at=datetime(2026, 8, 20, tzinfo=UTC),
        )
    except ValueError as error:
        message = str(error)
    assert "trade_calc_mode" in message
    print("SUCCESS: FR-BRK-161 missing field rejected:", message[:58])


def fr_brokers_162() -> None:
    """FR-BRK-162: dynamic cost evidence is a separate typed reference."""
    dumped = dump_provider_specification_snapshot(_snapshot())
    block = dumped["cost_evidence"]
    assert isinstance(block, dict)
    assert block["evidence_id"] == "cost-evidence/demo/4570/EURUSD"
    assert "commission" not in dumped
    print("SUCCESS: FR-BRK-162 cost evidence kept separate and typed")


def fr_brokers_163() -> None:
    """FR-BRK-163: snapshots are current observation only."""
    dumped = dump_provider_specification_snapshot(_snapshot())
    assert "effective_from" not in dumped
    parsed = parse_provider_specification_snapshot(dumped)
    assert verify_provider_specification_snapshot(parsed) is True
    assert get_provider_specification_snapshot_field(parsed, "environment") == "demo"
    print("SUCCESS: FR-BRK-163 current-only snapshot parsed and verified")


def main() -> None:
    """Run every FEAT-BRK-18 usage function."""
    print("FEATURE: FEAT-BRK-18 — Provider Specification Snapshots")
    fr_brokers_159()
    fr_brokers_160()
    fr_brokers_161()
    fr_brokers_162()
    fr_brokers_163()


if __name__ == "__main__":
    main()
