"""Integration coverage for composed local-source retrieval through the API.

These tests exercise the capability that made local files unreachable before
`CAP-DATA-025`: composing a configured local source from settings and reading a
committed artifact back through the public retrieval boundary, with no broker
terminal, credentials, or network access.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest
from app.services.data._settings import (
    LOCAL_SYMBOL_MANIFEST_NAME,
    DataSettings,
    data_settings_context,
)
from app.services.data.contracts import DataError, OHLCVRecord
from app.services.data.sources import composition as _runtime
from app.services.data.sources.contracts import (
    SourceReadRequest,
)
from app.services.data.sources.registry import _reset_registry, resolve_source
from app.utils import generate_id

_SYMBOL = "EURUSD"
_START = datetime(2026, 1, 1, tzinfo=UTC)


@pytest.fixture(autouse=True)
def isolated_runtime() -> None:
    """Reset process-local composition state around every test."""
    _reset_registry()
    _runtime._calendars.clear()
    _runtime._sessions.clear()
    _runtime._migrated_targets.clear()
    yield
    _reset_registry()
    _runtime._calendars.clear()
    _runtime._sessions.clear()
    _runtime._migrated_targets.clear()


def _bar(index: int) -> OHLCVRecord:
    """Return one canonical bar offset by whole minutes from the window start."""
    timestamp = _START + timedelta(minutes=index)
    return OHLCVRecord(
        timestamp=timestamp,
        open=Decimal("1.1000"),
        high=Decimal("1.1010"),
        low=Decimal("1.0990"),
        close=Decimal("1.1005"),
        volume=Decimal(100),
        price_unit="USD",
        volume_unit="lots",
        source="csv",
        source_symbol=_SYMBOL,
        source_revision="local-artifact-v1",
        available_at=timestamp + timedelta(seconds=1),
    )


def _settings(tmp_path: Path) -> DataSettings:
    """Return settings rooting local composition at a temporary data directory."""
    return DataSettings(
        database_url=f"sqlite:///{tmp_path / 'data.db'}",
        data_dir=tmp_path,
        data_local_sources=("csv",),
        data_raw_root=Path("data/raw"),
    )


def _write_manifest(raw_root: Path) -> None:
    """Declare one operator-supplied local symbol."""
    (raw_root / LOCAL_SYMBOL_MANIFEST_NAME).write_text(
        json.dumps(
            {
                _SYMBOL: {
                    "asset_class": "forex",
                    "base_currency": "EUR",
                    "quote_currency": "USD",
                    "revision": "operator-v1",
                    "retrieved_at": "2026-01-01T00:00:00Z",
                    "missing_fields": ["digits", "price_step", "quantity_step"],
                }
            }
        ),
        encoding="utf-8",
    )


@pytest.fixture
def composed_root(tmp_path: Path) -> Path:
    """Return a raw root containing a declared symbol manifest."""
    raw_root = tmp_path / "data" / "raw"
    raw_root.mkdir(parents=True)
    _write_manifest(raw_root)
    return raw_root


def test_local_source_composes_without_credentials_or_network(
    tmp_path: Path,
    composed_root: Path,
) -> None:
    """A configured local source is reachable with no provider dependency."""
    with data_settings_context(_settings(tmp_path)):
        _runtime.ensure_source("csv", generate_id("req"))
        source = resolve_source("csv")

    assert source is not None
    assert "csv" in _runtime.list_composable_sources()


def test_local_source_reads_only_the_requested_window(
    tmp_path: Path,
    composed_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A bounded request returns its window, not the whole artifact."""
    (composed_root / f"{_SYMBOL}_1m.csv").touch()
    dataset_records = tuple(_bar(index) for index in range(10))

    from tests.data.helpers import make_dataset

    stored = make_dataset().model_copy(
        update={"records": dataset_records, "symbol": _SYMBOL, "timeframe": "1m"}
    )
    monkeypatch.setattr(
        "app.services.data.sources.local_adapter.load_dataset",
        lambda _request: stored,
    )

    with data_settings_context(_settings(tmp_path)):
        request_id = generate_id("req")
        _runtime.ensure_source("csv", request_id)
        batch = resolve_source("csv").fetch(
            SourceReadRequest(
                source_id="csv",
                provider_symbol=_SYMBOL,
                data_kind="bars",
                timeframe="1m",
                start=_START + timedelta(minutes=2),
                end=_START + timedelta(minutes=5),
                limit=100,
                request_id=request_id,
            )
        )

    timestamps = [record["timestamp"] for record in batch.records]
    assert len(timestamps) == 3
    assert min(timestamps) == _START + timedelta(minutes=2)
    assert max(timestamps) == _START + timedelta(minutes=4)


def test_two_timeframes_for_one_symbol_are_independently_addressable(
    tmp_path: Path,
    composed_root: Path,
) -> None:
    """Distinct timeframe artifacts for one symbol resolve to distinct files."""
    (composed_root / f"{_SYMBOL}_1m.csv").touch()
    (composed_root / f"{_SYMBOL}_1h.csv").touch()

    with data_settings_context(_settings(tmp_path)):
        _runtime.ensure_source("csv", generate_id("req"))
        source = resolve_source("csv")
        minute_artifact, _ = source._artifact(_SYMBOL, "1m")
        hour_artifact, _ = source._artifact(_SYMBOL, "1h")

    assert minute_artifact.name == f"{_SYMBOL}_1m.csv"
    assert hour_artifact.name == f"{_SYMBOL}_1h.csv"
    assert minute_artifact != hour_artifact


def test_unsupported_source_identifier_fails_before_policy(tmp_path: Path) -> None:
    """An identifier outside the configured set never reaches source policy."""
    with data_settings_context(_settings(tmp_path)), pytest.raises(DataError) as error:
        _runtime.ensure_source("dukascopy", generate_id("req"))

    assert error.value.code == "UNSUPPORTED_SOURCE"
