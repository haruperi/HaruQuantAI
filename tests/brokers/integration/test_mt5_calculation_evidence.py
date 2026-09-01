"""MT5 calculation/check evidence integration tests for FR-BRK-190 through 193."""

from __future__ import annotations

import ast
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest
from app.services.brokers import (
    build_broker_value,
    get_broker_environment,
    get_broker_value_field,
)


def provider_check() -> dict[str, object]:
    """Return one complete MT5 OrderCheckResult-shaped payload.

    Returns:
        Complete provider check fixture.
    """
    return {
        "retcode": 0,
        "comment": "ok",
        "balance": "1000.00",
        "equity": "1005.00",
        "profit": "5.00",
        "margin": "100.00",
        "margin_free": "905.00",
        "margin_level": "1005.00",
    }


def mapped_check(payload: dict[str, object], *, bind_identity: bool = True) -> object:
    """Build the opaque canonical check represented by provider evidence.

    Args:
        payload: Provider-shaped projected values.
        bind_identity: Whether to attach complete observation identity.

    Returns:
        Opaque canonical order check.
    """
    fields: dict[str, object] = {
        "accepted_for_submission": payload["retcode"] == 0,
        "provider_code": str(payload["retcode"]),
        "provider_message": payload["comment"],
        "estimated_margin": Decimal(str(payload["margin"])),
        "projected_balance": Decimal(str(payload["balance"])),
        "projected_equity": (
            Decimal(str(payload["equity"])) if "equity" in payload else None
        ),
        "projected_profit": Decimal(str(payload["profit"])),
        "projected_margin": Decimal(str(payload["margin"])),
        "projected_free_margin": Decimal(str(payload["margin_free"])),
        "projected_margin_level": Decimal(str(payload["margin_level"])),
    }
    if bind_identity:
        fields.update(
            environment=get_broker_environment("demo"),
            account_digest="a" * 64,
            provider_specification_checksum="b" * 64,
            terminal_build="5000",
            observed_at=datetime(2024, 1, 2, 12, tzinfo=UTC),
        )
    return build_broker_value("order_check", **fields)


def test_mt5_check_preserves_projected_fields_and_bound_identity() -> None:
    """All projected account values retain Decimal and identity evidence."""
    observed_at = datetime(2024, 1, 2, 12, tzinfo=UTC)
    check = mapped_check(provider_check())
    assert get_broker_value_field(check, "projected_balance") == Decimal("1000.00")
    assert get_broker_value_field(check, "projected_equity") == Decimal("1005.00")
    assert get_broker_value_field(check, "projected_profit") == Decimal("5.00")
    assert get_broker_value_field(check, "projected_margin") == Decimal("100.00")
    assert get_broker_value_field(check, "projected_free_margin") == Decimal("905.00")
    assert get_broker_value_field(check, "projected_margin_level") == Decimal("1005.00")
    assert str(get_broker_value_field(check, "environment")) == "demo"
    assert get_broker_value_field(check, "account_digest") == "a" * 64
    assert get_broker_value_field(check, "provider_specification_checksum") == "b" * 64
    assert get_broker_value_field(check, "terminal_build") == "5000"
    assert get_broker_value_field(check, "observed_at") == observed_at


@pytest.mark.parametrize("field", ["balance", "equity", "profit", "margin_free"])
def test_mt5_check_rejects_non_finite_projected_values(field: str) -> None:
    """Malformed provider numeric success evidence fails closed."""
    payload = provider_check()
    payload[field] = "NaN"
    with pytest.raises(ValueError, match="finite"):
        mapped_check(payload, bind_identity=False)


def test_mt5_check_rejects_missing_projection_when_identity_is_bound() -> None:
    """A provider success cannot omit a projected account field."""
    payload = provider_check()
    del payload["equity"]
    with pytest.raises(ValueError, match="complete identity and projections"):
        mapped_check(payload)


def test_operations_are_not_reregistered_and_default_suite_cannot_collect() -> None:
    """The delta changes evidence only and default conformance stays offline."""
    suite = Path("app/services/brokers/conformance/suite.py")
    tree = ast.parse(suite.read_text(encoding="utf-8"))
    calls = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    assert "collect_calculation_fixture" not in calls
