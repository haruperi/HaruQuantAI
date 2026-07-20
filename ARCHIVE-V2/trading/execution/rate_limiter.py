"""Client-side token-bucket rate limiting primitives.

This module maintains deterministic, per-broker-provider token-bucket rate
limiters driven by an injected :class:`~app.services.trading.state.ports.Clock`
(TRD-FR-123). Rate exhaustion is surfaced as an immediate local block so
callers can short-circuit before dispatching to the broker, avoiding
provider-side penalty limits (TRD-FR-124).
"""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from app.services.trading.contracts import TradingContract
from app.services.trading.security.error_mapping import TradingMappedError
from app.utils.logger import logger

if TYPE_CHECKING:
    from app.services.trading.config.models import RateLimitSettings
    from app.services.trading.state.ports import Clock

MILLISECONDS_PER_SECOND = 1000


class RateLimitDecision(TradingContract):
    """Outcome of one rate-limit acquisition attempt.

    Attributes:
        allowed: Whether the request may proceed to the broker.
        remaining_tokens: Tokens remaining after this decision.
        retry_after_ms: Suggested local wait before retrying, when blocked.
    """

    allowed: bool
    remaining_tokens: Decimal
    retry_after_ms: int | None = None


class TokenBucketRateLimiter:
    """Deterministic token-bucket rate limiter for one broker provider.

    Args:
        settings: Rate-limit settings (max requests, window, burst).
        clock: Injected clock for deterministic elapsed-time reads.
    """

    def __init__(self, *, settings: RateLimitSettings, clock: Clock) -> None:
        """Initialize the token bucket at full burst capacity.

        Args:
            settings: Rate-limit settings (max requests, window, burst).
            clock: Injected clock for deterministic elapsed-time reads.
        """
        logger.info("Initializing token-bucket rate limiter, burst={}.", settings.burst)
        self._settings = settings
        self._clock = clock
        self._tokens = Decimal(settings.burst)
        self._last_refill = clock.monotonic()

    def _refill_rate_per_second(self) -> Decimal:
        """Return the configured token refill rate per second.

        Returns:
            Decimal: Tokens replenished per second.
        """
        logger.debug("Computing rate limiter refill rate per second.")
        return Decimal(self._settings.max_requests) / self._settings.per_seconds

    def _refill(self) -> None:
        """Replenish tokens based on elapsed monotonic time."""
        now = self._clock.monotonic()
        elapsed = now - self._last_refill
        if elapsed <= 0:
            logger.debug("No elapsed time since last refill; skipping.")
            return
        capacity = Decimal(self._settings.burst)
        refill = Decimal(str(elapsed)) * self._refill_rate_per_second()
        self._tokens = min(capacity, self._tokens + refill)
        self._last_refill = now
        logger.debug("Refilled rate limiter tokens to {}.", self._tokens)

    def try_acquire(self, *, cost: Decimal = Decimal(1)) -> RateLimitDecision:
        """Attempt to acquire tokens for one client-side request.

        Args:
            cost: Number of tokens this request consumes.

        Returns:
            RateLimitDecision: Whether the request is locally allowed.

        Raises:
            TradingMappedError: If ``cost`` is not positive.
        """
        logger.info("Attempting to acquire {} rate-limit token(s).", cost)
        if cost <= 0:
            raise TradingMappedError("cost must be positive.", code="INVALID_INPUT")
        self._refill()
        if self._tokens >= cost:
            self._tokens -= cost
            logger.debug("Rate limit token acquired; {} remaining.", self._tokens)
            return RateLimitDecision(allowed=True, remaining_tokens=self._tokens)

        deficit = cost - self._tokens
        refill_rate = self._refill_rate_per_second()
        retry_after_ms = None
        if refill_rate > 0:
            retry_after_ms = int((deficit / refill_rate) * MILLISECONDS_PER_SECOND)
        logger.info("Rate limit exhausted; blocking locally before broker dispatch.")
        return RateLimitDecision(
            allowed=False,
            remaining_tokens=self._tokens,
            retry_after_ms=retry_after_ms,
        )


class ProviderRateLimiterRegistry:
    """Per-broker-provider token-bucket rate limiter registry.

    Args:
        clock: Injected clock shared by every configured provider limiter.
    """

    def __init__(self, *, clock: Clock) -> None:
        """Initialize an empty per-provider rate limiter registry.

        Args:
            clock: Injected clock shared by every configured provider limiter.
        """
        logger.info("Initializing per-provider rate limiter registry.")
        self._clock = clock
        self._limiters: dict[str, TokenBucketRateLimiter] = {}

    def configure_provider(self, *, provider: str, settings: RateLimitSettings) -> None:
        """Configure (or replace) the rate limiter for one provider.

        Args:
            provider: Broker provider name.
            settings: Rate-limit settings for this provider.

        Raises:
            TradingMappedError: If ``provider`` is blank.
        """
        logger.info("Configuring rate limiter for provider {}.", provider)
        if not provider.strip():
            raise TradingMappedError(
                "provider must be non-empty.", code="INVALID_INPUT"
            )
        self._limiters[provider] = TokenBucketRateLimiter(
            settings=settings, clock=self._clock
        )

    def is_configured(self, *, provider: str) -> bool:
        """Return whether a rate limiter is configured for a provider.

        Args:
            provider: Broker provider name.

        Returns:
            bool: True when a limiter is configured for this provider.
        """
        logger.debug("Checking rate limiter configuration for provider {}.", provider)
        return provider in self._limiters

    def try_acquire(
        self, *, provider: str, cost: Decimal = Decimal(1)
    ) -> RateLimitDecision:
        """Attempt to acquire tokens for a request against one provider.

        Args:
            provider: Broker provider name.
            cost: Number of tokens this request consumes.

        Returns:
            RateLimitDecision: Whether the request is locally allowed.

        Raises:
            TradingMappedError: If no limiter is configured for ``provider``.
        """
        logger.info("Requesting rate-limit token for provider {}.", provider)
        limiter = self._limiters.get(provider)
        if limiter is None:
            message = f"No rate limiter configured for provider '{provider}'."
            raise TradingMappedError(message, code="CONFIGURATION_ERROR")
        return limiter.try_acquire(cost=cost)
