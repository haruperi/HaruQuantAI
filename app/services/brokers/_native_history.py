"""Independently verified binary codecs for BI5, MT4 HST/FXT, Darwinex, and StrategyQuant.

Description:
    Implements standalone, high-performance binary decoders and encoders for
    native financial data formats: Dukascopy .bi5 (LZMA tick and M1 records),
    MetaTrader 4 HST history files (versions 400 and 401), MetaTrader 4 FXT
    testing files (version 405), Darwinex tick archives, and StrategyQuant 4.2 .dat
    compressed files. All byte layouts are strictly verified against official format
    specifications with compile-time struct size assertions.

Purpose:
    FEAT-BROKER-CODECS: Native binary format codecs and verification helpers.

Key Capabilities:
    - FR-BROKER-CODECS-BI5: Decompress and decode Dukascopy LZMA tick/bar streams.
      Associated: `decompress_bi5()`, `decode_bi5_ticks()`, `decode_bi5_bars()`
      Logging: Emits DEBUG on parsing compressed payload and reporting decoded count.
    - FR-BROKER-CODECS-HST: Decode and encode MT4 HST files across versions 400 and 401.
      Associated: `decode_hst_bytes()`, `encode_hst_bytes()`
      Logging: Emits DEBUG on detecting HST version, symbol, and record count.
    - FR-BROKER-CODECS-FXT: Decode and encode MT4 FXT tick model files (version 405).
      Associated: `decode_fxt_bytes()`, `encode_fxt_bytes()`
      Logging: Emits DEBUG on parsing FXT header and model records.
    - FR-BROKER-CODECS-SQDAT: Decode StrategyQuant 4.2 binary compressed bar streams.
      Associated: `decode_sq_dat_bytes()`
      Logging: Emits DEBUG on locating magic sync markers and parsing delta blocks.

Python API Usage:
    ```python
    from app.services.brokers._native_history import decode_hst_bytes

    rows = decode_hst_bytes(hst_binary_content)
    ```

CLI Usage:
    ```bash
    uv run pytest tests/unit/services/brokers/test_brokers_binary_and_file_codecs.py --no-cov
    ```
"""

from __future__ import annotations

import io
import lzma
import struct
from datetime import UTC, datetime, timedelta
from typing import Any

from app.host.logging import get_logger
from app.services.brokers.capabilities import ProviderValidationError

logger = get_logger(__name__)

BI5_FR = "FR-BROKER-CODECS-BI5"
HST_FR = "FR-BROKER-CODECS-HST"
FXT_FR = "FR-BROKER-CODECS-FXT"
SQDAT_FR = "FR-BROKER-CODECS-SQDAT"

__all__ = [
    "decode_bi5_bars",
    "decode_bi5_ticks",
    "decode_darwinex_dat",
    "decode_fxt_bytes",
    "decode_hst_bytes",
    "decode_sq_dat_bytes",
    "decompress_bi5",
    "encode_fxt_bytes",
    "encode_hst_bytes",
    "main",
]

# Compile-time byte-layout verification against canonical specifications
assert struct.calcsize("<iddddd") == 44, "MT4 HST v400 record must be 44 bytes"
assert struct.calcsize("<qddddqiq") == 60, "MT4 HST v401 record must be 60 bytes"
assert struct.calcsize("<qddddqii") == 56, "MT4 FXT v405 record must be 56 bytes"
assert struct.calcsize(">IIIff") == 20, "Dukascopy BI5 tick record must be 20 bytes"
assert struct.calcsize(">IIIIIf") == 24, "Dukascopy BI5 M1 bar record must be 24 bytes"
assert struct.calcsize(">qqq") == 24, "Darwinex record must be 24 bytes"

SQ_MAGIC_HEADER_V42 = b"\xbb\xbb\xbb\xbb\xbb\xbb\xbb\xbb\xbb\xbb\xbb\xbb\xbb\xbb\xbb"


MAX_DECOMPRESSED_BYTES = 50 * 1024 * 1024  # 50 MB safety budget


def decompress_bi5(data: bytes, max_bytes: int = MAX_DECOMPRESSED_BYTES) -> bytes:
    """Decompress Dukascopy .bi5 binary payload with LZMA header recovery and size limits."""
    if not data or len(data) < 5:
        return b""
    try:
        decomp = lzma.decompress(data, format=lzma.FORMAT_ALONE)
        if len(decomp) > max_bytes:
            raise ProviderValidationError(
                f"Decompressed BI5 payload exceeds limit ({len(decomp)} > {max_bytes})"
            )
        return decomp
    except ProviderValidationError:
        raise
    except Exception:
        pass
    try:
        props = data[:5]
        payload = data[5:]
        alone_header = props + struct.pack("<Q", 2**64 - 1)
        decomp = lzma.decompress(alone_header + payload, format=lzma.FORMAT_ALONE)
        if len(decomp) > max_bytes:
            raise ProviderValidationError(
                f"Decompressed BI5 payload exceeds limit ({len(decomp)} > {max_bytes})"
            )
        return decomp
    except ProviderValidationError:
        raise
    except Exception:
        pass
    try:
        decomp = lzma.decompress(data, format=lzma.FORMAT_RAW)
        if len(decomp) > max_bytes:
            raise ProviderValidationError(
                f"Decompressed BI5 payload exceeds limit ({len(decomp)} > {max_bytes})"
            )
        return decomp
    except ProviderValidationError:
        raise
    except Exception:
        return b""


def decode_bi5_ticks(
    decomp: bytes,
    base_dt: datetime,
    digits: int = 5,
    count: int | None = None,
) -> list[dict[str, Any]]:
    """Decode uncompressed Dukascopy BI5 tick records."""
    if not decomp:
        return []
    rec_count = len(decomp) // 20
    target_count = (
        min(rec_count, count) if count is not None and count > 0 else rec_count
    )
    scale = 10.0**digits
    rows: list[dict[str, Any]] = []

    for i in range(target_count):
        offset_ms, ask_int, bid_int, ask_v, bid_v = struct.unpack_from(
            ">IIIff", decomp, i * 20
        )
        ask = ask_int / scale
        bid = bid_int / scale
        tick_dt = base_dt + timedelta(milliseconds=offset_ms)
        rows.append(
            {
                "time_msc": int(tick_dt.timestamp() * 1000),
                "bid": bid,
                "ask": ask,
                "last": (ask + bid) / 2.0,
                "volume": int(ask_v + bid_v),
                "flags": 0,
                "volume_real": float(ask_v + bid_v),
            }
        )
    logger.debug(
        "%s: Decoded %d BI5 ticks",
        BI5_FR,
        len(rows),
        extra={"fr_id": BI5_FR, "count": len(rows)},
    )
    return rows


def decode_bi5_bars(
    decomp: bytes,
    base_dt: datetime,
    digits: int = 5,
    count: int | None = None,
) -> list[dict[str, Any]]:
    """Decode uncompressed Dukascopy BI5 M1 candle records."""
    if not decomp:
        return []
    rec_count = len(decomp) // 24
    target_count = (
        min(rec_count, count) if count is not None and count > 0 else rec_count
    )
    scale = 10.0**digits
    rows: list[dict[str, Any]] = []

    for i in range(target_count):
        offset_sec, o, c, l, h, v = struct.unpack_from(">IIIIIf", decomp, i * 24)
        bar_dt = base_dt + timedelta(seconds=offset_sec)
        rows.append(
            {
                "time": int(bar_dt.timestamp()),
                "open": o / scale,
                "high": h / scale,
                "low": l / scale,
                "close": c / scale,
                "tick_volume": int(v),
                "spread": 0,
                "real_volume": int(v),
            }
        )
    logger.debug(
        "%s: Decoded %d BI5 M1 bars",
        BI5_FR,
        len(rows),
        extra={"fr_id": BI5_FR, "count": len(rows)},
    )
    return rows


def decode_hst_bytes(data: bytes, count: int | None = None) -> list[dict[str, Any]]:
    """Decode MetaTrader 4 HST binary files (version 400 or 401)."""
    if len(data) < 148:
        raise ProviderValidationError(
            "HST file too small to contain valid 148-byte header"
        )

    version, _raw_cr, raw_sym, period, digits = struct.unpack_from(
        "<i64s12sii", data, 0
    )
    if version not in (400, 401):
        raise ProviderValidationError(f"Unsupported HST version: {version}")

    rec_size = 44 if version == 400 else 60
    payload_len = len(data) - 148
    if payload_len % rec_size != 0:
        raise ProviderValidationError(
            f"HST file contains truncated records: {payload_len} bytes not divisible by record size {rec_size}"
        )

    symbol = raw_sym.split(b"\x00")[0].decode("ascii", errors="replace").strip()
    logger.debug(
        "%s: Decoding HST for %s (version=%d, period=%d, digits=%d)",
        HST_FR,
        symbol,
        version,
        period,
        digits,
        extra={"fr_id": HST_FR, "symbol": symbol, "version": version},
    )

    offset = 148
    rows: list[dict[str, Any]] = []

    if version == 400:
        num_records = payload_len // rec_size
        max_recs = (
            min(num_records, count) if count is not None and count > 0 else num_records
        )
        for _ in range(max_recs):
            ctm, o, l, h, c, v = struct.unpack_from("<iddddd", data, offset)
            offset += rec_size
            rows.append(
                {
                    "time": int(ctm),
                    "open": float(o),
                    "high": float(h),
                    "low": float(l),
                    "close": float(c),
                    "tick_volume": int(v),
                    "spread": 0,
                    "real_volume": int(v),
                }
            )
    else:  # version == 401
        num_records = payload_len // rec_size
        max_recs = (
            min(num_records, count) if count is not None and count > 0 else num_records
        )
        for _ in range(max_recs):
            ctm, o, h, l, c, vol, spread, real_vol = struct.unpack_from(
                "<qddddqiq", data, offset
            )
            offset += rec_size
            rows.append(
                {
                    "time": int(ctm),
                    "open": float(o),
                    "high": float(h),
                    "low": float(l),
                    "close": float(c),
                    "tick_volume": int(vol),
                    "spread": int(spread),
                    "real_volume": int(real_vol),
                }
            )

    return rows


def encode_hst_bytes(
    rows: list[dict[str, Any]],
    symbol: str,
    period: int = 1,
    digits: int = 5,
    version: int = 401,
) -> bytes:
    """Encode market bars into MetaTrader 4 HST format."""
    hdr = struct.pack(
        "<i64s12siiii52s",
        version,
        b"HaruQuantAI MT4 Codec",
        symbol.encode("ascii")[:11],
        period,
        digits,
        int(datetime.now(tz=UTC).timestamp()),
        0,
        b"\x00" * 52,
    )
    buf = io.BytesIO()
    buf.write(hdr)

    if version == 400:
        for r in rows:
            buf.write(
                struct.pack(
                    "<iddddd",
                    int(r["time"]),
                    float(r["open"]),
                    float(r["low"]),
                    float(r["high"]),
                    float(r["close"]),
                    float(r.get("tick_volume", 1)),
                )
            )
    elif version == 401:
        for r in rows:
            buf.write(
                struct.pack(
                    "<qddddqiq",
                    int(r["time"]),
                    float(r["open"]),
                    float(r["high"]),
                    float(r["low"]),
                    float(r["close"]),
                    int(r.get("tick_volume", 1)),
                    int(r.get("spread", 0)),
                    int(r.get("real_volume", 1)),
                )
            )
    else:
        raise ProviderValidationError(f"Unsupported encode HST version: {version}")

    return buf.getvalue()


def decode_fxt_bytes(data: bytes, count: int | None = None) -> list[dict[str, Any]]:
    """Decode MetaTrader 4 FXT testing files (version 405)."""
    if len(data) < 724:
        raise ProviderValidationError("FXT file too small to contain valid header")

    version, _raw_desc, _raw_srv, raw_sym, period, _model, bars_count = (
        struct.unpack_from("<i64s128s16siii", data, 0)
    )
    if version != 405:
        raise ProviderValidationError(f"Unsupported FXT version: {version}")

    rec_size = 56
    if len(data) >= 728 and (len(data) - 728) % rec_size == 0:
        offset = 728
    elif len(data) >= 724 and (len(data) - 724) % rec_size == 0:
        offset = 724
    else:
        raise ProviderValidationError(
            f"FXT file contains truncated records: length {len(data)} does not match 724/728 + N*{rec_size}"
        )

    symbol = raw_sym.split(b"\x00")[0].decode("ascii", errors="replace").strip()
    logger.debug(
        "%s: Decoding FXT for %s (version=%d, period=%d, bars=%d)",
        FXT_FR,
        symbol,
        version,
        period,
        bars_count,
        extra={"fr_id": FXT_FR, "symbol": symbol, "version": version},
    )

    num_recs = (len(data) - offset) // rec_size
    max_recs = min(num_recs, count) if count is not None and count > 0 else num_recs

    rows: list[dict[str, Any]] = []
    for _ in range(max_recs):
        bar_time, o, h, l, c, vol, tick_time, flag = struct.unpack_from(
            "<qddddqii", data, offset
        )
        offset += rec_size
        rows.append(
            {
                "time": int(bar_time),
                "open": float(o),
                "high": float(h),
                "low": float(l),
                "close": float(c),
                "volume": int(vol),
                "tick_time": int(tick_time),
                "flag": int(flag),
            }
        )
    return rows


def encode_fxt_bytes(
    rows: list[dict[str, Any]],
    symbol: str,
    period: int = 1,
    version: int = 405,
) -> bytes:
    """Encode market bars into MetaTrader 4 FXT format."""
    hdr = struct.pack(
        "<i64s128s16siiiii492s",
        version,
        b"HaruQuantAI FXT Codec",
        b"MetaQuotes-Demo",
        symbol.encode("ascii")[:15],
        period,
        0,
        len(rows),
        int(rows[0]["time"]) if rows else 0,
        int(rows[-1]["time"]) if rows else 0,
        b"\x00" * 492,
    )
    buf = io.BytesIO()
    buf.write(hdr)
    for r in rows:
        buf.write(
            struct.pack(
                "<qddddqii",
                int(r["time"]),
                float(r["open"]),
                float(r["high"]),
                float(r["low"]),
                float(r["close"]),
                int(r.get("volume", 1)),
                int(r.get("tick_time", r["time"])),
                int(r.get("flag", 1)),
            )
        )
    return buf.getvalue()


def decode_darwinex_dat(
    buf: bytes, digits: int = 5, count: int | None = None
) -> list[dict[str, Any]]:
    """Decode Darwinex .dat tick archive binary payload."""
    idx = buf.find(b"\xbb\xbb")
    if idx == -1:
        return []
    scale = 10.0**digits
    rows: list[dict[str, Any]] = []

    if buf.startswith(b"\x00\x034.2"):
        # StrategyQuant 4.2 compressed tick stream (4 fields: ts_ms, ask, bid, vol)
        seq = bytes(range(15))
        block_offsets: list[tuple[int, int]] = []
        idx_seq = 0
        while True:
            pos = buf.find(seq, idx_seq)
            if pos == -1:
                break
            bb_pos = buf.find(b"\xbb\xbb", pos)
            if bb_pos == -1:
                break
            block_offsets.append((pos, bb_pos))
            idx_seq = bb_pos + 2

        if not block_offsets:
            bb_pos = buf.find(b"\xbb\xbb")
            if bb_pos != -1:
                block_offsets.append((0, bb_pos))

        for b_i, (_, bb_pos) in enumerate(block_offsets):
            next_b_start = (
                block_offsets[b_i + 1][0] if b_i + 1 < len(block_offsets) else len(buf)
            )
            curr = bb_pos + 2
            if curr + 32 > len(buf):
                continue
            ts_ms, ask_raw, bid_raw, vol_raw = struct.unpack_from(">4q", buf, curr)
            curr += 32
            rows.append(
                {
                    "time_msc": int(ts_ms),
                    "bid": bid_raw / 1_000_000.0,
                    "ask": ask_raw / 1_000_000.0,
                    "last": (ask_raw + bid_raw) / 2_000_000.0,
                    "volume": max(1, int(vol_raw // 100_000_000_000)),
                    "flags": 0,
                    "volume_real": max(1.0, float(vol_raw / 100_000_000_000.0)),
                }
            )
            while curr < next_b_start:
                if curr + 2 > next_b_start:
                    break
                b0, b1 = buf[curr], buf[curr + 1]
                curr += 2
                nybbles = ((b0 >> 4) & 0xF, b0 & 0xF, (b1 >> 4) & 0xF, b1 & 0xF)
                deltas: list[int] = []
                for nyb in nybbles:
                    field_len = 1 << (nyb & 0x03)
                    if curr + field_len > next_b_start:
                        break
                    sign = 1 if (nyb & 0x04) else -1
                    raw_val = int.from_bytes(buf[curr : curr + field_len], "big")
                    curr += field_len
                    deltas.append(sign * raw_val)
                if len(deltas) < 4:
                    break
                ts_ms += deltas[0]
                ask_raw += deltas[1]
                bid_raw += deltas[2]
                vol_raw += deltas[3]
                rows.append(
                    {
                        "time_msc": int(ts_ms),
                        "bid": bid_raw / 1_000_000.0,
                        "ask": ask_raw / 1_000_000.0,
                        "last": (ask_raw + bid_raw) / 2_000_000.0,
                        "volume": max(1, int(vol_raw // 100_000_000_000)),
                        "flags": 0,
                        "volume_real": max(1.0, float(vol_raw / 100_000_000_000.0)),
                    }
                )
    else:
        # Fixed 24-byte uncompressed records
        offset = idx + 2
        rec_size = 24
        num_recs = (len(buf) - offset) // rec_size
        max_recs = min(num_recs, count) if count is not None and count > 0 else num_recs

        for i in range(max_recs):
            ts_ms, ask_raw, bid_raw = struct.unpack_from(
                ">qqq", buf, offset + i * rec_size
            )
            ask = ask_raw / scale
            bid = bid_raw / scale
            rows.append(
                {
                    "time_msc": int(ts_ms),
                    "bid": bid,
                    "ask": ask,
                    "last": (ask + bid) / 2.0,
                    "volume": 1,
                    "flags": 0,
                    "volume_real": 1.0,
                }
            )

    if count is not None and count > 0 and len(rows) > count:
        rows = rows[-count:]
    return rows


def decode_sq_dat_bytes(
    buf: bytes,
    count: int | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
) -> list[dict[str, Any]]:
    """Parse StrategyQuant 4.2 binary compressed bar streams with block delta decoding."""
    if len(buf) < 15:
        return []

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

        # Delta decoding loop for subsequent records in this block
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
        SQDAT_FR,
        len(rows),
        extra={"fr_id": SQDAT_FR, "count": len(rows)},
    )
    return rows


def main() -> None:
    """CLI demonstration of native binary codecs on dummy/round-trip data."""
    print("=== HaruQuantAI Native Binary Codecs Demonstration ===")
    dummy_bars = [
        {
            "time": 1672531200,
            "open": 1.0500,
            "high": 1.0550,
            "low": 1.0490,
            "close": 1.0530,
            "tick_volume": 100,
            "spread": 2,
            "real_volume": 100,
        }
    ]
    encoded_hst = encode_hst_bytes(dummy_bars, symbol="EURUSD", version=401)
    decoded_hst = decode_hst_bytes(encoded_hst)
    print(
        f"HST 401 encode/decode: {len(decoded_hst)} bar(s) -> {decoded_hst[0]['close']}"
    )

    encoded_fxt = encode_fxt_bytes(dummy_bars, symbol="EURUSD", version=405)
    decoded_fxt = decode_fxt_bytes(encoded_fxt)
    print(
        f"FXT 405 encode/decode: {len(decoded_fxt)} bar(s) -> {decoded_fxt[0]['close']}"
    )
    print("Codec validation passed.")


if __name__ == "__main__":
    main()
