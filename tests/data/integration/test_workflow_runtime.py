"""Integration evidence for Data runtime and evidence workflows."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest
from app.services.data import (
    AvailabilityRequest,
    DatasetSaveRequest,
    DataSettings,
    FeedConfig,
    FeedStatusRequest,
    FXConversionRequest,
    FXRateLeg,
    MarketContextEvidence,
    MarketContextRequest,
    MarketDataRequest,
    MarketSchedule,
    RawFeedEvent,
    ReconnectPolicy,
    ScheduleRequest,
    SessionWindow,
    SourceDescriptor,
    SourceLicensePolicy,
    SourcePromotionRequest,
    SymbolListRequest,
    SymbolMetadataRequest,
    SyntheticRequest,
    aggregate_ticks_to_bars,
    align_multitimeframe_data,
    data_settings_context,
    ensure_source,
    generate_synthetic_bars,
    generate_tick_series,
    get_data_availability,
    get_fx_conversion_evidence,
    get_market_context_evidence,
    get_market_data,
    get_market_hours,
    get_symbol_metadata,
    ingest_feed_event,
    list_symbols,
    promote_source,
    read_feed_status,
    register_source,
    resample_ohlcv,
    run_data_migrations,
    save_dataset,
    start_internal_feed,
    to_ohlcv_dataframe,
)
from app.utils import AuthContext, generate_id

from tests.data.helpers import make_dataset, register_local_test_source

_NOW = datetime(2026, 7, 1, 12, tzinfo=UTC)


class _FixedClock:
    """Return one deterministic UTC instant."""

    def now(self) -> datetime:
        """Return the configured workflow time."""
        return _NOW


class _ContextProvider:
    """Return deterministic, complete read-only market-context evidence."""

    def get_market_context(
        self,
        request: MarketContextRequest,
    ) -> MarketContextEvidence:
        """Return fresh evidence for the requested symbol."""
        return MarketContextEvidence(
            symbol=request.symbol,
            session_state="open",
            calendar_state="clear",
            spread=Decimal("0.0002"),
            spread_unit="USD",
            liquidity=Decimal(1000000),
            volatility=Decimal("0.01"),
            correlations={},
            crisis_flags=(),
            timezone=request.timezone,
            as_of=request.as_of,
            expires_at=request.as_of + timedelta(minutes=1),
            provenance={"source": "integration-fixture"},
            missing_fields=(),
            request_id=request.request_id,
        )


class _FXProvider:
    """Return one exact read-only FX rate leg."""

    def get_rate_leg(
        self,
        *,
        source_currency: str,
        target_currency: str,
        as_of: datetime,
        request_id: str,
    ) -> FXRateLeg:
        """Return the requested direct conversion evidence."""
        del request_id
        return FXRateLeg(
            source_currency=source_currency,
            target_currency=target_currency,
            rate=Decimal("1.10"),
            source_id="integration-fixture",
            provider_symbol=f"{source_currency}{target_currency}",
            as_of=as_of - timedelta(seconds=1),
            provenance={"quote": "declared-fixture"},
        )


class _Calendar:
    """Return current UTC hours using the public calendar protocol."""

    def get_schedule(
        self,
        *,
        source_id: str,
        symbol: str,
        timezone: str,
        observed_at: datetime,
        request_id: str,
    ) -> MarketSchedule:
        """Return one authoritative current session."""
        window = SessionWindow(
            label="open",
            opens_at=observed_at,
            closes_at=observed_at + timedelta(hours=1),
        )
        return MarketSchedule(
            source_id=source_id,
            symbol=symbol,
            timezone=timezone,
            hours=(window,),
            sessions=(window,),
            observed_at=observed_at,
            request_id=request_id,
        )


@pytest.fixture
def runtime(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> DataSettings:
    """Return isolated migrated runtime settings and empty volatile registries."""
    for target in (
        "app.services.data.sources.registry._registry",
        "app.services.data.sources.registry._instances",
        "app.services.data.sources.registry._identities",
        "app.services.data.sources.policy._policy_configs",
        "app.services.data.realtime_feeds.state._ACTIVE_FEEDS",
    ):
        monkeypatch.setattr(target, {})
    return DataSettings(
        database_url="sqlite:///workflow-runtime.sqlite3",
        data_dir=tmp_path,
        approved_storage_roots=(Path("data/raw"),),
    )


def _descriptor(source_id: str, *, readiness: str) -> SourceDescriptor:
    """Return one bounded source descriptor for runtime workflow tests."""
    return SourceDescriptor(
        source_id=source_id,
        readiness=readiness,
        capabilities=("ticks",),
        requires_credentials=False,
        requires_network=False,
        supports_writes=False,
        schema_version="v1",
        timezone="UTC",
        revision="source-v1",
        license_policy=SourceLicensePolicy(
            source_id=source_id,
            status="approved",
            permitted_workflows=("validation",),
            export_allowed=False,
            attribution_required=False,
        ),
        identity_mapping_revision="mapping-v1",
        promotion_evidence=("normalization", "quality", "operator_signoff"),
    )


def test_wf_data_008_persists_ingests_and_reads_feed_status(
    runtime: DataSettings,
) -> None:
    """Start a deterministic feed, ingest an event, and read persisted status."""
    request_id = generate_id("req")
    with data_settings_context(runtime):
        run_data_migrations(request_id)
        register_source(
            _descriptor("fixture-feed", readiness="staging"),
            object,  # type: ignore[arg-type]
        )
        config = FeedConfig(
            feed_id="wf-data-008",
            source_id="fixture-feed",
            symbol="EURUSD",
            data_kind="tick",
            source_capability="ticks",
            buffer_capacity=2,
            overflow_policy="drop_and_reconcile",
            heartbeat_timeout_seconds=30,
            reconnect_policy=ReconnectPolicy(
                max_retries=2,
                initial_backoff_seconds=1,
                max_backoff_seconds=4,
                jitter_seconds=1,
                circuit_cooldown_seconds=30,
            ),
            request_id=request_id,
        )
        started = start_internal_feed(config, clock=_FixedClock())
        accepted = ingest_feed_event(
            config.feed_id,
            RawFeedEvent(
                feed_id=config.feed_id,
                sequence=1,
                event_timestamp=_NOW,
                received_at=_NOW + timedelta(milliseconds=10),
                payload={"bid": 1.1, "ask": 1.2},
                request_id=request_id,
            ),
        )
        status = read_feed_status(
            FeedStatusRequest(feed_id=config.feed_id, request_id=request_id),
            clock=_FixedClock(),
        )

    assert started.state == "starting"
    assert accepted.accepted
    assert status.state == "running"
    assert status.buffer_depth == 1
    assert status.last_event_at == _NOW


def test_wf_data_011_persists_audited_reversible_promotion(
    runtime: DataSettings,
) -> None:
    """Promote and demote a source through authenticated durable transitions."""
    request_id = generate_id("req")
    auth = AuthContext(
        contract_version="v1",
        schema_id="utils.auth_context.v1",
        principal_id="integration-operator",
        principal_type="USER",
        roles=("admin",),
        permissions=(),
        scopes=(),
        tenant_or_environment="dev",
        request_id=request_id,
        workflow_id=generate_id("wf"),
        correlation_id=generate_id("cor"),
        issued_at=_NOW,
    )
    evidence = ("normalization", "quality", "operator_signoff")
    with data_settings_context(runtime):
        run_data_migrations(request_id)
        register_source(
            _descriptor("fixture-promotion", readiness="staging"),
            object,  # type: ignore[arg-type]
        )
        promoted = promote_source(
            SourcePromotionRequest(
                source_id="fixture-promotion",
                target_readiness="production",
                evidence=evidence,
                request_id=request_id,
            ),
            auth,
            timestamp_ns=1,
        )
        demoted = promote_source(
            SourcePromotionRequest(
                source_id="fixture-promotion",
                target_readiness="staging",
                evidence=("operator_signoff",),
                request_id=request_id,
            ),
            auth,
            timestamp_ns=2,
        )

    assert promoted.readiness == "production"
    assert demoted.readiness == "staging"


def test_wf_data_014_and_015_return_fresh_provider_evidence() -> None:
    """Normalize market-context and deterministic FX evidence from read providers."""
    context_request = MarketContextRequest(
        symbol="EURUSD",
        as_of=_NOW,
        max_age_seconds=60,
        requested_evidence=("session", "calendar", "spread", "liquidity"),
        timezone="UTC",
        request_id=generate_id("req"),
    )
    context = get_market_context_evidence(context_request, _ContextProvider())
    fx_request = FXConversionRequest(
        source_currency="EUR",
        target_currency="USD",
        as_of=_NOW,
        max_age_seconds=60,
        allowed_intermediates=("GBP",),
        max_legs=2,
        path_policy_id="direct-first",
        path_policy_version="v1",
        request_id=generate_id("req"),
    )
    fx = get_fx_conversion_evidence(fx_request, _FXProvider())

    assert context.session_state == "open"
    assert context.missing_fields == ()
    assert tuple((leg.source_currency, leg.target_currency) for leg in fx.legs) == (
        ("EUR", "USD"),
    )
    assert fx.composite_rate == Decimal("1.10")


def test_wf_data_004_005_and_016_transform_generate_and_derive() -> None:
    """Exercise deterministic transformation, synthetic, and tick derivation flows."""
    base = make_dataset()
    bars = tuple(
        base.records[0].model_copy(
            update={
                "timestamp": _NOW + timedelta(minutes=index),
                "available_at": _NOW + timedelta(minutes=index, seconds=1),
                "open": Decimal(100 + index),
                "high": Decimal(101 + index),
                "low": Decimal(99 + index),
                "close": Decimal("100.5") + index,
            }
        )
        for index in range(10)
    )
    quality = base.quality_report.model_copy(
        update={"record_count": len(bars), "checked_count": len(bars)}
    )
    minute_dataset = base.model_copy(
        update={
            "symbol": "EURUSD",
            "timeframe": "M1",
            "records": bars,
            "start": bars[0].timestamp,
            "end": bars[-1].timestamp,
            "available_at": bars[-1].available_at,
            "record_count": len(bars),
            "quality_report": quality,
        }
    )
    resampled = resample_ohlcv(minute_dataset, "M5")
    aligned = align_multitimeframe_data(
        {"M1": minute_dataset, "M5": resampled},
        target_timestamps=(minute_dataset.available_at,),
    )
    synthetic = generate_synthetic_bars(
        SyntheticRequest(
            symbol="EURUSD",
            data_kind="bars",
            timeframe="H1",
            start=_NOW,
            record_count=3,
            method="gbm",
            seed=42,
            parameters={
                "mu": Decimal("0.02"),
                "sigma": Decimal("0.10"),
                "start_val": Decimal("1.10"),
            },
            precision_policy="decimal_string",
            request_id=generate_id("req"),
        )
    )
    derived = generate_tick_series(
        synthetic,
        model="trading_bar",
        trading_timeframe="H1",
    )
    volume_ticks = tuple(
        tick.model_copy(update={"volume": Decimal(1), "volume_unit": "ticks"})
        for tick in derived.records
    )
    aggregated = aggregate_ticks_to_bars(
        derived.model_copy(update={"records": volume_ticks}),
        "H1",
        "last",
    )

    assert resampled.record_count == 2
    assert set(aligned) == {"M1", "M5"}
    assert synthetic.record_count == 3
    assert derived.record_count == 12
    assert aggregated.record_count == 3


def test_wf_data_009_discovers_metadata_and_measures_local_availability(
    runtime: DataSettings,
) -> None:
    """Use one real local artifact for discovery, metadata, and availability."""
    request_id = generate_id("req")
    raw_root = runtime.data_dir / "data" / "raw"  # type: ignore[operator]
    raw_root.mkdir(parents=True)
    base = make_dataset()
    second = base.records[0].model_copy(
        update={
            "timestamp": base.records[0].timestamp + timedelta(minutes=1),
            "available_at": base.records[0].available_at + timedelta(minutes=1),
        }
    )
    records = (base.records[0], second)
    dataset = base.model_copy(
        update={
            "records": records,
            "end": second.timestamp,
            "available_at": second.available_at,
            "record_count": len(records),
            "timeframe": "M1",
            "quality_report": base.quality_report.model_copy(
                update={"record_count": len(records), "checked_count": len(records)}
            ),
            "request_id": request_id,
        }
    )
    with data_settings_context(runtime):
        run_data_migrations(request_id)
        save_dataset(
            DatasetSaveRequest(
                dataset=dataset,
                relative_path=Path("data/raw/ABC_M1.csv"),
                format="csv",
                overwrite=False,
                request_id=request_id,
            )
        )
        register_local_test_source(raw_root, ("ABC",), source_id="local_csv")
        symbols = list_symbols(
            SymbolListRequest(
                source_id="local_csv",
                query="AB",
                limit=10,
                request_id=request_id,
            )
        )
        metadata = get_symbol_metadata(
            SymbolMetadataRequest(
                source_id="local_csv",
                symbol="ABC",
                request_id=request_id,
            )
        )
        history = get_market_data(
            MarketDataRequest(
                source_id="local_csv",
                symbol="ABC",
                data_kind="bars",
                timeframe="M1",
                start=dataset.start,
                end=dataset.end + timedelta(minutes=1),
                limit=10,
                use_cache=False,
                quality_failure_behavior="reject",
                workflow_context="research",
                precision_policy="decimal_string",
                request_id=request_id,
            )
        )
        analytical = to_ohlcv_dataframe(history)
        availability = get_data_availability(
            AvailabilityRequest(
                source_id="local_csv",
                symbol="ABC",
                data_kind="ohlcv",
                timeframe="M1",
                start=dataset.start,
                end=dataset.end + timedelta(minutes=1),
                max_probe_records=10,
                request_id=request_id,
            )
        )

    assert symbols.items == ("ABC",)
    assert metadata.canonical_symbol == "ABC"
    assert history.record_count == 2
    assert analytical.shape == (2, 6)
    assert availability.record_count == 2
    assert availability.completeness == Decimal("0.5")
    assert len(availability.gaps) == 1


def test_wf_data_010_returns_configured_utc_market_hours(
    runtime: DataSettings,
) -> None:
    """Compose a local source and return its normalized UTC hours."""
    assert runtime.data_dir is not None
    raw_root = runtime.data_dir / "data" / "raw"
    raw_root.mkdir(parents=True)
    (raw_root / "symbols.json").write_text(
        json.dumps(
            {
                "EURUSD": {
                    "asset_class": "forex",
                    "base_currency": "EUR",
                    "quote_currency": "USD",
                    "revision": "operator-v1",
                    "retrieved_at": "2026-07-01T00:00:00Z",
                    "missing_fields": [
                        "digits",
                        "price_step",
                        "quantity_step",
                    ],
                }
            }
        ),
        encoding="utf-8",
    )
    request_id = generate_id("req")
    with data_settings_context(runtime):
        run_data_migrations(request_id)
        ensure_source("csv", request_id)
        hours = get_market_hours(
            ScheduleRequest(
                source_id="csv",
                symbol="EURUSD",
                view="hours",
                timezone="UTC",
                request_id=request_id,
            ),
            _Calendar(),
        )

    assert hours.symbol == "EURUSD"
    assert hours.timezone == "UTC"
    assert hours.hours
