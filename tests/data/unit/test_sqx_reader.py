"""Unit tests for the SQX/QuantDataManager source reader (FEAT-DATA-15)."""

from __future__ import annotations

import sqlite3
import struct
from pathlib import Path

import pytest
from app.kernel.identity import generate_id
from app.services.data._settings import DataSettings, data_settings_context
from app.services.data.contracts import DataError
from app.services.data.sqx_source.reader import (
    list_sqx_symbols,
    read_sqx_m1,
    read_sqx_ticks,
)

_REQUEST_ID = "req-00000000-0000-4000-8000-000000000000"
_OP_SUB = 0
_OP_ADD = 1
_OP_ABS = 2


def _utf(value: str) -> bytes:
    encoded = value.encode("utf-8")
    return struct.pack(">H", len(encoded)) + encoded


def _write_header(handle, *, version: str = "4.2", records: int) -> None:
    handle.write(_utf(version))
    handle.write(_utf("B"))
    handle.write(_utf("TEST"))
    handle.write(struct.pack(">q", records))
    handle.write(struct.pack(">i", 0))
    handle.write(_utf("SnRbTs"))

    # A 19-byte sync chain plus block index precedes the first record.
    handle.write(bytes(19))


def _minimal_width(value: int) -> int:
    """Return the SQX width code fitting one non-negative value."""
    if value <= 0xFF:
        return 0
    if value <= 0xFFFF:
        return 1
    if value <= 0xFFFFFFFF:
        return 2
    return 3


def _encode(value: int) -> bytes:
    return value.to_bytes(1 << _minimal_width(value), "big")


def _field(value: int, op: int) -> tuple[int, int]:
    """Return (width_op_bits, encoded_bytes) for one field."""
    return _minimal_width(value) | (op << 2), _encode(value)


def _m1_record(fields: tuple[tuple[int, int], ...]) -> bytes:
    """Pack six (value, op) M1 fields into one config-headed record.

    Fields arrive in reader order (time, open, high, low, close, volume);
    the config nibbles place open/time in cfg0, low/high in cfg1, and
    volume/close in cfg2.
    """
    pairs = [_field(value, op) for value, op in fields]
    cfg0 = pairs[1][0] | (pairs[0][0] << 4)
    cfg1 = pairs[3][0] | (pairs[2][0] << 4)
    cfg2 = pairs[5][0] | (pairs[4][0] << 4)
    body = b"".join(encoded for _bits, encoded in pairs)
    return bytes((cfg0, cfg1, cfg2)) + body


def _synthetic_m1(path: Path) -> None:
    """Write a three-record M1 .dat: absolute first bar, then two deltas."""
    with path.open("wb") as handle:
        _write_header(handle, records=3)
        # Order: (time, open, high, low, close, volume) x (value, op).
        handle.write(
            _m1_record(
                (
                    (1167609600000, _OP_ABS),
                    (1319080, _OP_ABS),
                    (1319190, _OP_ABS),
                    (1318960, _OP_ABS),
                    (1319170, _OP_ABS),
                    (1000, _OP_ABS),
                )
            )
        )
        handle.write(
            _m1_record(
                (
                    (60000, _OP_ADD),
                    (10, _OP_ADD),
                    (0, _OP_ADD),
                    (0, _OP_ADD),
                    (5, _OP_ADD),
                    (1, _OP_ADD),
                )
            )
        )
        handle.write(
            _m1_record(
                (
                    (0, _OP_SUB),
                    (0, _OP_SUB),
                    (5, _OP_SUB),
                    (5, _OP_SUB),
                    (5, _OP_SUB),
                    (1, _OP_SUB),
                )
            )
        )


def _settings(tmp_path: Path):
    return DataSettings(
        database_url=None,
        data_dir=tmp_path,
        quantdata_manager_root=tmp_path / "qdm",
    )


def test_read_sqx_m1_decodes_absolute_additive_and_subtractive_records(
    tmp_path: Path,
) -> None:
    """The reader reconstructs bars from absolute and delta records."""
    (tmp_path / "qdm" / "user" / "data" / "History" / "TEST_M1").mkdir(parents=True)
    _synthetic_m1(
        tmp_path / "qdm" / "user" / "data" / "History" / "TEST_M1" / "TEST_M1_M1.dat"
    )
    with data_settings_context(_settings(tmp_path)):
        frame = read_sqx_m1("TEST", request_id=_REQUEST_ID)

    assert len(frame) == 3
    assert frame.iloc[0]["open"] == pytest.approx(1.31908)
    assert frame.iloc[1]["close"] == pytest.approx(1.319175)  # +5 points
    assert frame.iloc[2]["high"] == pytest.approx(1.319185)  # -5 points
    assert frame.iloc[0]["volume"] == pytest.approx(0.01)  # 1000 / 1e5


def test_read_sqx_m1_filters_by_start_and_end(tmp_path: Path) -> None:
    """Only bars inside the inclusive window are returned."""
    (tmp_path / "qdm" / "user" / "data" / "History" / "TEST_M1").mkdir(parents=True)
    _synthetic_m1(
        tmp_path / "qdm" / "user" / "data" / "History" / "TEST_M1" / "TEST_M1_M1.dat"
    )
    with data_settings_context(_settings(tmp_path)):
        frame = read_sqx_m1(
            "TEST",
            start=1167609660000,
            end=1167609720000,
            request_id=_REQUEST_ID,
        )

    assert len(frame) == 2


def test_read_sqx_m1_fails_closed_for_unknown_symbol(tmp_path: Path) -> None:
    """An unknown symbol resolves to a typed owner error."""
    (tmp_path / "qdm" / "user" / "data" / "History").mkdir(parents=True)
    with (
        data_settings_context(_settings(tmp_path)),
        pytest.raises(DataError, match="SQX_FILE_NOT_FOUND"),
    ):
        read_sqx_m1("MISSING", request_id=_REQUEST_ID)


def _tick_record(fields: tuple[tuple[int, int], ...]) -> bytes:
    """Pack four (value, op) tick fields into one config-headed record."""
    pairs = [_field(value, op) for value, op in fields]
    # cfg0: ask | time<<4 ; cfg1: volume | bid<<4
    cfg0 = pairs[1][0] | (pairs[0][0] << 4)
    cfg1 = pairs[3][0] | (pairs[2][0] << 4)
    body = b"".join(encoded for _bits, encoded in pairs)
    return bytes((cfg0, cfg1)) + body


def _synthetic_tick(path: Path) -> None:
    with path.open("wb") as handle:
        _write_header(handle, records=2)
        # Order: (time, ask, bid, volume) x (value, op).
        handle.write(
            _tick_record(
                (
                    (1167609600000, _OP_ABS),
                    (1319200, _OP_ABS),
                    (1319100, _OP_ABS),
                    (500, _OP_ABS),
                )
            )
        )
        handle.write(
            _tick_record(
                (
                    (50, _OP_ADD),
                    (5, _OP_ADD),
                    (5, _OP_ADD),
                    (1, _OP_ADD),
                )
            )
        )


def test_read_sqx_ticks_computes_floating_spread(tmp_path: Path) -> None:
    """Tick reads expose bid, ask, and their floating spread."""
    (tmp_path / "qdm" / "user" / "data" / "History" / "TEST").mkdir(parents=True)
    _synthetic_tick(
        tmp_path / "qdm" / "user" / "data" / "History" / "TEST" / "TEST_TICK.dat"
    )
    with data_settings_context(_settings(tmp_path)):
        frame = read_sqx_ticks("TEST", request_id=_REQUEST_ID)

    assert len(frame) == 2
    assert frame.iloc[0]["bid"] == pytest.approx(1.3191)
    assert frame.iloc[0]["ask"] == pytest.approx(1.3192)
    assert frame.iloc[0]["spread"] == pytest.approx(0.0001)
    assert frame.iloc[1]["bid"] == pytest.approx(1.319105)


def test_list_sqx_symbols_reads_the_catalogue_read_only(tmp_path: Path) -> None:
    """Symbol discovery reads the QuantDataManager SQLite catalogue."""
    database_dir = tmp_path / "qdm" / "user" / "data"
    database_dir.mkdir(parents=True)
    with sqlite3.connect(database_dir / "data.db") as conn:
        conn.execute(
            "CREATE TABLE DATA (SYMBOL TEXT, INSTRUMENT TEXT, TIMEFRAME TEXT, "
            "TIMEZONE TEXT, DATEFROM INTEGER, DATETO INTEGER, ROWS INTEGER)"
        )
        conn.execute(
            "INSERT INTO DATA VALUES ('EURUSD_M1', 'EURUSD', 'M1', 'Etc/UCT', "
            "1167609600000, 1785531599000, 7314561)"
        )
    with data_settings_context(_settings(tmp_path)):
        frame = list_sqx_symbols(request_id=_REQUEST_ID)

    assert len(frame) == 1
    row = frame.iloc[0]
    assert row["instrument"] == "EURUSD"
    assert row["start_date"] == "2007-01-01"
    assert row["total_records"] == 7314561


def test_missing_root_fails_closed(tmp_path: Path) -> None:
    """An absent QuantDataManager root raises the typed owner error."""
    with data_settings_context(_settings(tmp_path)), pytest.raises(DataError):
        read_sqx_m1("TEST", request_id=generate_id("req"))
