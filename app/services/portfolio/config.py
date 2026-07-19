"""Required Portfolio-owned settings with no hidden business defaults."""

from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from pydantic_settings import SettingsConfigDict

from app.services.portfolio.exceptions import PortfolioError
from app.utils import AppSettings, logger


class RebalanceSchedule(BaseModel):
    """Deterministic UTC interval schedule.

    Attributes:
        anchor_at: UTC instant from which schedule intervals are measured.
        interval_seconds: Positive interval between reviews.
    """

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        strict=True,
    )

    anchor_at: datetime
    interval_seconds: int = Field(gt=0)

    @field_validator("anchor_at")
    @classmethod
    def _validate_anchor(cls, value: datetime) -> datetime:
        """Require an aware UTC anchor.

        Args:
            value: Candidate schedule anchor.

        Returns:
            Validated UTC anchor.

        Raises:
            ValueError: If the timestamp is naive or non-UTC.
        """
        logger.debug("Validating Portfolio rebalance schedule anchor")
        if value.tzinfo is None or value.utcoffset() != timedelta(0):
            raise ValueError("schedule anchor must be aware UTC")
        return value


class PortfolioSettings(AppSettings):
    """Complete required Portfolio policy configuration.

    Attributes:
        portfolio_weight_sum_tolerance: Positive accepted sum variance.
        portfolio_min_weight: Inclusive component weight floor.
        portfolio_max_weight: Inclusive component weight ceiling.
        portfolio_max_strategies: Positive maximum component count.
        portfolio_min_evidence_observations: Positive inverse-volatility minimum.
        portfolio_max_evidence_age_seconds: Positive evidence freshness limit.
        portfolio_allocation_decision_ttl_seconds: Positive Risk decision age limit.
        portfolio_activation_approval_policy: Exact policy reference by profile.
        portfolio_rebalance_drift_threshold: Non-negative drift threshold.
        portfolio_rebalance_schedule: Required deterministic UTC schedule.
    """

    model_config = SettingsConfigDict(
        env_file=AppSettings.model_config.get("env_file"),
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        case_sensitive=False,
        extra="ignore",
        frozen=True,
        strict=True,
        populate_by_name=True,
    )

    portfolio_weight_sum_tolerance: Decimal = Field(
        validation_alias="PORTFOLIO_WEIGHT_SUM_TOLERANCE",
    )
    portfolio_min_weight: Decimal = Field(
        validation_alias="PORTFOLIO_MIN_WEIGHT",
    )
    portfolio_max_weight: Decimal = Field(
        validation_alias="PORTFOLIO_MAX_WEIGHT",
    )
    portfolio_max_strategies: int = Field(
        gt=0,
        validation_alias="PORTFOLIO_MAX_STRATEGIES",
    )
    portfolio_min_evidence_observations: int = Field(
        gt=0,
        validation_alias="PORTFOLIO_MIN_EVIDENCE_OBSERVATIONS",
    )
    portfolio_max_evidence_age_seconds: int = Field(
        gt=0,
        validation_alias="PORTFOLIO_MAX_EVIDENCE_AGE_SECONDS",
    )
    portfolio_allocation_decision_ttl_seconds: int = Field(
        gt=0,
        validation_alias="PORTFOLIO_ALLOCATION_DECISION_TTL_SECONDS",
    )
    portfolio_activation_approval_policy: dict[str, str] = Field(
        validation_alias="PORTFOLIO_ACTIVATION_APPROVAL_POLICY",
    )
    portfolio_rebalance_drift_threshold: Decimal = Field(
        validation_alias="PORTFOLIO_REBALANCE_DRIFT_THRESHOLD",
    )
    portfolio_rebalance_schedule: RebalanceSchedule = Field(
        validation_alias="PORTFOLIO_REBALANCE_SCHEDULE",
    )

    @field_validator(
        "portfolio_weight_sum_tolerance",
        "portfolio_min_weight",
        "portfolio_max_weight",
        "portfolio_rebalance_drift_threshold",
    )
    @classmethod
    def _validate_decimal(cls, value: Decimal) -> Decimal:
        """Reject non-finite Portfolio configuration decimals.

        Args:
            value: Candidate Decimal setting.

        Returns:
            Validated finite Decimal.

        Raises:
            ValueError: If the value is non-finite.
        """
        logger.debug("Validating Portfolio Decimal setting")
        if not value.is_finite():
            raise ValueError("Portfolio Decimal setting must be finite")
        return value

    @model_validator(mode="after")
    def _validate_policy(self) -> Self:
        """Validate cross-setting Portfolio policy invariants.

        Returns:
            Validated settings.

        Raises:
            PortfolioError: If any required policy relationship is invalid.
        """
        logger.info("Validating complete Portfolio settings")
        if self.portfolio_weight_sum_tolerance <= 0:
            raise PortfolioError("PORT_CONFIG_INVALID", "WEIGHT_TOLERANCE")
        if self.portfolio_min_weight < 0:
            raise PortfolioError("PORT_CONFIG_INVALID", "MIN_WEIGHT")
        if not self.portfolio_min_weight <= self.portfolio_max_weight <= Decimal(1):
            raise PortfolioError("PORT_CONFIG_INVALID", "MAX_WEIGHT")
        if self.portfolio_rebalance_drift_threshold < 0:
            raise PortfolioError("PORT_CONFIG_INVALID", "DRIFT_THRESHOLD")
        policies = self.portfolio_activation_approval_policy
        if set(policies) != {"simulation", "paper", "live"}:
            raise PortfolioError("PORT_CONFIG_INVALID", "APPROVAL_POLICY")
        if any(not value or value != value.strip() for value in policies.values()):
            raise PortfolioError("PORT_CONFIG_INVALID", "APPROVAL_POLICY")
        return self

    def evidence_max_age(self) -> timedelta:
        """Return the configured evidence freshness duration.

        Returns:
            Positive evidence maximum age.
        """
        logger.debug("Building Portfolio evidence freshness duration")
        return timedelta(seconds=self.portfolio_max_evidence_age_seconds)


__all__: tuple[str, ...] = ("PortfolioSettings", "RebalanceSchedule")
