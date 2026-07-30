"""Function-only construction and inspection boundary for Analytics values."""

from __future__ import annotations

from typing import Any

from app.services.analytics.contracts import models as _models


def _create(name: str, values: dict[str, object]) -> object:
    """Construct one internal Analytics value by its registered model name.

    Returns:
        The constructed opaque Analytics value.
    """
    return getattr(_models, name)(**values)


def create_analytics_value(value_type: str, /, **values: object) -> object:
    """Create one registered opaque Analytics value.

    Args:
        value_type: Exact internal Analytics model name.
        **values: Validated model field values.

    Returns:
        Opaque Analytics value.

    Raises:
        TypeError: If the requested model is unavailable.
    """
    model: Any = getattr(_models, value_type, None)
    if not isinstance(model, type):
        message = f"Unknown Analytics value type: {value_type}"
        raise TypeError(message)
    return model(**values)


def create_analytics_run_config(**values: object) -> object:
    """Create an Analytics run configuration.

    Returns:
        The opaque run configuration.
    """
    return _create("AnalyticsRunConfig", dict(values))


def create_closed_trade_ledger(**values: object) -> object:
    """Create a validated closed-trade daily-P&L ledger.

    Returns:
        The opaque daily-P&L ledger.
    """
    return _create("ClosedTradeLedger", dict(values))


def create_risk_free_rate_evidence(**values: object) -> object:
    """Create source-backed risk-free-rate evidence.

    Returns:
        The opaque risk-free-rate evidence.
    """
    return _create("RiskFreeRateEvidence", dict(values))


def create_statistical_validation_config(**values: object) -> object:
    """Create a bounded statistical-validation configuration.

    Returns:
        The opaque statistical configuration.
    """
    return _create("StatisticalValidationConfig", dict(values))


def create_portfolio_rebalance_measurement_request(**values: object) -> object:
    """Create a hash-bound rebalance measurement request.

    Returns:
        The opaque rebalance measurement request.
    """
    return _create("PortfolioRebalanceMeasurementRequest", dict(values))


def get_analytics_value_field(value: object, field: str) -> object:
    """Return one public field from an opaque Analytics value.

    Raises:
        ValueError: If the requested value does not expose the field.
    """
    if not field or field.startswith("_") or not hasattr(value, field):
        raise ValueError("Analytics value does not expose the requested field")
    return getattr(value, field)


def is_analytics_value(value: object, model_name: str) -> bool:
    """Return whether a value is an instance of one registered Analytics model."""
    model: Any = getattr(_models, model_name, None)
    return isinstance(value, model) if isinstance(model, type) else False
