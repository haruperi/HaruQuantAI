"""Focused tests for small DATA validation and restoration boundaries."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace

import pytest
from app.services.data import (
    DataError,
    FeedConfig,
    MarketSchedule,
    ReconnectPolicy,
    SessionWindow,
    SymbolMetadata,
    SyntheticRequest,
)
from app.services.data.economic_calendar.normalization import (
    normalize_calendar_number,
)
from app.services.data.economic_calendar.parsing import parse_calendar_row
from app.services.data.evidence.freshness import is_fresh
from app.services.data.quality.asset_metadata import validate_symbol_metadata
from app.services.data.realtime_feeds.state import _restore_active_feed
from app.services.data.synthetic_data.provenance import SYNTHETIC_SOURCE
from app.services.data.synthetic_data.randomness import require_seed
from app.services.data.time_sessions import schedule
from app.utils import generate_id

_NOW = datetime(2026, 7, 23, 12, tzinfo=UTC)


def _feed_config() -> FeedConfig:
    """Return one deterministic feed configuration."""
    return FeedConfig(
        feed_id="feed-restore",
        source_id="fixture",
        symbol="EURUSD",
        data_kind="tick",
        source_capability="ticks",
        buffer_capacity=4,
        overflow_policy="drop_and_reconcile",
        heartbeat_timeout_seconds=10,
        reconnect_policy=ReconnectPolicy(
            max_retries=2,
            initial_backoff_seconds=1,
            max_backoff_seconds=4,
            jitter_seconds=0,
            circuit_cooldown_seconds=30,
        ),
        request_id=generate_id("req"),
    )


def _feed_row(config: FeedConfig) -> dict[str, None | bool | int | float | str]:
    """Return persisted feed controls matching a configuration."""
    return {
        "source_id": config.source_id,
        "symbol": config.symbol,
        "data_kind": config.data_kind,
        "timeframe": config.timeframe,
        "source_capability": config.source_capability,
        "buffer_capacity": config.buffer_capacity,
        "overflow_policy": config.overflow_policy,
        "heartbeat_timeout_seconds": config.heartbeat_timeout_seconds,
        "state": "running",
        "heartbeat_at": _NOW.isoformat(),
        "last_event_at": _NOW.isoformat(),
        "dropped_count": 1,
        "gap_count": 2,
        "reconnect_count": 3,
        "breaker_state": "open",
        "breaker_opened_at": _NOW.isoformat(),
        "drift_ms": 4,
        "last_error": "bounded",
        "buffer_depth": 0,
    }


def _metadata(**updates: object) -> SymbolMetadata:
    """Return complete deterministic symbol metadata."""
    values: dict[str, object] = {
        "canonical_symbol": "EURUSD",
        "provider_symbol": "EURUSD",
        "asset_class": "fx",
        "base_currency": "EUR",
        "quote_currency": "USD",
        "digits": 5,
        "price_step": Decimal("0.00001"),
        "quantity_step": Decimal("0.01"),
        "source_id": "fixture",
        "revision": "r1",
        "retrieved_at": _NOW,
        "request_id": generate_id("req"),
    }
    values.update(updates)
    return SymbolMetadata(**values)  # type: ignore[arg-type]


def test_small_normalization_and_freshness_boundaries() -> None:
    """Wrapper boundaries preserve exact values and reject unsafe freshness."""
    assert normalize_calendar_number("1.5K") == Decimal("1500.0")
    assert normalize_calendar_number("-") is None
    event = parse_calendar_row(
        "forexfactory",
        {
            "timestamp": "2026-07-23T12:00:00Z",
            "title": "Policy Rate",
            "country": "USD",
            "impact": "High",
            "actual": "1.5%",
            "forecast": "1.0%",
            "previous": "0.5%",
        },
    )
    assert event is not None
    assert event.actual == Decimal("1.5")
    assert is_fresh(_NOW - timedelta(seconds=5), _NOW, timedelta(seconds=5))
    assert not is_fresh(_NOW + timedelta(seconds=1), _NOW, timedelta(seconds=5))
    assert not is_fresh(
        _NOW.replace(tzinfo=None),
        _NOW,
        timedelta(seconds=5),
    )


def test_synthetic_seed_boundary_and_provenance() -> None:
    """Synthetic generation requires replayable seed evidence."""
    seeded = SyntheticRequest(
        symbol="EURUSD",
        data_kind="bars",
        timeframe="M1",
        start=_NOW,
        record_count=2,
        method="gbm",
        seed=7,
        parameters={
            "mu": Decimal("0.01"),
            "sigma": Decimal("0.10"),
            "start_val": Decimal("1.10"),
        },
        precision_policy="decimal_string",
        request_id=generate_id("req"),
    )
    unseeded = seeded.model_copy(update={"seed": None})
    assert require_seed(seeded) == 7
    with pytest.raises(ValueError, match="requires a seed"):
        require_seed(unseeded)
    assert SYNTHETIC_SOURCE == "synthetic"


def test_feed_restore_rehydrates_controls_and_blocks_volatile_depth() -> None:
    """Persisted controls restore exactly while volatile buffers fail closed."""
    config = _feed_config()
    row = _feed_row(config)
    active = _restore_active_feed(config, row, _NOW + timedelta(seconds=1))
    assert active.state == "running"
    assert active.heartbeat_at == _NOW
    assert active.breaker_opened_at == _NOW
    assert active.drift_ms == 4
    assert active.last_error == "bounded"

    row["buffer_depth"] = 1
    blocked = _restore_active_feed(config, row, _NOW)
    assert blocked.state == "blocked"
    assert blocked.last_error == "STATE_RECOVERY_FAILED"

    row["source_id"] = "different"
    with pytest.raises(DataError) as captured:
        _restore_active_feed(config, row, _NOW)
    assert captured.value.code == "VALIDATION_FAILED"


def test_symbol_metadata_validation_covers_required_precision_rules() -> None:
    """Governed metadata fails closed for missing or inconsistent precision."""
    valid = _metadata()
    assert validate_symbol_metadata(valid) is valid

    with pytest.raises(DataError) as missing:
        validate_symbol_metadata(_metadata(missing_fields=("asset_class",)))
    assert missing.value.code == "MISSING_ASSET_METADATA"

    with pytest.raises(DataError) as non_positive:
        validate_symbol_metadata(
            _metadata().model_copy(update={"quantity_step": Decimal(0)})
        )
    assert non_positive.value.code == "PRECISION_MISMATCH"

    with pytest.raises(DataError) as inconsistent:
        validate_symbol_metadata(_metadata(price_step=Decimal("0.01")))
    assert inconsistent.value.code == "PRECISION_MISMATCH"


def test_schedule_request_and_evidence_validation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Schedule calls validate style, view, provider errors, and evidence identity."""
    request_id = generate_id("req")
    request = schedule.schedule_request(
        None,
        view="hours",
        source_id="fixture",
        symbol="EURUSD",
        timezone=None,
        request_id=request_id,
    )
    assert request.timezone == "UTC"
    assert (
        schedule.schedule_request(
            request,
            view="hours",
            source_id=None,
            symbol=None,
            timezone=None,
            request_id=None,
        )
        is request
    )
    with pytest.raises(DataError):
        schedule.schedule_request(
            request,
            view="sessions",
            source_id=None,
            symbol=None,
            timezone=None,
            request_id=None,
        )

    monkeypatch.setattr(
        schedule,
        "get_source_descriptor",
        lambda _source_id: SimpleNamespace(readiness="production"),
    )
    observed_at = _NOW
    window = SessionWindow(
        label="open",
        opens_at=_NOW,
        closes_at=_NOW + timedelta(hours=1),
    )
    expected = MarketSchedule(
        source_id=request.source_id,
        symbol=request.symbol,
        timezone=request.timezone,
        hours=(window,),
        sessions=(window,),
        observed_at=observed_at,
        request_id=request.request_id,
    )

    class _Calendar:
        """Return one configured schedule."""

        def get_schedule(self, **_kwargs: object) -> MarketSchedule:
            """Return deterministic evidence."""
            return expected

    class _Clock:
        """Return one deterministic UTC instant."""

        def now(self) -> datetime:
            """Return the configured instant."""
            return observed_at

    clock = _Clock()

    assert (
        schedule.get_current_schedule(
            request,
            _Calendar(),
            clock=clock,
        )
        == expected
    )

    class _BrokenCalendar:
        """Raise a raw provider exception."""

        def get_schedule(self, **_kwargs: object) -> MarketSchedule:
            """Raise a provider failure."""
            raise RuntimeError("sensitive provider detail")

    with pytest.raises(DataError) as unavailable:
        schedule.get_current_schedule(
            request,
            _BrokenCalendar(),
            clock=clock,
        )
    assert unavailable.value.code == "SOURCE_UNAVAILABLE"

    stale = expected.model_copy(update={"symbol": "GBPUSD"})

    class _StaleCalendar:
        """Return mismatched schedule evidence."""

        def get_schedule(self, **_kwargs: object) -> MarketSchedule:
            """Return stale evidence."""
            return stale

    with pytest.raises(DataError) as stale_error:
        schedule.get_current_schedule(
            request,
            _StaleCalendar(),
            clock=clock,
        )
    assert stale_error.value.code == "STALE_EVIDENCE"
