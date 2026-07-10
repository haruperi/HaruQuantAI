"""Tests for the supplemental brownfield hardening tasks (DATA-UPG-056..064).

Covers: the central limits manifest, source readiness/license enforcement,
credential redaction in broker failure paths, local path safety, market/session
calendar deferral, and golden dataset fixtures for downstream regression tests.
"""

import json
from pathlib import Path

import pytest
from app.services.data import feeds, validation
from app.services.data.gateway import get_data
from app.services.data.models import OHLCVRecord, TickRecord
from app.services.data.sources import BrokerBackedAdapter
from app.services.data.validation import (
    SOURCE_READINESS_REGISTRY,
    VALID_SOURCE_READINESS_STATES,
    validate_source_readiness,
)
from app.utils.errors import ExternalServiceError, ValidationError

GOLDEN_FIXTURES_DIR = Path("tests/fixtures/data/golden")


# --- DATA-UPG-056: central limits manifest -----------------------------------
def test_central_limits_manifest_values_are_documented() -> None:
    """Verify the documented limits manifest matches the source constants."""
    assert (validation.DEFAULT_OHLCV_LIMIT, validation.MAX_OHLCV_LIMIT) == (5000, 50000)
    assert (validation.DEFAULT_TICK_LIMIT, validation.MAX_TICK_LIMIT) == (10000, 250000)
    assert (validation.DEFAULT_SPREAD_LIMIT, validation.MAX_SPREAD_LIMIT) == (
        10000,
        250000,
    )
    assert validation.MAX_SYNTHETIC_BARS == 100000
    assert validation.MAX_SYNTHETIC_TICKS == 250000
    assert validation.MAX_PERSISTED_SYNTHETIC_SIZE == 1000000
    assert validation.DEFAULT_BACKFILL_OHLCV_CHUNK_RECORDS == 100000
    assert validation.DEFAULT_BACKFILL_OHLCV_CHUNK_DAYS == 30
    assert validation.DEFAULT_BACKFILL_TICK_CHUNK_RECORDS == 1000000
    assert validation.DEFAULT_BACKFILL_TICK_CHUNK_DAYS == 1
    assert validation.DEFAULT_CACHE_TTL_DAILY == 86400
    assert validation.DEFAULT_CACHE_TTL_INTRADAY == 3600
    assert validation.DEFAULT_CACHE_TTL_TICK == 900
    assert validation.DEFAULT_CACHE_TTL_LIVE == 0
    assert validation.MAX_CACHE_TTL_OVERRIDE_DAYS == 7
    assert validation.MAX_SYMBOLS_PER_JOB == 500
    assert validation.MAX_TIMEFRAMES_PER_JOB == 20
    assert validation.MIN_SCHEDULER_FREQUENCY_SECONDS == 60
    assert validation.RESAMPLE_PERFORMANCE_BENCHMARK_BARS == 100000
    assert validation.RESAMPLE_PERFORMANCE_THRESHOLD_SECONDS == 3.0
    assert feeds.DEFAULT_FEED_BUFFER_CAPACITY == 10000
    assert feeds.DEFAULT_HEARTBEAT_TIMEOUT_SECONDS == 30.0
    policy = feeds.DEFAULT_RECONNECT_POLICY
    assert (
        policy.max_retries,
        policy.base_backoff_seconds,
        policy.max_backoff_seconds,
        policy.jitter_ratio,
        policy.circuit_breaker_cooldown_seconds,
    ) == (5, 0.5, 30.0, 0.2, 60.0)


# --- DATA-UPG-060: source readiness and license manifest with enforcement ----
def test_source_readiness_registry_covers_every_adapter_source() -> None:
    """Verify every registered source adapter has a declared readiness state."""
    assert set(SOURCE_READINESS_REGISTRY) == {
        "csv",
        "parquet",
        "synthetic",
        "mt5",
        "ctrader",
        "dukascopy",
        "binance",
        "yahoo",
    }
    assert set(SOURCE_READINESS_REGISTRY.values()).issubset(
        VALID_SOURCE_READINESS_STATES
    )
    assert SOURCE_READINESS_REGISTRY["csv"] == "production"
    assert SOURCE_READINESS_REGISTRY["synthetic"] == "production"
    assert SOURCE_READINESS_REGISTRY["mt5"] == "staging"


def test_validate_source_readiness_allows_production_under_any_context() -> None:
    """Verify production-ready sources are allowed under every workflow context."""
    for context in (
        "research",
        "backtest",
        "validation",
        "risk",
        "execution_bound",
    ):
        assert validate_source_readiness("synthetic", context) == "production"


def test_validate_source_readiness_gates_staging_sources_under_risk_contexts() -> None:
    """Verify staging sources are rejected under risk/execution_bound contexts."""
    assert validate_source_readiness("mt5", "research") == "staging"
    with pytest.raises(ValidationError) as exc_info:
        validate_source_readiness("mt5", "risk")
    assert exc_info.value.code == "LICENSE_RESTRICTION"
    with pytest.raises(ValidationError) as exc_info:
        validate_source_readiness("mt5", "execution_bound")
    assert exc_info.value.code == "LICENSE_RESTRICTION"


def test_validate_source_readiness_rejects_not_available_source() -> None:
    """Verify an explicitly not_available source is always rejected."""
    validation.SOURCE_READINESS_REGISTRY["_test_disabled_source"] = "not_available"
    try:
        with pytest.raises(ValidationError) as exc_info:
            validate_source_readiness("_test_disabled_source", "research")
        assert exc_info.value.code == "UNSUPPORTED_OPERATION"
    finally:
        del validation.SOURCE_READINESS_REGISTRY["_test_disabled_source"]


def test_get_data_enforces_source_readiness_for_risk_workflow() -> None:
    """Verify the gateway rejects a staging source under a risk workflow context."""
    with pytest.raises(ValidationError):
        get_data(
            symbol="EURUSD",
            start_time="2026-06-01T00:00:00Z",
            end_time="2026-06-01T01:00:00Z",
            data_kind="ohlcv",
            timeframe="M1",
            source="ctrader",
            workflow_context="execution_bound",
        )


def test_create_data_update_job_enforces_source_readiness() -> None:
    """Verify scheduler job creation rejects a not_available source (DATA-FR-040)."""
    from app.services.data.scheduler import create_data_update_job

    validation.SOURCE_READINESS_REGISTRY["_test_disabled_source"] = "not_available"
    try:
        with pytest.raises(ValidationError) as exc_info:
            create_data_update_job(
                name="disabled_source_job",
                source="_test_disabled_source",
                symbols=["EURUSD"],
                timeframes=["M1"],
                data_kind="ohlcv",
                storage_format="csv",
                storage_path="data/raw",
            )
        assert exc_info.value.code == "UNSUPPORTED_OPERATION"
    finally:
        del validation.SOURCE_READINESS_REGISTRY["_test_disabled_source"]


# --- DATA-UPG-059: credential and secret redaction ----------------------------
def test_broker_backed_adapter_redacts_credential_like_failure_text() -> None:
    """Verify broker connection failures are redacted before crossing the boundary."""

    class LeakyClient:
        connected = False

        def is_connected(self) -> bool:
            return self.connected

        def connect(self) -> None:
            raise RuntimeError("auth failed: password=hunter2 token=abcdef0123456789")

        def get_bars(self, **_kwargs: object) -> None:
            return None

        def get_ticks(self, **_kwargs: object) -> None:
            return None

    adapter = BrokerBackedAdapter(
        source="fake_leaky",
        client_factory=LeakyClient,
        unavailable_message="fake broker unavailable",
        error_code="BROKER_UNAVAILABLE",
        symbols=["EURUSD"],
        metadata={"ready": True},
    )
    from datetime import UTC, datetime

    with pytest.raises(ExternalServiceError) as exc_info:
        adapter.get_market_data(
            "EURUSD",
            "H1",
            datetime(2026, 6, 1, tzinfo=UTC),
            datetime(2026, 6, 2, tzinfo=UTC),
        )
    assert "hunter2" not in str(exc_info.value)


# --- DATA-UPG-058: local path safety verification ------------------------------
def test_approved_storage_roots_reject_absolute_and_traversal_paths() -> None:
    """Verify path safety rejects traversal, hidden segments, and unsafe roots."""
    from app.services.data.storage import validate_storage_path

    with pytest.raises(ValidationError):
        validate_storage_path("../../etc/passwd.csv")
    with pytest.raises(ValidationError):
        validate_storage_path("data/raw/.git/config.csv")
    with pytest.raises(ValidationError):
        validate_storage_path("C:/Windows/System32/evil.csv")
    with pytest.raises(ValidationError):
        validate_storage_path("data/raw/unsafe.exe")


# --- DATA-UPG-061: market/session calendar ownership --------------------------
def test_get_market_hours_discloses_historical_reconstruction_as_unsupported() -> None:
    """Verify get_market_hours only ever returns current configured hours."""
    hours = validation.get_market_hours("EURUSD")
    assert hours["historical_hours_supported"] is False


# --- DATA-UPG-062: golden fixtures and downstream contract alignment ----------
def test_golden_ohlcv_fixture_matches_canonical_contract() -> None:
    """Verify the golden OHLCV fixture validates against OHLCVRecord."""
    records = json.loads((GOLDEN_FIXTURES_DIR / "eurusd_m5_bars.json").read_text())
    assert len(records) == 20
    for record in records:
        validated = OHLCVRecord(**record)
        assert validated.symbol == "EURUSD"
        assert validated.timeframe == "M5"


def test_golden_tick_fixture_matches_canonical_contract() -> None:
    """Verify the golden tick fixture validates against TickRecord."""
    records = json.loads((GOLDEN_FIXTURES_DIR / "eurusd_ticks.json").read_text())
    assert len(records) == 20
    for record in records:
        validated = TickRecord(**record)
        assert validated.symbol == "EURUSD"


def test_golden_fixtures_are_reproducible_from_the_seeded_generator() -> None:
    """Verify the golden fixtures match fresh output from the same seed."""
    from app.services.data.transforms import generate_synthetic_bars

    fixture_bars = json.loads((GOLDEN_FIXTURES_DIR / "eurusd_m5_bars.json").read_text())
    regenerated = generate_synthetic_bars(
        "EURUSD", "M5", "2026-01-01T00:00:00Z", 20, 1.1000, 0.0001, 0.001, seed=20260101
    )
    assert fixture_bars == regenerated
