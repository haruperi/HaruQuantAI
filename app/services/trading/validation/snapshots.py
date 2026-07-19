"""Explicit route facts without unavailable or stale neutral defaults."""

from collections.abc import Callable, Mapping
from datetime import datetime, timedelta
from types import MappingProxyType
from typing import Self

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from app.services.trading.contracts import TradingError, TradingRequest, TradingRoute
from app.services.trading.contracts.models import JsonValue
from app.utils import logger, to_json_safe


class RouteSnapshot(BaseModel):
    """Immutable route facts with provenance and freshness evidence.

    Attributes:
        facts: Explicit account, symbol, quote, and permission facts.
        source_id: Read-source provenance.
        authority_id: Route truth authority.
        available: Whether source evidence was available.
        fresh: Whether source evidence met its configured freshness policy.
    """

    model_config = ConfigDict(frozen=True, extra="forbid", allow_inf_nan=False)

    route: TradingRoute
    provider_id: str | None
    account_id: str
    symbol: str | None
    facts: Mapping[str, JsonValue]
    source_id: str
    authority_id: str
    observed_at: datetime
    expires_at: datetime
    available: bool
    fresh: bool
    capabilities: tuple[str, ...]

    @field_validator("account_id", "source_id", "authority_id")
    @classmethod
    def _validate_text(cls, value: str) -> str:
        """Validate required snapshot provenance text.

        Args:
            value: Candidate identifier.

        Returns:
            Validated identifier.

        Raises:
            ValueError: If text is blank or untrimmed.
        """
        logger.debug("Validating RouteSnapshot provenance text")
        if not value or value != value.strip():
            raise ValueError("route snapshot text must be non-empty and trimmed")
        return value

    @field_validator("provider_id", "symbol")
    @classmethod
    def _validate_optional_text(cls, value: str | None) -> str | None:
        """Validate optional route snapshot text.

        Args:
            value: Candidate optional identifier.

        Returns:
            Validated optional identifier.

        Raises:
            ValueError: If supplied text is blank or untrimmed.
        """
        logger.debug("Validating optional RouteSnapshot text")
        if value is not None and (not value or value != value.strip()):
            raise ValueError("optional snapshot text must be non-empty and trimmed")
        return value

    @field_validator("facts", mode="before")
    @classmethod
    def _validate_facts(cls, value: Mapping[str, object]) -> Mapping[str, JsonValue]:
        """Validate and freeze explicit JSON-safe facts.

        Args:
            value: Candidate route facts.

        Returns:
            Immutable JSON-safe route facts.

        Raises:
            TypeError: If facts are not a serializable mapping.
        """
        logger.debug("Validating explicit RouteSnapshot facts")
        safe = to_json_safe(value)
        if not isinstance(safe, dict):
            raise TypeError("route snapshot facts must be a mapping")
        return MappingProxyType(safe)

    @field_validator("capabilities")
    @classmethod
    def _validate_capabilities(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        """Validate explicit unique capability evidence.

        Args:
            value: Candidate capabilities.

        Returns:
            Validated capability tuple.

        Raises:
            ValueError: If capabilities are blank or duplicated.
        """
        logger.debug("Validating RouteSnapshot capabilities")
        if any(not item or item != item.strip() for item in value):
            raise ValueError("snapshot capabilities must be non-empty and trimmed")
        if len(set(value)) != len(value):
            raise ValueError("snapshot capabilities must be unique")
        return value

    @field_validator("observed_at", "expires_at")
    @classmethod
    def _validate_time(cls, value: datetime) -> datetime:
        """Validate route snapshot UTC time evidence.

        Args:
            value: Candidate timestamp.

        Returns:
            Validated UTC timestamp.

        Raises:
            ValueError: If timestamp is naive or non-UTC.
        """
        logger.debug("Validating RouteSnapshot UTC time")
        if value.tzinfo is None or value.utcoffset() != timedelta(0):
            raise ValueError("route snapshot time must be timezone-aware UTC")
        return value

    @model_validator(mode="after")
    def _validate_lifetime(self) -> Self:
        """Validate snapshot lifetime.

        Returns:
            Validated snapshot.

        Raises:
            ValueError: If expiry does not follow observation.
        """
        logger.debug("Validating RouteSnapshot lifetime")
        if self.expires_at <= self.observed_at:
            raise ValueError("route snapshot expiry must follow observation")
        return self


def get_route_snapshot(
    request: TradingRequest,
    source: Callable[[TradingRoute, str | None], Mapping[str, JsonValue]],
) -> RouteSnapshot:
    """Read explicit timestamped route facts and fail closed.

    Args:
        request: Governed request defining exact route scope.
        source: Injected read-only route-fact source.

    Returns:
        Available fresh route snapshot.

    Raises:
        TradingError: If source evidence is unavailable, stale, malformed, or
            scope-incompatible.
    """
    logger.info("Reading explicit Trading route snapshot")
    try:
        raw = source(request.route, request.provider_id)
        snapshot = RouteSnapshot.model_validate(dict(raw))
    except Exception as error:
        logger.warning("Trading route snapshot source was malformed")
        raise TradingError(
            "SERVICE_UNAVAILABLE",
            "Route snapshot source is unavailable or malformed",
            trace_context={"request_id": request.request_id},
        ) from error
    if not snapshot.available:
        raise TradingError("SERVICE_UNAVAILABLE", "Route snapshot is unavailable")
    if not snapshot.fresh or snapshot.expires_at <= request.system_time:
        raise TradingError("STALE_EVIDENCE", "Route snapshot is stale")
    if (
        snapshot.route != request.route
        or snapshot.provider_id != request.provider_id
        or snapshot.account_id != request.account_id
        or snapshot.symbol != request.symbol
    ):
        raise TradingError("SCOPE_MISMATCH", "Route snapshot scope does not match")
    return snapshot


__all__ = ["RouteSnapshot", "get_route_snapshot"]
