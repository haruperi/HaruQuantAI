"""Unit tests for client-side token-bucket rate limiting primitives."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from app.services.trading.config.models import RateLimitSettings
from app.services.trading.execution.rate_limiter import (
    ProviderRateLimiterRegistry,
    TokenBucketRateLimiter,
)
from app.services.trading.security.error_mapping import TradingMappedError


class MutableClock:
    """Test clock with a controllable monotonic value."""

    def __init__(self) -> None:
        """Initialize the clock at monotonic time zero."""
        self.moment = 0.0

    def now_utc(self) -> datetime:
        """Return a fixed UTC timestamp."""
        return datetime(2026, 7, 9, 10, 0, tzinfo=UTC)

    def now_ptp(self) -> datetime:
        """Return a fixed PTP timestamp."""
        return self.now_utc()

    def monotonic(self) -> float:
        """Return the controllable monotonic value."""
        return self.moment


def _settings(**overrides: object) -> RateLimitSettings:
    defaults: dict[str, object] = {
        "max_requests": 10,
        "per_seconds": Decimal("1.0"),
        "burst": 5,
    }
    defaults.update(overrides)
    return RateLimitSettings(**defaults)  # type: ignore[arg-type]


def test_try_acquire_consumes_tokens_up_to_burst() -> None:
    """Requests are allowed up to the configured burst capacity."""
    clock = MutableClock()
    limiter = TokenBucketRateLimiter(settings=_settings(burst=3), clock=clock)
    results = [limiter.try_acquire() for _ in range(3)]
    exhausted = limiter.try_acquire()
    assert all(result.allowed for result in results)
    assert exhausted.allowed is False
    assert exhausted.retry_after_ms is not None


def test_try_acquire_rejects_non_positive_cost() -> None:
    """try_acquire rejects a non-positive cost."""
    clock = MutableClock()
    limiter = TokenBucketRateLimiter(settings=_settings(), clock=clock)
    with pytest.raises(TradingMappedError):
        limiter.try_acquire(cost=Decimal(0))


def test_refill_replenishes_tokens_over_elapsed_time() -> None:
    """Tokens refill deterministically as monotonic time advances."""
    clock = MutableClock()
    limiter = TokenBucketRateLimiter(
        settings=_settings(max_requests=10, per_seconds=Decimal("1.0"), burst=1),
        clock=clock,
    )
    first = limiter.try_acquire()
    immediate_retry = limiter.try_acquire()
    clock.moment = 1.0
    after_refill = limiter.try_acquire()
    assert first.allowed is True
    assert immediate_retry.allowed is False
    assert after_refill.allowed is True


def test_refill_caps_tokens_at_burst_capacity() -> None:
    """Refill never exceeds the configured burst capacity."""
    clock = MutableClock()
    limiter = TokenBucketRateLimiter(
        settings=_settings(max_requests=100, per_seconds=Decimal("1.0"), burst=2),
        clock=clock,
    )
    clock.moment = 100.0
    decision = limiter.try_acquire(cost=Decimal(2))
    assert decision.allowed is True
    assert decision.remaining_tokens == Decimal(0)


def test_registry_requires_configured_provider() -> None:
    """The registry fails closed for an unconfigured provider."""
    clock = MutableClock()
    registry = ProviderRateLimiterRegistry(clock=clock)
    assert registry.is_configured(provider="mt5") is False
    with pytest.raises(TradingMappedError):
        registry.try_acquire(provider="mt5")


def test_registry_configure_provider_rejects_blank_name() -> None:
    """configure_provider rejects a blank provider name."""
    clock = MutableClock()
    registry = ProviderRateLimiterRegistry(clock=clock)
    with pytest.raises(TradingMappedError):
        registry.configure_provider(provider=" ", settings=_settings())


def test_registry_configure_and_acquire() -> None:
    """A configured provider allows acquisition through the registry."""
    clock = MutableClock()
    registry = ProviderRateLimiterRegistry(clock=clock)
    registry.configure_provider(provider="mt5", settings=_settings(burst=1))
    assert registry.is_configured(provider="mt5") is True
    decision = registry.try_acquire(provider="mt5")
    assert decision.allowed is True
