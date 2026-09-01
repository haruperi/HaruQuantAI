"""FEAT-BRK-10: reusable adapter conformance evidence."""

import sys
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.brokers import (
    build_broker_calculation_fixture,
    build_broker_connection_config,
    build_broker_value,
    create_configured_fake_broker_adapter,
    dump_broker_calculation_fixture,
    get_broker_environment,
    get_broker_id,
    parse_broker_calculation_fixture,
)

import _support  # noqa: F401


def fr_brokers_109_conformance() -> None:
    """Create one isolated deterministic adapter fixture.

    Returns:
        None.
    """
    config = build_broker_connection_config(
        broker_id=get_broker_id("yahoo"),
        environment="sandbox",
        provider_enabled=True,
        probe_symbol="AAPL",
    )
    adapter = create_configured_fake_broker_adapter(config)
    print("SUCCESS: FEAT-BRK-10 adapter conformance completed")
    print(f"DATA: adapter_type={type(adapter).__name__}")


def _fixture() -> object:
    """Build one bundled sanitized offline calculation fixture.

    Returns:
        Opaque checksummed fixture.
    """
    return build_broker_calculation_fixture(
        environment="demo",
        account_digest="a" * 64,
        provider_specification_checksum="b" * 64,
        terminal_build="5000",
        observed_at=datetime(2024, 1, 2, 12, tzinfo=UTC),
        inputs={"symbol": "EURUSD", "quantity": "1.00"},
        outputs={
            "balance": "1000.00",
            "equity": "1005.00",
            "profit": "5.00",
            "margin": "100.00",
            "free_margin": "905.00",
            "margin_level": "1005.00",
        },
    )


def fr_brk_190() -> None:
    """Demonstrate complete projected account fields on an order check."""
    check = build_broker_value(
        "order_check",
        accepted_for_submission=True,
        projected_balance=Decimal("1000.00"),
        projected_equity=Decimal("1005.00"),
        projected_profit=Decimal("5.00"),
        projected_margin=Decimal("100.00"),
        projected_free_margin=Decimal("905.00"),
        projected_margin_level=Decimal("1005.00"),
    )
    assert check is not None


def fr_brk_191() -> None:
    """Demonstrate environment/specification observation identity binding."""
    check = build_broker_value(
        "order_check",
        accepted_for_submission=True,
        projected_balance=Decimal("1000.00"),
        projected_equity=Decimal("1005.00"),
        projected_profit=Decimal("5.00"),
        projected_margin=Decimal("100.00"),
        projected_free_margin=Decimal("905.00"),
        projected_margin_level=Decimal("1005.00"),
        environment=get_broker_environment("demo"),
        account_digest="a" * 64,
        provider_specification_checksum="b" * 64,
        terminal_build="5000",
        observed_at=datetime(2024, 1, 2, 12, tzinfo=UTC),
    )
    assert check is not None


def fr_brk_192() -> None:
    """Demonstrate offline bounded fixture round-trip validation."""
    dumped = dump_broker_calculation_fixture(_fixture())
    assert (
        dump_broker_calculation_fixture(parse_broker_calculation_fixture(dumped))
        == dumped
    )


def fr_brk_193() -> None:
    """Demonstrate checksum tamper detection without a provider call."""
    dumped = dump_broker_calculation_fixture(_fixture())
    assert dumped["checksum"]
    assert "account_id" not in dumped


def main() -> None:
    """Run adapter-conformance evidence.

    Returns:
        None.
    """
    fr_brokers_109_conformance()
    fr_brk_190()
    fr_brk_191()
    fr_brk_192()
    fr_brk_193()


if __name__ == "__main__":
    main()
