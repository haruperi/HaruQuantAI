"""Production-like snapshot feed assembly for shadow workflows.

Classes and functions:
    ShadowDataFeed: Class. Provides ShadowDataFeed behavior for execution workflows.
    build_shadow_data_feed: Function. Provides build_shadow_data_feed behavior for execution workflows.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.services.risk.domain.snapshot import (
    AccountSnapshot,
    MarketSnapshot,
    PortfolioSnapshot,
)


@dataclass(frozen=True)
class ShadowDataFeed:
    """Normalized shadow workflow feed built from live-shaped snapshots."""

    account_snapshot_ref: str
    portfolio_snapshot_ref: str
    market_snapshot_ref: str
    environment: str
    payload: dict[str, object]


def build_shadow_data_feed(
    *,
    account_snapshot: AccountSnapshot,
    portfolio_snapshot: PortfolioSnapshot,
    market_snapshot: MarketSnapshot,
    environment: str = "shadow",
) -> ShadowDataFeed:
    """Package production-like snapshots into one shadow workflow feed payload."""
    return ShadowDataFeed(
        account_snapshot_ref=account_snapshot.snapshot_id,
        portfolio_snapshot_ref=portfolio_snapshot.snapshot_id,
        market_snapshot_ref=market_snapshot.snapshot_id,
        environment=environment,
        payload={
            "account": account_snapshot.model_dump(mode="json"),
            "portfolio": portfolio_snapshot.model_dump(mode="json"),
            "market": market_snapshot.model_dump(mode="json"),
        },
    )
