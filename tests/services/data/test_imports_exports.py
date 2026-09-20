"""Tests for FEAT-DATA-IMPORTS-EXPORTS (app/services/data/imports_exports.py)."""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest
from app.contracts.data import (
    DataFormatSpecification,
    SessionNotFoundError,
    UnsupportedExportFormatError,
)
from app.services.data.datasets import (
    DatasetConfig,
    DatasetServiceImpl,
)
from app.services.data.imports_exports import (
    ImportExportConfig,
    ImportExportServiceImpl,
)
from app.services.data.quality import QualityServiceImpl
from app.services.data.sessions import (
    SessionServiceImpl,
)
from app.services.persistence.data import (
    DataPersistenceConfig,
    DataPersistenceServiceImpl,
)
from app.services.persistence.database import (
    DatabaseConfig,
    DatabaseServiceImpl,
)


async def _setup_import_export(tmp_path: Path) -> ImportExportServiceImpl:
    db_file = tmp_path / "test_impexp.db"
    db = DatabaseServiceImpl(DatabaseConfig(database_path=db_file))
    persist = DataPersistenceServiceImpl(
        db, DataPersistenceConfig(preseed_defaults=True)
    )
    await persist.initialize_schema()
    ds_svc = DatasetServiceImpl(
        persist, DatasetConfig(storage_dir=tmp_path / "datasets")
    )
    session_svc = SessionServiceImpl(persist)
    return ImportExportServiceImpl(
        dataset_service=ds_svc,
        session_service=session_svc,
        config=ImportExportConfig(),
    )


def test_import_and_export_bars_csv(tmp_path: Path) -> None:
    """Verify importing tabular CSV bars and exporting back to disk."""

    async def _test() -> None:
        service = await _setup_import_export(tmp_path)

        csv_content = (
            "Date,Time,Open,High,Low,Close,Volume\n"
            "2026.06.01,10:00:00,1.0500,1.0510,1.0490,1.0505,100\n"
            "2026.06.01,10:01:00,1.0505,1.0515,1.0500,1.0512,150\n"
            "2026.06.01,10:02:00,1.0512,1.0520,1.0510,1.0518,200\n"
        )
        input_csv = tmp_path / "eurusd_m1.csv"
        input_csv.write_text(csv_content, encoding="utf-8")

        spec = DataFormatSpecification(
            delimiter=",",
            has_header=True,
            datetime_format="%Y.%m.%d %H:%M:%S",
            date_col=0,
            time_col=1,
            open_col=2,
            high_col=3,
            low_col=4,
            close_col=5,
            volume_col=6,
        )

        res = await service.import_tabular_file(
            file_path=str(input_csv),
            symbol="EURUSD",
            timeframe="M1",
            format_spec=spec,
        )
        assert res.records_imported == 3
        assert res.error_count == 0
        assert res.data_kind == "bars"

        # Export dataset
        export_out = tmp_path / "exported_eurusd.csv"
        exp_res = await service.export_dataset(
            dataset_id=res.dataset_id,
            destination_path=str(export_out),
            format_name="csv",
        )
        assert exp_res.records_exported == 3
        assert export_out.exists()
        assert exp_res.sha256_hash != ""

        lines = export_out.read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) == 4  # Header + 3 bars
        assert "Date,Time,Open,High,Low,Close,Volume" in lines[0]

    asyncio.run(_test())


def test_import_with_malformed_rows(tmp_path: Path) -> None:
    """Verify isolation of corrupted rows during CSV ingestion."""

    async def _test() -> None:
        service = await _setup_import_export(tmp_path)

        csv_content = (
            "Date,Time,Open,High,Low,Close,Volume\n"
            "2026.06.01,10:00:00,1.0500,1.0510,1.0490,1.0505,100\n"
            "CORRUPT_ROW_DATA,XYZ,INVALID\n"
            "2026.06.01,10:02:00,1.0512,1.0520,1.0510,1.0518,200\n"
        )
        input_csv = tmp_path / "corrupt.csv"
        input_csv.write_text(csv_content, encoding="utf-8")

        spec = DataFormatSpecification(
            delimiter=",",
            has_header=True,
            datetime_format="%Y.%m.%d %H:%M:%S",
            date_col=0,
            time_col=1,
            open_col=2,
            high_col=3,
            low_col=4,
            close_col=5,
            volume_col=6,
        )

        res = await service.import_tabular_file(
            file_path=str(input_csv),
            symbol="EURUSD",
            timeframe="M1",
            format_spec=spec,
        )
        assert res.records_imported == 2
        assert res.error_count == 1
        assert len(res.row_errors) == 1

    asyncio.run(_test())


def test_import_and_export_ticks_csv(tmp_path: Path) -> None:
    """Verify importing and exporting tick data."""

    async def _test() -> None:
        service = await _setup_import_export(tmp_path)

        csv_content = (
            "Date,Time,Bid,Ask,Volume\n"
            "2026.06.01,10:00:00.100,1.0500,1.0501,1.0\n"
            "2026.06.01,10:00:00.250,1.0501,1.0502,2.0\n"
        )
        input_csv = tmp_path / "ticks.csv"
        input_csv.write_text(csv_content, encoding="utf-8")

        spec = DataFormatSpecification(
            delimiter=",",
            has_header=True,
            datetime_format="%Y.%m.%d %H:%M:%S.%f",
            date_col=0,
            time_col=1,
            bid_col=2,
            ask_col=3,
            volume_col=4,
        )

        res = await service.import_tabular_file(
            file_path=str(input_csv),
            symbol="EURUSD",
            timeframe="tick",
            format_spec=spec,
        )
        assert res.records_imported == 2
        assert res.data_kind == "ticks"

        # Export ticks
        export_out = tmp_path / "exported_ticks.csv"
        exp_res = await service.export_dataset(
            dataset_id=res.dataset_id,
            destination_path=str(export_out),
            format_name="csv",
        )
        assert exp_res.records_exported == 2
        assert export_out.exists()

    asyncio.run(_test())


def test_unsupported_export_format(tmp_path: Path) -> None:
    """Verify UnsupportedExportFormatError is raised for non-CSV formats."""

    async def _test() -> None:
        service = await _setup_import_export(tmp_path)

        csv_content = (
            "Date,Time,Open,High,Low,Close,Volume\n"
            "2026.06.01,10:00:00,1.0500,1.0510,1.0490,1.0505,100\n"
        )
        input_csv = tmp_path / "test_bars.csv"
        input_csv.write_text(csv_content, encoding="utf-8")

        spec = DataFormatSpecification(
            delimiter=",",
            has_header=True,
            datetime_format="%Y.%m.%d %H:%M:%S",
            date_col=0,
            time_col=1,
            open_col=2,
            high_col=3,
            low_col=4,
            close_col=5,
            volume_col=6,
        )

        res = await service.import_tabular_file(
            file_path=str(input_csv),
            symbol="EURUSD",
            timeframe="M1",
            format_spec=spec,
        )

        with pytest.raises(
            UnsupportedExportFormatError, match="Unsupported export format"
        ):
            await service.export_dataset(
                dataset_id=res.dataset_id,
                destination_path=str(tmp_path / "out.json"),
                format_name="json",
            )

    asyncio.run(_test())


def test_import_with_unknown_session(tmp_path: Path) -> None:
    """Verify SessionNotFoundError is raised when non-existent session is passed."""

    async def _test() -> None:
        service = await _setup_import_export(tmp_path)

        csv_content = (
            "Date,Time,Open,High,Low,Close,Volume\n"
            "2026.06.01,10:00:00,1.0500,1.0510,1.0490,1.0505,100\n"
        )
        input_csv = tmp_path / "test_bars.csv"
        input_csv.write_text(csv_content, encoding="utf-8")

        with pytest.raises(
            SessionNotFoundError, match="Trading session 'NonExistent' not found"
        ):
            await service.import_tabular_file(
                file_path=str(input_csv),
                symbol="EURUSD",
                timeframe="M1",
                session_name="NonExistent",
            )

    asyncio.run(_test())


def test_import_with_quality_evaluation_and_report_persistence(
    tmp_path: Path,
) -> None:
    """Verify import calculates quality score and persists report to database."""

    async def _test() -> None:
        db_file = tmp_path / "test_import_quality.db"
        db = DatabaseServiceImpl(DatabaseConfig(database_path=db_file))
        persist = DataPersistenceServiceImpl(
            db, DataPersistenceConfig(preseed_defaults=True)
        )
        await persist.initialize_schema()
        ds_svc = DatasetServiceImpl(
            persist, DatasetConfig(storage_dir=tmp_path / "datasets")
        )
        session_svc = SessionServiceImpl(persist)
        quality_svc = QualityServiceImpl()
        service = ImportExportServiceImpl(
            dataset_service=ds_svc,
            quality_service=quality_svc,
            session_service=session_svc,
            persistence=persist,
            config=ImportExportConfig(),
        )

        csv_content = (
            "Date,Time,Open,High,Low,Close,Volume\n"
            "2026.06.01,10:00:00,1.0500,1.0510,1.0490,1.0505,100\n"
            "2026.06.01,10:01:00,1.0505,1.0515,1.0500,1.0512,150\n"
        )
        input_csv = tmp_path / "quality_bars.csv"
        input_csv.write_text(csv_content, encoding="utf-8")

        spec = DataFormatSpecification(
            delimiter=",",
            has_header=True,
            datetime_format="%Y.%m.%d %H:%M:%S",
            date_col=0,
            time_col=1,
            open_col=2,
            high_col=3,
            low_col=4,
            close_col=5,
            volume_col=6,
        )

        res = await service.import_tabular_file(
            file_path=str(input_csv),
            symbol="EURUSD",
            timeframe="M1",
            format_spec=spec,
        )

        manifest = await ds_svc.get_manifest(res.dataset_id)
        assert manifest is not None
        assert manifest.quality_score > 0.0

        report = await persist.get_quality_report(f"qr_{res.dataset_id}")
        assert report is not None
        assert report.dataset_id == res.dataset_id
        assert report.total_records == 2

    asyncio.run(_test())
