"""Point-in-time market-news evidence for ``FEAT-DATA-TRACK_MARKET_NEWS``.

Observations and revisions are append-only evidence. Queries expose only observations
that were already known at the requested ``as_of`` instant; later cancellations and
revisions never leak backward. Coverage requests fail closed because the current v1
contract has no source-coverage manifest from which completeness could be proven.
"""

from __future__ import annotations

import asyncio
from datetime import timedelta

from app.contracts.common.models import ProblemDetails
from app.contracts.data.errors import DataFailure
from app.contracts.data.models import (
    TrackMarketNewsRequest,
    TrackMarketNewsSuccess,
)
from app.kernel.time import parse_utc_timestamp
from app.services.data.track_market_news.news_store import MarketNewsStore


def _failure(
    request_id: str,
    *,
    code: str,
    detail: str,
    status: int = 422,
) -> DataFailure:
    """Build one stable market-news failure.

    Args:
        request_id: Public request identity.
        code: Closed Data failure code.
        detail: Safe failure detail.
        status: HTTP-style problem status.

    Returns:
        Contract-native Data failure.
    """
    return DataFailure(
        request_id=request_id,
        code=code,  # type: ignore[arg-type]
        problem=ProblemDetails(
            status=status,
            code=code,
            detail=detail,
            request_id=request_id,
        ),
    )


class TrackMarketNewsService:
    """Capability implementation for point-in-time market-news evidence."""

    def __init__(self, store: MarketNewsStore) -> None:
        """Initialize the service with feature-owned persistence.

        Args:
            store: Market-news persistence adapter.
        """
        self._store = store

    async def track_market_news(
        self,
        request: TrackMarketNewsRequest,
    ) -> TrackMarketNewsSuccess | DataFailure:
        """Record, revise, or query market-news evidence.

        Args:
            request: Operation-discriminated market-news request.

        Returns:
            Contract-native success or deterministic failure.
        """
        if request.operation == "RECORD":
            assert request.observation is not None
            await self._store.record_observation(request.observation)
            return TrackMarketNewsSuccess(
                request_id=request.request_id,
                observation=request.observation,
            )

        if request.operation == "REVISE":
            assert request.revision is not None
            recorded = await self._store.record_revision(request.revision)
            if not recorded:
                return _failure(
                    request.request_id,
                    code="DATA_NOT_FOUND",
                    detail="Referenced market-news observation is not available",
                    status=404,
                )
            return TrackMarketNewsSuccess(
                request_id=request.request_id,
                revision=request.revision,
            )

        assert request.as_of is not None
        assert request.from_at is not None
        assert request.to_at is not None
        if request.require_complete_coverage:
            return _failure(
                request.request_id,
                code="DATA_COVERAGE_INCOMPLETE",
                detail=(
                    "Complete market-news coverage cannot be proven because the v1 "
                    "request does not identify a source coverage manifest"
                ),
            )
        observations = await self._store.query(
            as_of=request.as_of,
            from_at=request.from_at,
            to_at=request.to_at,
            source_id=request.source_id,
            category=request.category,
            language=request.language,
            impact=request.impact,
        )
        if request.freshness_limit_seconds is not None:
            as_of = parse_utc_timestamp(request.as_of)
            limit = timedelta(seconds=request.freshness_limit_seconds)
            stale = tuple(
                observation
                for observation in observations
                if as_of - parse_utc_timestamp(observation.retrieved_at) > limit
            )
            if stale:
                return _failure(
                    request.request_id,
                    code="DATA_COVERAGE_INCOMPLETE",
                    detail="Stored market-news evidence exceeds the requested freshness limit",
                )
        return TrackMarketNewsSuccess(
            request_id=request.request_id,
            observations=observations,
        )


async def _demo() -> None:
    """Demonstrate the point-in-time contract shape with a temporary store."""
    import tempfile
    from pathlib import Path

    from app.contracts.data.models import MarketNewsObservation, MarketNewsRevision
    from app.kernel.identity import generate_uuid7

    with tempfile.TemporaryDirectory() as temporary_directory:
        service = TrackMarketNewsService(
            MarketNewsStore(Path(temporary_directory) / "news.sqlite3")
        )
        observation = MarketNewsObservation(
            observation_id=generate_uuid7(),
            source_id="demo.calendar",
            provider_item_id="cpi-1",
            first_seen_at="2026-01-01T08:00:00.000000Z",
            retrieved_at="2026-01-01T08:00:00.000000Z",
            scheduled_at="2026-01-01T13:30:00.000000Z",
            category="CPI",
            impact="HIGH",
            language="en",
            payload_hash="0" * 64,
        )
        await service.track_market_news(
            TrackMarketNewsRequest(
                request_id=generate_uuid7(),
                capability_snapshot_id=generate_uuid7(),
                operation="RECORD",
                observation=observation,
            )
        )
        await service.track_market_news(
            TrackMarketNewsRequest(
                request_id=generate_uuid7(),
                capability_snapshot_id=generate_uuid7(),
                operation="REVISE",
                revision=MarketNewsRevision(
                    revision_id=generate_uuid7(),
                    observation_id=observation.observation_id,
                    revision=1,
                    kind="CANCELLATION",
                    visible_from="2026-01-01T10:00:00.000000Z",
                    content_hash="1" * 64,
                ),
            )
        )
        before = await service.track_market_news(
            TrackMarketNewsRequest(
                request_id=generate_uuid7(),
                capability_snapshot_id=generate_uuid7(),
                operation="QUERY",
                as_of="2026-01-01T09:00:00.000000Z",
                from_at="2026-01-01T00:00:00.000000Z",
                to_at="2026-01-02T00:00:00.000000Z",
            )
        )
        print(before.model_dump(mode="json"))


if __name__ == "__main__":
    asyncio.run(_demo())
