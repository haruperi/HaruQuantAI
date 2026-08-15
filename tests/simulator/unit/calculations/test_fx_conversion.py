"""Evidence-bound FX conversion tests."""

from datetime import timedelta
from decimal import Decimal

from app.services.data import build_fx_conversion_evidence, build_fx_rate_leg
from app.services.simulator import convert_account_currency, unwrap_simulation_response

from tests.simulator.unit.calculations.test_profit import NOW, evidence


def convert(evidence_value: object) -> Decimal:
    """Return one unwrapped account-currency conversion."""
    return unwrap_simulation_response(
        convert_account_currency(
            amount=Decimal(10),
            source_currency="EUR",
            target_currency="JPY",
            as_of=NOW,
            currency_digits=2,
            rounding_rule="ROUND_HALF_EVEN",
            evidence=evidence_value,
        ),
        operation="test.convert_account_currency",
    )


def test_direct_and_evidenced_two_leg_conversion_are_exact() -> None:
    """Direct/inverse semantics and triangulation come only from Data legs."""
    direct = evidence("EUR", "JPY", "160")
    assert convert(direct) == Decimal("1600.00")
    first = build_fx_rate_leg(
        source_currency="EUR",
        target_currency="USD",
        rate=Decimal("1.2"),
        source_id="one",
        provider_symbol="EURUSD",
        as_of=NOW,
        provenance={"kind": "test"},
    )
    second = build_fx_rate_leg(
        source_currency="USD",
        target_currency="JPY",
        rate=Decimal(150),
        source_id="two",
        provider_symbol="USDJPY",
        as_of=NOW,
        provenance={"kind": "test"},
    )
    two_leg = build_fx_conversion_evidence(
        source_currency="EUR",
        target_currency="JPY",
        legs=(first, second),
        composite_rate=Decimal(180),
        as_of=NOW,
        expires_at=NOW + timedelta(hours=1),
        path_policy_id="two-leg",
        path_policy_version="v1",
        provenance={"kind": "test"},
        request_id="req-22222222-2222-4222-8222-222222222222",
    )
    assert convert(two_leg) == Decimal("1800.00")


def test_missing_or_mismatched_conversion_fails_closed() -> None:
    """Simulation never synthesizes absent currency evidence."""
    response = convert_account_currency(
        amount=Decimal(10),
        source_currency="EUR",
        target_currency="JPY",
        as_of=NOW,
        currency_digits=2,
        rounding_rule="ROUND_HALF_EVEN",
        evidence=None,
    )
    assert response.data is None
    mismatch = evidence("EUR", "USD", "1.2")
    assert (
        convert_account_currency(
            amount=Decimal(10),
            source_currency="EUR",
            target_currency="JPY",
            as_of=NOW,
            currency_digits=2,
            rounding_rule="ROUND_HALF_EVEN",
            evidence=mismatch,
        ).data
        is None
    )
