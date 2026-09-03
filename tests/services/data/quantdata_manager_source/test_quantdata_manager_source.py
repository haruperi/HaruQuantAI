"""Comprehensive tests for QuantDataManager Source service."""

from __future__ import annotations

import re
import sqlite3
import struct
from pathlib import Path

import pytest
from app.contracts.data.errors import DataFailure
from app.contracts.data.models import (
    ImportQuantdataRequest,
    ImportQuantdataSuccess,
    QuantDataImportSpec,
)
from app.services.data.quantdata_manager_source.config import (
    QuantDataManagerConfig,
)
from app.services.data.quantdata_manager_source.quantdata_manager_source import (
    QuantDataManagerSourceService,
    _generate_uuid7,
    data_decode_quantdata_files,
    data_discover_quantdata_series,
    data_sync_quantdata_catalogue,
    decode_quantdata_dat,
    main,
)

_SYNC_BYTES = 19


def _create_synthetic_m1_file(path: Path, records: int = 2) -> None:
    """Write a valid synthetic StrategyQuant version 4.2 M1 binary file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as handle:
        v_bytes = b"4.2"
        handle.write(struct.pack(">H", len(v_bytes)) + v_bytes)
        tf_bytes = b"B"
        handle.write(struct.pack(">H", len(tf_bytes)) + tf_bytes)
        sym_bytes = b"EURUSD"
        handle.write(struct.pack(">H", len(sym_bytes)) + sym_bytes)
        handle.write(struct.pack(">q", records))
        handle.write(struct.pack(">i", 0))
        ex_bytes = b"SnRbTs"
        handle.write(struct.pack(">H", len(ex_bytes)) + ex_bytes)
        handle.write(bytes(_SYNC_BYTES))

        # Record 1 (ABS)
        cfg0 = (0x0B << 4) | 0x0A
        cfg1 = (0x0A << 4) | 0x0A
        cfg2 = (0x0A << 4) | 0x0A
        handle.write(bytes((cfg0, cfg1, cfg2)))
        handle.write((1609459200000).to_bytes(8, "big"))
        handle.write((1100000).to_bytes(4, "big"))
        handle.write((1105000).to_bytes(4, "big"))
        handle.write((1095000).to_bytes(4, "big"))
        handle.write((1102000).to_bytes(4, "big"))
        handle.write((100000).to_bytes(4, "big"))

        if records > 1:
            # Record 2 (ADD)
            cfg0_2 = (0x05 << 4) | 0x04
            cfg1_2 = (0x04 << 4) | 0x04
            cfg2_2 = (0x04 << 4) | 0x04
            handle.write(bytes((cfg0_2, cfg1_2, cfg2_2)))
            handle.write((60000).to_bytes(2, "big"))
            handle.write((100).to_bytes(1, "big"))
            handle.write((50).to_bytes(1, "big"))
            handle.write((20).to_bytes(1, "big"))
            handle.write((30).to_bytes(1, "big"))
            handle.write((0).to_bytes(1, "big"))


def _create_synthetic_tick_file(path: Path) -> None:
    """Write a valid synthetic StrategyQuant version 4.2 Tick binary file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as handle:
        v_bytes = b"4.2"
        handle.write(struct.pack(">H", len(v_bytes)) + v_bytes)
        tf_bytes = b"T"
        handle.write(struct.pack(">H", len(tf_bytes)) + tf_bytes)
        sym_bytes = b"GBPUSD"
        handle.write(struct.pack(">H", len(sym_bytes)) + sym_bytes)
        handle.write(struct.pack(">q", 1))
        handle.write(struct.pack(">i", 0))
        ex_bytes = b"SnRbTs"
        handle.write(struct.pack(">H", len(ex_bytes)) + ex_bytes)
        handle.write(bytes(_SYNC_BYTES))

        cfg0 = (0x0B << 4) | 0x0A
        cfg1 = (0x0A << 4) | 0x08
        cfg2 = 0x00
        handle.write(bytes((cfg0, cfg1, cfg2)))
        handle.write((1609459200000).to_bytes(8, "big"))
        handle.write((1350000).to_bytes(4, "big"))
        handle.write((1350020).to_bytes(4, "big"))
        handle.write((100).to_bytes(1, "big"))


@pytest.fixture
def test_environment(
    tmp_path: Path,
) -> tuple[Path, QuantDataManagerSourceService, QuantDataImportSpec]:
    """Prepare a populated test environment with synthetic .dat files."""
    history = tmp_path / "user" / "data" / "History"
    _create_synthetic_m1_file(history / "EURUSD_M1.dat", records=2)
    _create_synthetic_tick_file(history / "GBPUSD_TICK.dat")

    db_file = tmp_path / "user" / "data" / "data.db"
    with sqlite3.connect(db_file) as conn:
        conn.execute(
            """
            CREATE TABLE DATA (
                ID INTEGER PRIMARY KEY,
                SYMBOL TEXT,
                TIMEFRAME TEXT,
                BROKER TEXT,
                DATEFROM INTEGER,
                DATETO INTEGER,
                FILENAME TEXT
            )
            """
        )
        conn.execute(
            """
            INSERT INTO DATA VALUES (
                1, 'EURUSD', 'M1', 'TestBroker',
                1609459200000, 1609459260000, 'EURUSD_M1.dat'
            )
            """
        )
        conn.commit()

    service = QuantDataManagerSourceService(
        config=QuantDataManagerConfig(allowed_root=tmp_path)
    )
    spec = QuantDataImportSpec(
        spec_id=_generate_uuid7(),
        allowed_root=tmp_path.as_posix(),
        decoder_version="4.2",
    )
    return tmp_path, service, spec


def test_discover_quantdata_series(
    test_environment: tuple[Path, QuantDataManagerSourceService, QuantDataImportSpec],
) -> None:
    """Verify FR-DATA-DISCOVER_QUANTDATA_SERIES discovery behavior."""
    root, service, spec = test_environment
    discovered = data_discover_quantdata_series(service, spec, root)
    assert len(discovered) == 2

    symbols = {d["symbol"] for d in discovered}
    assert "EURUSD" in symbols
    assert "GBPUSD" in symbols

    eurusd = next(d for d in discovered if d["symbol"] == "EURUSD")
    assert eurusd["timeframe"] == "M1"
    assert eurusd["broker"] == "TestBroker"
    assert "user/data/History/EURUSD_M1.dat" in eurusd["relative_path"]


def test_decode_quantdata_files(
    test_environment: tuple[Path, QuantDataManagerSourceService, QuantDataImportSpec],
) -> None:
    """Verify FR-DATA-DECODE_QUANTDATA_FILES decoding behavior."""
    root, service, spec = test_environment
    decoded = data_decode_quantdata_files(service, spec, root)
    assert len(decoded) == 2

    eurusd = next(d for d in decoded if d["symbol"] == "EURUSD")
    assert eurusd["version"] == "4.2"
    assert eurusd["decoded_count"] == 2
    rows = eurusd["rows"]
    assert rows[0]["open"] == pytest.approx(1.1000)
    assert rows[0]["high"] == pytest.approx(1.1050)
    assert rows[0]["low"] == pytest.approx(1.0950)
    assert rows[0]["close"] == pytest.approx(1.1020)
    assert rows[0]["volume"] == pytest.approx(1.00)

    assert rows[1]["open"] == pytest.approx(1.1001)
    assert rows[1]["high"] == pytest.approx(1.10505)

    gbpusd = next(d for d in decoded if d["symbol"] == "GBPUSD")
    assert gbpusd["decoded_count"] == 1
    assert gbpusd["rows"][0]["bid"] == pytest.approx(1.3500)
    assert gbpusd["rows"][0]["ask"] == pytest.approx(1.35002)


def test_decode_corrupt_files(tmp_path: Path) -> None:
    """Verify decoder failure on corrupted or unsupported files."""
    bad_ver_file = tmp_path / "bad_version.dat"
    with bad_ver_file.open("wb") as h:
        v_bytes = b"3.9"
        h.write(struct.pack(">H", len(v_bytes)) + v_bytes)
        h.write(struct.pack(">H", 1) + b"B")
        h.write(struct.pack(">H", 4) + b"TEST")

    with pytest.raises(
        ValueError,
        match=re.escape("Unsupported QuantDataManager file version 3.9"),
    ):
        decode_quantdata_dat(bad_ver_file.read_bytes(), expected_decoder_version="4.2")

    truncated_bytes = bytes([0, 3, 52, 46, 50, 0, 1, 66])
    with pytest.raises(ValueError, match="Truncated"):
        decode_quantdata_dat(truncated_bytes)


@pytest.mark.asyncio
async def test_sync_quantdata_catalogue(
    test_environment: tuple[Path, QuantDataManagerSourceService, QuantDataImportSpec],
) -> None:
    """Verify FR-DATA-SYNC_QUANTDATA_CATALOGUE and lineage recording."""
    root, service, spec = test_environment
    versions = await data_sync_quantdata_catalogue(service, spec, root)
    assert len(versions) == 2

    for v in versions:
        assert v.version == 1
        assert v.precision in (
            "SELECTED_TIMEFRAME",
            "REAL_TICK_RECORDED_SPREAD",
        )
        assert len(v.content_hash) == 64

    with service.get_connection() as conn:
        cursor = conn.execute("SELECT * FROM quantdata_lineage")
        rows = cursor.fetchall()
        assert len(rows) == 2


@pytest.mark.asyncio
async def test_import_quantdata_capability_operations(
    test_environment: tuple[Path, QuantDataManagerSourceService, QuantDataImportSpec],
) -> None:
    """Verify import_quantdata capability endpoint operations."""
    _root, service, spec = test_environment

    req_disc = ImportQuantdataRequest(
        request_id=_generate_uuid7(),
        capability_snapshot_id=_generate_uuid7(),
        operation="DISCOVER",
        spec=spec,
    )
    res_disc = await service.import_quantdata(req_disc)
    assert isinstance(res_disc, ImportQuantdataSuccess)
    assert res_disc.outcome == "SUCCESS"

    req_dec = ImportQuantdataRequest(
        request_id=_generate_uuid7(),
        capability_snapshot_id=_generate_uuid7(),
        operation="DECODE",
        spec=spec,
    )
    res_dec = await service.import_quantdata(req_dec)
    assert isinstance(res_dec, ImportQuantdataSuccess)
    assert res_dec.outcome == "SUCCESS"

    req_sync = ImportQuantdataRequest(
        request_id=_generate_uuid7(),
        capability_snapshot_id=_generate_uuid7(),
        operation="SYNC",
        spec=spec,
    )
    res_sync = await service.import_quantdata(req_sync)
    assert isinstance(res_sync, ImportQuantdataSuccess)
    assert len(res_sync.committed_version_ids) == 2

    bad_spec = QuantDataImportSpec(
        spec_id=_generate_uuid7(),
        allowed_root="/non/existent/root/path",
        decoder_version="4.2",
    )
    req_bad = ImportQuantdataRequest(
        request_id=_generate_uuid7(),
        capability_snapshot_id=_generate_uuid7(),
        operation="DISCOVER",
        spec=bad_spec,
    )
    res_bad = await service.import_quantdata(req_bad)
    assert isinstance(res_bad, DataFailure)
    assert res_bad.code == "DATA_QUANTDATA_INVALID"


@pytest.mark.asyncio
async def test_main_executable_scenario_harness() -> None:
    """Verify that the designated __main__ scenario harness runs cleanly."""
    await main()


def test_persistence_helpers(tmp_path: Path) -> None:
    """Verify QuantDataPersistence record_spec, read_legacy_sqlite, and close."""
    import sqlite3

    from app.services.data.quantdata_manager_source._persistence import (
        QuantDataPersistence,
    )

    db_path = tmp_path / "legacy.db"
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE DATA (id INTEGER, val TEXT)")
    conn.execute("INSERT INTO DATA VALUES (1, 'test')")
    conn.commit()
    conn.close()

    rows = QuantDataPersistence.read_legacy_sqlite(db_path)
    assert len(rows) == 1
    assert rows[0]["val"] == "test"

    from app.services.data.quantdata_manager_source.config import QuantDataManagerConfig

    persist = QuantDataPersistence(QuantDataManagerConfig())
    persist.record_spec("spec_1", "/allowed/root", "4.2")
    persist.close()
