"""Unit coverage for timeframe-scoped local artifacts and bounded local reads."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest
from app.kernel.identity import generate_id
from app.services.data.contracts import (
    DataError,
    DataQualityReport,
    MarketDataset,
    OHLCVRecord,
)
from app.services.data.contracts.responses import unwrap_data_response
from app.services.data.sources.contracts import (
    SourceReadRequest,
)
from app.services.data.sources.local_adapter import LocalMarketDataSource

START = datetime(2026, 1, 1, tzinfo=UTC)
END = START + timedelta(minutes=1)
AVAILABLE = END + timedelta(seconds=1)


def make_bar(timestamp=START):
    """Return one exact canonical OHLCV record."""
    return OHLCVRecord(
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
    return DataQualityReport(
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
    return MarketDataset(
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


_SYMBOL = "ABC"
_START = datetime(2026, 1, 1, tzinfo=UTC)
_REQ_ID = "req-00000000-0000-4000-8000-000000000000"


def _unwrap(response):
    """Extract the raw payload from a StandardResponse for assertions."""
    return unwrap_data_response(
        response, operation="data.sources.test", request_id=_REQ_ID
    )


def _bar(index: int) -> OHLCVRecord:
    """Return one canonical bar offset by whole minutes from the fixture start."""
    timestamp = _START + timedelta(minutes=index)
    return OHLCVRecord(
        timestamp=timestamp,
        open=Decimal("10.0"),
        high=Decimal("11.0"),
        low=Decimal("9.0"),
        close=Decimal("10.5"),
        volume=Decimal(100),
        price_unit="USD",
        volume_unit="shares",
        source="fixture",
        source_symbol=_SYMBOL,
        source_revision="rev-1",
        available_at=timestamp + timedelta(seconds=1),
    )


def _read_request(
    *,
    timeframe: str | None = "1m",
    start: datetime | None = None,
    end: datetime | None = None,
    limit: int = 100,
    source_id: str = "local_csv",
) -> SourceReadRequest:
    """Return one bounded local source read request."""
    return SourceReadRequest(
        source_id=source_id,
        provider_symbol=_SYMBOL,
        data_kind="bars",
        timeframe=timeframe,
        start=start,
        end=end,
        limit=limit,
        request_id=generate_id("req"),
    )


def _source(raw_root: Path) -> LocalMarketDataSource:
    """Return a local source rooted at an existing absolute directory."""
    return LocalMarketDataSource(
        source_id="local_csv",
        raw_root=raw_root,
        metadata={},
    )


@pytest.fixture
def raw_root(tmp_path: Path) -> Path:
    """Return an existing absolute raw root nested two levels under a data dir."""
    root = tmp_path / "data" / "raw"
    root.mkdir(parents=True)
    return root


def test_timeframes_are_individually_addressable(raw_root: Path) -> None:
    """A timeframe-scoped stem wins over the bare symbol stem."""
    (raw_root / f"{_SYMBOL}_1m.csv").touch()
    (raw_root / f"{_SYMBOL}.csv").touch()

    artifact, artifact_format = _source(raw_root)._artifact(_SYMBOL, "1m")

    assert artifact.name == f"{_SYMBOL}_1m.csv"
    assert artifact_format == "csv"


def test_artifact_falls_back_to_bare_symbol_stem(raw_root: Path) -> None:
    """A kind without a timeframe still resolves the bare symbol artifact."""
    (raw_root / f"{_SYMBOL}.csv").touch()

    artifact, _ = _source(raw_root)._artifact(_SYMBOL, None)

    assert artifact.name == f"{_SYMBOL}.csv"


def test_artifact_prefers_scoped_stem_before_falling_back(raw_root: Path) -> None:
    """The bare stem is used only when no timeframe-scoped artifact exists."""
    (raw_root / f"{_SYMBOL}.csv").touch()

    artifact, _ = _source(raw_root)._artifact(_SYMBOL, "1m")

    assert artifact.name == f"{_SYMBOL}.csv"


def test_missing_artifact_fails_closed(raw_root: Path) -> None:
    """No candidate stem present is a deterministic not-found failure."""
    with pytest.raises(DataError) as error:
        _source(raw_root)._artifact(_SYMBOL, "1m")

    assert error.value.code == "DATA_NOT_FOUND"


def test_select_applies_half_open_window() -> None:
    """Selection includes the start bound and excludes the end bound."""
    records = tuple(_bar(index) for index in range(5))

    selected = LocalMarketDataSource._select(
        records,
        _read_request(
            start=_START + timedelta(minutes=1),
            end=_START + timedelta(minutes=3),
        ),
    )

    assert tuple(record.timestamp for record in selected) == (
        _START + timedelta(minutes=1),
        _START + timedelta(minutes=2),
    )


def test_select_truncates_to_limit_keeping_earliest() -> None:
    """A bounded read keeps the earliest records so results stay deterministic."""
    records = tuple(_bar(index) for index in range(5))

    selected = LocalMarketDataSource._select(records, _read_request(limit=2))

    assert len(selected) == 2
    assert selected[0].timestamp == _START
    assert selected[1].timestamp == _START + timedelta(minutes=1)


def test_select_without_bounds_returns_every_record() -> None:
    """An unbounded window within the limit returns the whole artifact."""
    records = tuple(_bar(index) for index in range(3))

    selected = LocalMarketDataSource._select(records, _read_request())

    assert len(selected) == 3


def test_fetch_rejects_a_mismatched_source_id(raw_root: Path) -> None:
    """A request naming another source never reads this source's artifacts."""
    response = _source(raw_root).fetch(_read_request(source_id="other"))

    assert response.status != "success"
    assert response.error is not None
    assert response.error.code == "INVALID_INPUT"


def test_fetch_reports_empty_when_the_window_selects_nothing(
    raw_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A non-empty artifact whose records fall outside the window fails closed."""
    (raw_root / f"{_SYMBOL}_1m.csv").touch()
    monkeypatch.setattr(
        "app.services.data.sources.local_adapter.load_dataset",
        lambda _request: make_dataset(),
    )

    response = _source(raw_root).fetch(
        _read_request(
            start=_START + timedelta(days=365),
            end=_START + timedelta(days=366),
        )
    )

    assert response.status != "success"
    assert response.error is not None
    assert response.error.code == "EMPTY_RESULT"


def test_fetch_honours_range_and_limit(
    raw_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The source boundary returns only the requested window, not the whole file."""
    (raw_root / f"{_SYMBOL}_1m.csv").touch()
    dataset = make_dataset().model_copy(
        update={"records": tuple(_bar(index) for index in range(10))}
    )
    monkeypatch.setattr(
        "app.services.data.sources.local_adapter.load_dataset",
        lambda _request: dataset,
    )

    batch = _unwrap(_source(raw_root).fetch(_read_request(limit=3)))

    assert len(batch.records) == 3
