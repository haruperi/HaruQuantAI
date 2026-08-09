"""Injected Strategy and Risk expectancy provider adapters."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from datetime import datetime
from decimal import Decimal

from app.services.research.expectancy.contracts import parse_approved_expectancy_profile
from app.services.research.expectancy.governance import get_min_reward_risk_override

type ProfileLoader = Callable[[str], Mapping[str, object] | None]


def build_strategy_expectancy_provider(
    *, profile_loader: ProfileLoader, now_provider: Callable[[], datetime]
) -> Callable[[Mapping[str, object]], Mapping[str, object]]:
    """Build Strategy's exact-version expectancy provider.

    Args:
        profile_loader: Injected profile lookup by profile identity.
        now_provider: Injected UTC clock.

    Returns:
        Provider callable accepted by Strategy.
    """

    def _provider(reference: Mapping[str, object]) -> Mapping[str, object]:
        profile = profile_loader(str(reference["profile_id"]))
        if profile is None:
            return {"status": "NOT_ELIGIBLE"}
        parsed = parse_approved_expectancy_profile(profile)
        active = get_min_reward_risk_override(
            parsed,
            strategy_ref=str(parsed["strategy_ref"]),
            now_utc=now_provider(),
        )
        status = (
            "ELIGIBLE"
            if active is not None
            and parsed["exact_version"] == reference.get("exact_version")
            else "NOT_ELIGIBLE"
        )
        return {
            "status": status,
            "profile_id": parsed["profile_id"],
            "exact_version": parsed["exact_version"],
        }

    return _provider


def build_risk_expectancy_provider(
    *, profile_loader: ProfileLoader, now_provider: Callable[[], datetime]
) -> Callable[[str], Decimal | None]:
    """Build Risk's reward/risk override provider.

    Args:
        profile_loader: Injected profile lookup by strategy identity.
        now_provider: Injected UTC clock.

    Returns:
        Provider callable accepted by Risk.
    """

    def _provider(strategy_ref: str) -> Decimal | None:
        profile = profile_loader(strategy_ref)
        if profile is None:
            return None
        parsed = parse_approved_expectancy_profile(profile)
        return get_min_reward_risk_override(
            parsed, strategy_ref=strategy_ref, now_utc=now_provider()
        )

    return _provider


__all__ = ("build_risk_expectancy_provider", "build_strategy_expectancy_provider")
