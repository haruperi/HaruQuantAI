"""Homogeneous full-domain usage program for app.services.data.

Ties all registered Data features (FEAT-DATA-01 through FEAT-DATA-16) together into a single,
sequential, step-by-step pipeline matching real-world operational execution order:
1. Canonical Data Contracts (FEAT-DATA-01)
2. Data Source Governance & Policy (FEAT-DATA-10)
3. Data Persistence, Locking & Cache Lifecycle (FEAT-DATA-06)
4. Market Data Retrieval & Availability (FEAT-DATA-02)
5. Local Dataset Loading & Storage (FEAT-DATA-03)
6. Synthetic Data Generation (FEAT-DATA-04)
7. Tick-Series Derivation (FEAT-DATA-05)
8. Data Quality & Adversarial Validation (FEAT-DATA-07)
9. Data Transformation, Resampling & Multi-timeframe Alignment (FEAT-DATA-08)
10. Time, Market Hours & Session Handling (FEAT-DATA-09)
11. Economic Calendar Normalization & Queries (FEAT-DATA-11)
12. Real-Time Feed Lifecycle & Observability (FEAT-DATA-12)
13. Scheduler & Data Job Management (FEAT-DATA-13)
14. Cross-Domain Normalized Evidence (FEAT-DATA-14)
15. Audit Evidence & Durable Querying (FEAT-DATA-15)
16. Point-in-Time Research Source Evidence (FEAT-DATA-16)
"""

from __future__ import annotations

import asyncio
import sys
import tempfile
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.brokers import create_connected_broker, disconnect_broker
from app.services.data import (
    acquire_write_lock,
    aggregate_ticks_to_bars,
    align_datasets,
    align_multitimeframe_data,
    assess_research_source_eligibility,
    build_account_snapshot_request,
    build_active_market_sessions_request,
    build_audit_event_query,
    build_availability_request,
    build_cache_read_request,
    build_cache_write_request,
    build_data_error,
    build_data_quality_report,
    build_data_settings,
    build_dataset_load_request,
    build_dataset_save_request,
    build_economic_event,
    build_economic_event_store,
    build_error_definition,
    build_event_impact,
    build_exchange_session_request,
    build_feed_config,
    build_feed_status_request,
    build_fx_conversion_request,
    build_fx_rate_leg,
    build_job_definition,
    build_job_status_request,
    build_market_context_evidence,
    build_market_context_request,
    build_market_data_request,
    build_market_dataset,
    build_market_hours_request,
    build_ohlcv_record,
    build_quality_issue,
    build_raw_feed_event,
    build_reconnect_policy,
    build_research_source_ingest_request,
    build_research_source_policy,
    build_research_source_query,
    build_spread_record,
    build_statement_plan,
    build_symbol_list_request,
    build_symbol_metadata,
    build_symbol_metadata_request,
    build_synthetic_request,
    build_tick_record,
    build_transaction_request,
    classify_gap,
    clear_data_cache,
    create_data_update_job,
    data_settings_context,
    data_start_time,
    detect_price_jumps,
    detect_timestamp_gaps,
    detect_zero_volume_bars,
    discover_symbols,
    ensure_source,
    evaluate_source_policy,
    execute_transaction,
    fetch_symbol_metadata,
    generate_synthetic_bars,
    generate_synthetic_ticks,
    generate_tick_series,
    get_account_state_snapshot,
    get_active_market_sessions,
    get_cache_entry,
    get_calendar_sites,
    get_data_update_job_status,
    get_exchange_sessions,
    get_feed_status,
    get_forex_named_sessions,
    get_fx_conversion_evidence,
    get_market_context_evidence,
    get_market_data,
    get_market_hours,
    get_persisted_events,
    get_quality_policy,
    get_source_descriptor,
    get_timeframe_spec,
    ingest_feed_event,
    ingest_research_source,
    inspect_availability,
    inspect_dataset_quality,
    is_news_restricted_events,
    list_composable_sources,
    list_registered_sources,
    list_symbols,
    load_dataset,
    load_local_dataset,
    persist_audit_event,
    persist_economic_events,
    project_research_source_evidence,
    put_cache_entry,
    query_audit_events,
    query_research_sources,
    read_feed_status,
    resample_dataset,
    resample_ohlcv,
    run_data_migrations,
    run_data_operation,
    run_data_update_job_once,
    save_market_data,
    start_data_update_job,
    start_internal_feed,
    stop_data_update_job,
    summarize_quality_remediation,
    to_ohlcv_dataframe,
    to_tick_dataframe,
    validate_research_source_policy,
    validate_symbol_metadata,
)
from app.utils import create_audit_event, create_auth_context, generate_id

_START = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)
_END = _START + timedelta(minutes=100)
_REQUEST_ID = "req-00000000-0000-4000-8000-000000000001"


def _print_stage(stage_num: int, name: str, summary: str) -> None:
    print(f"\n\n{'-' * 80}")
    print(f"Stage {stage_num}: {name}")
    print(f"Description: {summary}")
    print(f"{'-' * 80}")


def _run_stage_1_contracts() -> Any:
    _print_stage(
        1,
        "Canonical Data Contracts (FEAT-DATA-01)",
        "Construct canonical OHLCV, tick, and spread records, quality report, and market dataset.",
    )
    bar = build_ohlcv_record(
        timestamp=_START,
        source="mt5",
        source_symbol="EURUSD",
        available_at=_START,
        open=Decimal("1.1000"),
        high=Decimal("1.1020"),
        low=Decimal("1.0990"),
        close=Decimal("1.1010"),
        volume=Decimal(100),
        price_unit="quote",
        volume_unit="ticks",
        spread=Decimal("0.0002"),
        spread_unit="price",
    )
    tick = build_tick_record(
        timestamp=_START,
        source="mt5",
        source_symbol="EURUSD",
        available_at=_START,
        bid=Decimal("1.1000"),
        ask=Decimal("1.1002"),
        last=Decimal("1.1001"),
        volume=Decimal(1),
        price_unit="quote",
        volume_unit="ticks",
    )
    spread = build_spread_record(
        timestamp=_START,
        source="mt5",
        source_symbol="EURUSD",
        available_at=_START,
        spread=Decimal(2),
        unit="points",
        scale=5,
    )
    issue = build_quality_issue(
        code="MISSING_BARS",
        severity="warning",
        message="One bounded example issue",
        affected_count=1,
        samples=("2026-07-01T12:01:00Z",),
        blocking_workflows=(),
    )
    report = build_data_quality_report(
        quality_status="passed",
        quality_score=Decimal("1.00"),
        issues=(issue,),
        warnings=(),
        record_count=1,
        checked_count=1,
        truncated=False,
        sample_limit=10,
        schema_version="v1",
        generated_at=_END,
    )
    dataset = build_market_dataset(
        normalization_version="v1",
        data_kind="bars",
        symbol="EURUSD",
        timeframe="M1",
        records=(bar,),
        start=_START,
        end=_START,
        available_at=_START,
        record_count=1,
        quality_report=report,
        source_metadata={"source": "mt5"},
        license_metadata={"license": "fixture-only"},
        cache_status="not_used",
        workflow_context="research",
        precision_policy="decimal_string",
        request_id=_REQUEST_ID,
    )
    err = build_data_error(
        "VALIDATION_FAILED", safe_details={"op": "usage"}, request_id=_REQUEST_ID
    )
    err_def = build_error_definition(
        "TEST", "data", "usage", False, "info", "test error", "none"
    )

    print(
        f"\nData -> OHLCVRecord(symbol={bar.source_symbol}, close={bar.close}), "
        f"\nTickRecord(bid={tick.bid}, ask={tick.ask}), "
        f"\nSpreadRecord(spread={spread.spread}), "
        f"\nMarketDataset(symbol={dataset.symbol}, records={dataset.record_count}), "
        f"\nDataError(code={err.code}), ErrorDef={err_def.code}"
    )
    return dataset


def _run_stage_2_sources() -> None:
    _print_stage(
        2,
        "Data Source Governance (FEAT-DATA-10)",
        "List registered/composable sources, build source descriptor, evaluate policy.",
    )
    composable = list_composable_sources()
    ensure_source("mt5", _REQUEST_ID)
    registered = list_registered_sources()
    desc_res = get_source_descriptor("mt5")

    mkt_req = build_market_data_request(
        source_id="mt5",
        symbol="EURUSD",
        data_kind="bars",
        timeframe="M1",
        start=_START,
        end=_END,
        limit=100,
        use_cache=True,
        quality_failure_behavior="warn",
        workflow_context="research",
        precision_policy="decimal_string",
        request_id=_REQUEST_ID,
    )
    eval_policy = evaluate_source_policy(mkt_req)

    print(
        f"\nData -> Registered Sources={len(registered.data or [])}, "
        f"\nComposable Sources={len(composable.data or [])}, "
        f"\nDescriptor Status='{desc_res.status}', "
        f"\nPolicy Evaluated Status='{eval_policy.status}'"
    )


def _run_stage_3_persistence(dataset: Any, root: Path) -> None:
    _print_stage(
        3,
        "Persistence, Transactions & Cache (FEAT-DATA-06)",
        "Run migrations, acquire path-scoped write locks, test cache storage, and execute transactions.",
    )
    mig_res = run_data_migrations(_REQUEST_ID)
    lock_res = acquire_write_lock(root / "lock.target", _REQUEST_ID)

    write_req = build_cache_write_request(
        dataset=dataset,
        key="cache-key-pipeline-1",
        ttl_seconds=300,
        source_revision="rev-1",
        raw_data_hash="hash-1",
        request_id=_REQUEST_ID,
    )
    put_res = put_cache_entry(write_req)

    read_req = build_cache_read_request(
        key="cache-key-pipeline-1",
        allow_stale=False,
        request_id=_REQUEST_ID,
    )
    cached = get_cache_entry(read_req)
    cleared = clear_data_cache(request_id=_REQUEST_ID)

    stmt_plan = build_statement_plan(
        statements=("SELECT 1;",),
        parameter_sets=((),),
        max_rows=10,
    )
    tx_req = build_transaction_request(plan=stmt_plan, request_id=_REQUEST_ID)
    tx_res = execute_transaction(tx_req)

    print(
        f"\nData -> Migration Status='{mig_res.status}', "
        f"\nLock Status='{lock_res.status}', "
        f"\nCache Put='{put_res.status}', "
        f"\nCache Retrieved Status='{cached.status}', "
        f"\nCache Cleared='{cleared.status}', "
        f"\nTx Status='{tx_res.status}'"
    )


def _run_stage_4_retrieval() -> None:
    _print_stage(
        4,
        "Market Data Retrieval & Availability (FEAT-DATA-02)",
        "Discover symbols, fetch symbol metadata, retrieve OHLCV/tick/spread series and check availability.",
    )
    sym_list_req = build_symbol_list_request(
        source_id="mt5", limit=10, request_id=_REQUEST_ID
    )
    symbols = list_symbols(sym_list_req)
    discovered = discover_symbols(sym_list_req)

    meta_req = build_symbol_metadata_request(
        source_id="mt5", symbol="EURUSD", request_id=_REQUEST_ID
    )
    meta = fetch_symbol_metadata(meta_req)

    mkt_req = build_market_data_request(
        source_id="mt5",
        symbol="EURUSD",
        data_kind="bars",
        timeframe="M1",
        start=_START,
        end=_END,
        limit=100,
        use_cache=True,
        quality_failure_behavior="warn",
        workflow_context="research",
        precision_policy="decimal_string",
        request_id=_REQUEST_ID,
    )
    bars_res = get_market_data(mkt_req)

    avail_req = build_availability_request(
        source_id="mt5",
        symbol="EURUSD",
        data_kind="ohlcv",
        timeframe="M1",
        start=_START,
        end=_END,
        max_probe_records=100,
        request_id=_REQUEST_ID,
    )
    avail = inspect_availability(avail_req)

    print(
        f"\nData -> Symbols Status='{symbols.status}', "
        f"\nDiscovered Status='{discovered.status}', "
        f"\nMetadata Status='{meta.status}', "
        f"\nBars Status='{bars_res.status}', "
        f"\nAvail Status='{avail.status}'"
        f"\nBars=\n{to_ohlcv_dataframe(bars_res.data)}, "
    )


def _run_stage_5_local_datasets(dataset: Any, root: Path) -> None:
    _print_stage(
        5,
        "Local Dataset Loading & Storage (FEAT-DATA-03)",
        "Save MarketDataset to local disk and reload via manifest-verified dataset loaders.",
    )
    rel_path = Path("data/raw/EURUSD_M1.parquet")
    save_req = build_dataset_save_request(
        dataset=dataset,
        relative_path=rel_path,
        format="parquet",
        overwrite=True,
        request_id=dataset.request_id,
    )
    saved = save_market_data(save_req)

    load_req = build_dataset_load_request(
        relative_path=rel_path, format="parquet", request_id=_REQUEST_ID
    )
    loaded = load_dataset(load_req)
    loaded_local = load_local_dataset(load_req)

    print(
        f"\nData -> Save Status='{saved.status}', "
        f"\nLoad Status='{loaded.status}', "
        f"\nLocal Load Status='{loaded_local.status}'"
    )


def _run_stage_6_synthetic() -> Any:
    _print_stage(
        6,
        "Synthetic Data Generation (FEAT-DATA-04)",
        "Generate reproducible synthetic bar and tick series with fixed random seed.",
    )
    req = build_synthetic_request(
        symbol="EURUSD",
        data_kind="bars",
        timeframe="M1",
        start=_START,
        record_count=5,
        method="gbm",
        seed=42,
        parameters={
            "mu": Decimal("0.02"),
            "sigma": Decimal("0.10"),
            "start_val": Decimal("1.1000"),
        },
        precision_policy="decimal_string",
        request_id=_REQUEST_ID,
    )
    syn_bars = generate_synthetic_bars(req)
    syn_ticks = generate_synthetic_ticks(req.model_copy(update={"data_kind": "ticks"}))

    print(
        f"\nData -> Synthetic Bars Count={len(syn_bars.data.records if syn_bars.data else [])}, "
        f"\nSynthetic Ticks Count={len(syn_ticks.data.records if syn_ticks.data else [])}"
        f"\nSynthetic Bars=\n{to_ohlcv_dataframe(syn_bars.data)}"
    )
    return syn_bars.data


def _run_stage_7_tick_derivation(syn_bars_dataset: Any) -> None:
    _print_stage(
        7,
        "Tick-Series Derivation (FEAT-DATA-05)",
        "Derive fixed-point tick series from bar series.",
    )
    derived = generate_tick_series(
        syn_bars_dataset,
        model="trading_bar",
        trading_timeframe="M1",
        request_id=_REQUEST_ID,
    )
    print(
        f"\nData -> Derived Ticks Status='{derived.status}', "
        f"\nDerived Ticks Count={len(derived.data.records if derived.data else [])}"
        f"\nDerived Ticks=\n{to_tick_dataframe(derived.data)}"
    )


def _run_stage_8_quality(dataset: Any) -> None:
    _print_stage(
        8,
        "Data Quality & Adversarial Validation (FEAT-DATA-07)",
        "Inspect series for gaps, spikes, zero volume, flat lines, and validate metadata.",
    )
    qual_res = inspect_dataset_quality(dataset)
    gaps = detect_timestamp_gaps(dataset.records, timeframe="M1")
    zero_vol = detect_zero_volume_bars(dataset.records)
    jumps = detect_price_jumps(dataset.records)

    sym_meta = build_symbol_metadata(
        canonical_symbol="EURUSD",
        provider_symbol="EURUSD",
        asset_class="fx",
        base_currency="EUR",
        quote_currency="USD",
        digits=5,
        price_step=Decimal("0.00001"),
        quantity_step=Decimal("0.01"),
        source_id="mt5",
        revision="r1",
        retrieved_at=_START,
        request_id=_REQUEST_ID,
    )
    meta_val = validate_symbol_metadata(sym_meta)
    policy = get_quality_policy()
    remed = summarize_quality_remediation(qual_res.data or dataset.quality_report)

    report_data = qual_res.data or dataset.quality_report
    print(
        f"\nData -> Quality Report: status='{report_data.quality_status}', score={report_data.quality_score}, issues={len(report_data.issues)}, records={report_data.record_count}"
        f"\nDetected Gaps={gaps.data}"
        f"\nZero Volume={zero_vol.data}"
        f"\nPrice Jumps={jumps.data}"
        f"\nSymbol Meta Valid={meta_val.data.provider_symbol}"
        f"\nQuality Policy={policy.data.profile if policy.data else None}"
        f"\nRemediation Summary={remed.data}"
    )


def _run_stage_9_transformation(dataset: Any) -> None:
    _print_stage(
        9,
        "Data Transformation & Resampling (FEAT-DATA-08)",
        "Resample datasets, aggregate ticks to bars, align multi-timeframe series, and project DataFrames.",
    )
    resampled = resample_dataset(dataset, target_timeframe="M5")
    resample_ohlcv_res = resample_ohlcv(dataset, target_timeframe="M5")

    tick = build_tick_record(
        timestamp=_START,
        source="mt5",
        source_symbol="EURUSD",
        available_at=_START,
        bid=Decimal("1.1000"),
        ask=Decimal("1.1002"),
        last=Decimal("1.1001"),
        volume=Decimal(1),
        price_unit="quote",
        volume_unit="ticks",
    )
    tick_ds = dataset.model_copy(
        update={
            "data_kind": "ticks",
            "timeframe": None,
            "records": (tick,),
        }
    )
    agg_bars = aggregate_ticks_to_bars(tick_ds, "M1", "last")
    aligned = align_datasets({"M1": dataset}, target=[_START])
    aligned_mtf = align_multitimeframe_data({"M1": dataset}, target_timestamps=[_START])
    df = to_ohlcv_dataframe(dataset)

    print(
        f"Data -> resampled_status='{resampled.status}', "
        f"resampled_ohlcv_status='{resample_ohlcv_res.status}', "
        f"aggregated_bars_status='{agg_bars.status}', "
        f"aligned_status='{aligned.status}', "
        f"mtf_aligned_status='{aligned_mtf.status}', "
        f"dataframe_rows={len(df) if df is not None else 0}"
    )


def _run_stage_10_time_sessions() -> None:
    _print_stage(
        10,
        "Time & Session Handling (FEAT-DATA-09)",
        "Query market hours, exchange sessions, active market sessions, forex named sessions, and classify gaps.",
    )
    hours_req = build_market_hours_request(
        source_id="ctrader", symbol="EURUSD", request_id=_REQUEST_ID
    )
    hours = get_market_hours(hours_req)
    exch_req = build_exchange_session_request(
        symbol="EURUSD",
        calendar_code="XNYS",
        start=_START.date(),
        end=_END.date(),
        request_id=_REQUEST_ID,
    )
    exch = get_exchange_sessions(exch_req)
    active_req = build_active_market_sessions_request(
        symbol="EURUSD", at=_START, request_id=_REQUEST_ID
    )
    active = get_active_market_sessions(active_req)
    forex_sessions = get_forex_named_sessions()
    sessions_dict = (
        forex_sessions.data
        if hasattr(forex_sessions, "data") and forex_sessions.data
        else forex_sessions
    )
    gap_kind = classify_gap(_START, _START + timedelta(hours=2))
    tf_spec = get_timeframe_spec("M1")

    print(
        f"Data -> market_hours_status='{hours.status}', "
        f"exchange_sessions_count={len(exch.data or [])}, "
        f"active_sessions_count={len(active.data.sessions if active.data else [])}, "
        f"forex_named_sessions={list(sessions_dict.keys() if isinstance(sessions_dict, dict) else [])}, "
        f"gap_kind='{gap_kind.data if hasattr(gap_kind, 'data') else gap_kind}', "
        f"timeframe_spec_seconds={tf_spec.data.duration.total_seconds() if tf_spec.data else None}"
    )


def _run_stage_11_economic_calendar() -> None:
    _print_stage(
        11,
        "Economic Calendar (FEAT-DATA-11)",
        "Query economic calendar portals, store and inspect economic events, check news restrictions.",
    )
    sites = get_calendar_sites()
    event = build_economic_event(
        id="evt-1",
        provider="fixture",
        name="FOMC Rate Decision",
        category=None,
        country="USD",
        currency="USD",
        scheduled_at=_START,
        impact=build_event_impact(3),
        actual=Decimal("5.25"),
        forecast=Decimal("5.25"),
        previous=Decimal("5.00"),
        revised_previous=None,
        actual_raw="5.25%",
        forecast_raw="5.25%",
        previous_raw="5.00%",
        unit="percent",
        source="fixture",
        source_url=None,
        updated_at=None,
    )
    store = build_economic_event_store()
    persisted = persist_economic_events([event], store=store, request_id=_REQUEST_ID)
    events_res = get_persisted_events(
        _START - timedelta(days=1),
        _END + timedelta(days=1),
        store=store,
        request_id=_REQUEST_ID,
    )
    restricted = is_news_restricted_events([event], at=_START)

    sites_count = len(sites.data if hasattr(sites, "data") and sites.data else sites)

    print(
        f"Data -> calendar_sites_count={sites_count}, "
        f"persisted_status='{persisted.status}', "
        f"retrieved_events_status='{events_res.status}', "
        f"is_news_restricted={restricted.data if hasattr(restricted, 'data') else restricted}"
    )


def _run_stage_12_realtime_feeds() -> None:
    _print_stage(
        12,
        "Real-Time Feed Lifecycle & Observability (FEAT-DATA-12)",
        "Configure internal feeds, ingest feed events, and query feed status.",
    )
    reconnect_pol = build_reconnect_policy(
        max_retries=3,
        initial_backoff_seconds=1,
        max_backoff_seconds=10,
        jitter_seconds=1,
        circuit_cooldown_seconds=30,
    )
    config = build_feed_config(
        feed_id="feed-eurusd-1",
        source_id="mt5",
        symbol="EURUSD",
        data_kind="tick",
        source_capability="ticks",
        buffer_capacity=100,
        overflow_policy="drop_and_reconcile",
        heartbeat_timeout_seconds=10,
        reconnect_policy=reconnect_pol,
        request_id=_REQUEST_ID,
    )
    started = start_internal_feed(config)
    raw_event = build_raw_feed_event(
        feed_id="feed-eurusd-1",
        sequence=1,
        event_timestamp=_START,
        received_at=_START,
        payload={"bid": "1.1000", "ask": "1.1002"},
        request_id=_REQUEST_ID,
    )
    ingested = ingest_feed_event("feed-eurusd-1", raw_event)
    feed_status_req = build_feed_status_request(
        feed_id="feed-eurusd-1", request_id=_REQUEST_ID
    )
    status = read_feed_status(feed_status_req)
    feed_status_obj = get_feed_status(feed_status_req)

    print(
        f"Data -> feed_started='{started.state}', "
        f"event_ingested='{ingested.accepted}', "
        f"feed_status_read='{status.state}', "
        f"feed_state='{feed_status_obj.data.state if hasattr(feed_status_obj, 'data') and feed_status_obj.data else feed_status_obj.state}'"
    )


def _run_stage_13_data_jobs() -> None:
    _print_stage(
        13,
        "Scheduler & Data Job Management (FEAT-DATA-13)",
        "Build, start, query, run-once, and stop background data update jobs.",
    )
    job_def = build_job_definition(
        job_id="job-backfill-eurusd",
        source_id="mt5",
        symbols=("EURUSD",),
        timeframes=("M1",),
        data_kinds=("ohlcv",),
        start=_START,
        end=_END,
        interval_seconds=60,
        enabled=True,
        created_at=_START,
        request_id=_REQUEST_ID,
    )
    created = create_data_update_job(job_def, request_id=_REQUEST_ID)
    started = start_data_update_job("job-backfill-eurusd", request_id=_REQUEST_ID)
    job_stat_req = build_job_status_request(
        job_id="job-backfill-eurusd", request_id=_REQUEST_ID
    )
    status = get_data_update_job_status(job_stat_req)
    ran = run_data_update_job_once("job-backfill-eurusd", request_id=_REQUEST_ID)
    stopped = stop_data_update_job("job-backfill-eurusd", request_id=_REQUEST_ID)

    print(
        f"Data -> job_created='{created.job_id if hasattr(created, 'job_id') else created}', "
        f"job_started='{started.state if hasattr(started, 'state') else started}', "
        f"job_status='{status.state if hasattr(status, 'state') else status}', "
        f"job_run_once='{ran.state if hasattr(ran, 'state') else ran}', "
        f"job_stopped='{stopped.state if hasattr(stopped, 'state') else stopped}'"
    )


def _run_stage_14_evidence() -> None:
    _print_stage(
        14,
        "Cross-Domain Normalized Evidence (FEAT-DATA-14)",
        "Provide fail-closed MarketContextEvidence, FXConversionEvidence, and AccountStateSnapshot.",
    )

    class _ContextProvider:
        def get_market_context(self, _request: object) -> object:
            request_id = getattr(_request, "request_id", generate_id("req"))
            as_of = getattr(_request, "as_of", _START)
            return run_data_operation(
                operation="data.evidence.market_context_provider.get_market_context",
                request_id=request_id,
                start_time=data_start_time(),
                raw=lambda: build_market_context_evidence(
                    symbol=getattr(_request, "symbol", "EURUSD"),
                    session_state=None,
                    calendar_state=None,
                    spread=Decimal("0.00015"),
                    spread_unit="quote_currency",
                    liquidity=None,
                    volatility=None,
                    correlations={},
                    crisis_flags=(),
                    timezone=getattr(_request, "timezone", "UTC"),
                    as_of=as_of,
                    expires_at=as_of + timedelta(seconds=60),
                    provenance={"source": "mt5"},
                    missing_fields=("session", "calendar", "liquidity", "volatility"),
                    request_id=request_id,
                ),
            )

    class _FXProvider:
        def get_rate_leg(
            self,
            *,
            source_currency: str,
            target_currency: str,
            as_of: datetime,
            request_id: str,
        ) -> object:
            return run_data_operation(
                operation="data.evidence.fx_rate_provider.get_rate_leg",
                request_id=request_id,
                start_time=data_start_time(),
                raw=lambda: build_fx_rate_leg(
                    source_currency=source_currency,
                    target_currency=target_currency,
                    rate=Decimal("1.0850"),
                    source_id="mt5",
                    provider_symbol=f"{source_currency}{target_currency}",
                    as_of=as_of,
                    provenance={"source": "mt5-observation"},
                ),
            )

    ctx_req = build_market_context_request(
        symbol="EURUSD",
        max_age_seconds=60,
        requested_evidence=("spread",),
        timezone="UTC",
        as_of=_START,
        request_id=_REQUEST_ID,
    )
    ctx_ev = get_market_context_evidence(ctx_req, _ContextProvider())

    fx_req = build_fx_conversion_request(
        source_currency="EUR",
        target_currency="USD",
        as_of=_START,
        max_age_seconds=300,
        allowed_intermediates=("GBP",),
        max_legs=2,
        path_policy_id="direct-first",
        path_policy_version="v1",
        request_id=_REQUEST_ID,
    )
    fx_ev = get_fx_conversion_evidence(fx_req, _FXProvider())

    adapter = asyncio.run(create_connected_broker("mt5"))
    try:
        account_info = asyncio.run(adapter.get_account_info())
        if account_info.status != "success":
            raise RuntimeError(f"Account-info request failed: {account_info.status}")
        account_data = account_info.data
        if account_data is None:
            raise RuntimeError("Account-info response had no data")

        acc_req = build_account_snapshot_request(
            source_id="mt5",
            account_id=account_data.account_id,
            max_age_seconds=315360000,
            request_id=_REQUEST_ID,
        )
        acc_ev = get_account_state_snapshot(acc_req, adapter)
    finally:
        asyncio.run(disconnect_broker(adapter))

    print(
        f"Data -> market_context_status='{ctx_ev.status}', "
        f"fx_conversion_status='{fx_ev.status}', "
        f"account_snapshot_status='{acc_ev.status}'"
    )


def _run_stage_15_audit() -> None:
    _print_stage(
        15,
        "Audit Evidence & Durable Querying (FEAT-DATA-15)",
        "Persist redacted audit events and execute authorized bounded audit queries.",
    )
    audit_evt = create_audit_event(
        contract_version="v1",
        schema_id="utils.audit_event.v1",
        event_id=generate_id("evt"),
        timestamp=_START,
        domain="data",
        action="usage_test",
        principal_id="user_admin",
        request_id=_REQUEST_ID,
        correlation_id=generate_id("cor"),
        causation_id=generate_id("cau"),
        payload={"status": "ok"},
    )
    persisted = persist_audit_event(audit_evt)
    query_req = build_audit_event_query(
        start=_START - timedelta(days=1),
        end=_END + timedelta(days=1),
        domain="data",
        limit=10,
        request_id=_REQUEST_ID,
    )
    auth_ctx = create_auth_context(
        principal_id="user_admin",
        principal_type="USER",
        roles=("admin",),
        permissions=("audit:read",),
        scopes=("audit",),
        tenant_or_environment="dev",
        request_id=_REQUEST_ID,
        workflow_id=generate_id("wf"),
        correlation_id=generate_id("cor"),
        issued_at=_START,
    )
    query_res = query_audit_events(query_req, auth_context=auth_ctx)

    print(
        f"Data -> audit_event_persisted='{persisted.status}', "
        f"audit_query_status='{query_res.status}', "
        f"retrieved_audit_events={len(query_res.data.events if query_res.data else [])}"
    )


def _run_stage_16_research_sources() -> None:
    _print_stage(
        16,
        "Point-in-Time Research Source Evidence (FEAT-DATA-16)",
        "Validate research policies, ingest research evidence, query decision-time documents, and assess eligibility.",
    )
    policy = build_research_source_policy(
        "policy-federal-reserve-v1",
        "federal-reserve",
        ("www.federalreserve.gov",),
        ("dev",),
        ("research",),
        ("US",),
        False,
        30,
        10,
        60.0,
        None,
    )

    ingest_req = build_research_source_ingest_request(
        source_url="https://www.federalreserve.gov/feeds/press_all.xml",
        source_id="federal-reserve",
        source_kind="macro",
        external_id="press-release-1",
        title="Federal Reserve Board",
        asset_scope=("EURUSD", "USD"),
        issuer_scope=(),
        language="en",
        event_at=None,
        published_at=_START - timedelta(minutes=5),
        available_at=_START,
        decision_use="research",
        environment="dev",
        license_id="public-official-feed",
        currency="USD",
        unit=None,
        request_id=_REQUEST_ID,
    )
    validate_research_source_policy(ingest_req, policy, now=_START)
    doc = ingest_research_source(ingest_req, policy=policy, now=_START)

    search_query = build_research_source_query(
        decision_time=_START,
        source_kinds=("macro",),
        asset_scope=("EURUSD",),
    )
    search_res = query_research_sources(search_query)
    eligibility = assess_research_source_eligibility(doc, decision_time=_START)
    projected = project_research_source_evidence(doc)

    print(
        f"Data -> document_ingested_id='{doc.document_id if hasattr(doc, 'document_id') else doc}', "
        f"query_sources_count={len(search_res.records if hasattr(search_res, 'records') else [])}, "
        f"eligibility_is_eligible={eligibility.is_eligible if hasattr(eligibility, 'is_eligible') else eligibility}, "
        f"projected_locator='{projected.get('canonical_locator')}'"
    )


def main() -> None:
    """Execute complete end-to-end Data domain pipeline."""
    print("=" * 88)
    print("DATA DOMAIN: FULL HOMOGENEOUS END-TO-END PIPELINE EXAMPLE")
    print(
        "Ties FEAT-DATA-01 through FEAT-DATA-16 sequentially in realistic runtime order."
    )
    print("=" * 88)

    with tempfile.TemporaryDirectory(prefix="data-pipeline-features-") as tmp_dir:
        root_resolved = Path(tmp_dir).resolve()
        settings = build_data_settings(
            database_url="sqlite:///data_pipeline.db",
            data_dir=root_resolved,
            sqlite_busy_timeout_seconds=1.0,
            write_lock_lease_seconds=10.0,
            approved_storage_roots=(
                Path(),
                Path("raw"),
                Path("processed"),
                Path("data"),
                Path("data/raw"),
                Path("data/processed"),
            ),
            data_provider_sources=("mt5", "ctrader", "csv"),
            data_raw_root=Path("data/raw"),
            data_processed_root=Path("data/processed"),
        )
        with data_settings_context(settings):
            dataset = _run_stage_1_contracts()
            _run_stage_2_sources()
            _run_stage_3_persistence(dataset, root_resolved)
            _run_stage_4_retrieval()
            _run_stage_5_local_datasets(dataset, root_resolved)
            syn_bars = _run_stage_6_synthetic()
            _run_stage_7_tick_derivation(syn_bars)
            _run_stage_8_quality(dataset)
            _run_stage_9_transformation(dataset)
            _run_stage_10_time_sessions()
            _run_stage_11_economic_calendar()
            _run_stage_12_realtime_feeds()
            _run_stage_13_data_jobs()
            _run_stage_14_evidence()
            _run_stage_15_audit()
            _run_stage_16_research_sources()

    print("\n" + "=" * 88)
    print("Data -> full_domain_pipeline_status='completed'")
    print("SUCCESS: All 16 Data domain features executed in realistic pipeline order!")
    print("=" * 88)


if __name__ == "__main__":
    main()
