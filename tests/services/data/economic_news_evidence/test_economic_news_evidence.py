"""Unit tests for Economic Calendar and News Evidence service."""

import pytest
from app.contracts.catalogue.models import InstrumentRef
from app.contracts.data.errors import DataFailure
from app.contracts.data.models import (
    MarketNewsObservation,
    MarketNewsRevision,
    TrackMarketNewsRequest,
    TrackMarketNewsSuccess,
)
from app.services.data.economic_news_evidence.config import (
    EconomicNewsEvidenceConfig,
)
from app.services.data.economic_news_evidence.economic_news_evidence import (
    TrackMarketNewsService,
    _generate_uuid7,
    _run_usage_scenarios,
    compute_payload_hash,
)


def _make_obs(
    *,
    obs_id: str | None = None,
    source_id: str = "FOREX_FACTORY",
    provider_item_id: str = "item-001",
    retrieved_at: str = "2026-08-01T10:00:00.000000Z",
    scheduled_at: str = "2026-08-05T12:30:00.000000Z",
    category: str = "Non-Farm Payrolls",
    impact: str = "HIGH",
    language: str = "en",
    currency: str = "USD",
) -> MarketNewsObservation:
    payload = {"source": source_id, "item": provider_item_id, "category": category}
    return MarketNewsObservation(
        observation_id=obs_id or _generate_uuid7(),
        source_id=source_id,
        provider_item_id=provider_item_id,
        first_seen_at="2026-08-01T00:00:00.000000Z",
        retrieved_at=retrieved_at,
        scheduled_at=scheduled_at,
        published_at=None,
        scope_currencies=(currency,),
        scope_instruments=(InstrumentRef(instrument_id=_generate_uuid7()),),
        category=category,
        impact=impact,  # type: ignore[arg-type]
        language=language,
        payload_hash=compute_payload_hash(payload),
    )


@pytest.mark.asyncio
async def test_record_news_observation_success() -> None:
    """Test FR-DATA-RECORD_NEWS_OBSERVATIONS standard recording."""
    service = TrackMarketNewsService()
    obs = _make_obs()
    req = TrackMarketNewsRequest(
        request_id=_generate_uuid7(),
        capability_snapshot_id=_generate_uuid7(),
        operation="RECORD",
        observation=obs,
    )
    res = await service.track_market_news(req)
    assert isinstance(res, TrackMarketNewsSuccess)
    assert res.observation == obs
    assert res.outcome == "SUCCESS"


@pytest.mark.asyncio
async def test_record_news_observation_idempotent() -> None:
    """Test idempotent re-recording of identical observation."""
    service = TrackMarketNewsService()
    obs = _make_obs()
    req1 = TrackMarketNewsRequest(
        request_id=_generate_uuid7(),
        capability_snapshot_id=_generate_uuid7(),
        operation="RECORD",
        observation=obs,
    )
    res1 = await service.track_market_news(req1)
    assert isinstance(res1, TrackMarketNewsSuccess)

    # Re-record with same source and provider item
    obs2 = _make_obs(
        obs_id=_generate_uuid7(),
        source_id=obs.source_id,
        provider_item_id=obs.provider_item_id,
    )
    # Ensure payload hash matches
    object.__setattr__(obs2, "payload_hash", obs.payload_hash)

    req2 = TrackMarketNewsRequest(
        request_id=_generate_uuid7(),
        capability_snapshot_id=_generate_uuid7(),
        operation="RECORD",
        observation=obs2,
    )
    res2 = await service.track_market_news(req2)
    assert isinstance(res2, TrackMarketNewsSuccess)
    assert res2.observation is not None
    assert res2.observation.observation_id == obs.observation_id


@pytest.mark.asyncio
async def test_record_news_invalid_payload_hash() -> None:
    """Test rejection of invalid payload hash."""
    service = TrackMarketNewsService()
    obs = _make_obs()
    object.__setattr__(obs, "payload_hash", "invalid-hash")
    req = TrackMarketNewsRequest(
        request_id=_generate_uuid7(),
        capability_snapshot_id=_generate_uuid7(),
        operation="RECORD",
        observation=obs,
    )
    res = await service.track_market_news(req)
    assert isinstance(res, DataFailure)
    assert res.code == "DATA_VALIDATION_FAILED"


@pytest.mark.asyncio
async def test_version_news_revisions_success() -> None:
    """Test FR-DATA-VERSION_NEWS_REVISIONS revision tracking."""
    service = TrackMarketNewsService()
    obs = _make_obs()
    await service.track_market_news(
        TrackMarketNewsRequest(
            request_id=_generate_uuid7(),
            capability_snapshot_id=_generate_uuid7(),
            operation="RECORD",
            observation=obs,
        )
    )

    rev = MarketNewsRevision(
        revision_id=_generate_uuid7(),
        observation_id=obs.observation_id,
        revision=1,
        kind="VALUES",
        actual="200000",
        forecast="180000",
        previous="170000",
        visible_from="2026-08-05T12:30:05.000000Z",
        content_hash=compute_payload_hash({"actual": 200000}),
    )
    req = TrackMarketNewsRequest(
        request_id=_generate_uuid7(),
        capability_snapshot_id=_generate_uuid7(),
        operation="REVISE",
        revision=rev,
    )
    res = await service.track_market_news(req)
    assert isinstance(res, TrackMarketNewsSuccess)
    assert res.revision == rev


@pytest.mark.asyncio
async def test_version_news_revision_missing_observation() -> None:
    """Test revision for non-existent observation returns DATA_NOT_FOUND."""
    service = TrackMarketNewsService()
    rev = MarketNewsRevision(
        revision_id=_generate_uuid7(),
        observation_id=_generate_uuid7(),
        revision=1,
        kind="VALUES",
        visible_from="2026-08-05T12:30:05.000000Z",
        content_hash=compute_payload_hash({"val": 1}),
    )
    req = TrackMarketNewsRequest(
        request_id=_generate_uuid7(),
        capability_snapshot_id=_generate_uuid7(),
        operation="REVISE",
        revision=rev,
    )
    res = await service.track_market_news(req)
    assert isinstance(res, DataFailure)
    assert res.code == "DATA_NOT_FOUND"


@pytest.mark.asyncio
async def test_version_news_revision_conflict() -> None:
    """Test conflicting revision payload returns DATA_VERSION_CONFLICT."""
    service = TrackMarketNewsService()
    obs = _make_obs()
    await service.track_market_news(
        TrackMarketNewsRequest(
            request_id=_generate_uuid7(),
            capability_snapshot_id=_generate_uuid7(),
            operation="RECORD",
            observation=obs,
        )
    )

    rev1 = MarketNewsRevision(
        revision_id=_generate_uuid7(),
        observation_id=obs.observation_id,
        revision=1,
        kind="VALUES",
        visible_from="2026-08-05T12:30:05.000000Z",
        content_hash="a" * 64,
    )
    await service.track_market_news(
        TrackMarketNewsRequest(
            request_id=_generate_uuid7(),
            capability_snapshot_id=_generate_uuid7(),
            operation="REVISE",
            revision=rev1,
        )
    )

    rev2 = MarketNewsRevision(
        revision_id=_generate_uuid7(),
        observation_id=obs.observation_id,
        revision=1,
        kind="CANCELLATION",
        visible_from="2026-08-05T12:30:10.000000Z",
        content_hash="b" * 64,
    )
    res = await service.track_market_news(
        TrackMarketNewsRequest(
            request_id=_generate_uuid7(),
            capability_snapshot_id=_generate_uuid7(),
            operation="REVISE",
            revision=rev2,
        )
    )
    assert isinstance(res, DataFailure)
    assert res.code == "DATA_VERSION_CONFLICT"


@pytest.mark.asyncio
async def test_query_market_news_point_in_time_lookahead_safety() -> None:
    """Test FR-DATA-QUERY_MARKET_NEWS point-in-time lookahead safety."""
    service = TrackMarketNewsService()
    obs1 = _make_obs(
        retrieved_at="2026-08-01T10:00:00.000000Z",
        scheduled_at="2026-08-05T12:30:00.000000Z",
        category="CPI",
    )
    obs2 = _make_obs(
        retrieved_at="2026-08-03T10:00:00.000000Z",
        scheduled_at="2026-08-06T12:30:00.000000Z",
        category="GDP",
    )
    await service.track_market_news(
        TrackMarketNewsRequest(
            request_id=_generate_uuid7(),
            capability_snapshot_id=_generate_uuid7(),
            operation="RECORD",
            observation=obs1,
        )
    )
    await service.track_market_news(
        TrackMarketNewsRequest(
            request_id=_generate_uuid7(),
            capability_snapshot_id=_generate_uuid7(),
            operation="RECORD",
            observation=obs2,
        )
    )

    # Query as of 2026-08-02: obs2 was retrieved on 2026-08-03, so it MUST NOT be visible!
    req = TrackMarketNewsRequest(
        request_id=_generate_uuid7(),
        capability_snapshot_id=_generate_uuid7(),
        operation="QUERY",
        as_of="2026-08-02T00:00:00.000000Z",
        from_at="2026-08-01T00:00:00.000000Z",
        to_at="2026-08-10T00:00:00.000000Z",
    )
    res = await service.track_market_news(req)
    assert isinstance(res, TrackMarketNewsSuccess)
    assert len(res.observations) == 1
    assert res.observations[0].observation_id == obs1.observation_id


@pytest.mark.asyncio
async def test_query_market_news_filters() -> None:
    """Test query filtering by source, impact, and category."""
    service = TrackMarketNewsService()
    obs_high = _make_obs(impact="HIGH", category="NFP", source_id="SRC_A")
    obs_low = _make_obs(impact="LOW", category="PPI", source_id="SRC_B")
    await service.track_market_news(
        TrackMarketNewsRequest(
            request_id=_generate_uuid7(),
            capability_snapshot_id=_generate_uuid7(),
            operation="RECORD",
            observation=obs_high,
        )
    )
    await service.track_market_news(
        TrackMarketNewsRequest(
            request_id=_generate_uuid7(),
            capability_snapshot_id=_generate_uuid7(),
            operation="RECORD",
            observation=obs_low,
        )
    )

    # Filter by source_id
    req_src = TrackMarketNewsRequest(
        request_id=_generate_uuid7(),
        capability_snapshot_id=_generate_uuid7(),
        operation="QUERY",
        as_of="2026-08-10T00:00:00.000000Z",
        from_at="2026-08-01T00:00:00.000000Z",
        to_at="2026-08-10T00:00:00.000000Z",
        source_id="SRC_A",
    )
    res_src = await service.track_market_news(req_src)
    assert isinstance(res_src, TrackMarketNewsSuccess)
    assert len(res_src.observations) == 1
    assert res_src.observations[0].observation_id == obs_high.observation_id

    # Filter by impact
    req_imp = TrackMarketNewsRequest(
        request_id=_generate_uuid7(),
        capability_snapshot_id=_generate_uuid7(),
        operation="QUERY",
        as_of="2026-08-10T00:00:00.000000Z",
        from_at="2026-08-01T00:00:00.000000Z",
        to_at="2026-08-10T00:00:00.000000Z",
        impact=("HIGH",),
    )
    res_imp = await service.track_market_news(req_imp)
    assert isinstance(res_imp, TrackMarketNewsSuccess)
    assert len(res_imp.observations) == 1
    assert res_imp.observations[0].impact == "HIGH"


@pytest.mark.asyncio
async def test_query_market_news_coverage_incomplete() -> None:
    """Test require_complete_coverage failure when no observations match."""
    service = TrackMarketNewsService()
    req = TrackMarketNewsRequest(
        request_id=_generate_uuid7(),
        capability_snapshot_id=_generate_uuid7(),
        operation="QUERY",
        as_of="2026-08-10T00:00:00.000000Z",
        from_at="2026-08-01T00:00:00.000000Z",
        to_at="2026-08-10T00:00:00.000000Z",
        require_complete_coverage=True,
    )
    res = await service.track_market_news(req)
    assert isinstance(res, DataFailure)
    assert res.code == "DATA_COVERAGE_INCOMPLETE"


def test_project_trade_restrictions() -> None:
    """Test FR-DATA-PROJECT_TRADE_RESTRICTIONS non-authorizing projection."""
    service = TrackMarketNewsService()
    obs = _make_obs(
        scheduled_at="2026-08-07T12:30:00.000000Z",
        impact="HIGH",
        currency="USD",
        category="NFP",
    )
    service._observations[obs.observation_id] = obs

    proj = service.project_trade_restrictions(
        as_of="2026-08-07T00:00:00.000000Z",
        from_at="2026-08-07T00:00:00.000000Z",
        to_at="2026-08-07T23:59:59.000000Z",
        currencies=("USD",),
        min_impact="HIGH",
        buffer_minutes_before=15,
        buffer_minutes_after=30,
    )
    assert proj.authorizing is False
    assert len(proj.windows) == 1
    w = proj.windows[0]
    assert w.event_id == obs.observation_id
    assert w.currency == "USD"
    assert "2026-08-07T12:15:00" in w.window_start
    assert "2026-08-07T13:00:00" in w.window_end


def test_govern_network_imports() -> None:
    """Test FR-DATA-GOVERN_NETWORK_IMPORTS rate limiting and validation."""
    cfg = EconomicNewsEvidenceConfig(default_rate_limit_per_minute=2)
    service = TrackMarketNewsService(config=cfg)

    # 1. Normal import with credential redaction
    raw = [
        {
            "provider_item_id": "1",
            "category": "CPI",
            "api_key": "sample-key-01",  # pragma: allowlist secret
        },
        {"provider_item_id": "2", "category": "NFP"},
        {"category": "MissingItemID"},
    ]

    res1 = service.govern_network_import(
        source_id="FOREX_FACTORY",
        raw_records=raw,
        license_id="LIC-123",
        checkpoint="cp_01",
    )
    assert res1.imported_count == 2
    assert res1.rejected_count == 1
    assert raw[0]["api_key"] == "[REDACTED]"
    assert res1.checkpoint == "cp_01"

    # 2. Second request within rate limit
    res2 = service.govern_network_import(
        source_id="FOREX_FACTORY",
        raw_records=[{"provider_item_id": "3", "category": "GDP"}],
        license_id="LIC-123",
    )
    assert res2.imported_count == 1

    # 3. Third request hits rate limit (limit is 2/min)
    res3 = service.govern_network_import(
        source_id="FOREX_FACTORY",
        raw_records=[{"provider_item_id": "4", "category": "FOMC"}],
        license_id="LIC-123",
    )
    assert res3.imported_count == 0
    assert "Rate limit exceeded" in res3.findings[0]


@pytest.mark.asyncio
async def test_run_usage_scenarios_harness() -> None:
    """Verify execution of standalone usage scenarios harness."""
    await _run_usage_scenarios()


@pytest.mark.asyncio
async def test_track_market_news_missing_fields_and_invalid_op() -> None:
    """Verify DataFailure on missing fields or invalid operation."""
    service = TrackMarketNewsService()

    # RECORD with missing observation
    req_record = TrackMarketNewsRequest.model_construct(
        request_id=_generate_uuid7(),
        capability_snapshot_id=_generate_uuid7(),
        operation="RECORD",
        observation=None,
        schema_version=1,
    )
    res1 = await service.track_market_news(req_record)
    assert isinstance(res1, DataFailure)
    assert res1.code == "DATA_VALIDATION_FAILED"

    # REVISE with missing revision
    req_revise = TrackMarketNewsRequest.model_construct(
        request_id=_generate_uuid7(),
        capability_snapshot_id=_generate_uuid7(),
        operation="REVISE",
        revision=None,
        schema_version=1,
    )
    res2 = await service.track_market_news(req_revise)
    assert isinstance(res2, DataFailure)
    assert res2.code == "DATA_VALIDATION_FAILED"

    # Invalid payload hash
    obs_bad_hash = _make_obs()
    object.__setattr__(obs_bad_hash, "payload_hash", "invalid-hash")
    req_bad_hash = TrackMarketNewsRequest(
        request_id=_generate_uuid7(),
        capability_snapshot_id=_generate_uuid7(),
        operation="RECORD",
        observation=obs_bad_hash,
    )
    res3 = await service.track_market_news(req_bad_hash)
    assert isinstance(res3, DataFailure)
    assert res3.code == "DATA_VALIDATION_FAILED"


def test_economic_news_persistence_store() -> None:
    """Verify EconomicNewsPersistenceStore methods."""
    from app.services.data.economic_news_evidence._persistence import (
        EconomicNewsPersistenceStore,
    )

    store = EconomicNewsPersistenceStore()
    obs = _make_obs()
    store.add_observation(obs)
    assert store.get_observation(obs.observation_id) == obs
    assert len(store.get_all_observations()) == 1
    assert store.get_by_source_key(obs.source_id, obs.provider_item_id) == obs
    assert store.get_by_source_key("unknown", "unknown") is None

    from app.contracts.data.models import MarketNewsRevision

    rev = MarketNewsRevision(
        revision_id=_generate_uuid7(),
        observation_id=obs.observation_id,
        revision=1,
        kind="VALUES",
        actual="100",
        forecast=None,
        previous=None,
        visible_from="2026-08-01T00:00:00.000000Z",
        content_hash="0" * 64,
    )
    store.add_revision(rev)
    assert len(store.get_revisions(obs.observation_id)) == 1

    store.record_rate_limit("src1", 1000.0)
    assert store.get_rate_limits("src1") == [1000.0]

    store.set_checkpoint("src1", "cp1")
    assert store.get_checkpoint("src1") == "cp1"

    store.clear()
    assert len(store.get_all_observations()) == 0
