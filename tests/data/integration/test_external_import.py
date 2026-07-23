"""Integration evidence for WF-DATA-017 external artifact admission."""

from __future__ import annotations

from pathlib import Path

from app.services.data._settings import DataSettings, data_settings_context
from app.services.data.local_datasets.contracts import DatasetLoadRequest
from app.services.data.persistence.contracts import (
    ColumnMapping,
    ExternalImportRequest,
)
from app.services.data.persistence.dataset_writer import load_dataset
from app.services.data.persistence.external_import import import_external_dataset
from app.services.data.persistence.migrations import run_data_migrations
from app.utils import generate_id


def test_external_import_measures_commits_and_reloads(tmp_path: Path) -> None:
    """A declared foreign artifact crosses quality, storage, and audit boundaries."""
    raw = tmp_path / "raw"
    raw.mkdir()
    (raw / "EURUSD.csv").write_text(
        "timestamp,open,high,low,close,volume\n"
        "2026-01-01T00:00:00Z,1.1,1.2,1.0,1.15,100\n"
        "2026-01-01T00:01:00Z,1.15,1.25,1.05,1.2,110\n",
        encoding="utf-8",
    )
    settings = DataSettings(
        database_url="sqlite:///data.db",
        data_dir=tmp_path,
        sqlite_busy_timeout_seconds=1.0,
        write_lock_lease_seconds=10.0,
        approved_storage_roots=(Path("raw"),),
    )
    request_id = generate_id("req")
    request = ExternalImportRequest(
        relative_path=Path("raw/EURUSD.csv"),
        format="csv",
        dialect="standard",
        mapping=ColumnMapping(
            timestamp="timestamp",
            open="open",
            high="high",
            low="low",
            close="close",
            volume="volume",
        ),
        symbol="EURUSD",
        data_kind="bars",
        timeframe="M1",
        source_id="vendor-export",
        workflow_context="research",
        precision_policy="decimal_string",
        price_unit="USD",
        volume_unit="lots",
        destination_path=Path("raw/EURUSD_M1.csv"),
        request_id=request_id,
    )

    with data_settings_context(settings):
        run_data_migrations(generate_id("req"))
        manifest = import_external_dataset(request)
        loaded = load_dataset(
            DatasetLoadRequest(
                relative_path=manifest.relative_path,
                format="csv",
                request_id=generate_id("req"),
            )
        )

    assert loaded.record_count == 2
    assert loaded.quality_report.quality_status != "failed"
    assert loaded.source_metadata["origin"] == "external_import"
