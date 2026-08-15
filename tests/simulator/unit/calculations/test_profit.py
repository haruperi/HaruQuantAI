"""Effective-dated FX profit tests."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.services.data import build_fx_conversion_evidence, build_fx_rate_leg
from app.services.simulator import calculate_fx_profit, unwrap_simulation_response

NOW = datetime(2024, 1, 2, 12, tzinfo=UTC)


def revision(**overrides: object) -> dict[str, object]:
    """Return one complete Data-shaped provider revision."""
    payload: dict[str, object] = {
        "calculation_mode": "FOREX",
        "contract_size": "100000",
        "point": "0.00001",
        "tick_size": "0.00001",
        "tick_value": "1",
        "base_currency": "EUR",
        "profit_currency": "USD",
        "margin_currency": "USD",
        "leverage": "100",
        "margin_initial": None,
        "margin_maintenance": None,
        "margin_hedged": "500",
        "margin_hedged_use_leg": False,
        "account_currency": "USD",
        "currency_digits": 2,
        "rounding_rule": "ROUND_HALF_EVEN",
    }
    payload.update(overrides)
    return {
        "complete_coverage": True,
        "revision_id": "revision-1",
        "snapshot_checksum": "a" * 64,
        "effective_from": NOW.isoformat(),
        "effective_to": (NOW + timedelta(days=1)).isoformat(),
        "payload": payload,
    }


def evidence(source: str, target: str, rate: str) -> object:
    """Return one exact Data-owned direct conversion evidence."""
    leg = build_fx_rate_leg(
        source_currency=source,
        target_currency=target,
        rate=Decimal(rate),
        source_id="fixture-rate",
        provider_symbol=source + target,
        as_of=NOW,
        provenance={"kind": "test"},
    )
    return build_fx_conversion_evidence(
        source_currency=source,
        target_currency=target,
        legs=(leg,),
        composite_rate=Decimal(rate),
        as_of=NOW,
        expires_at=NOW + timedelta(hours=1),
        path_policy_id="direct-only",
        path_policy_version="v1",
        provenance={"kind": "test"},
        request_id="req-11111111-1111-4111-8111-111111111111",
    )


def calculate(side: str, close: str, spec: dict[str, object] | None = None) -> Decimal:
    """Return one unwrapped exact profit result."""
    return unwrap_simulation_response(
        calculate_fx_profit(
            spec or revision(),
            side=side,
            volume=Decimal(1),
            open_price=Decimal("1.1000"),
            close_price=Decimal(close),
            as_of=NOW,
            fx_evidence=None,
        ),
        operation="test.calculate_fx_profit",
    )


def test_profit_handles_each_side_with_contract_size_not_tick_value() -> None:
    """FOREX P/L uses price delta, contract size, volume, and side."""
    assert calculate("BUY", "1.1010") == Decimal("100.00")
    assert calculate("SELL", "1.0990") == Decimal("100.00")


def test_profit_converts_profit_currency_with_data_evidence() -> None:
    """Profit conversion uses only the supplied Data-owned composite path."""
    spec = revision(profit_currency="EUR", account_currency="USD")
    result = unwrap_simulation_response(
        calculate_fx_profit(
            spec,
            side="BUY",
            volume=Decimal(1),
            open_price=Decimal("1.1000"),
            close_price=Decimal("1.1010"),
            as_of=NOW,
            fx_evidence=evidence("EUR", "USD", "1.2"),
        ),
        operation="test.converted_profit",
    )
    assert result == Decimal("120.00")
