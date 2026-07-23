"""Unit coverage for explicit audited external artifact import.

[CAP-DATA-026 Phase 2] Copy of the legacy storage test, re-pointed at the
new `persistence`/`audit` modules. The legacy copy still guards `storage/`
until Phase 11 deletes it. Behaviour assertions are unchanged.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from app.services.data._settings import DataSettings, data_settings_context
from app.services.data.contracts import DataError
from app.services.data.persistence.contracts import ColumnMapping, ExternalImportRequest
from app.services.data.persistence.external_import import (
    describe_import_dialects,
    import_external_dataset,
)
from app.utils import generate_id

_STANDARD_CSV = (
    "timestamp,open,high,low,close,volume\n"
    "2026-01-01T00:00:00Z,1.1,1.2,1.0,1.15,100\n"
    "2026-01-01T00:01:00Z,1.15,1.25,1.05,1.2,110\n"
)

_MT5_CSV = (
    "<DATE>\t<TIME>\t<OPEN>\t<HIGH>\t<LOW>\t<CLOSE>\t<TICKVOL>\n"
    "2026.01.01\t00:00:00\t1.1\t1.2\t1.0\t1.15\t100\n"
    "2026.01.01\t00:01:00\t1.15\t1.25\t1.05\t1.2\t110\n"
)

_GAPPED_CSV = (
    "timestamp,open,high,low,close,volume\n"
    "2026-01-01T00:00:00Z,1.1,1.2,1.0,1.15,100\n"
    "2026-01-01T00:01:00Z,1.15,1.25,1.05,1.2,110\n"
    "2026-01-01T00:30:00Z,1.2,1.3,1.1,1.25,120\n"
)


def _mapping(**overrides: str | None) -> ColumnMapping:
    """Return a canonical-name bar mapping with optional overrides."""
    base: dict[str, str | None] = {
        "timestamp": "timestamp",
        "open": "open",
        "high": "high",
        "low": "low",
        "close": "close",
        "volume": "volume",
    }
    base.update(overrides)
    return ColumnMapping(**base)  # type: ignore[arg-type]


def _request(
    tmp_path: Path,
    *,
    dialect: str = "standard",
    mapping: ColumnMapping | None = None,
    source_name: str = "EURUSD.csv",
) -> ExternalImportRequest:
    """Return an import declaration rooted under the temp data directory."""
    return ExternalImportRequest(
        relative_path=Path("raw") / source_name,
        format="csv",
        dialect=dialect,
        mapping=mapping if mapping is not None else _mapping(),
        symbol="EURUSD",
        data_kind="bars",
        timeframe="M1",
        source_id="vendor_export",
        workflow_context="research",
        precision_policy="decimal_string",
        price_unit="USD",
        volume_unit="lots",
        destination_path=Path("raw") / "EURUSD_M1.csv",
        request_id=generate_id("req"),
    )


@pytest.fixture
def data_root(tmp_path: Path) -> Path:
    """Return a temp data directory containing an approved raw root."""
    (tmp_path / "raw").mkdir()
    return tmp_path


def _settings(tmp_path: Path) -> DataSettings:
    """Return settings whose approved roots cover the temp raw directory."""
    return DataSettings(
        database_url=f"sqlite:///{tmp_path / 'data.db'}",
        data_dir=tmp_path,
        approved_storage_roots=(Path("raw"),),
    )


def test_supported_dialects_are_described() -> None:
    """A caller can discover valid dialects without trial and error."""
    dialects = describe_import_dialects()

    assert "standard" in dialects
    assert "mt5_export" in dialects


def test_unknown_dialect_is_rejected(data_root: Path) -> None:
    """An unlisted dialect never reaches the filesystem."""
    with pytest.raises(DataError):
        _request(data_root, dialect="excel_2003")


def test_import_never_infers_a_governed_field() -> None:
    """Bar imports must declare timeframe and all four OHLC columns."""
    with pytest.raises(DataError):
        ExternalImportRequest(
            relative_path=Path("raw/EURUSD.csv"),
            format="csv",
            dialect="standard",
            mapping=_mapping(close=None),
            symbol="EURUSD",
            data_kind="bars",
            timeframe="M1",
            source_id="vendor_export",
            workflow_context="research",
            precision_policy="decimal_string",
            price_unit="USD",
            volume_unit="lots",
            destination_path=Path("raw/EURUSD_M1.csv"),
            request_id=generate_id("req"),
        )


def test_bar_import_requires_a_timeframe() -> None:
    """A bar artifact without a declared timeframe is not admissible."""
    with pytest.raises(DataError):
        ExternalImportRequest(
            relative_path=Path("raw/EURUSD.csv"),
            format="csv",
            dialect="standard",
            mapping=_mapping(),
            symbol="EURUSD",
            data_kind="bars",
            timeframe=None,
            source_id="vendor_export",
            workflow_context="research",
            precision_policy="decimal_string",
            price_unit="USD",
            volume_unit="lots",
            destination_path=Path("raw/EURUSD_M1.csv"),
            request_id=generate_id("req"),
        )


def test_missing_artifact_fails_closed(data_root: Path) -> None:
    """An absent source artifact is corruption, not an empty import."""
    with data_settings_context(_settings(data_root)), pytest.raises(DataError) as error:
        import_external_dataset(_request(data_root))

    assert error.value.code == "FILE_CORRUPTED"


def test_declared_columns_absent_from_artifact_fail_validation(
    data_root: Path,
) -> None:
    """A mapping that does not match the artifact fails rather than guessing."""
    (data_root / "raw" / "EURUSD.csv").write_text(_STANDARD_CSV, encoding="utf-8")
    request = _request(data_root, mapping=_mapping(close="settlement"))

    with data_settings_context(_settings(data_root)), pytest.raises(DataError) as error:
        import_external_dataset(request)

    assert error.value.code == "VALIDATION_FAILED"


def test_import_admits_a_standard_csv(
    data_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A declared standard artifact becomes a manifest-backed dataset."""
    (data_root / "raw" / "EURUSD.csv").write_text(_STANDARD_CSV, encoding="utf-8")
    captured: dict[str, object] = {}
    monkeypatch.setattr(
        "app.services.data.persistence.external_import.save_dataset",
        lambda request: captured.setdefault("dataset", request.dataset),
    )
    monkeypatch.setattr(
        "app.services.data.persistence.external_import.persist_audit_event",
        lambda event: captured.setdefault("event", event),
    )

    with data_settings_context(_settings(data_root)):
        import_external_dataset(_request(data_root))

    dataset = captured["dataset"]
    assert dataset.record_count == 2  # type: ignore[union-attr]
    assert dataset.symbol == "EURUSD"  # type: ignore[union-attr]
    assert dataset.source_metadata["origin"] == "external_import"  # type: ignore[union-attr]


def test_import_admits_an_mt5_export(
    data_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Tab-delimited angle-bracket exports are admitted under their dialect."""
    (data_root / "raw" / "EURUSD.csv").write_text(_MT5_CSV, encoding="utf-8")
    captured: dict[str, object] = {}
    monkeypatch.setattr(
        "app.services.data.persistence.external_import.save_dataset",
        lambda request: captured.setdefault("dataset", request.dataset),
    )
    monkeypatch.setattr(
        "app.services.data.persistence.external_import.persist_audit_event",
        lambda _event: None,
    )
    mapping = ColumnMapping(
        timestamp="<DATE>",
        open="<OPEN>",
        high="<HIGH>",
        low="<LOW>",
        close="<CLOSE>",
        volume="<TICKVOL>",
    )

    with data_settings_context(_settings(data_root)):
        import_external_dataset(
            _request(data_root, dialect="mt5_export", mapping=mapping)
        )

    dataset = captured["dataset"]
    assert dataset.record_count == 2  # type: ignore[union-attr]


def test_import_records_external_origin_in_audit(
    data_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Provenance of an externally originated artifact is always audited."""
    (data_root / "raw" / "EURUSD.csv").write_text(_STANDARD_CSV, encoding="utf-8")
    events: list[object] = []
    monkeypatch.setattr(
        "app.services.data.persistence.external_import.save_dataset",
        lambda _request: None,
    )
    monkeypatch.setattr(
        "app.services.data.persistence.external_import.persist_audit_event",
        events.append,
    )

    with data_settings_context(_settings(data_root)):
        import_external_dataset(_request(data_root))

    assert len(events) == 1
    assert events[0].action == "import_external_dataset"  # type: ignore[union-attr]
    assert events[0].payload["origin"] == "external"  # type: ignore[union-attr]


def test_import_rejects_blocking_measured_quality(
    data_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A missing-bar issue blocks persistence and audit of an external artifact."""
    (data_root / "raw" / "EURUSD.csv").write_text(
        _GAPPED_CSV,
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "app.services.data.persistence.external_import.save_dataset",
        lambda _request: pytest.fail("failed-quality import reached persistence"),
    )
    monkeypatch.setattr(
        "app.services.data.persistence.external_import.persist_audit_event",
        lambda _event: pytest.fail("failed-quality import reached audit"),
    )

    with data_settings_context(_settings(data_root)), pytest.raises(DataError) as error:
        import_external_dataset(_request(data_root))

    assert error.value.code == "DATA_QUALITY_FAILED"
