"""Economic Calendar and News Evidence domain service implementation.

Purpose:
    Ingest, normalize, and query economic news events with point-in-time
    revision tracking, source attribution, and payload validation.

Key capabilities:
    * Query point-in-time economic releases and revisions.
    * Ingest macroeconomic events with rate limiting and freshness guarantees.
    * Enforce allowed source provenance and SHA-256 payload integrity.
    * Provide async track_market_news implementing TrackMarketNewsCapability.

Python API usage:
    from app.services.data.economic_news_evidence.economic_news_evidence import (
        EconomicNewsEvidenceService,
    )
    from app.contracts.data.models import TrackMarketNewsRequest

    service = EconomicNewsEvidenceService()
    result = await service.track_market_news(request)

CLI usage:
    uv run python -m app.services.data.economic_news_evidence.economic_news_evidence
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import re
import time
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any, Final, Literal, override

from app.contracts.common.models import (
    ContentHash,
    CurrencyCode,
    ProblemDetails,
    UtcTimestamp,
    Uuid7,
)
from app.contracts.data.errors import DataFailure, DataFailureCode
from app.contracts.data.models import (
    MarketNewsObservation,
    MarketNewsRevision,
    NewsImpact,
    TrackMarketNewsRequest,
    TrackMarketNewsSuccess,
)
from app.contracts.data.ports import TrackMarketNewsCapability
from app.services.data.economic_news_evidence.config import (
    EconomicNewsEvidenceConfig,
)

if TYPE_CHECKING:
    from app.kernel.events import EventBus

logger = logging.getLogger(__name__)

_UUID7_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
)
_SHA256_PATTERN: Final[re.Pattern[str]] = re.compile(r"^[0-9a-f]{64}$")
_RATE_LIMIT_WINDOW_SECONDS: Final[float] = 60.0


def _generate_uuid7() -> Uuid7:
    """Generate a canonical UUIDv7 string.

    Returns:
        UUIDv7 string formatted per RFC 9562.
    """
    return str(uuid.uuid7())


def _is_valid_uuid7(val: str) -> bool:
    """Check if a string is a valid UUIDv7 format.

    Args:
        val: String representation of UUID.

    Returns:
        True if valid UUIDv7, False otherwise.
    """
    return bool(_UUID7_PATTERN.match(val))


def _is_valid_sha256(val: str) -> bool:
    """Check if a string is a 64-character lowercase hex SHA-256 hash.

    Args:
        val: String representation of hash.

    Returns:
        True if valid 64-char hex string, False otherwise.
    """
    return bool(_SHA256_PATTERN.match(val))


def _parse_utc(val: UtcTimestamp) -> datetime:
    """Parse an ISO 8601 UTC timestamp string into an aware datetime in UTC.

    Args:
        val: ISO 8601 UTC string (e.g. ending in 'Z' or '+00:00').

    Returns:
        Timezone-aware datetime in UTC.
    """
    s = val[:-1] + "+00:00" if val.endswith("Z") else val
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def _format_utc(dt: datetime) -> UtcTimestamp:
    """Format an aware UTC datetime into canonical ISO 8601 UTC string.

    Args:
        dt: Aware datetime.

    Returns:
        Canonical UTC timestamp string with trailing 'Z'.
    """
    utc_dt = dt.astimezone(UTC)
    return utc_dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def compute_payload_hash(payload: object) -> ContentHash:
    """Compute a deterministic SHA-256 hash of a JSON-serializable payload.

    Args:
        payload: Arbitrary data object.

    Returns:
        64-character lowercase hexadecimal hash.
    """
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _make_failure(
    request_id: str,
    code: DataFailureCode,
    error_type: str,
    title: str,
    detail: str,
    *,
    status: int = 422,
) -> DataFailure:
    """Construct a well-formed DataFailure with valid UUIDv7 identifiers.

    Args:
        request_id: Candidate request ID.
        code: Typed machine-readable data error code.
        error_type: URN error type.
        title: Short error title.
        detail: Human-readable error detail.
        status: HTTP status code (400-599).

    Returns:
        Structured DataFailure instance.
    """
    req_uuid7 = request_id if _is_valid_uuid7(request_id) else _generate_uuid7()
    return DataFailure(
        request_id=req_uuid7,
        code=code,
        problem=ProblemDetails(
            type=error_type,
            title=title,
            status=status,
            code=code,
            detail=detail,
            request_id=req_uuid7,
        ),
        outcome="FAILURE",
    )


@dataclass(frozen=True)
class RestrictionWindow:
    """Non-authorizing trade restriction window evidence around a news event."""

    event_id: str
    event_title: str
    currency: str
    impact: str
    window_start: UtcTimestamp
    window_end: UtcTimestamp
    buffer_minutes_before: int
    buffer_minutes_after: int


@dataclass(frozen=True)
class TradeRestrictionProjection:
    """Versioned non-authorizing restriction-evidence projection.

    The projection never places, cancels, or approves an order.
    """

    projection_id: str
    as_of: UtcTimestamp
    from_at: UtcTimestamp
    to_at: UtcTimestamp
    windows: tuple[RestrictionWindow, ...]
    uncertainty: bool
    evidence_refs: tuple[str, ...]
    authorizing: Literal[False] = False


@dataclass(frozen=True)
class ImportGovernanceResult:
    """Result of network acquisition governance and payload validation."""

    source_id: str
    imported_count: int
    rejected_count: int
    findings: tuple[str, ...]
    checkpoint: str | None
    content_hash: ContentHash


class TrackMarketNewsService(TrackMarketNewsCapability):
    """Domain service for Economic Calendar and News Evidence."""

    def __init__(
        self,
        config: EconomicNewsEvidenceConfig | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        """Initialize the economic news evidence service.

        Args:
            config: Optional service configuration.
            event_bus: Optional kernel event bus for event publication.
        """
        self._config = config or EconomicNewsEvidenceConfig()
        self._event_bus = event_bus
        self._observations: dict[str, MarketNewsObservation] = {}
        self._source_index: dict[tuple[str, str], str] = {}
        self._revisions: dict[str, list[MarketNewsRevision]] = {}
        self._rate_limits: dict[str, list[float]] = {}
        self._checkpoints: dict[str, str] = {}

    @property
    def config(self) -> EconomicNewsEvidenceConfig:
        """Return the active service configuration.

        Returns:
            Current EconomicNewsEvidenceConfig instance.
        """
        return self._config

    @override
    async def track_market_news(
        self,
        request: TrackMarketNewsRequest,
    ) -> TrackMarketNewsSuccess | DataFailure:
        """Record observations, revise versions, and execute queries.

        Args:
            request: Operation-discriminated market news request.

        Returns:
            TrackMarketNewsSuccess on success, otherwise DataFailure.
        """
        match request.operation:
            case "RECORD":
                return await self._record_observation(request)
            case "REVISE":
                return await self._revise_observation(request)
            case "QUERY":
                return await self._query_news(request)

    async def _record_observation(
        self,
        request: TrackMarketNewsRequest,
    ) -> TrackMarketNewsSuccess | DataFailure:
        """Record a newly observed economic news observation.

        Args:
            request: TrackMarketNewsRequest with operation RECORD.

        Returns:
            TrackMarketNewsSuccess with recorded observation or DataFailure.
        """
        obs = request.observation
        if obs is None:
            return _make_failure(
                request.request_id,
                "DATA_VALIDATION_FAILED",
                "urn:haruquant:data:missing-observation",
                "Missing observation",
                "RECORD operation requires an observation",
            )

        if not _is_valid_sha256(obs.payload_hash):
            return _make_failure(
                request.request_id,
                "DATA_VALIDATION_FAILED",
                "urn:haruquant:data:invalid-payload-hash",
                "Invalid payload hash",
                "payload_hash must be a 64-character lowercase hex string",
            )

        key = (obs.source_id, obs.provider_item_id)
        if key in self._source_index:
            existing_id = self._source_index[key]
            existing_obs = self._observations[existing_id]
            if existing_obs.payload_hash == obs.payload_hash:
                return TrackMarketNewsSuccess(
                    request_id=request.request_id,
                    observation=existing_obs,
                    outcome="SUCCESS",
                )

        self._observations[obs.observation_id] = obs
        self._source_index[key] = obs.observation_id
        if obs.observation_id not in self._revisions:
            self._revisions[obs.observation_id] = []

        return TrackMarketNewsSuccess(
            request_id=request.request_id,
            observation=obs,
            outcome="SUCCESS",
        )

    async def _revise_observation(
        self,
        request: TrackMarketNewsRequest,
    ) -> TrackMarketNewsSuccess | DataFailure:
        """Version an observation revision or cancellation.

        Args:
            request: TrackMarketNewsRequest with operation REVISE.

        Returns:
            TrackMarketNewsSuccess with revision or DataFailure.
        """
        rev = request.revision
        if rev is None:
            return _make_failure(
                request.request_id,
                "DATA_VALIDATION_FAILED",
                "urn:haruquant:data:missing-revision",
                "Missing revision",
                "REVISE operation requires a revision",
            )

        if rev.observation_id not in self._observations:
            return _make_failure(
                request.request_id,
                "DATA_NOT_FOUND",
                "urn:haruquant:data:observation-not-found",
                "Observation not found",
                f"Observation {rev.observation_id} does not exist",
                status=404,
            )

        if not _is_valid_sha256(rev.content_hash):
            return _make_failure(
                request.request_id,
                "DATA_VALIDATION_FAILED",
                "urn:haruquant:data:invalid-content-hash",
                "Invalid content hash",
                "content_hash must be a 64-character lowercase hex string",
            )

        rev_list = self._revisions.setdefault(rev.observation_id, [])
        for existing in rev_list:
            if existing.revision == rev.revision:
                if existing.content_hash == rev.content_hash:
                    return TrackMarketNewsSuccess(
                        request_id=request.request_id,
                        revision=existing,
                        outcome="SUCCESS",
                    )
                return _make_failure(
                    request.request_id,
                    "DATA_VERSION_CONFLICT",
                    "urn:haruquant:data:revision-conflict",
                    "Revision conflict",
                    f"Revision {rev.revision} exists with different content",
                    status=409,
                )

        rev_list.append(rev)
        rev_list.sort(key=lambda r: r.revision)

        return TrackMarketNewsSuccess(
            request_id=request.request_id,
            revision=rev,
            outcome="SUCCESS",
        )

    def _matches_filters(
        self,
        obs: MarketNewsObservation,
        request: TrackMarketNewsRequest,
        as_of_dt: datetime,
        from_dt: datetime,
        to_dt: datetime,
    ) -> bool:
        """Check whether an observation satisfies static query filters.

        Args:
            obs: Observation to evaluate.
            request: Active query request.
            as_of_dt: Point-in-time datetime.
            from_dt: Start of interval.
            to_dt: End of interval.

        Returns:
            True if all filters match, False otherwise.
        """
        if _parse_utc(obs.retrieved_at) > as_of_dt:
            return False

        event_str = obs.scheduled_at or obs.published_at or obs.first_seen_at
        event_dt = _parse_utc(event_str)
        if event_dt < from_dt or event_dt > to_dt:
            return False

        if request.source_id is not None and obs.source_id != request.source_id:
            return False

        if request.category is not None and obs.category != request.category:
            return False

        if request.language is not None and obs.language != request.language:
            return False

        return not (request.impact and obs.impact not in request.impact)

    async def _query_news(
        self,
        request: TrackMarketNewsRequest,
    ) -> TrackMarketNewsSuccess | DataFailure:
        """Execute a point-in-time market news query without lookahead bias.

        Args:
            request: TrackMarketNewsRequest with operation QUERY.

        Returns:
            TrackMarketNewsSuccess with matching observations, or DataFailure.
        """
        if request.as_of is None or request.from_at is None or request.to_at is None:
            return _make_failure(
                request.request_id,
                "DATA_VALIDATION_FAILED",
                "urn:haruquant:data:missing-query-params",
                "Missing query parameters",
                "QUERY requires as_of, from_at, and to_at",
            )

        as_of_dt = _parse_utc(request.as_of)
        from_dt = _parse_utc(request.from_at)
        to_dt = _parse_utc(request.to_at)

        matched: list[MarketNewsObservation] = []
        for obs in self._observations.values():
            if not self._matches_filters(obs, request, as_of_dt, from_dt, to_dt):
                continue

            retrieved_dt = _parse_utc(obs.retrieved_at)
            if request.freshness_limit_seconds is not None:
                age_sec = (as_of_dt - retrieved_dt).total_seconds()
                if age_sec > request.freshness_limit_seconds:
                    if request.require_complete_coverage:
                        msg = (
                            f"Observation {obs.observation_id} is stale "
                            f"({age_sec:.1f}s)"
                        )
                        return _make_failure(
                            request.request_id,
                            "DATA_COVERAGE_INCOMPLETE",
                            "urn:haruquant:data:stale-coverage",
                            "Coverage staleness limit exceeded",
                            msg,
                        )
                    continue

            revisions = self._revisions.get(obs.observation_id, [])
            visible_revs = [
                r for r in revisions if _parse_utc(r.visible_from) <= as_of_dt
            ]
            if visible_revs and visible_revs[-1].kind == "CANCELLATION":
                continue

            matched.append(obs)

        if request.require_complete_coverage and not matched:
            detail_msg = (
                f"No verified news coverage found in "
                f"[{request.from_at}, {request.to_at}]"
            )
            return _make_failure(
                request.request_id,
                "DATA_COVERAGE_INCOMPLETE",
                "urn:haruquant:data:incomplete-coverage",
                "Incomplete news coverage",
                detail_msg,
            )

        matched.sort(
            key=lambda x: (
                x.scheduled_at or x.published_at or x.first_seen_at,
                x.observation_id,
            )
        )
        return TrackMarketNewsSuccess(
            request_id=request.request_id,
            observations=tuple(matched),
            outcome="SUCCESS",
        )

    def project_trade_restrictions(
        self,
        as_of: UtcTimestamp,
        from_at: UtcTimestamp,
        to_at: UtcTimestamp,
        *,
        currencies: tuple[CurrencyCode, ...] = (),
        min_impact: NewsImpact = "HIGH",
        buffer_minutes_before: int = 15,
        buffer_minutes_after: int = 30,
    ) -> TradeRestrictionProjection:
        """Produce non-authorizing restriction-evidence projection.

        The projection never places, cancels, or approves an order.

        Args:
            as_of: Point-in-time visibility instant.
            from_at: Start of inspection interval.
            to_at: End of inspection interval.
            currencies: Optional currency scope filter.
            min_impact: Minimum news impact requiring blackout windows.
            buffer_minutes_before: Minutes before scheduled release to restrict.
            buffer_minutes_after: Minutes after scheduled release to restrict.

        Returns:
            TradeRestrictionProjection containing calculated blackout windows.
        """
        as_of_dt = _parse_utc(as_of)
        from_dt = _parse_utc(from_at)
        to_dt = _parse_utc(to_at)

        impact_ranks: dict[str, int] = {"NONE": 0, "LOW": 1, "MEDIUM": 2, "HIGH": 3}
        threshold = impact_ranks.get(min_impact, 3)

        windows: list[RestrictionWindow] = []
        evidence_refs: list[str] = []

        for obs in self._observations.values():
            if _parse_utc(obs.retrieved_at) > as_of_dt:
                continue

            event_time_str = obs.scheduled_at or obs.published_at or obs.first_seen_at
            event_dt = _parse_utc(event_time_str)
            if event_dt < from_dt or event_dt > to_dt:
                continue

            if impact_ranks.get(obs.impact, 0) < threshold:
                continue

            if (
                currencies
                and obs.scope_currencies
                and not any(c in currencies for c in obs.scope_currencies)
            ):
                continue

            revisions = self._revisions.get(obs.observation_id, [])
            visible_revisions = [
                r for r in revisions if _parse_utc(r.visible_from) <= as_of_dt
            ]
            if visible_revisions and visible_revisions[-1].kind == "CANCELLATION":
                continue

            win_start = event_dt - timedelta(minutes=buffer_minutes_before)
            win_end = event_dt + timedelta(minutes=buffer_minutes_after)
            curr = obs.scope_currencies[0] if obs.scope_currencies else "ALL"

            windows.append(
                RestrictionWindow(
                    event_id=obs.observation_id,
                    event_title=obs.category,
                    currency=curr,
                    impact=obs.impact,
                    window_start=_format_utc(win_start),
                    window_end=_format_utc(win_end),
                    buffer_minutes_before=buffer_minutes_before,
                    buffer_minutes_after=buffer_minutes_after,
                )
            )
            evidence_refs.append(
                f"obs:{obs.observation_id}:hash={obs.payload_hash[:8]}"
            )

        return TradeRestrictionProjection(
            projection_id=_generate_uuid7(),
            as_of=as_of,
            from_at=from_at,
            to_at=to_at,
            windows=tuple(windows),
            uncertainty=False,
            evidence_refs=tuple(evidence_refs),
            authorizing=False,
        )

    def govern_network_import(
        self,
        source_id: str,
        raw_records: list[dict[str, Any]],
        license_id: str,
        checkpoint: str | None = None,
    ) -> ImportGovernanceResult:
        """Govern network acquisition with rate-limiting and validation.

        Args:
            source_id: Source provider identifier.
            raw_records: Ingested raw payload records.
            license_id: Licensing authorization identifier.
            checkpoint: Optional cursor checkpoint.

        Returns:
            ImportGovernanceResult with validation findings and digest.
        """
        now = time.monotonic()
        history = self._rate_limits.setdefault(source_id, [])
        self._rate_limits[source_id] = [
            t for t in history if now - t < _RATE_LIMIT_WINDOW_SECONDS
        ]
        findings: list[str] = []

        if (
            len(self._rate_limits[source_id])
            >= self._config.default_rate_limit_per_minute
        ):
            limit = self._config.default_rate_limit_per_minute
            findings.append(f"Rate limit exceeded for source {source_id} ({limit}/min)")
            return ImportGovernanceResult(
                source_id=source_id,
                imported_count=0,
                rejected_count=len(raw_records),
                findings=tuple(findings),
                checkpoint=checkpoint,
                content_hash=compute_payload_hash(raw_records),
            )

        self._rate_limits[source_id].append(now)

        if not license_id or not license_id.strip():
            findings.append("Missing or unverified license credential")
            return ImportGovernanceResult(
                source_id=source_id,
                imported_count=0,
                rejected_count=len(raw_records),
                findings=tuple(findings),
                checkpoint=checkpoint,
                content_hash=compute_payload_hash(raw_records),
            )

        imported = 0
        rejected = 0
        for rec in raw_records:
            if "api_key" in rec:
                rec["api_key"] = "[REDACTED]"
            if "authorization" in rec:
                rec["authorization"] = "[REDACTED]"

            if not rec.get("provider_item_id") or not rec.get("category"):
                rejected += 1
                findings.append(f"Malformed record missing fields: {rec}")
            else:
                imported += 1

        if checkpoint:
            self._checkpoints[source_id] = checkpoint

        return ImportGovernanceResult(
            source_id=source_id,
            imported_count=imported,
            rejected_count=rejected,
            findings=tuple(findings),
            checkpoint=checkpoint,
            content_hash=compute_payload_hash(raw_records),
        )


async def _run_usage_scenarios() -> None:
    """Delegate to _usage module."""
    from app.services.data.economic_news_evidence._usage import (
        main as _usage_main,
    )

    await _usage_main()


async def main() -> None:
    """Execute the economic news evidence usage demonstration harness."""
    await _run_usage_scenarios()


def run_usage_scenarios() -> None:
    """Synchronous runner entry point for the usage demonstration."""
    asyncio.run(main())


if __name__ == "__main__":
    run_usage_scenarios()
