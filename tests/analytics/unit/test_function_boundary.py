"""Focused tests for Analytics' function-only value boundary."""

import inspect
from dataclasses import asdict, fields
from decimal import Decimal

import pytest
from app.services.analytics import (
    create_analytics_run_config,
    create_analytics_value,
    create_closed_trade_ledger,
    create_portfolio_rebalance_measurement_request,
    create_risk_free_rate_evidence,
    create_statistical_validation_config,
    get_analytics_dashboard_snapshot,
    get_analytics_value_field,
    is_analytics_value,
)

from tests.analytics._support import _config, _measurement_request


def test_package_all_exports_only_standalone_functions() -> None:
    """Enforce the literal function-only public API gate."""
    from app.services import analytics

    assert analytics.__all__
    assert all(
        inspect.isfunction(getattr(analytics, name)) for name in analytics.__all__
    )


def test_value_factories_construct_all_registered_boundary_values() -> None:
    """Construct each specialized opaque value through standalone functions."""
    config = _config()
    statistics = create_statistical_validation_config(**asdict(config.statistics))
    rate = create_risk_free_rate_evidence(**asdict(config.risk_free_rate))
    run_config = create_analytics_run_config(
        **(asdict(config) | {"statistics": statistics, "risk_free_rate": rate})
    )
    ledger = create_closed_trade_ledger(daily_pnl=(Decimal(1), Decimal(-1)))
    request = _measurement_request()
    measurement = create_portfolio_rebalance_measurement_request(
        **{field.name: getattr(request, field.name) for field in fields(request)}
    )

    assert get_analytics_value_field(run_config, "max_trades") == 100
    assert is_analytics_value(ledger, "ClosedTradeLedger")
    assert is_analytics_value(measurement, "PortfolioRebalanceMeasurementRequest")
    assert (
        create_analytics_value("ClosedTradeLedger", daily_pnl=(Decimal(1), Decimal(-1)))
        == ledger
    )


def test_value_boundary_rejects_unknown_or_private_fields() -> None:
    """Fail closed for unknown model names and inaccessible fields."""
    with pytest.raises(TypeError, match="Unknown Analytics"):
        create_analytics_value("MissingValue")
    assert not is_analytics_value(object(), "MissingValue")
    with pytest.raises(ValueError, match="does not expose"):
        get_analytics_value_field(object(), "_private")


@pytest.mark.parametrize("view", ["equity_curve", "summary"])
def test_dashboard_snapshot_is_explicitly_unavailable(view: str) -> None:
    """Return timestamped unavailable evidence without invented dashboard data."""
    snapshot = get_analytics_dashboard_snapshot(view)
    assert snapshot["view"] == view
    assert snapshot["status"] == "unavailable"


def test_dashboard_snapshot_rejects_unowned_view() -> None:
    """Reject dashboard views outside the Analytics contract."""
    with pytest.raises(ValueError, match="unsupported"):
        get_analytics_dashboard_snapshot("orders")
