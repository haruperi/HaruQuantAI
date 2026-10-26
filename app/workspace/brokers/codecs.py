"""Shared market data binary stream codecs and decoders.

Provides standalone, zero-dependency binary parsing for StrategyQuant compressed
`.dat` bar archives and binary payloads across broker implementations.
"""

from __future__ import annotations

import struct
from datetime import UTC, datetime
from typing import Any

from app.host.logging import get_logger

logger = get_logger(__name__)

CODEC_FR = "FR-BROKER-CODECS-SQDAT"
SQ_MAGIC_HEADER_V42 = b"SQ42\x01\x00"

__all__ = ["CODEC_FR", "SQ_MAGIC_HEADER_V42", "decode_sq_dat_bytes"]


def decode_sq_dat_bytes(
    buf: bytes,
    count: int | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
) -> list[dict[str, Any]]:
    """Parse StrategyQuant 4.2 binary compressed bar streams with block delta decoding."""
    if len(buf) < 15:
        return []

    # Fast tail slice if only recent bounded count requested without date filters
    if count is not None and count > 0 and date_from is None and date_to is None:
        tail_size = max(2_000_000, count * 2000)
        if len(buf) > tail_size:
            buf = buf[-tail_size:]

    blocks: list[int] = []
    idx = 0
    while idx < len(buf):
        pos = buf.find(b"\xbb\xbb\xbb", idx)
        if pos == -1:
            break
        blocks.append(pos)
        end_pos = pos + 3
        while end_pos < len(buf) and buf[end_pos] == 0xBB:
            end_pos += 1
        idx = end_pos

    if not blocks:
        return []

    rows: list[dict[str, Any]] = []

    for b_idx_rel, b_off in enumerate(blocks):
        next_b_off = blocks[b_idx_rel + 1] if b_idx_rel + 1 < len(blocks) else len(buf)
        curr = b_off + 3
        while curr < next_b_off and buf[curr] == 0xBB:
            curr += 1

        anchor_off = None
        for offset in range(curr, min(curr + 16, next_b_off - 48 + 1)):
            val = struct.unpack_from(">Q", buf, offset)[0]
            if 500_000_000_000 <= val <= 5_000_000_000_000:
                anchor_off = offset
                break

        if anchor_off is None:
            continue

        curr = anchor_off
        ts_ms = struct.unpack_from(">Q", buf, curr)[0]
        o_raw, h_raw, l_raw, c_raw, v_raw = struct.unpack_from(">5q", buf, curr + 8)
        curr += 48

        dt = datetime.fromtimestamp(ts_ms / 1000.0, tz=UTC)
        include = True
        if date_from and dt < date_from:
            include = False
        if date_to and dt > date_to:
            include = False

        o_val = o_raw / 1_000_000.0
        h_val = h_raw / 1_000_000.0
        l_val = l_raw / 1_000_000.0
        c_val = c_raw / 1_000_000.0

        if (
            include
            and l_val > 0
            and l_val <= min(o_val, c_val) <= max(o_val, c_val) <= h_val
        ):
            rows.append(
                {
                    "time": int(ts_ms / 1000.0),
                    "open": o_val,
                    "high": h_val,
                    "low": l_val,
                    "close": c_val,
                    "tick_volume": max(0, int(v_raw // 100_000)),
                    "spread": 0,
                    "real_volume": max(0, int(v_raw // 100_000)),
                }
            )

        while curr < next_b_off:
            if curr + 3 > next_b_off:
                break
            flag_bytes = buf[curr : curr + 3]
            curr += 3
            b0, b1, b2 = flag_bytes[0], flag_bytes[1], flag_bytes[2]
            nybbles = (
                (b0 >> 4) & 0xF,
                b0 & 0xF,
                (b1 >> 4) & 0xF,
                b1 & 0xF,
                (b2 >> 4) & 0xF,
                b2 & 0xF,
            )
            deltas: list[int] = []
            for nyb in nybbles:
                field_len = 1 << (nyb & 0x03)
                if curr + field_len > next_b_off:
                    break
                sign = 1 if (nyb & 0x04) else -1
                raw_val = int.from_bytes(buf[curr : curr + field_len], "big")
                curr += field_len
                deltas.append(sign * raw_val)

            if len(deltas) < 6:
                break

            ts_ms += deltas[0]
            o_raw += deltas[1]
            h_raw += deltas[2]
            l_raw += deltas[3]
            c_raw += deltas[4]
            v_raw += deltas[5]

            bar_dt = datetime.fromtimestamp(ts_ms / 1000.0, tz=UTC)
            if date_from and bar_dt < date_from:
                continue
            if date_to and bar_dt > date_to:
                continue

            o_val = o_raw / 1_000_000.0
            h_val = h_raw / 1_000_000.0
            l_val = l_raw / 1_000_000.0
            c_val = c_raw / 1_000_000.0

            if l_val > 0 and l_val <= min(o_val, c_val) <= max(o_val, c_val) <= h_val:
                rows.append(
                    {
                        "time": int(ts_ms / 1000.0),
                        "open": o_val,
                        "high": h_val,
                        "low": l_val,
                        "close": c_val,
                        "tick_volume": max(0, int(v_raw // 100_000)),
                        "spread": 0,
                        "real_volume": max(0, int(v_raw // 100_000)),
                    }
                )

    rows.sort(key=lambda r: r["time"])
    if count is not None and count > 0 and len(rows) > count:
        rows = rows[-count:]

    logger.debug(
        "%s: Decoded %d SQ .dat bars",
        CODEC_FR,
        len(rows),
        extra={"fr_id": CODEC_FR, "count": len(rows)},
    )
    return rows
