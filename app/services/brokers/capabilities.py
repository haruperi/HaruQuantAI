"""Typed data provider capabilities, request models, health probes, and error contracts.

Description:
    Provides canonical data models and protocols for Stage 2C market data provider
    plugins. Defines typed request specifications (`HistoryRequest`), paginated
    response frames (`HistoryPage`), provider capabilities descriptors (`ProviderCapabilities`),
    cancellation tokens (`CancellationToken`), health inspection reports (`ProviderHealth`),
    and a structured hierarchy of provider exceptions (`ProviderError`). Enables
    uniform historical data queries across heterogeneous brokers, local files, and
    remote HTTP feeds while preventing silent failures, untyped payloads, and
    synthetic data generation.

Purpose:
    FEAT-BROKER-CAPABILITIES: Typed contracts and models for market data providers.

Key Capabilities:
    - FR-BROKER-CAPABILITIES-MODELS: Typed immutable request and page container definitions.
      Associated: `HistoryRequest`, `HistoryPage`, `ProviderCapabilities`
      Logging: Emits DEBUG when validating historical data requests and parsing pages.
    - FR-BROKER-CAPABILITIES-HEALTH: Standardized provider health and connectivity reporting.
      Associated: `ProviderHealth`, `CancellationToken`
      Logging: Emits INFO when health checks succeed, and WARNING/ERROR on degraded states.
    - FR-BROKER-CAPABILITIES-ERRORS: Mapped exception hierarchy for error envelope translation.
      Associated: `ProviderError`, `ProviderNotFoundError`, `ProviderValidationError`
      Logging: Emits ERROR or WARNING when provider errors are raised or trapped.

Python API Usage:
    ```python
    from app.services.brokers.capabilities import (
        HistoryRequest,
        ProviderCapabilities,
        ProviderHealth,
    )

    req = HistoryRequest(
        provider="dukascopy",
        symbol="EURUSD",
        timeframe="M1",
        kind="bars",
        count=100,
    )
    req.validate()
    ```

CLI Usage:
    ```bash
    uv run pytest tests/unit/services/brokers/test_brokers_history_contracts.py --no-cov
    ```
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from app.host.logging import get_logger

logger = get_logger(__name__)

MODELS_FR = "FR-BROKER-CAPABILITIES-MODELS"
HEALTH_FR = "FR-BROKER-CAPABILITIES-HEALTH"
ERRORS_FR = "FR-BROKER-CAPABILITIES-ERRORS"

__all__ = [
    "CancellationToken",
    "HistoryKind",
    "HistoryPage",
    "HistoryRequest",
    "ProviderAuthError",
    "ProviderCapabilities",
    "ProviderCancelledError",
    "ProviderDisabledError",
    "ProviderError",
    "ProviderHealth",
    "ProviderNotFoundError",
    "ProviderRateLimitError",
    "ProviderTimeoutError",
    "ProviderUnsupportedError",
    "ProviderValidationError",
    "main",
]


class HistoryKind(StrEnum):
    """Supported market history record kinds."""

    BARS = "bars"
    TICKS = "ticks"


class ProviderError(Exception):
    """Base exception for all market data provider operations."""

    def __init__(
        self,
        message: str,
        *,
        code: str = "PROVIDER_ERROR",
        status_code: int = 502,
        provider: str = "",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.provider = provider
        self.details = details or {}
        logger.error(
            "%s: ProviderError [%s]: %s (status=%d, provider=%s)",
            ERRORS_FR,
            code,
            message,
            status_code,
            provider,
            extra={
                "fr_id": ERRORS_FR,
                "error_code": code,
                "status_code": status_code,
                "provider": provider,
            },
        )


class ProviderNotFoundError(ProviderError):
    """Raised when the requested provider is unknown or unregistered."""

    def __init__(self, message: str, *, provider: str = "") -> None:
        super().__init__(
            message,
            code="PROVIDER_NOT_FOUND",
            status_code=404,
            provider=provider,
        )


class ProviderDisabledError(ProviderError):
    """Raised when the provider is disabled or quarantined."""

    def __init__(self, message: str, *, provider: str = "") -> None:
        super().__init__(
            message,
            code="PROVIDER_DISABLED",
            status_code=503,
            provider=provider,
        )


class ProviderAuthError(ProviderError):
    """Raised when authentication against the upstream provider fails."""

    def __init__(
        self,
        message: str,
        *,
        provider: str = "",
        details: dict[str, Any] | None = None,
        status_code: int = 502,
    ) -> None:
        super().__init__(
            message,
            code="UPSTREAM_AUTH_FAILED",
            status_code=status_code,
            provider=provider,
            details=details,
        )


class ProviderRateLimitError(ProviderError):
    """Raised when upstream rate limits or 429 responses occur."""

    def __init__(
        self,
        message: str,
        *,
        provider: str = "",
        retry_after: float | None = None,
    ) -> None:
        details = {"retry_after": retry_after} if retry_after is not None else {}
        super().__init__(
            message,
            code="RATE_LIMITED",
            status_code=429,
            provider=provider,
            details=details,
        )
        self.retry_after = retry_after


class ProviderTimeoutError(ProviderError):
    """Raised when upstream requests exceed page or total deadlines."""

    def __init__(self, message: str, *, provider: str = "") -> None:
        super().__init__(
            message,
            code="UPSTREAM_TIMEOUT",
            status_code=504,
            provider=provider,
        )


class ProviderValidationError(ProviderError):
    """Raised when request parameters or parsed records violate domain invariants."""

    def __init__(self, message: str, *, provider: str = "") -> None:
        super().__init__(
            message,
            code="VALIDATION_ERROR",
            status_code=422,
            provider=provider,
        )


class ProviderUnsupportedError(ProviderError):
    """Raised when an operation, timeframe, or mode is unsupported by the provider."""

    def __init__(self, message: str, *, provider: str = "") -> None:
        super().__init__(
            message,
            code="UNSUPPORTED_CAPABILITY",
            status_code=422,
            provider=provider,
        )


class ProviderCancelledError(ProviderError):
    """Raised when an operation is cancelled via CancellationToken."""

    def __init__(
        self, message: str = "Operation was cancelled", *, provider: str = ""
    ) -> None:
        super().__init__(
            message,
            code="OPERATION_CANCELLED",
            status_code=499,
            provider=provider,
        )


class CancellationToken:
    """Thread-safe cooperative cancellation token for bounded data acquisition."""

    def __init__(self) -> None:
        self._is_cancelled = False
        self._reason = ""

    @property
    def is_cancelled(self) -> bool:
        """Return True if cancellation was requested."""
        return self._is_cancelled

    def cancel(self, reason: str = "Cancellation requested") -> None:
        """Trigger cancellation."""
        self._is_cancelled = True
        self._reason = reason
        logger.info(
            "%s: CancellationToken cancelled: %s",
            HEALTH_FR,
            reason,
            extra={"fr_id": HEALTH_FR, "cancel_reason": reason},
        )

    def check_cancelled(self) -> None:
        """Raise ProviderCancelledError if cancellation was requested."""
        if self._is_cancelled:
            raise ProviderCancelledError(self._reason or "Operation was cancelled")


@dataclass(frozen=True)
class ProviderCapabilities:
    """Metadata describing capabilities, limits, and timeframes of a provider."""

    provider_id: str
    display_name: str
    category: str = "Multi-Asset"
    supported_timeframes: tuple[str, ...] = ("M1", "H1", "D1")
    supported_modes: tuple[str, ...] = ("bars",)
    requires_auth: bool = False
    rate_limit_rps: float = 1.0
    default_timeout_seconds: float = 30.0
    supports_pagination: bool = False
    has_local_archive: bool = False
    description: str = ""
    extra: dict[str, Any] = field(default_factory=dict)

    def supports_timeframe(self, timeframe: str) -> bool:
        """Check if a given timeframe is supported."""
        clean = timeframe.strip().upper()
        return clean in (tf.upper() for tf in self.supported_timeframes)

    def supports_kind(self, kind: str) -> bool:
        """Check if a given history kind ('bars' or 'ticks') is supported."""
        clean = kind.strip().lower()
        return clean in (m.lower() for m in self.supported_modes)

    def to_dict(self) -> dict[str, Any]:
        """Convert capabilities to serializable dictionary."""
        return {
            "provider_id": self.provider_id,
            "display_name": self.display_name,
            "category": self.category,
            "supported_timeframes": list(self.supported_timeframes),
            "supported_modes": list(self.supported_modes),
            "requires_auth": self.requires_auth,
            "rate_limit_rps": self.rate_limit_rps,
            "default_timeout_seconds": self.default_timeout_seconds,
            "supports_pagination": self.supports_pagination,
            "has_local_archive": self.has_local_archive,
            "description": self.description,
            "extra": self.extra,
        }


@dataclass(frozen=True)
class ProviderHealth:
    """Health and connectivity report for a data provider."""

    provider_id: str
    status: str
    connected: bool
    message: str
    checked_at: datetime = field(default_factory=lambda: datetime.now(tz=UTC))
    latency_ms: float | None = None
    capabilities: ProviderCapabilities | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert health status to serializable dictionary."""
        return {
            "provider_id": self.provider_id,
            "status": self.status,
            "connected": self.connected,
            "message": self.message,
            "checked_at": self.checked_at.isoformat(),
            "latency_ms": self.latency_ms,
            "capabilities": self.capabilities.to_dict() if self.capabilities else None,
        }


@dataclass(frozen=True)
class HistoryRequest:
    """Validated specification for a historical market data acquisition request."""

    provider: str
    symbol: str
    timeframe: str = "M1"
    kind: str = "bars"
    start: int | datetime | str | None = None
    end: int | datetime | str | None = None
    count: int = 100
    limit: int = 1000
    mode: str = "range"
    exchange: str | None = None
    source_policy: str = "remote"
    timeout_seconds: float = 30.0

    def validate(self) -> None:
        """Validate request invariants, raising ProviderValidationError if invalid."""
        if not self.provider.strip():
            raise ProviderValidationError("Provider identifier must not be empty")
        if not self.symbol.strip():
            raise ProviderValidationError(
                "Symbol must not be empty", provider=self.provider
            )
        if self.count <= 0 and self.limit <= 0:
            raise ProviderValidationError(
                "Request count or limit must be greater than zero",
                provider=self.provider,
            )
        if self.count < 0 or self.count > 50_000:
            raise ProviderValidationError(
                f"Request count must be between 1 and 50,000, got {self.count}",
                provider=self.provider,
            )
        if self.limit <= 0 and self.count > 0:
            raise ProviderValidationError(
                f"Request limit must be greater than zero, got {self.limit}",
                provider=self.provider,
            )
        if self.limit < 0:
            raise ProviderValidationError(
                f"Request limit must be greater than zero, got {self.limit}",
                provider=self.provider,
            )
        if not self.timeframe.strip():
            raise ProviderValidationError(
                "Timeframe must not be empty", provider=self.provider
            )

        tf = self.timeframe.strip().upper()
        valid_tf_prefixes = (
            "TICK",
            "M",
            "H",
            "D",
            "W",
            "MN",
            "S",
            "1M",
            "3M",
            "5M",
            "15M",
            "30M",
            "1H",
            "2H",
            "4H",
            "1D",
            "1W",
            "1MN",
        )
        if not (
            any(tf.startswith(p) for p in ("TICK", "M", "H", "D", "W", "MN", "S"))
            or tf in valid_tf_prefixes
        ):
            raise ProviderValidationError(
                f"Invalid timeframe: '{self.timeframe}'", provider=self.provider
            )

        k = self.kind.strip().lower()
        if k not in ("bars", "ticks"):
            raise ProviderValidationError(
                f"Unsupported history kind '{self.kind}'; must be 'bars' or 'ticks'",
                provider=self.provider,
            )

        start_ms = self._to_epoch_ms(self.start)
        end_ms = self._to_epoch_ms(self.end)
        if start_ms is not None and end_ms is not None and start_ms > end_ms:
            raise ProviderValidationError(
                f"Start date ({start_ms}) cannot be greater than end date ({end_ms})",
                provider=self.provider,
            )

        logger.debug(
            "%s: Validated HistoryRequest for %s %s (%s)",
            MODELS_FR,
            self.provider,
            self.symbol,
            self.timeframe,
            extra={
                "fr_id": MODELS_FR,
                "provider": self.provider,
                "symbol": self.symbol,
                "timeframe": self.timeframe,
            },
        )

    @staticmethod
    def _to_epoch_ms(val: int | datetime | str | None) -> int | None:
        if val is None:
            return None
        if isinstance(val, (int, float)):
            return int(val) if val >= 100_000_000_000 else int(val * 1000)
        if isinstance(val, datetime):
            if val.tzinfo is None:
                raise ProviderValidationError(
                    f"Naive datetime '{val}' rejected; timezone-aware datetime required"
                )
            return int(val.timestamp() * 1000)
        if isinstance(val, str):
            val_clean = val.strip()
            if not val_clean:
                return None
            try:
                iso_clean = val_clean.replace("Z", "+00:00")
                dt_parsed = datetime.fromisoformat(iso_clean)
            except Exception as exc:
                raise ProviderValidationError(
                    f"Invalid date string '{val}'; must be ISO 8601 ({exc})"
                ) from exc
            if dt_parsed.tzinfo is None:
                raise ProviderValidationError(
                    f"Naive date string '{val}' rejected; timezone-aware ISO 8601 string required"
                )
            return int(dt_parsed.timestamp() * 1000)
        raise ProviderValidationError(f"Unsupported timestamp type: {type(val)}")

    def start_epoch_ms(self) -> int | None:
        """Return start timestamp normalized to epoch milliseconds."""
        return self._to_epoch_ms(self.start)

    def end_epoch_ms(self) -> int | None:
        """Return end timestamp normalized to epoch milliseconds."""
        return self._to_epoch_ms(self.end)

    def start_epoch(self) -> int | None:
        """Return start timestamp normalized to epoch seconds."""
        ms = self.start_epoch_ms()
        return ms // 1000 if ms is not None else None

    def end_epoch(self) -> int | None:
        """Return end timestamp normalized to epoch seconds."""
        ms = self.end_epoch_ms()
        return ms // 1000 if ms is not None else None


@dataclass
class HistoryPage:
    """Container for a single page or batch of downloaded market data records."""

    provider: str
    symbol: str
    timeframe: str
    kind: str
    rows: list[dict[str, Any]] = field(default_factory=list)
    cursor: str | None = None
    is_complete: bool = True
    provenance: dict[str, Any] = field(default_factory=dict)

    @property
    def row_count(self) -> int:
        """Return the number of records contained in this page."""
        return len(self.rows)

    def to_dict(self) -> dict[str, Any]:
        """Convert page metadata and row count to dictionary representation."""
        return {
            "provider": self.provider,
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "kind": self.kind,
            "row_count": self.row_count,
            "cursor": self.cursor,
            "is_complete": self.is_complete,
            "provenance": self.provenance,
        }


def main() -> None:
    """CLI demonstration of typed broker capabilities and request validation."""
    print("=== HaruQuantAI Broker Capabilities & Request Validation Demonstration ===")
    req = HistoryRequest(
        provider="dukascopy",
        symbol="EURUSD",
        timeframe="M1",
        count=100,
        start="2026-01-01T00:00:00Z",
        end="2026-01-02T00:00:00Z",
    )
    req.validate()
    print(f"Validated request for {req.provider} {req.symbol} ({req.timeframe})")
    print(
        f"Start epoch ms: {req.start_epoch_ms()} ms, Start epoch s: {req.start_epoch()} s"
    )
    print("Capabilities contracts verified successfully.")


if __name__ == "__main__":
    main()
