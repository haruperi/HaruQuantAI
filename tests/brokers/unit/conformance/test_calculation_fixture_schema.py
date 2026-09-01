"""Calculation fixture schema tests for FR-BRK-192 and FR-BRK-193."""

# ruff: noqa: INP001

from __future__ import annotations

import asyncio
from datetime import UTC, datetime

import pytest
from tests.brokers.conformance import (
    build_broker_calculation_fixture,
    collect_broker_calculation_fixture,
    dump_broker_calculation_fixture,
    parse_broker_calculation_fixture,
)

NOW = datetime(2024, 1, 2, 12, tzinfo=UTC)
OUTPUTS = {
    "balance": "1000.00",
    "equity": "1005.00",
    "profit": "5.00",
    "margin": "100.00",
    "free_margin": "905.00",
    "margin_level": "1005.00",
}


def fixture_fields() -> dict[str, object]:
    """Return complete sanitized fixture fields.

    Returns:
        Valid fixture field mapping.
    """
    return {
        "environment": "demo",
        "account_digest": "a" * 64,
        "provider_specification_checksum": "b" * 64,
        "terminal_build": "5000",
        "observed_at": NOW,
        "inputs": {"symbol": "EURUSD", "quantity": "1.00"},
        "outputs": OUTPUTS,
    }


def test_fixture_round_trip_is_json_safe_immutable_and_checksummed() -> None:
    """Canonical dump/parse preserves one bounded sanitized artifact."""
    fixture = build_broker_calculation_fixture(**fixture_fields())
    dumped = dump_broker_calculation_fixture(fixture)
    assert dumped["schema_id"] == "brokers.calculation_fixture.v1"
    assert dumped["checksum"]
    assert (
        dump_broker_calculation_fixture(parse_broker_calculation_fixture(dumped))
        == dumped
    )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("account_digest", "raw-account"),
        ("provider_specification_checksum", "short"),
        ("observed_at", datetime.fromisoformat("2024-01-02T12:00:00")),
        ("outputs", {**OUTPUTS, "profit": float("nan")}),
        ("inputs", {"api_token": "secret"}),
    ],
)
def test_fixture_rejects_missing_float_nan_secret_or_identity_tamper(
    field: str, value: object
) -> None:
    """Invalid, non-JSON-safe, or sensitive evidence fails closed."""
    fields = fixture_fields()
    fields[field] = value
    with pytest.raises((TypeError, ValueError)):
        build_broker_calculation_fixture(**fields)


def test_fixture_rejects_missing_projected_field_and_checksum_tamper() -> None:
    """Complete projected outputs and exact checksum are mandatory."""
    fields = fixture_fields()
    fields["outputs"] = {
        key: value for key, value in OUTPUTS.items() if key != "equity"
    }
    with pytest.raises(ValueError, match="omit projected"):
        build_broker_calculation_fixture(**fields)
    dumped = dump_broker_calculation_fixture(
        build_broker_calculation_fixture(**fixture_fields())
    )
    dumped["terminal_build"] = "tampered"
    with pytest.raises(ValueError, match="checksum mismatch"):
        parse_broker_calculation_fixture(dumped)


def test_collection_is_dev_demo_only_and_digests_raw_account() -> None:
    """Collection blocks every unsafe route and emits no raw account identity."""

    async def exercise() -> None:
        calls = 0

        async def provider_call() -> dict[str, object]:
            nonlocal calls
            calls += 1
            return dict(OUTPUTS)

        common = {
            "account_id": "12345678",
            "provider_specification_checksum": "b" * 64,
            "terminal_build": "5000",
            "observed_at": NOW,
            "inputs": {"symbol": "EURUSD"},
            "provider_call": provider_call,
        }
        with pytest.raises(PermissionError):
            await collect_broker_calculation_fixture(
                app_environment="prod", broker_environment="demo", **common
            )
        with pytest.raises(PermissionError):
            await collect_broker_calculation_fixture(
                app_environment="dev", broker_environment="live", **common
            )
        assert calls == 0
        fixture = await collect_broker_calculation_fixture(
            app_environment="dev", broker_environment="demo", **common
        )
        dumped = dump_broker_calculation_fixture(fixture)
        assert calls == 1
        assert dumped["account_digest"] != "12345678"
        assert "12345678" not in str(dumped)

    asyncio.run(exercise())
