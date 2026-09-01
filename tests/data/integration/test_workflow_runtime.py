"""Integration evidence for Data runtime and evidence workflows."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest
from app.contracts.common.models import create_auth_context
from app.kernel.identity import generate_id
from app.services.data import (
    aggregate_ticks_to_bars,
    align_multitimeframe_data,
    build_availability_request,
    build_data_quality_report,
    build_data_response,
    build_data_settings,
    build_dataset_save_request,
    build_feed_config,
    build_feed_status_request,
    build_fx_conversion_request,
    build_fx_rate_leg,
    build_local_market_data_source,
    build_market_context_evidence,
    build_market_context_request,
    build_market_data_request,
    build_market_dataset,
    build_market_schedule,
    build_ohlcv_record,
    build_raw_feed_event,
    build_reconnect_policy,
    build_schedule_request,
    build_session_window,
    build_source_descriptor,
    build_source_identity,
    build_source_license_policy,
    build_source_policy_config,
    build_source_promotion_request,
    build_symbol_list_request,
    build_symbol_metadata,
    build_symbol_metadata_request,
    build_synthetic_request,
    data_settings_context,
    data_start_time,
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
    register_source_policy,
    resample_ohlcv,
    run_data_migrations,
    save_dataset,
    start_internal_feed,
    to_ohlcv_dataframe,
    unwrap_data_response,
)

START = datetime(2026, 1, 1, tzinfo=UTC)
END = START + timedelta(minutes=1)
AVAILABLE = END + timedelta(seconds=1)


def make_bar(timestamp=START):
    """Return one exact canonical OHLCV record."""
    return build_ohlcv_record(
        timestamp=timestamp,
        open=Decimal("10.0"),
        high=Decimal("11.0"),
        low=Decimal("9.0"),
        close=Decimal("10.5"),
        volume=Decimal(100),
        price_unit="USD",
        volume_unit="shares",
        source="fixture",
        source_symbol="ABC",
        source_revision="rev-1",
        available_at=timestamp + timedelta(seconds=1),
    )


def make_quality(count=1):
    """Return passing bounded quality evidence."""
    return build_data_quality_report(
        quality_status="perfect",
        quality_decision="accepted",
        quality_score=Decimal(100),
        issues=(),
        warnings=(),
        record_count=count,
        checked_count=count,
        truncated=False,
        sample_limit=10,
        schema_version="v1",
        generated_at=AVAILABLE,
    )


def make_dataset():
    """Return one immutable provider-neutral market dataset."""
    bar = make_bar()
    return build_market_dataset(
        normalization_version="v1",
        data_kind="bars",
        symbol="ABC",
        timeframe="1m",
        records=(bar,),
        start=START,
        end=START,
        available_at=AVAILABLE,
        record_count=1,
        quality_report=make_quality(),
        source_metadata={"source": "fixture"},
        license_metadata={"status": "approved"},
        cache_status="miss",
        workflow_context="research",
        precision_policy="decimal_string",
        request_id="req-491e2e64ca4b441c7f08620130e0e40d107775c753ca238bea74d87a1dd9f667",
    )


def register_local_test_source(raw_root, symbols, source_id="local_csv"):
    """Register one explicitly rooted local source with complete test policy."""
    request_id = generate_id("req")
    metadata = {
        symbol: build_symbol_metadata(
            canonical_symbol=symbol,
            provider_symbol=symbol,
            asset_class="equity",
            quote_currency="USD",
            timezone="UTC",
            source_id=source_id,
            revision="metadata-v1",
            retrieved_at=AVAILABLE,
            missing_fields=("base_currency", "digits", "price_step", "quantity_step"),
            request_id=request_id,
        )
        for symbol in symbols
    }
    identities = tuple(
        build_source_identity(
            source_id=source_id,
            canonical_symbol=symbol,
            friendly_name=symbol,
            provider_symbol=symbol,
            mapping_revision="mapping-v1",
            provenance={"fixture": "explicit"},
            request_id=request_id,
        )
        for symbol in symbols
    )
    descriptor = build_source_descriptor(
        source_id=source_id,
        readiness="production",
        capabilities=("bars", "ticks", "spreads"),
        requires_credentials=False,
        requires_network=False,
        supports_writes=False,
        schema_version="v1",
        timezone="UTC",
        revision="source-v1",
        license_policy=build_source_license_policy(
            source_id=source_id,
            status="approved",
            permitted_workflows=("backtest", "research", "risk", "validation"),
            export_allowed=True,
            attribution_required=False,
        ),
        identity_mapping_revision="mapping-v1",
        promotion_evidence=("fixture",),
    )
    register_source(
        descriptor,
        lambda: build_local_market_data_source(
            source_id=source_id, raw_root=raw_root, metadata=metadata
        ),
        identities,
    )
    register_source_policy(
        build_source_policy_config(
            source_id=source_id,
            rate_limit=1_000,
            rate_window_seconds=60,
            breaker_failure_threshold=3,
            breaker_recovery_seconds=60,
        )
    )


def _unwrap(response):
    return unwrap_data_response(
        response,
        operation="data.time_sessions.test",
        request_id="req-00000000-0000-4000-8000-000000000000",
    )


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
        request: object,
    ) -> object:
        """Return fresh evidence for the requested symbol."""
        return build_data_response(
            operation="data.evidence.get_market_context_evidence",
            request_id=request.request_id,
            start_time=data_start_time(),
            data=build_market_context_evidence(
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
            ),
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
    ) -> object:
        """Return the requested direct conversion evidence."""
        return build_data_response(
            operation="data.evidence.get_fx_conversion_evidence",
            request_id=request_id,
            start_time=data_start_time(),
            data=build_fx_rate_leg(
                source_currency=source_currency,
                target_currency=target_currency,
                rate=Decimal("1.10"),
                source_id="integration-fixture",
                provider_symbol=f"{source_currency}{target_currency}",
                as_of=as_of - timedelta(seconds=1),
                provenance={"quote": "declared-fixture"},
            ),
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
    ) -> object:
        """Return one authoritative current session."""
        window = build_session_window(
            label="open",
            opens_at=observed_at,
            closes_at=observed_at + timedelta(hours=1),
        )
        return build_market_schedule(
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
) -> object:
    """Return isolated migrated runtime settings and empty volatile registries."""
    for target in (
        "app.services.data.sources.registry._registry",
        "app.services.data.sources.registry._instances",
        "app.services.data.sources.registry._identities",
        "app.services.data.sources.policy._policy_configs",
        "app.services.data.market_events.state._ACTIVE_FEEDS",
    ):
        monkeypatch.setattr(target, {})
    return build_data_settings(
        database_url="sqlite:///workflow-runtime.sqlite3",
        data_dir=tmp_path,
        sqlite_busy_timeout_seconds=1.5,
        write_lock_lease_seconds=30.0,
        approved_storage_roots=(Path("data/raw"),),
    )


def _descriptor(source_id: str, *, readiness: str) -> object:
    """Return one bounded source descriptor for runtime workflow tests."""
    return build_source_descriptor(
        source_id=source_id,
        readiness=readiness,
        capabilities=("ticks",),
        requires_credentials=False,
        requires_network=False,
        supports_writes=False,
        schema_version="v1",
        timezone="UTC",
        revision="source-v1",
        license_policy=build_source_license_policy(
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
    runtime: object,
) -> None:
    """Start a deterministic feed, ingest an event, and read persisted status."""
    request_id = generate_id("req")
    with data_settings_context(runtime):
        run_data_migrations(request_id)
        register_source(
            _descriptor("fixture-feed", readiness="staging"),
            object,  # type: ignore[arg-type]
        )
        config = build_feed_config(
            feed_id="wf-data-008",
            source_id="fixture-feed",
            symbol="EURUSD",
            data_kind="tick",
            source_capability="ticks",
            buffer_capacity=2,
            overflow_policy="drop_and_reconcile",
            heartbeat_timeout_seconds=30,
            reconnect_policy=build_reconnect_policy(
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
            build_raw_feed_event(
                feed_id=config.feed_id,
                sequence=1,
                event_timestamp=_NOW,
                received_at=_NOW + timedelta(milliseconds=10),
                payload={"bid": 1.1, "ask": 1.2},
                request_id=request_id,
            ),
        )
        status = read_feed_status(
            build_feed_status_request(feed_id=config.feed_id, request_id=request_id),
            clock=_FixedClock(),
        )

    assert started.state == "starting"
    assert accepted.accepted
    assert status.state == "running"
    assert status.buffer_depth == 1
    assert status.last_event_at == _NOW


def test_wf_data_011_persists_audited_reversible_promotion(
    runtime: object,
) -> None:
    """Promote and demote a source through authenticated durable transitions."""
    request_id = generate_id("req")
    auth = create_auth_context(
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
        promoted = _unwrap(
            promote_source(
                build_source_promotion_request(
                    source_id="fixture-promotion",
                    target_readiness="production",
                    evidence=evidence,
                    request_id=request_id,
                ),
                auth,
                timestamp_ns=1,
            )
        )
        demoted = _unwrap(
            promote_source(
                build_source_promotion_request(
                    source_id="fixture-promotion",
                    target_readiness="staging",
                    evidence=("operator_signoff",),
                    request_id=request_id,
                ),
                auth,
                timestamp_ns=2,
            )
        )

    assert promoted.readiness == "production"
    assert demoted.readiness == "staging"


def test_wf_data_014_and_015_return_fresh_provider_evidence() -> None:
    """Normalize market-context and deterministic FX evidence from read providers."""
    context_request = build_market_context_request(
        symbol="EURUSD",
        as_of=_NOW,
        max_age_seconds=60,
        requested_evidence=("session", "calendar", "spread", "liquidity"),
        timezone="UTC",
        request_id=generate_id("req"),
    )
    context = _unwrap(get_market_context_evidence(context_request, _ContextProvider()))
    fx_request = build_fx_conversion_request(
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
    fx = _unwrap(get_fx_conversion_evidence(fx_request, _FXProvider()))

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
    resampled = _unwrap(resample_ohlcv(minute_dataset, "M5"))
    aligned = _unwrap(
        align_multitimeframe_data(
            {"M1": minute_dataset, "M5": resampled},
            target_timestamps=(minute_dataset.available_at,),
        )
    )
    synthetic = _unwrap(
        generate_synthetic_bars(
            build_synthetic_request(
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
    )
    derived = _unwrap(
        generate_tick_series(
            synthetic,
            model="trading_bar",
            trading_timeframe="H1",
        )
    )
    volume_ticks = tuple(
        tick.model_copy(update={"volume": Decimal(1), "volume_unit": "ticks"})
        for tick in derived.records
    )
    aggregated = _unwrap(
        aggregate_ticks_to_bars(
            derived.model_copy(update={"records": volume_ticks}),
            "H1",
            "last",
        )
    )

    assert resampled.record_count == 2
    assert set(aligned) == {"M1", "M5"}
    assert synthetic.record_count == 3
    assert derived.record_count == 12
    assert aggregated.record_count == 3


def test_wf_data_009_discovers_metadata_and_measures_local_availability(
    runtime: object,
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
            build_dataset_save_request(
                dataset=dataset,
                relative_path=Path("data/raw/ABC_M1.csv"),
                format="csv",
                overwrite=False,
                request_id=request_id,
            )
        )
        register_local_test_source(raw_root, ("ABC",), source_id="local_csv")
        symbols = _unwrap(
            list_symbols(
                build_symbol_list_request(
                    source_id="local_csv",
                    query="AB",
                    limit=10,
                    request_id=request_id,
                )
            )
        )
        metadata = _unwrap(
            get_symbol_metadata(
                build_symbol_metadata_request(
                    source_id="local_csv",
                    symbol="ABC",
                    request_id=request_id,
                )
            )
        )
        history = _unwrap(
            get_market_data(
                build_market_data_request(
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
        )
        analytical = to_ohlcv_dataframe(history)
        availability = _unwrap(
            get_data_availability(
                build_availability_request(
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
        )

    assert symbols.items == ("ABC",)
    assert metadata.canonical_symbol == "ABC"
    assert history.record_count == 2
    assert analytical.shape == (2, 6)
    assert availability.record_count == 2
    assert availability.completeness == Decimal("0.5")
    assert len(availability.gaps) == 1


def test_wf_data_010_returns_configured_utc_market_hours(
    runtime: object,
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
        hours = _unwrap(
            get_market_hours(
                build_schedule_request(
                    source_id="csv",
                    symbol="EURUSD",
                    view="hours",
                    timezone="UTC",
                    request_id=request_id,
                ),
                _Calendar(),
            )
        )

    assert hours.symbol == "EURUSD"
    assert hours.timezone == "UTC"
    assert hours.hours
