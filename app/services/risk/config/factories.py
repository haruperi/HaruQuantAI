"""Function-only construction and inspection for Risk configuration values."""

from __future__ import annotations

from app.services.risk.config.mandates import DrawdownMode, FirmMandate
from app.services.risk.config.profiles import RiskConfig


def create_firm_mandate(**values: object) -> FirmMandate:
    """Construct one validated firm mandate.

    Args:
        **values: Mandate field values.

    Returns:
        Validated internal firm mandate.
    """
    return FirmMandate.model_validate(values)


def create_risk_config(**values: object) -> RiskConfig:
    """Construct one validated Risk configuration.

    Args:
        **values: Configuration field values.

    Returns:
        Validated internal Risk configuration.
    """
    return RiskConfig.model_validate(values)


def get_drawdown_mode(value: str) -> DrawdownMode:
    """Resolve one canonical drawdown mode.

    Args:
        value: Registered drawdown-mode value or member name.

    Returns:
        Internal canonical drawdown mode.
    """
    member = DrawdownMode.__members__.get(value.upper())
    return member if member is not None else DrawdownMode(value.lower())


__all__ = ["create_firm_mandate", "create_risk_config", "get_drawdown_mode"]
