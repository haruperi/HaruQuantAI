"""Unit tests for delimiter sniffing and MetaTrader binary export formats."""

from __future__ import annotations

import asyncio
import struct
from datetime import UTC, datetime
from pathlib import Path

from app.contracts.data import (
    BarRecord,
    DataFormatSpecification,
    TickRecord,
)
from app.services.data.datasets import (
    DatasetConfig,
    DatasetServiceImpl,
)
from app.services.data.imports_exports import (
    ImportExportConfig,
    ImportExportServiceImpl,
    _export_bars_to_mt4_hst,
    _export_bars_to_mt5,
    _export_to_mt4_fxt,
)
from app.services.persistence.data import (
    DataPersistenceConfig,
    DataPersistenceServiceImpl,
)
from app.services.persistence.database import (
    DatabaseConfig,
    DatabaseServiceImpl,
)


async def _setup_impexp(tmp_path: Path) -> ImportExportServiceImpl:
    db_file = tmp_path / "test_mt.db"
    db = DatabaseServiceImpl(DatabaseConfig(database_path=db_file))
    persist = DataPersistenceServiceImpl(
        db, DataPersistenceConfig(preseed_defaults=True)
    )
    await persist.initialize_schema()
    ds_svc = DatasetServiceImpl(
        persist, DatasetConfig(storage_dir=tmp_path / "datasets")
    )
    return ImportExportServiceImpl(
        dataset_service=ds_svc,
        config=ImportExportConfig(),
    )


def test_sniff_format_spec_semicolon(tmp_path: Path) -> None:
    """Verify auto-sniffing of semicolon-delimited CSV files without manual format spec."""

    async def _test() -> None:
        impexp = await _setup_impexp(tmp_path)
        csv_file = tmp_path / "semicolon_bars.csv"
        csv_file.write_text(
            "2026.01.01 00:00:00;1.1000;1.1050;1.0950;1.1020;150.0\n"
            "2026.01.01 01:00:00;1.1020;1.1080;1.1000;1.1060;200.0\n",
            encoding="utf-8",
        )

        res = await impexp.import_tabular_file(
            file_path=str(csv_file),
            symbol="EURUSD",
            timeframe="H1",
            format_spec=None,
        )

        assert res.records_imported == 2
        assert res.error_count == 0
        assert bool(res.dataset_id)

    asyncio.run(_test())


def test_sniff_format_spec_tab_header(tmp_path: Path) -> None:
    """Verify auto-sniffing of tab-delimited files with headers."""

    async def _test() -> None:
        impexp = await _setup_impexp(tmp_path)
        tsv_file = tmp_path / "tab_bars.tsv"
        tsv_file.write_text(
            "Date\tTime\tOpen\tHigh\tLow\tClose\tVolume\n"
            "2026-01-01\t00:00:00\t1.1000\t1.1050\t1.0950\t1.1020\t150.0\n",
            encoding="utf-8",
        )

        res = await impexp.import_tabular_file(
            file_path=str(tsv_file),
            symbol="EURUSD",
            timeframe="H1",
            format_spec=None,
        )

        assert res.records_imported == 1
        assert res.error_count == 0

    asyncio.run(_test())


def test_export_bars_to_mt4_hst(tmp_path: Path) -> None:
    """Verify binary export of bars to MetaTrader 4 HST format."""
    out_file = tmp_path / "EURUSD60.hst"
    bars = [
        BarRecord(
            timestamp=datetime(2026, 1, 1, 0, 0, tzinfo=UTC),
            open=1.1000,
            high=1.1050,
            low=1.0950,
            close=1.1020,
            volume=100.0,
        ),
        BarRecord(
            timestamp=datetime(2026, 1, 1, 1, 0, tzinfo=UTC),
            open=1.1020,
            high=1.1080,
            low=1.1000,
            close=1.1060,
            volume=120.0,
        ),
    ]

    count, size, sha256_hash, path_str = _export_bars_to_mt4_hst(
        bars=bars,
        symbol="EURUSD",
        timeframe="H1",
        out_path=out_file,
    )

    assert count == 2
    assert size == 148 + (2 * 60)
    assert len(sha256_hash) == 64
    assert Path(path_str).exists()

    with out_file.open("rb") as f:
        header_data = f.read(148)
        assert len(header_data) == 148
        version, copyright_b, sym_b, period, digits, _timesign, _last_sync, _ = (
            struct.unpack("<i64s12siiii52s", header_data)
        )
        assert version == 401
        assert b"HaruQuantAI MT4 HST" in copyright_b
        assert sym_b.strip(b"\x00") == b"EURUSD"
        assert period == 60
        assert digits == 5

        # Bar 0
        rec_data0 = f.read(60)
        ctm, o, low_val, high_val, c, vol, _spread, _real_vol = struct.unpack(
            "<qddddqiq", rec_data0
        )
        assert ctm == int(bars[0].timestamp.timestamp())
        assert o == 1.1000
        assert low_val == 1.0950
        assert high_val == 1.1050
        assert c == 1.1020
        assert vol == 100


def test_export_bars_to_mt4_fxt(tmp_path: Path) -> None:
    """Verify binary export of bars to MetaTrader 4 FXT format."""
    out_file = tmp_path / "EURUSD1_0.fxt"
    bars = [
        BarRecord(
            timestamp=datetime(2026, 1, 1, 0, 0, tzinfo=UTC),
            open=1.1000,
            high=1.1050,
            low=1.0950,
            close=1.1020,
            volume=50.0,
        ),
    ]

    count, size, _, _ = _export_to_mt4_fxt(
        bars=bars,
        ticks=[],
        symbol="EURUSD",
        timeframe="M1",
        out_path=out_file,
    )

    assert count == 1
    assert size == 728 + 56

    with out_file.open("rb") as f:
        header_data = f.read(728)
        assert len(header_data) == 728
        version, desc_b, _server_b, sym_b, period = struct.unpack(
            "<i64s128s12si", header_data[:212]
        )
        assert version == 405
        assert b"HaruQuantAI MT4 FXT" in desc_b
        assert sym_b.strip(b"\x00") == b"EURUSD"
        assert period == 1

        rec_data = f.read(56)
        bar_time, o, low_val, high_val, c, vol, _ts, _flag = struct.unpack(
            "<qddddqii", rec_data
        )
        assert bar_time == int(bars[0].timestamp.timestamp())
        assert o == 1.1000
        assert low_val == 1.0950
        assert high_val == 1.1050
        assert c == 1.1020
        assert vol == 50


def test_export_ticks_to_mt4_fxt(tmp_path: Path) -> None:
    """Verify binary export of ticks to MetaTrader 4 FXT format."""
    out_file = tmp_path / "EURUSD_ticks.fxt"
    ticks = [
        TickRecord(
            timestamp=datetime(2026, 1, 1, 0, 0, 1, tzinfo=UTC),
            bid=1.1000,
            ask=1.1002,
            bid_volume=10.0,
        ),
        TickRecord(
            timestamp=datetime(2026, 1, 1, 0, 0, 2, tzinfo=UTC),
            bid=1.1001,
            ask=1.1003,
            bid_volume=15.0,
        ),
    ]

    count, size, _, _ = _export_to_mt4_fxt(
        bars=[],
        ticks=ticks,
        symbol="EURUSD",
        timeframe="TICK",
        out_path=out_file,
    )

    assert count == 2
    assert size == 728 + (2 * 56)


def test_export_bars_to_mt5(tmp_path: Path) -> None:
    """Verify binary export of bars to MetaTrader 5 binary format."""
    out_file = tmp_path / "EURUSD_H1.mt5b"
    bars = [
        BarRecord(
            timestamp=datetime(2026, 1, 1, 0, 0, tzinfo=UTC),
            open=1.2000,
            high=1.2050,
            low=1.1980,
            close=1.2030,
            volume=80.0,
        ),
    ]

    count, size, _, _ = _export_bars_to_mt5(
        bars=bars,
        symbol="EURUSD",
        timeframe="H1",
        out_path=out_file,
    )

    assert count == 1
    assert size == 128 + 60

    with out_file.open("rb") as f:
        header_data = f.read(128)
        assert len(header_data) == 128
        magic = header_data[:4]
        assert magic == b"MT5B"

        rec_data = f.read(60)
        time_sec, o, high_val, low_val, c, tick_vol, _spread, _real_vol = struct.unpack(
            "<qddddqiq", rec_data
        )
        assert time_sec == int(bars[0].timestamp.timestamp())
        assert o == 1.2000
        assert high_val == 1.2050
        assert low_val == 1.1980
        assert c == 1.2030
        assert tick_vol == 80


def test_service_export_mt4_and_mt5(tmp_path: Path) -> None:
    """Verify service-level export_dataset dispatching to MT4 and MT5 binary formats."""

    async def _test() -> None:
        db_file = tmp_path / "test_svc_mt.db"
        db = DatabaseServiceImpl(DatabaseConfig(database_path=db_file))
        persist = DataPersistenceServiceImpl(
            db, DataPersistenceConfig(preseed_defaults=True)
        )
        await persist.initialize_schema()
        ds_svc = DatasetServiceImpl(
            persist, DatasetConfig(storage_dir=tmp_path / "datasets")
        )
        impexp = ImportExportServiceImpl(
            dataset_service=ds_svc,
            config=ImportExportConfig(),
        )

        csv_file = tmp_path / "sample.csv"
        csv_file.write_text(
            "2026-01-01 00:00:00,1.1000,1.1050,1.0950,1.1020,100\n"
            "2026-01-01 01:00:00,1.1020,1.1080,1.1000,1.1060,120\n",
            encoding="utf-8",
        )
        spec = DataFormatSpecification(
            delimiter=",",
            has_header=False,
            datetime_format="%Y-%m-%d %H:%M:%S",
            date_col=0,
            open_col=1,
            high_col=2,
            low_col=3,
            close_col=4,
            volume_col=5,
        )

        import_res = await impexp.import_tabular_file(
            file_path=str(csv_file),
            symbol="EURUSD",
            timeframe="H1",
            format_spec=spec,
        )
        assert bool(import_res.dataset_id)

        # Export to MT4 HST
        hst_dest = tmp_path / "exports" / "EURUSD60.hst"
        res_hst = await impexp.export_dataset(
            dataset_id=import_res.dataset_id,
            destination_path=str(hst_dest),
            format_name="mt4_hst",
        )
        assert res_hst.records_exported == 2
        assert hst_dest.exists()

        # Export to MT5
        mt5_dest = tmp_path / "exports" / "EURUSD_H1.mt5b"
        res_mt5 = await impexp.export_dataset(
            dataset_id=import_res.dataset_id,
            destination_path=str(mt5_dest),
            format_name="mt5",
        )
        assert res_mt5.records_exported == 2
        assert mt5_dest.exists()

    asyncio.run(_test())
