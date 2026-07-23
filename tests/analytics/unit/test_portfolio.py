"""Unit tests for currency-safe Analytics portfolio composition."""

# ruff: noqa: INP001

from datetime import datetime, timedelta
from decimal import Decimal

import pytest
from app.services.analytics.contracts import AnalyticsValidationError
from app.services.analytics.reports.portfolio import build_portfolio_performance_report
from app.utils import logger
from tests.analytics._support import _report


def test_portfolio_builder_never_sums_mixed_currency_raw_pnl() -> None:
    """Mixed component currencies block when exact FX evidence is absent."""
    logger.debug("Testing Analytics mixed-currency portfolio blocker")
    usd, config = _report(account_currency="USD")
    eur, _ = _report(account_currency="EUR")
    with pytest.raises(AnalyticsValidationError, match="FX"):
        build_portfolio_performance_report(
            (usd, eur), base_currency="USD", fx_evidence=None, config=config
        )


def test_portfolio_builder_aggregates_actual_same_currency_pnl() -> None:
    """Same-currency component PnL is summed from actual report evidence."""
    logger.debug("Testing Analytics same-currency portfolio aggregation")
    first, config = _report()
    second, _ = _report(profit=10)
    portfolio = build_portfolio_performance_report(
        (first, second), base_currency="USD", fx_evidence=None, config=config
    )
    net = next(
        metric
        for metric in portfolio.sections[0].metrics
        if metric.metric_key == "net_pnl"
    )
    assert net.value == 18


def test_portfolio_builder_invalid_components_count() -> None:
    """Empty or excess components fail validation."""
    usd, config = _report(account_currency="USD")
    # Empty
    with pytest.raises(AnalyticsValidationError, match="component count is invalid"):
        build_portfolio_performance_report(
            (), base_currency="USD", fx_evidence=None, config=config
        )

    # Exceeds max components
    config.max_portfolio_components = 1
    with pytest.raises(AnalyticsValidationError, match="component count is invalid"):
        build_portfolio_performance_report(
            (usd, usd), base_currency="USD", fx_evidence=None, config=config
        )


def test_portfolio_builder_invalid_base_currency() -> None:
    """Empty or whitespace base currency fails validation."""
    usd, config = _report(account_currency="USD")
    with pytest.raises(AnalyticsValidationError, match="base currency is required"):
        build_portfolio_performance_report(
            (usd,), base_currency="", fx_evidence=None, config=config
        )
    with pytest.raises(AnalyticsValidationError, match="base currency is required"):
        build_portfolio_performance_report(
            (usd,), base_currency=" USD ", fx_evidence=None, config=config
        )


def test_portfolio_builder_incompatible_schema() -> None:
    """Incompatible contract version or schema ID fails validation."""
    usd, config = _report(account_currency="USD")
    bad_report = usd.model_copy(update={"contract_version": "v2"})
    with pytest.raises(AnalyticsValidationError, match="schema is incompatible"):
        build_portfolio_performance_report(
            (bad_report,), base_currency="USD", fx_evidence=None, config=config
        )

    bad_schema = usd.model_copy(update={"schema_id": "other.schema"})
    with pytest.raises(AnalyticsValidationError, match="schema is incompatible"):
        build_portfolio_performance_report(
            (bad_schema,), base_currency="USD", fx_evidence=None, config=config
        )


def test_portfolio_builder_mismatched_windows() -> None:
    """Mismatched measurement windows fail validation."""
    usd, config = _report(account_currency="USD")
    eur, _ = _report(account_currency="EUR")
    # Alter measurement window in eur
    bad_eur = eur.model_copy(
        update={
            "precision_metadata": {
                **eur.precision_metadata,
                "measurement_start": eur.precision_metadata["measurement_start"]
                + timedelta(days=1),
            }
        }
    )
    with pytest.raises(AnalyticsValidationError, match="windows do not match"):
        build_portfolio_performance_report(
            (usd, bad_eur), base_currency="USD", fx_evidence=None, config=config
        )


def test_portfolio_builder_invalid_measurement_windows() -> None:
    """Missing or invalid measurement windows fail validation."""
    usd, config = _report(account_currency="USD")

    # Missing
    bad_usd = usd.model_copy(update={"precision_metadata": {}})
    with pytest.raises(AnalyticsValidationError, match="window is missing"):
        build_portfolio_performance_report(
            (bad_usd,), base_currency="USD", fx_evidence=None, config=config
        )

    # Naive timestamp
    naive_dt = datetime(2026, 7, 19)
    bad_usd2 = usd.model_copy(
        update={
            "precision_metadata": {
                "measurement_start": naive_dt,
                "measurement_end": usd.precision_metadata["measurement_end"],
            }
        }
    )
    with pytest.raises(AnalyticsValidationError, match="window is invalid"):
        build_portfolio_performance_report(
            (bad_usd2,), base_currency="USD", fx_evidence=None, config=config
        )

    # End < Start
    bad_usd3 = usd.model_copy(
        update={
            "precision_metadata": {
                "measurement_start": usd.precision_metadata["measurement_end"],
                "measurement_end": usd.precision_metadata["measurement_start"],
            }
        }
    )
    with pytest.raises(AnalyticsValidationError, match="window is invalid"):
        build_portfolio_performance_report(
            (bad_usd3,), base_currency="USD", fx_evidence=None, config=config
        )


def test_portfolio_builder_invalid_fx_evidence_contracts() -> None:
    """Incompatible FX conversion evidence structure fails validation."""
    usd, config = _report(account_currency="USD")
    eur, _ = _report(account_currency="EUR")

    # Malformed keys
    bad_evidence = {
        "contract_version": "v1",
        "schema_id": "data.fx_conversion_evidence.v1",
        "source_currency": "EUR",
        "target_currency": "USD",
        # missing other fields
    }
    with pytest.raises(AnalyticsValidationError, match="evidence is missing"):
        build_portfolio_performance_report(
            (usd, eur), base_currency="USD", fx_evidence=bad_evidence, config=config
        )

    # Incompatible schema
    bad_schema = {
        "contract_version": "v2",
        "schema_id": "data.fx_conversion_evidence.v1",
        "source_currency": "EUR",
        "target_currency": "USD",
        "legs": (),
        "composite_rate": Decimal("1.1"),
        "as_of": eur.created_at,
        "expires_at": eur.created_at + timedelta(days=1),
        "path_policy_id": "policy-1",
        "path_policy_version": "v1",
        "provenance": "test",
        "request_id": "req-1",
    }
    with pytest.raises(AnalyticsValidationError, match="evidence is incompatible"):
        build_portfolio_performance_report(
            (usd, eur), base_currency="USD", fx_evidence=bad_schema, config=config
        )

    # Mismatched target currency
    bad_target = {
        "contract_version": "v1",
        "schema_id": "data.fx_conversion_evidence.v1",
        "source_currency": "EUR",
        "target_currency": "GBP",
        "legs": (),
        "composite_rate": Decimal("1.1"),
        "as_of": eur.created_at,
        "expires_at": eur.created_at + timedelta(days=1),
        "path_policy_id": "policy-1",
        "path_policy_version": "v1",
        "provenance": "test",
        "request_id": "req-1",
    }
    with pytest.raises(AnalyticsValidationError, match="evidence is incompatible"):
        build_portfolio_performance_report(
            (usd, eur), base_currency="USD", fx_evidence=bad_target, config=config
        )


def test_portfolio_builder_invalid_fx_evidence_values() -> None:
    """Stale, non-finite, negative, or naive FX rates fail validation."""
    usd, config = _report(account_currency="USD")
    eur, _ = _report(account_currency="EUR")

    def _good_evidence(
        rate: object = Decimal("1.1"),
        as_of: object = eur.created_at,
        expires_at: object = eur.created_at + timedelta(days=1),
    ) -> dict[str, object]:
        return {
            "contract_version": "v1",
            "schema_id": "data.fx_conversion_evidence.v1",
            "source_currency": "EUR",
            "target_currency": "USD",
            "legs": (),
            "composite_rate": rate,
            "as_of": as_of,
            "expires_at": expires_at,
            "path_policy_id": "policy-1",
            "path_policy_version": "v1",
            "provenance": "test",
            "request_id": "req-1",
        }

    # Stale (expired)
    expired = _good_evidence(expires_at=eur.created_at - timedelta(days=1))
    with pytest.raises(AnalyticsValidationError, match="stale or invalid"):
        build_portfolio_performance_report(
            (usd, eur), base_currency="USD", fx_evidence=expired, config=config
        )

    # Negative rate
    negative = _good_evidence(rate=Decimal("-1.1"))
    with pytest.raises(AnalyticsValidationError, match="stale or invalid"):
        build_portfolio_performance_report(
            (usd, eur), base_currency="USD", fx_evidence=negative, config=config
        )

    # Infinite rate
    infinite = _good_evidence(rate=Decimal("Infinity"))
    with pytest.raises(AnalyticsValidationError, match="stale or invalid"):
        build_portfolio_performance_report(
            (usd, eur), base_currency="USD", fx_evidence=infinite, config=config
        )

    # Naive as_of
    naive_dt = datetime(2026, 7, 19)
    naive_as_of = _good_evidence(as_of=naive_dt)
    with pytest.raises(AnalyticsValidationError, match="stale or invalid"):
        build_portfolio_performance_report(
            (usd, eur), base_currency="USD", fx_evidence=naive_as_of, config=config
        )


def test_portfolio_builder_no_aggregable_currency_evidence() -> None:
    """Component reports with no currency metrics fail validation."""
    usd, config = _report(account_currency="USD")
    # Empty out the metrics
    empty_usd = usd.model_copy(update={"sections": ()})
    with pytest.raises(
        AnalyticsValidationError, match="no aggregable currency evidence"
    ):
        build_portfolio_performance_report(
            (empty_usd,), base_currency="USD", fx_evidence=None, config=config
        )


def test_portfolio_builder_metric_value_not_decimal() -> None:
    """A currency metric value that is not Decimal fails validation."""
    usd, config = _report(account_currency="USD")
    from app.services.analytics.contracts.models import MetricEvidence, SectionEvidence

    # Replace metrics with a float value metric
    bad_metric = MetricEvidence(
        metric_key="net_pnl",
        status="calculated",
        value=10.5,  # float instead of Decimal
        unit="currency",
        source_context="source-1",
    )
    bad_usd = usd.model_copy(
        update={
            "sections": (
                SectionEvidence(
                    section_key="overall", status="completed", metrics=(bad_metric,)
                ),
            )
        }
    )
    with pytest.raises(
        AnalyticsValidationError, match="currency metric must be Decimal"
    ):
        build_portfolio_performance_report(
            (bad_usd,), base_currency="USD", fx_evidence=None, config=config
        )
