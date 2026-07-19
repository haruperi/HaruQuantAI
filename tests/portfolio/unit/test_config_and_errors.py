"""Unit tests for required Portfolio settings and error catalog."""

# ruff: noqa: INP001

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from app.services.portfolio.config import PortfolioSettings, RebalanceSchedule
from app.services.portfolio.exceptions import (
    PORTFOLIO_ERROR_CODES,
    PortfolioError,
    PortfolioErrorPayload,
)
from app.utils import HaruQuantError, logger
from pydantic import ValidationError


def test_settings_have_no_business_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify missing owned settings block service configuration.

    Args:
        monkeypatch: Pytest environment mutation helper.
    """
    logger.info("Testing Portfolio configuration has no business defaults")
    for field in PortfolioSettings.model_fields.values():
        for alias in (field.validation_alias, field.alias):
            if isinstance(alias, str):
                monkeypatch.delenv(alias, raising=False)

    with pytest.raises(ValidationError):
        PortfolioSettings()


def test_settings_validate_cross_field_policy(
    portfolio_settings: PortfolioSettings,
) -> None:
    """Verify complete settings expose exact validated durations.

    Args:
        portfolio_settings: Complete explicit Portfolio settings.
    """
    logger.info("Testing Portfolio configuration cross-field policy")
    assert portfolio_settings.evidence_max_age().total_seconds() == 3600
    assert portfolio_settings.portfolio_min_weight == Decimal(0)

    invalid = portfolio_settings.model_dump()
    invalid["portfolio_max_weight"] = Decimal("1.1")
    with pytest.raises(PortfolioError, match="PORT_CONFIG_INVALID"):
        PortfolioSettings(**invalid)


def test_schedule_requires_aware_utc() -> None:
    """Verify schedule timestamps and intervals are explicit and valid."""
    logger.info("Testing Portfolio UTC schedule validation")
    with pytest.raises(ValidationError):
        RebalanceSchedule(
            anchor_at=datetime(2026, 7, 19, 12, 0, tzinfo=UTC).replace(tzinfo=None),
            interval_seconds=3600,
        )
    with pytest.raises(ValidationError):
        RebalanceSchedule(
            anchor_at=datetime(2026, 7, 19, 12, 0, tzinfo=UTC),
            interval_seconds=0,
        )


def test_error_catalog_is_closed_and_utils_based() -> None:
    """Verify Portfolio errors extend Utils and expose safe payloads."""
    logger.info("Testing closed Portfolio error catalog")
    error = PortfolioError("PORT_EVIDENCE_INVALID", "STALE")

    assert isinstance(error, HaruQuantError)
    assert error.to_payload() == PortfolioErrorPayload(
        code="PORT_EVIDENCE_INVALID",
        detail="STALE",
    )
    assert "PORT_INTERNAL_ERROR" in PORTFOLIO_ERROR_CODES
    with pytest.raises(ValueError, match="not registered"):
        PortfolioError("UNKNOWN")
