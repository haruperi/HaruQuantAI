"""Executable usage demonstration harness for Economic News Evidence."""

from __future__ import annotations

import asyncio

from app.contracts.catalogue.models import InstrumentRef
from app.contracts.data.models import (
    MarketNewsObservation,
    MarketNewsRevision,
    TrackMarketNewsRequest,
    TrackMarketNewsSuccess,
)
from app.services.data.economic_news_evidence.economic_news_evidence import (
    TrackMarketNewsService,
    _generate_uuid7,
    compute_payload_hash,
)


async def _run_usage_scenarios() -> None:
    """Run standalone executable usage scenarios for FEAT-DATA-TRACK_MARKET_NEWS."""
    service = TrackMarketNewsService()
    snap_id = _generate_uuid7()
    obs_id = _generate_uuid7()

    print("Scenario 1: FR-DATA-RECORD_NEWS_OBSERVATIONS - Record observation")
    obs = MarketNewsObservation(
        observation_id=obs_id,
        source_id="FOREX_FACTORY",
        provider_item_id="ff-nfp-2026-08",
        first_seen_at="2026-08-01T00:00:00.000000Z",
        retrieved_at="2026-08-01T00:00:00.000000Z",
        scheduled_at="2026-08-07T12:30:00.000000Z",
        published_at=None,
        scope_currencies=("USD",),
        scope_instruments=(InstrumentRef(instrument_id=_generate_uuid7()),),
        category="Non-Farm Employment Change",
        impact="HIGH",
        language="en",
        payload_hash=compute_payload_hash({"event": "NFP", "source": "FF"}),
    )
    req1 = TrackMarketNewsRequest(
        request_id=_generate_uuid7(),
        capability_snapshot_id=snap_id,
        operation="RECORD",
        observation=obs,
    )
    res1 = await service.track_market_news(req1)
    if isinstance(res1, TrackMarketNewsSuccess) and res1.observation:
        print(f"[OK] Observation recorded: {res1.observation.observation_id}")

    print("\nScenario 2: FR-DATA-VERSION_NEWS_REVISIONS - Version revision")
    rev = MarketNewsRevision(
        revision_id=_generate_uuid7(),
        observation_id=obs_id,
        revision=1,
        kind="VALUES",
        actual="185000",
        forecast="175000",
        previous="160000",
        visible_from="2026-08-07T12:30:01.000000Z",
        content_hash=compute_payload_hash({"actual": 185000, "forecast": 175000}),
    )
    req2 = TrackMarketNewsRequest(
        request_id=_generate_uuid7(),
        capability_snapshot_id=snap_id,
        operation="REVISE",
        revision=rev,
    )
    res2 = await service.track_market_news(req2)
    if isinstance(res2, TrackMarketNewsSuccess) and res2.revision:
        print(f"[OK] Revision versioned: rev {res2.revision.revision}")

    print("\nScenario 3: FR-DATA-QUERY_MARKET_NEWS - Point-in-time query")
    req3 = TrackMarketNewsRequest(
        request_id=_generate_uuid7(),
        capability_snapshot_id=snap_id,
        operation="QUERY",
        as_of="2026-08-08T00:00:00.000000Z",
        from_at="2026-08-01T00:00:00.000000Z",
        to_at="2026-08-10T00:00:00.000000Z",
        source_id="FOREX_FACTORY",
        impact=("HIGH",),
    )
    res3 = await service.track_market_news(req3)
    if isinstance(res3, TrackMarketNewsSuccess):
        cnt = len(res3.observations)
        print(f"[OK] Point-in-time query returned {cnt} observations")

    print("\nScenario 4: FR-DATA-PROJECT_TRADE_RESTRICTIONS - Restriction projection")
    proj = service.project_trade_restrictions(
        as_of="2026-08-07T12:00:00.000000Z",
        from_at="2026-08-07T00:00:00.000000Z",
        to_at="2026-08-07T23:59:59.000000Z",
        currencies=("USD",),
        min_impact="HIGH",
    )
    win_cnt = len(proj.windows)
    print(
        f"[OK] Trade restrictions projected: {win_cnt} windows "
        f"(authorizing={proj.authorizing})"
    )

    print("\nScenario 5: FR-DATA-GOVERN_NETWORK_IMPORTS - Governed network import")
    gov_res = service.govern_network_import(
        source_id="FOREX_FACTORY",
        raw_records=[
            {
                "provider_item_id": "item-101",
                "category": "CPI",
                "api_key": "sample-key-101",  # pragma: allowlist secret
            },
            {
                "provider_item_id": "item-102",
                "category": "FOMC",
                "authorization": "Bearer sample-token-102",  # pragma: allowlist secret
            },
        ],
        license_id="LIC-FF-2026-HARU",
        checkpoint="cp_2026_w32",
    )
    print(
        f"[OK] Network import governed: imported={gov_res.imported_count}, "
        f"rejected={gov_res.rejected_count}"
    )

    print("\nAll usage scenarios completed successfully.")


async def main() -> None:
    """Execute all economic news evidence usage scenarios."""
    await _run_usage_scenarios()


def run_usage_scenarios() -> None:
    """Run all usage scenarios synchronously."""
    asyncio.run(main())


if __name__ == "__main__":
    run_usage_scenarios()
