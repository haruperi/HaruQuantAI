"""Regression coverage for SQ minute-bar archive boundaries."""

import struct
from datetime import UTC, datetime

from app.workspace.brokers.codecs import SQ_MAGIC_HEADER_V42, decode_sq_dat_bytes


def test_sq_decoder_stops_at_non_minute_trailer() -> None:
    """A plausible OHLC trailer must not become an off-grid extra bar."""
    timestamp = int(datetime(2025, 1, 6, tzinfo=UTC).timestamp() * 1000)
    anchor = struct.pack(
        ">Q5q", timestamp, 1_100_000, 1_100_010, 1_099_990, 1_100_000, 100_000
    )

    def delta(milliseconds: int) -> bytes:
        return b"\x54\x44\x44" + milliseconds.to_bytes(2, "big") + bytes(5)

    archive = (
        SQ_MAGIC_HEADER_V42 + b"\xbb\xbb\xbb" + anchor + delta(60_000) + delta(59_000)
    )
    rows = decode_sq_dat_bytes(archive)

    assert [row["time"] for row in rows] == [timestamp // 1000, timestamp // 1000 + 60]
    assert all(row["open"] == 1.1 for row in rows)
