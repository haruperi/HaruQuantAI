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
from app.services.data import (
    build_data_quality_report,
    build_data_settings,
    build_market_dataset,
    build_ohlcv_record,
    build_source_read_request,
    data_settings_context,
    ensure_source,
    list_composable_sources,
    resolve_source,
)
from app.utils import generate_id

_SYMBOL = "EURUSD"
_START = datetime(2026, 1, 1, tzinfo=UTC)

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
        quality_status="passed",
        quality_score=Decimal(1),
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


@pytest.fixture(autouse=True)
def isolated_runtime(monkeypatch: pytest.MonkeyPatch) -> None:
    """Reset process-local composition state around every test."""
    for target in (
        "app.services.data.sources.registry._registry",
        "app.services.data.sources.registry._instances",
        "app.services.data.sources.registry._identities",
        "app.services.data.sources.composition._calendars",
        "app.services.data.sources.composition._sessions",
        "app.services.data.sources.composition._migrated_targets",
    ):
        replacement: object = set() if target.endswith("_migrated_targets") else {}
        monkeypatch.setattr(target, replacement)


def _bar(index: int) -> object:
    """Return one canonical bar offset by whole minutes from the window start."""
    timestamp = _START + timedelta(minutes=index)
    return build_ohlcv_record(
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


def _settings(tmp_path: Path) -> object:
    """Return settings rooting local composition at a temporary data directory."""
    return build_data_settings(
        database_url=f"sqlite:///{tmp_path / 'data.db'}",
        data_dir=tmp_path,
        data_local_sources=("csv",),
        data_raw_root=Path("data/raw"),
    )


def _write_manifest(raw_root: Path) -> None:
    """Declare one operator-supplied local symbol."""
    (raw_root / "symbols.json").write_text(
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
        ensure_res = ensure_source("csv", generate_id("req"))
        assert ensure_res.status == "success"
        source_res = resolve_source("csv")
        assert source_res.status == "success"
        assert source_res.data is not None
        source = source_res.data
        sources_res = list_composable_sources()
        assert sources_res.status == "success"
        assert sources_res.data is not None
        sources = sources_res.data

    assert source is not None
    assert "csv" in sources


def test_local_source_reads_only_the_requested_window(
    tmp_path: Path,
    composed_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A bounded request returns its window, not the whole artifact."""
    (composed_root / f"{_SYMBOL}_1m.csv").touch()
    dataset_records = tuple(_bar(index) for index in range(10))

    stored = make_dataset().model_copy(
        update={"records": dataset_records, "symbol": _SYMBOL, "timeframe": "1m"}
    )
    monkeypatch.setattr(
        "app.services.data.sources.local_adapter.load_dataset",
        lambda _request: stored,
    )

    with data_settings_context(_settings(tmp_path)):
        request_id = generate_id("req")
        ensure_source("csv", request_id)
        source_res = resolve_source("csv")
        assert source_res.status == "success"
        assert source_res.data is not None
        batch_res = source_res.data.fetch(
            build_source_read_request(
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
        assert batch_res.status == "success", f"fetch failed: {batch_res.error}"
        batch = batch_res.data

    timestamps = [record["timestamp"] for record in batch.records]
    assert len(timestamps) == 3
    assert min(timestamps) == _START + timedelta(minutes=2)
    assert max(timestamps) == _START + timedelta(minutes=4)


def test_two_timeframes_for_one_symbol_are_independently_addressable(
    tmp_path: Path,
    composed_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Distinct timeframe artifacts for one symbol resolve to distinct files."""
    (composed_root / f"{_SYMBOL}_1m.csv").touch()
    (composed_root / f"{_SYMBOL}_1h.csv").touch()
    observed_paths: list[Path] = []

    stored = make_dataset().model_copy(update={"symbol": _SYMBOL, "timeframe": "1m"})

    def load_requested_artifact(request: object) -> object:
        observed_paths.append(request.relative_path)
        return stored

    monkeypatch.setattr(
        "app.services.data.sources.local_adapter.load_dataset",
        load_requested_artifact,
    )

    with data_settings_context(_settings(tmp_path)):
        ensure_source("csv", generate_id("req"))
        source_res = resolve_source("csv")
        assert source_res.status == "success"
        assert source_res.data is not None
        source = source_res.data
        for timeframe in ("1m", "1h"):
            source.fetch(
                build_source_read_request(
                    source_id="csv",
                    provider_symbol=_SYMBOL,
                    data_kind="bars",
                    timeframe=timeframe,
                    limit=100,
                    request_id=generate_id("req"),
                )
            )

    assert [path.name for path in observed_paths] == [
        f"{_SYMBOL}_1m.csv",
        f"{_SYMBOL}_1h.csv",
    ]


def test_unsupported_source_identifier_fails_before_policy(tmp_path: Path) -> None:
    """An identifier outside the configured set never reaches source policy."""
    with data_settings_context(_settings(tmp_path)):
        res = ensure_source("not-configured-source", generate_id("req"))

    assert res.status == "error"
    assert res.error is not None
    assert res.error.code == "UNSUPPORTED_SOURCE"
