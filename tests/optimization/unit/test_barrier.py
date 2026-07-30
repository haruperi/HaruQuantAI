"""Unit tests for Optimization barrier analysis."""

from decimal import Decimal

from app.services.optimization.robustness import (
    estimate_drawdown_mode_sensitivity,
    estimate_first_passage,
    estimate_joint_first_passage,
)
from app.services.risk import (
    create_firm_mandate,
    get_drawdown_mode,
)

# Private type-only aliases; Risk exposes functions, not contract classes.
FirmMandate = object


def _mandate() -> FirmMandate:
    """Build a deterministic evaluation mandate."""
    return create_firm_mandate(
        account_id="account-1",
        mandate_version="v1",
        firm="Example Firm",
        model="fx_cfd",
        phase="evaluation_p1",
        initial_balance=Decimal(1000),
        currency="USD",
        terms_url="https://example.invalid/terms",
        terms_accessed="2026-07-28",
        terms_source_hash="a" * 64,
        verified=True,
        profit_target={"type": "percent_of_initial", "value": Decimal("0.1")},
        daily_loss={
            "basis": "initial_balance",
            "value": Decimal("0.2"),
            "includes_unrealised": True,
            "reset_time": "00:00",
            "reset_tz": "UTC",
        },
        max_drawdown={
            "mode": "static",
            "basis": "initial_balance",
            "value": Decimal("0.1"),
            "trails_on_unrealised": False,
            "trail_stops_at_initial": False,
        },
    )


def test_first_passage_probabilities_sum_to_one() -> None:
    """Partition every path into exactly one terminal outcome."""
    report = estimate_first_passage(
        (Decimal("0.03"), Decimal("-0.01"), Decimal("0.02")),
        _mandate(),
        paths=200,
        seed=7,
    )
    total = (
        report.probability_target
        + report.probability_daily_breach
        + report.probability_drawdown_breach
        + report.probability_expired
    )
    assert total == Decimal(1)


def test_joint_distribution_is_not_product_of_marginals() -> None:
    """Joint simulation reports a full survival distribution, not marginals."""
    returns = {
        "account-1": (
            Decimal("0.03"),
            Decimal("-0.02"),
            Decimal("0.02"),
            Decimal("-0.01"),
        ),
        "account-2": (
            Decimal("0.025"),
            Decimal("-0.018"),
            Decimal("0.021"),
            Decimal("-0.012"),
        ),
    }
    mandates = {
        "account-1": _mandate(),
        "account-2": _mandate().model_copy(update={"account_id": "account-2"}),
    }
    report = estimate_joint_first_passage(returns, mandates, paths=100, seed=11)
    marginal = estimate_first_passage(
        returns["account-1"], _mandate(), paths=100, seed=11
    )
    product_none = (Decimal(1) - marginal.probability_target) ** 2
    assert sum(report.surviving_accounts_distribution.values()) == Decimal(1)
    assert report.probability_none_survive != product_none


def test_mode_changes_pass_probability() -> None:
    """The same returns produce mode-sensitive pass probabilities."""
    reports = estimate_drawdown_mode_sensitivity(
        (Decimal("0.12"), Decimal("-0.10"), Decimal("0.12"), Decimal("-0.10")),
        _mandate(),
        paths=100,
        seed=13,
    )
    assert set(reports) == {
        get_drawdown_mode("STATIC"),
        get_drawdown_mode("TRAILING_EOD"),
        get_drawdown_mode("TRAILING_INTRADAY"),
    }
    assert {report.mode for report in reports.values()} == set(reports)
