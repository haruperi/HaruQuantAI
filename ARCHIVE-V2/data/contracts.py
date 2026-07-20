"""Typed contracts for the market data service boundary.

This module defines lightweight protocols and aliases used to describe Data
service boundaries without importing broker SDKs or leaking provider-native
objects across module boundaries.
"""

from __future__ import annotations

import hashlib
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any, Protocol, runtime_checkable

import pandas as pd
from app.services.data.errors import DataValidationError as ValidationError
from app.utils.logger import logger
from app.utils.normalization import normalize_timestamp
from app.utils.standard import SENSITIVE_KEY_PATTERN, canonical_json
from pydantic import BaseModel, Field, field_validator, model_validator

type JsonScalar = str | int | float | bool | None
type JsonValue = JsonScalar | list[JsonValue] | dict[str, JsonValue]
type DataRecord = dict[str, JsonValue]
type DataRecords = list[DataRecord]
type SymbolMetadataRecord = dict[str, JsonValue]

_SCHEMA_VERSION_MIN_PARTS = 2

_TRACE_FIELDS: frozenset[str] = frozenset(
    {"created_at", "request_id", "workflow_id", "correlation_id"}
)


class Contract(BaseModel):
    """Local base model for data service contracts."""

    schema_version: str = Field(
        default="1.0.0",
        description="Contract schema version (major.minor.patch).",
    )
    created_at: str = Field(
        default_factory=lambda: datetime.now(UTC).isoformat(),
        description="UTC ISO 8601 creation timestamp.",
    )
    request_id: str | None = Field(default=None, description="Correlation request ID.")
    workflow_id: str | None = Field(
        default=None, description="Associated workflow run identifier."
    )
    correlation_id: str | None = Field(
        default=None, description="Causation correlation identifier."
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Namespaced adapter, provider, or experimental fields.",
    )

    @field_validator("metadata")
    @classmethod
    def validate_metadata_structure(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Validate metadata namespacing and secret safety."""
        for key in value:
            if not isinstance(key, str):
                raise TypeError("Metadata keys must be strings.")
            if "." not in key and ":" not in key:
                msg = (
                    f"Metadata key '{key}' is not namespaced. "
                    "Keys must be namespaced with a '.' or ':' separator."
                )
                raise ValueError(msg)
            if SENSITIVE_KEY_PATTERN.search(key):
                msg = (
                    f"Metadata key '{key}' matches sensitive key pattern "
                    "and is not allowed."
                )
                raise ValueError(msg)
        try:
            canonical_json(value)
        except (TypeError, ValueError) as exc:
            msg = f"Metadata is not deterministically serializable: {exc}"
            raise ValueError(msg) from exc
        return value

    @model_validator(mode="after")
    def validate_trace_identifiers(self) -> Contract:
        """Validate trace identifier fields."""
        for name in ("request_id", "workflow_id", "correlation_id"):
            value = getattr(self, name)
            if value is not None and (not isinstance(value, str) or not value.strip()):
                msg = f"{name} must be a non-empty string or None."
                raise ValueError(msg)
        return self

    def to_json(self) -> str:
        """Serialize this contract to deterministic canonical JSON."""
        try:
            return canonical_json(self.model_dump())
        except (TypeError, ValueError) as exc:
            msg = f"Failed to serialize contract: {exc}"
            raise ValidationError(msg) from exc

    def content_hash(self) -> str:
        """Calculate a stable SHA256 hash over business-data fields only."""
        payload = {
            key: value
            for key, value in self.model_dump().items()
            if key not in _TRACE_FIELDS
        }
        try:
            serialized = canonical_json(payload)
        except (TypeError, ValueError) as exc:
            msg = f"Failed to compute content hash: {exc}"
            raise ValidationError(msg) from exc
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def contract_hash(self) -> str:
        """Calculate SHA256 hash over the full serialized contract."""
        return hashlib.sha256(self.to_json().encode("utf-8")).hexdigest()

    def check_compatibility(self, target_version: str) -> bool:
        """Check whether this contract version is compatible with a target."""
        min_parts = 2
        try:
            current_parts = [int(part) for part in self.schema_version.split(".")]
            target_parts = [int(part) for part in target_version.split(".")]
            if len(current_parts) < min_parts or len(target_parts) < min_parts:
                return False
            if current_parts[0] != target_parts[0]:
                return False
            return current_parts[1] >= target_parts[1]
        except ValueError:
            return False


@runtime_checkable
class BrokerMarketDataPort(Protocol):
    """Read-only broker market data client contract.

    Implementations are owned by ``app.services.brokers``. Data adapters may
    use this port only for connection-readiness checks and market-data reads.
    Broker account, order, position, or live-execution mutation methods are
    intentionally absent from this protocol.
    """

    def is_connected(self) -> bool:
        """Return whether the read-only broker data client is connected.

        Returns:
            True when the broker data client is connected, otherwise False.
        """
        logger.debug("BrokerMarketDataPort.is_connected contract invoked.")
        raise NotImplementedError

    def connect(self) -> bool | None:
        """Open the broker data connection when required.

        Returns:
            Optional provider connection result. Existing broker clients may
            return True/False, while some future clients may return None.

        Raises:
            Exception: Implementations may raise provider-specific connection
                errors, which data adapters must map to deterministic service
                errors.
        """
        logger.debug("BrokerMarketDataPort.connect contract invoked.")
        raise NotImplementedError

    def get_bars(
        self,
        *,
        symbol: str,
        timeframe: str,
        date_from: datetime,
        date_to: datetime,
    ) -> pd.DataFrame | None:
        """Read historical OHLCV bars from a broker data source.

        Args:
            symbol: Provider symbol identifier.
            timeframe: Provider timeframe identifier.
            date_from: Inclusive UTC start datetime.
            date_to: Inclusive UTC end datetime.

        Returns:
            A pandas DataFrame containing provider bar rows, or None when no
            rows are available.
        """
        logger.debug(
            "BrokerMarketDataPort.get_bars contract invoked for {} {} from {} to {}.",
            symbol,
            timeframe,
            date_from.isoformat(),
            date_to.isoformat(),
        )
        raise NotImplementedError

    def get_ticks(
        self,
        *,
        symbol: str,
        start: datetime,
        end: datetime,
        as_dataframe: bool = True,
    ) -> pd.DataFrame | None:
        """Read historical ticks from a broker data source.

        Args:
            symbol: Provider symbol identifier.
            start: Inclusive UTC start datetime.
            end: Inclusive UTC end datetime.
            as_dataframe: Whether the broker client should return a DataFrame.

        Returns:
            A pandas DataFrame containing provider tick rows, or None when no
            rows are available.
        """
        logger.debug(
            "BrokerMarketDataPort.get_ticks contract invoked for {} from {} to {} "
            "as_dataframe={}.",
            symbol,
            start.isoformat(),
            end.isoformat(),
            as_dataframe,
        )
        raise NotImplementedError


type BrokerMarketDataFactory = Callable[[], BrokerMarketDataPort]


@runtime_checkable
class SourceAdapterPort(Protocol):
    """Internal source adapter contract for normalized market data records."""

    def is_ready(self) -> bool:
        """Return whether the source adapter is configured for read calls.

        Returns:
            True when the source is ready, otherwise False.
        """
        logger.debug("SourceAdapterPort.is_ready contract invoked.")
        raise NotImplementedError

    def get_market_data(
        self,
        symbol: str,
        timeframe: str,
        start_time: datetime,
        end_time: datetime,
        *,
        request_id: str | None = None,
    ) -> DataRecords:
        """Fetch normalized historical OHLCV records.

        Args:
            symbol: Canonical symbol identifier.
            timeframe: Canonical timeframe identifier.
            start_time: Inclusive UTC start datetime.
            end_time: Inclusive UTC end datetime.
            request_id: Optional trace identifier.

        Returns:
            Normalized JSON-safe market data records.
        """
        logger.debug(
            "SourceAdapterPort.get_market_data contract invoked for {} {} from {} "
            "to {}.",
            symbol,
            timeframe,
            start_time.isoformat(),
            end_time.isoformat(),
            extra={"request_id": request_id},
        )
        raise NotImplementedError

    def get_tick_data(
        self,
        symbol: str,
        start_time: datetime,
        end_time: datetime,
        *,
        request_id: str | None = None,
    ) -> DataRecords:
        """Fetch normalized historical tick records.

        Args:
            symbol: Canonical symbol identifier.
            start_time: Inclusive UTC start datetime.
            end_time: Inclusive UTC end datetime.
            request_id: Optional trace identifier.

        Returns:
            Normalized JSON-safe tick records.
        """
        logger.debug(
            "SourceAdapterPort.get_tick_data contract invoked for {} from {} to {}.",
            symbol,
            start_time.isoformat(),
            end_time.isoformat(),
            extra={"request_id": request_id},
        )
        raise NotImplementedError

    def list_symbols(self, *, request_id: str | None = None) -> list[str]:
        """List symbols discovered from the source.

        Args:
            request_id: Optional trace identifier.

        Returns:
            Sorted or provider-defined symbol identifiers.
        """
        logger.debug(
            "SourceAdapterPort.list_symbols contract invoked.",
            extra={"request_id": request_id},
        )
        raise NotImplementedError

    def get_symbol_metadata(
        self,
        symbol: str,
        *,
        request_id: str | None = None,
    ) -> SymbolMetadataRecord:
        """Return normalized metadata for a symbol.

        Args:
            symbol: Canonical symbol identifier.
            request_id: Optional trace identifier.

        Returns:
            JSON-safe symbol metadata.
        """
        logger.debug(
            "SourceAdapterPort.get_symbol_metadata contract invoked for {}.",
            symbol,
            extra={"request_id": request_id},
        )
        raise NotImplementedError


# Canonical market-data error codes
ERR_SYMBOL_UNAVAILABLE = "SYMBOL_UNAVAILABLE"
ERR_UNSUPPORTED_TIMEFRAME = "UNSUPPORTED_TIMEFRAME"
ERR_STALE_DATA = "STALE_DATA"
ERR_PROVIDER_ERROR = "PROVIDER_ERROR"
ERR_MALFORMED_PAYLOAD = "MALFORMED_PAYLOAD"

ALLOWED_TIMEFRAMES = {
    "M1",
    "M2",
    "M3",
    "M4",
    "M5",
    "M6",
    "M10",
    "M12",
    "M15",
    "M20",
    "M30",
    "H1",
    "H2",
    "H3",
    "H4",
    "H6",
    "H8",
    "H12",
    "D1",
    "W1",
    "MN1",
}

# Canonical duration in seconds for each supported timeframe.
_TIMEFRAME_DURATIONS: dict[str, int] = {
    "M1": 60,
    "M2": 120,
    "M3": 180,
    "M4": 240,
    "M5": 300,
    "M6": 360,
    "M10": 600,
    "M12": 720,
    "M15": 900,
    "M20": 1200,
    "M30": 1800,
    "H1": 3600,
    "H2": 7200,
    "H3": 10800,
    "H4": 14400,
    "H6": 21600,
    "H8": 28800,
    "H12": 43200,
    "D1": 86400,
    "W1": 604800,
    "MN1": 2592000,
}


def _validate_timestamp_iso(v: str) -> str:
    """Validate and normalize a timestamp to an ISO UTC string.

    Args:
        v: Raw timestamp string to parse and normalize.

    Returns:
        ISO 8601 UTC timestamp string.

    Raises:
        ValueError: If ``v`` cannot be parsed as a valid timestamp.
    """
    try:
        return normalize_timestamp(v).isoformat()
    except Exception as e:
        # Broad catch is intentional: normalize_timestamp may raise either
        # stdlib ValueError/TypeError or app.utils.standard.ValidationError.
        # All failures must surface as ValueError for Pydantic field validators.
        msg = f"Invalid timestamp format: {v}"
        raise ValueError(msg) from e


class Symbol(Contract):
    """Canonical Symbol specification details.

    Attributes:
        symbol: Canonical symbol name (e.g. ``EURUSD``).
        broker_symbol: Broker-specific symbol string.
        asset_class: Asset class (forex, commodity, index, crypto, etc.).
        quote_currency: Quote-side currency code.
        base_currency: Base-side currency code.
        precision: Decimal digits in price representation.
        lot_step: Minimum lot increment.
        lot_min: Minimum allowed trade size in lots.
        lot_max: Maximum allowed trade size in lots.
        tick_size: Minimum price fluctuation step.
        tick_value: Monetary value of one tick.
        contract_size: Size of one standard lot contract.
        provider_metadata: Adapter-specific supplemental fields.
    """

    symbol: str = Field(..., description="Canonical symbol name (e.g. EURUSD).")
    broker_symbol: str = Field(
        ..., description="Broker-specific symbol representation."
    )
    asset_class: str = Field(
        ..., description="Asset class (forex, commodity, index, crypto, etc.)."
    )
    quote_currency: str = Field(..., description="Quote currency code.")
    base_currency: str = Field(..., description="Base currency code.")
    precision: int = Field(
        ..., ge=0, description="Decimal digits in price representation."
    )
    lot_step: float = Field(..., gt=0.0, description="Minimum lot increment size.")
    lot_min: float = Field(
        ..., gt=0.0, description="Minimum allowed trade size in lots."
    )
    lot_max: float = Field(
        ..., gt=0.0, description="Maximum allowed trade size in lots."
    )
    tick_size: float = Field(..., gt=0.0, description="Minimum price fluctuation step.")
    tick_value: float = Field(
        ..., gt=0.0, description="Monetary value of one minimum tick."
    )
    contract_size: float = Field(
        ..., gt=0.0, description="Size of one standard lot contract."
    )
    provider_metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Adapter-specific supplemental symbol metadata.",
    )

    @model_validator(mode="after")
    def validate_lot_limits(self) -> Symbol:
        """Enforce that lot_min <= lot_max.

        Returns:
            The validated Symbol instance.

        Raises:
            ValueError: If lot_min exceeds lot_max.
        """
        if self.lot_min > self.lot_max:
            msg = (
                f"lot_min ({self.lot_min}) cannot be "
                f"greater than lot_max ({self.lot_max})."
            )
            raise ValueError(msg)
        return self


class Timeframe(Contract):
    """Canonical Timeframe definition.

    Attributes:
        name: Canonical timeframe identifier (e.g. ``M5``, ``H1``, ``D1``).
        duration_seconds: Duration of the timeframe in seconds.
    """

    name: str = Field(..., description="Canonical timeframe name (e.g. M5, H1, D1).")
    duration_seconds: int = Field(
        ..., gt=0, description="Timeframe duration in seconds."
    )

    @field_validator("name")
    @classmethod
    def validate_timeframe_name(cls, v: str) -> str:
        """Reject unsupported timeframe identifiers.

        Args:
            v: The timeframe string to validate.

        Returns:
            The validated timeframe string.

        Raises:
            ValueError: If ``v`` is not in ``ALLOWED_TIMEFRAMES``.
        """
        if v not in ALLOWED_TIMEFRAMES:
            msg = (
                f"Unsupported timeframe: {v}. "
                f"Must be one of {sorted(ALLOWED_TIMEFRAMES)}"
            )
            raise ValueError(msg)
        return v

    @classmethod
    def from_name(cls, name: str, **kwargs: Any) -> Timeframe:  # noqa: ANN401
        """Construct a Timeframe from its canonical name only.

        Derives ``duration_seconds`` deterministically from the built-in
        lookup table so callers do not need to supply the duration manually.

        Args:
            name: Canonical timeframe identifier (e.g. ``'M5'``, ``'H4'``).
            **kwargs: Additional Contract base fields (e.g. ``schema_version``).

        Returns:
            A fully validated :class:`Timeframe` instance.

        Raises:
            ValueError: If ``name`` is not a supported timeframe.
        """
        if name not in _TIMEFRAME_DURATIONS:
            msg = (
                f"Unsupported timeframe: {name}. "
                f"Must be one of {sorted(ALLOWED_TIMEFRAMES)}"
            )
            raise ValueError(msg)
        return cls(name=name, duration_seconds=_TIMEFRAME_DURATIONS[name], **kwargs)


class Bar(Contract):
    """Canonical representation of a single OHLCV bar.

    Attributes:
        timestamp: UTC ISO 8601 bar open timestamp.
        open: Bar open price.
        high: Bar high price.
        low: Bar low price.
        close: Bar close price.
        volume: Trading volume for the bar period, if available.
        spread: Average or closing spread for the bar period, if available.
        symbol: Canonical symbol name.
        timeframe: Timeframe identifier (e.g. ``M15``, ``H1``).
        source: Provider adapter identifier string.
        source_metadata: Structured provenance metadata for this bar
            (e.g. feed version, normalization flags, quality scores).
    """

    timestamp: str = Field(..., description="UTC ISO 8601 bar open timestamp.")
    open: float = Field(..., gt=0.0, description="Bar open price.")
    high: float = Field(..., gt=0.0, description="Bar high price.")
    low: float = Field(..., gt=0.0, description="Bar low price.")
    close: float = Field(..., gt=0.0, description="Bar close price.")
    volume: float | None = Field(default=None, ge=0.0, description="Trading volume.")
    spread: float | None = Field(
        default=None, ge=0.0, description="Average or end spread."
    )
    symbol: str = Field(..., description="Canonical Symbol name.")
    timeframe: str = Field(..., description="Timeframe name (e.g. M15).")
    source: str = Field(..., description="Provider source adapter identifier.")
    source_metadata: dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Structured provenance metadata for this bar "
            "(e.g. feed version, normalization flags, quality scores)."
        ),
    )

    @field_validator("timestamp")
    @classmethod
    def validate_time(cls, v: str) -> str:
        """Validate and normalize the bar timestamp.

        Args:
            v: Raw timestamp string.

        Returns:
            ISO 8601 UTC timestamp string.

        Raises:
            ValueError: If ``v`` is not a parseable timestamp.
        """
        return _validate_timestamp_iso(v)

    @field_validator("timeframe")
    @classmethod
    def validate_tf(cls, v: str) -> str:
        """Reject unsupported timeframe identifiers.

        Args:
            v: Timeframe string to validate.

        Returns:
            The validated timeframe string.

        Raises:
            ValueError: If ``v`` is not in ``ALLOWED_TIMEFRAMES``.
        """
        if v not in ALLOWED_TIMEFRAMES:
            msg = f"Unsupported timeframe: {v}"
            raise ValueError(msg)
        return v

    @model_validator(mode="after")
    def validate_ohlc(self) -> Bar:
        """Enforce physical OHLC price boundary constraints.

        Returns:
            The validated Bar instance.

        Raises:
            ValueError: If low > high, or open/close are outside [low, high].
        """
        if self.low > self.high:
            msg = (
                f"Low price ({self.low}) cannot be "
                f"greater than High price ({self.high})."
            )
            raise ValueError(msg)
        if self.open > self.high or self.close > self.high:
            raise ValueError("Open and Close prices must not exceed High price.")
        if self.open < self.low or self.close < self.low:
            raise ValueError("Open and Close prices must not fall below Low price.")
        return self


class Tick(Contract):
    """Canonical market tick representation.

    Attributes:
        timestamp: UTC ISO 8601 tick timestamp.
        bid: Best bid price.
        ask: Best ask price.
        last: Last traded price, if available.
        volume: Trade volume at this tick, if available.
        symbol: Canonical symbol name.
        source: Origin source adapter identifier.
    """

    timestamp: str = Field(..., description="UTC ISO 8601 timestamp.")
    bid: float = Field(..., gt=0.0, description="Bid price.")
    ask: float = Field(..., gt=0.0, description="Ask price.")
    last: float | None = Field(default=None, gt=0.0, description="Last trade price.")
    volume: float | None = Field(default=None, ge=0.0, description="Volume size.")
    symbol: str = Field(..., description="Canonical Symbol name.")
    source: str = Field(..., description="Origin source identifier.")

    @field_validator("timestamp")
    @classmethod
    def validate_time(cls, v: str) -> str:
        """Validate and normalize the tick timestamp.

        Args:
            v: Raw timestamp string.

        Returns:
            ISO 8601 UTC timestamp string.

        Raises:
            ValueError: If ``v`` is not a parseable timestamp.
        """
        return _validate_timestamp_iso(v)

    @model_validator(mode="after")
    def validate_tick_prices(self) -> Tick:
        """Enforce ask >= bid price constraint.

        Returns:
            The validated Tick instance.

        Raises:
            ValueError: If ask is less than bid.
        """
        if self.ask < self.bid:
            msg = f"Ask ({self.ask}) cannot be less than Bid ({self.bid})."
            raise ValueError(msg)
        return self


class Spread(Contract):
    """Canonical spread snapshot.

    Attributes:
        bid: Best bid price.
        ask: Best ask price.
        spread_points: Spread size expressed in broker points.
        spread_price: Spread size expressed in price units.
        timestamp: UTC ISO 8601 snapshot timestamp.
        symbol: Symbol name.
        source: Source adapter identifier.
    """

    bid: float = Field(..., gt=0.0, description="Bid price.")
    ask: float = Field(..., gt=0.0, description="Ask price.")
    spread_points: float = Field(
        ..., ge=0.0, description="Spread size in broker points."
    )
    spread_price: float = Field(..., ge=0.0, description="Spread size in price units.")
    timestamp: str = Field(..., description="UTC ISO 8601 timestamp.")
    symbol: str = Field(..., description="Symbol name.")
    source: str = Field(..., description="Source adapter name.")

    @field_validator("timestamp")
    @classmethod
    def validate_time(cls, v: str) -> str:
        """Validate and normalize the spread timestamp.

        Args:
            v: Raw timestamp string.

        Returns:
            ISO 8601 UTC timestamp string.

        Raises:
            ValueError: If ``v`` is not a parseable timestamp.
        """
        return _validate_timestamp_iso(v)

    @model_validator(mode="after")
    def validate_spread_prices(self) -> Spread:
        """Enforce ask >= bid price constraint.

        Returns:
            The validated Spread instance.

        Raises:
            ValueError: If ask is less than bid.
        """
        if self.ask < self.bid:
            msg = f"Ask ({self.ask}) cannot be less than Bid ({self.bid})."
            raise ValueError(msg)
        return self


class DataSlice(Contract):
    """Canonical bounded batch of bars, ticks, or records.

    Carries source, retrieval, transformation, and quality metadata so
    that all downstream consumers can fully reconstruct data provenance.
    """

    bars: list[Bar] = Field(default_factory=list, description="Time series bars batch.")
    ticks: list[Tick] = Field(
        default_factory=list, description="Time series ticks batch."
    )
    symbol: str = Field(..., description="Symbol name.")
    timeframe: str = Field(..., description="Timeframe name (e.g. M5, H1).")
    source: str = Field(..., description="Data source adapter name.")

    # Raw provider data lineage fields
    provider: str = Field(..., description="Originating raw provider name.")
    provider_request_id: str | None = Field(
        default=None, description="Request ID from provider if available."
    )
    retrieved_at: str = Field(
        ..., description="UTC timestamp when data was fetched from provider."
    )
    normalized_at: str = Field(
        ..., description="UTC timestamp when data was normalized."
    )
    transformation_hash: str | None = Field(
        default=None, description="Hash fingerprint of the normalization rule."
    )
    source_hash: str | None = Field(
        default=None, description="SHA256 hash of the original raw payload."
    )

    # Quality metadata
    quality_metadata: dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Data quality indicators such as completeness_ratio, "
            "missing_bars_count, gap_count, or anomaly_flags."
        ),
    )

    @field_validator("timeframe")
    @classmethod
    def validate_timeframe_name(cls, v: str) -> str:
        """Reject unsupported timeframe identifiers.

        Args:
            v: The timeframe string to validate.

        Returns:
            The validated timeframe string.

        Raises:
            ValueError: If ``v`` is not in ``ALLOWED_TIMEFRAMES``.
        """
        if v not in ALLOWED_TIMEFRAMES:
            msg = (
                f"Unsupported timeframe: {v}. "
                f"Must be one of {sorted(ALLOWED_TIMEFRAMES)}"
            )
            raise ValueError(msg)
        return v

    @field_validator("retrieved_at", "normalized_at")
    @classmethod
    def validate_lineage_times(cls, v: str) -> str:
        """Validate and normalize lineage timestamp fields.

        Args:
            v: The timestamp string to validate.

        Returns:
            ISO 8601 UTC timestamp string.

        Raises:
            ValueError: If ``v`` cannot be parsed as a valid timestamp.
        """
        return _validate_timestamp_iso(v)
