"""Normalized route-authority facts for Trading reconciliation."""

from collections.abc import Mapping
from datetime import datetime, timedelta
from types import MappingProxyType
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from app.services.trading.contracts import TradingRoute
from app.services.trading.contracts.models import JsonValue
from app.utils import logger, to_json_safe


def _freeze_mapping(value: Mapping[str, object]) -> Mapping[str, JsonValue]:
    """Validate and freeze JSON-safe authority facts.

    Args:
        value: Candidate authority fact mapping.

    Returns:
        Immutable JSON-safe mapping.

    Raises:
        TypeError: If facts cannot be represented as a mapping.
    """
    logger.debug("Freezing normalized Trading authority facts")
    safe = to_json_safe(value)
    if not isinstance(safe, dict):
        raise TypeError("authority facts must be a JSON-safe mapping")
    return MappingProxyType(safe)


class AuthoritySnapshot(BaseModel):
    """Immutable normalized account, order, position, and time authority evidence.

    Attributes:
        route: Authority route represented by the snapshot.
        authority_id: Broker or Simulation authority identifier.
        account_id: Exact account/tenant reconciliation scope.
        account: Normalized account facts without provider objects.
        orders: Provider-order facts keyed by authority identity.
        positions: Provider-position facts keyed by authority identity.
        observed_at: UTC authority observation time.
        expires_at: UTC freshness deadline.
    """

    model_config = ConfigDict(frozen=True, extra="forbid", allow_inf_nan=False)

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["trading.authority_snapshot.v1"] = (
        "trading.authority_snapshot.v1"
    )
    route: TradingRoute
    authority_id: str
    account_id: str
    source_id: str
    account: Mapping[str, JsonValue]
    orders: Mapping[str, JsonValue]
    positions: Mapping[str, JsonValue]
    observed_at: datetime
    expires_at: datetime
    available: Literal[True] = True

    @field_validator("authority_id", "account_id", "source_id")
    @classmethod
    def _validate_text(cls, value: str) -> str:
        """Validate required authority provenance text.

        Args:
            value: Candidate provenance value.

        Returns:
            Validated trimmed text.

        Raises:
            ValueError: If text is blank or untrimmed.
        """
        logger.debug("Validating AuthoritySnapshot provenance text")
        if not value or value != value.strip():
            raise ValueError("authority provenance must be non-empty and trimmed")
        return value

    @field_validator("account", "orders", "positions", mode="before")
    @classmethod
    def _validate_facts(
        cls,
        value: Mapping[str, object],
    ) -> Mapping[str, JsonValue]:
        """Validate immutable JSON-safe authority facts.

        Args:
            value: Candidate normalized fact mapping.

        Returns:
            Immutable JSON-safe fact mapping.
        """
        logger.debug("Validating AuthoritySnapshot fact mapping")
        return _freeze_mapping(value)

    @field_validator("observed_at", "expires_at")
    @classmethod
    def _validate_time(cls, value: datetime) -> datetime:
        """Validate timezone-aware UTC authority timestamps.

        Args:
            value: Candidate timestamp.

        Returns:
            Validated UTC timestamp.

        Raises:
            ValueError: If timestamp is naive or non-UTC.
        """
        logger.debug("Validating AuthoritySnapshot UTC timestamp")
        if value.tzinfo is None or value.utcoffset() != timedelta(0):
            raise ValueError("authority timestamp must be timezone-aware UTC")
        return value

    @model_validator(mode="after")
    def _validate_freshness_window(self) -> Self:
        """Validate the explicit authority freshness interval.

        Returns:
            Validated authority snapshot.

        Raises:
            ValueError: If the freshness interval is empty or inverted.
        """
        logger.debug("Validating AuthoritySnapshot freshness window")
        if self.expires_at <= self.observed_at:
            raise ValueError("authority snapshot expiry must follow observation")
        return self


__all__ = ["AuthoritySnapshot"]
