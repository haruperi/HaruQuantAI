"""Unit evidence for independent Trading order-policy v2 contracts."""

# ruff: noqa: INP001

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from app.services.trading import (
    create_legacy_compatible_trading_request,
    create_order_intent_v2,
    create_trading_request_v2,
)
from pydantic import ValidationError

NOW = datetime(2026, 8, 15, tzinfo=UTC)
CHECKSUM = "a" * 64


@pytest.fixture(autouse=True)
def _provider_snapshot(monkeypatch: pytest.MonkeyPatch) -> None:
    """Expose deterministic opaque provider fields through the public getter."""

    def get_field(_snapshot: object, field: str) -> object:
        return {
            "filling_modes": ("FOK", "IOC", "RETURN"),
            "expiration_modes": ("GTC", "DAY", "SPECIFIED", "SPECIFIED_DAY"),
            "checksum": CHECKSUM,
        }[field]

    monkeypatch.setattr(
        "app.services.brokers.get_provider_specification_snapshot_field", get_field
    )


def _request_values() -> dict[str, object]:
    """Return complete v2 request material."""
    return {
        "request_id": "req-11111111-1111-4111-8111-111111111111",
        "workflow_id": "wf-22222222-2222-4222-8222-222222222222",
        "correlation_id": "cor-33333333-3333-4333-8333-333333333333",
        "route": "sim",
        "action": "submit_order",
        "account_id": "account-001",
        "strategy_id": "strategy-001",
        "strategy_version": "v1",
        "intent_id": "intent-001",
        "symbol": "EURUSD",
        "side": "BUY",
        "order_type": "MARKET",
        "quantity_unit": "units",
        "quantity": Decimal(1),
        "risk_decision_id": "risk-001",
        "action_policy_verdict_id": "verdict-001",
        "approval_token_ref": "approval-001",
        "idempotency_key": "key-001",
        "canonical_material_version": "v2",
        "system_time": NOW,
        "valid_until": NOW + timedelta(minutes=5),
    }


@pytest.mark.parametrize("fill_policy", ["FOK", "IOC", "RETURN", "BOC"])
@pytest.mark.parametrize("time_policy", ["GTC", "DAY", "SPECIFIED", "SPECIFIED_DAY"])
def test_fr_trd_097_098_policy_cartesian_product(
    fill_policy: str, time_policy: str
) -> None:
    """FR-TRD-097/098: every explicit pair is validated against the snapshot."""
    values = _request_values()
    if time_policy.startswith("SPECIFIED"):
        values["expiration"] = NOW + timedelta(days=1)
    if fill_policy == "BOC":
        with pytest.raises(ValueError, match="fill_policy is unsupported"):
            create_trading_request_v2(
                provider_specification=object(),
                fill_policy=fill_policy,
                time_policy=time_policy,
                **values,
            )
        return
    request = create_trading_request_v2(
        provider_specification=object(),
        fill_policy=fill_policy,
        time_policy=time_policy,
        **values,
    )
    assert (request.fill_policy, request.time_policy) == (fill_policy, time_policy)
    assert request.provider_specification_checksum == CHECKSUM


@pytest.mark.parametrize(
    ("time_policy", "expiration"),
    [
        ("SPECIFIED", None),
        ("SPECIFIED_DAY", None),
        ("GTC", NOW + timedelta(days=1)),
        ("DAY", NOW + timedelta(days=1)),
        ("SPECIFIED", datetime(2026, 8, 16)),  # noqa: DTZ001 - invalid fixture.
    ],
)
def test_fr_trd_099_expiration_shape_fails_closed(
    time_policy: str, expiration: datetime | None
) -> None:
    """FR-TRD-099: missing, contradictory, and naive expiry is rejected."""
    with pytest.raises(ValidationError):
        create_trading_request_v2(
            provider_specification=object(),
            fill_policy="FOK",
            time_policy=time_policy,
            expiration=expiration,
            **_request_values(),
        )


def test_fr_trd_100_v2_is_immutable_and_legacy_is_labelled() -> None:
    """FR-TRD-100: v2 is immutable and explicit legacy decoding is excluded."""
    request = create_trading_request_v2(
        provider_specification=object(),
        fill_policy="FOK",
        time_policy="GTC",
        **_request_values(),
    )
    with pytest.raises(ValidationError):
        request.fill_policy = "IOC"
    legacy = create_legacy_compatible_trading_request(
        legacy_profile_version="trading-order-policy-legacy-v1",
        provider_specification=object(),
        **_request_values(),
    )
    assert legacy.legacy_compatibility is True
    assert legacy.canonical_parity_eligible is False
    with pytest.raises(ValueError, match="unknown legacy"):
        create_legacy_compatible_trading_request(
            legacy_profile_version="missing",
            provider_specification=object(),
            **_request_values(),
        )


def test_fr_trd_112_order_intent_preserves_both_policies() -> None:
    """FR-TRD-112: executable intent independently preserves both policies."""
    values = _request_values()
    intent = create_order_intent_v2(
        provider_specification=object(),
        fill_policy="IOC",
        time_policy="SPECIFIED_DAY",
        expiration=NOW + timedelta(days=1),
        client_order_id="trd-001",
        request_id=values["request_id"],
        workflow_id=values["workflow_id"],
        correlation_id=values["correlation_id"],
        route="sim",
        provider_id=None,
        account_id=values["account_id"],
        strategy_id=values["strategy_id"],
        strategy_version="v1",
        source_intent_id="intent-001",
        symbol="EURUSD",
        action="submit_order",
        side="BUY",
        order_type="MARKET",
        quantity_unit="units",
        approved_volume=Decimal(1),
        risk_approved_volume=Decimal(1),
        idempotency_hash="b" * 64,
        canonical_material_version="v2",
        risk_decision_id="risk-001",
        action_policy_verdict_id="verdict-001",
        approval_token_ref="approval-001",
        created_at=NOW,
        valid_until=NOW + timedelta(days=2),
    )
    assert (intent.fill_policy, intent.time_policy) == ("IOC", "SPECIFIED_DAY")
