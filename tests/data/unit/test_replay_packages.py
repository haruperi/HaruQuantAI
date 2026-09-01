"""Unit tests for deterministic no-lookahead replay packages (feature)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest
from app.kernel.identity import generate_id
from app.services.data import build_replay_package, parse_replay_package
from app.services.data.contracts import DataError
from app.services.data.replay import packages as service

_T0 = datetime(2026, 8, 7, 12, tzinfo=UTC)


def _fake_dataset(records: tuple[SimpleNamespace, ...]) -> SimpleNamespace:
    """Return one structural dataset fixture carrying the supplied records."""
    return SimpleNamespace(records=records)


def _record(available_at: datetime) -> SimpleNamespace:
    """Return one structural canonical-record fixture."""
    return SimpleNamespace(available_at=available_at, timestamp=available_at)


@pytest.fixture
def isolated_replay(monkeypatch: pytest.MonkeyPatch):
    """Replace source access and dataset retrieval with deterministic fakes."""
    from app.services.data.sources import composition

    monkeypatch.setattr(composition, "ensure_storage", lambda *_args: None)
    monkeypatch.setattr(composition, "ensure_identity", lambda *_args: None)


def test_build_replay_package_validates_symbols_and_coverage() -> None:
    """A package requires at least one symbol and start before end."""
    package = build_replay_package(
        source_id="mt5",
        symbols=("EURUSD", "GBPUSD"),
        data_kind="ticks",
        start=_T0,
        end=_T0 + timedelta(days=1),
        request_id=generate_id("req"),
    )
    assert package.symbols == ("EURUSD", "GBPUSD")

    with pytest.raises(DataError, match="INVALID_INPUT"):
        build_replay_package(
            source_id="mt5",
            symbols=(),
            data_kind="ticks",
            start=_T0,
            end=_T0 + timedelta(days=1),
            request_id=generate_id("req"),
        )


def test_build_replay_package_requires_timeframe_for_bars() -> None:
    """A bars package without a timeframe fails closed."""
    with pytest.raises(DataError, match="INVALID_INPUT"):
        build_replay_package(
            source_id="mt5",
            symbols=("EURUSD",),
            data_kind="bars",
            timeframe=None,
            start=_T0,
            end=_T0 + timedelta(days=1),
            request_id=generate_id("req"),
        )


def test_replay_package_round_trips_through_json_mapping() -> None:
    """`parse_replay_package` reconstructs what `build_replay_package` built."""
    package = build_replay_package(
        source_id="mt5",
        symbols=("EURUSD",),
        data_kind="ticks",
        start=_T0,
        end=_T0 + timedelta(days=1),
        request_id=generate_id("req"),
    )
    mapping = package.model_dump(mode="json")
    reparsed = parse_replay_package(mapping)
    assert reparsed == package


def test_stream_replay_events_excludes_events_not_yet_available(
    isolated_replay: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    """No event whose `available_at` exceeds `as_of` is ever yielded."""
    del isolated_replay
    visible = _record(_T0)
    future = _record(_T0 + timedelta(hours=1))
    monkeypatch.setattr(
        service,
        "_fetch_market_dataset_raw",
        lambda _request: _fake_dataset((visible, future)),
    )
    package = build_replay_package(
        source_id="mt5",
        symbols=("EURUSD",),
        data_kind="ticks",
        start=_T0,
        end=_T0 + timedelta(days=1),
        request_id=generate_id("req"),
    )

    events = list(service.stream_replay_events(package, as_of=_T0))

    assert len(events) == 1
    assert events[0].available_at == _T0
    assert events[0].sequence == 0


def test_stream_replay_events_orders_deterministically_across_symbols(
    isolated_replay: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Events from multiple symbols interleave by (available_at, symbol)."""
    del isolated_replay

    def _fake_fetch(request: object) -> SimpleNamespace:
        symbol = request.symbol  # type: ignore[attr-defined]
        offset = timedelta(seconds=1) if symbol == "GBPUSD" else timedelta(0)
        return _fake_dataset((_record(_T0 + offset),))

    monkeypatch.setattr(service, "_fetch_market_dataset_raw", _fake_fetch)
    package = build_replay_package(
        source_id="mt5",
        symbols=("GBPUSD", "EURUSD"),
        data_kind="ticks",
        start=_T0,
        end=_T0 + timedelta(days=1),
        request_id=generate_id("req"),
    )

    events = list(service.stream_replay_events(package, as_of=_T0 + timedelta(hours=1)))

    assert [event.symbol for event in events] == ["EURUSD", "GBPUSD"]
    assert [event.sequence for event in events] == [0, 1]


def test_stream_replay_events_rejects_naive_as_of(
    isolated_replay: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A naive `as_of` fails closed rather than silently assuming UTC."""
    del isolated_replay
    monkeypatch.setattr(
        service, "_fetch_market_dataset_raw", lambda _request: _fake_dataset(())
    )
    package = build_replay_package(
        source_id="mt5",
        symbols=("EURUSD",),
        data_kind="ticks",
        start=_T0,
        end=_T0 + timedelta(days=1),
        request_id=generate_id("req"),
    )

    with pytest.raises(ValueError, match="as_of must be timezone-aware UTC"):
        list(service.stream_replay_events(package, as_of=_T0.replace(tzinfo=None)))
