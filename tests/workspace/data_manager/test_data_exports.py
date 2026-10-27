"""Exports contain actual fixture prices and independently checked binary records."""

import struct

from app.workspace.data_manager.data.exports import DataExports
from app.workspace.data_manager.data.review import DatasetReview


def test_csv_and_mt5_export_match_source(recorded_history):
    gateway, identifier, root = recorded_history
    frame = DatasetReview(gateway, identifier).frame()
    exporter = DataExports(gateway)
    path = root / "prices.csv"
    exporter.export_csv(frame, path, {"delimiter": ";"})
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    assert len(lines) == 7 and "1.12" in lines[1] and ";" in lines[1]
    exporter.export_mt5(frame, path, {"fixed_spread": 2})
    assert "1.12" in path.read_text(encoding="utf-8-sig")


def test_mt4_headers_and_first_record_against_binary_layout(recorded_history):
    gateway, identifier, root = recorded_history
    frame = DatasetReview(gateway, identifier).frame()
    paths = DataExports(gateway).export_mt4(
        frame, root, "EURUSD", {"mode": "all", "timeframe": "M1"}
    )
    hst = next(p for p in paths if p.suffix == ".hst").read_bytes()
    assert struct.unpack_from("<i", hst)[0] == 401
    assert len(hst) == 148 + 6 * 60
    stamp, open_, high, low, close, volume, _, _ = struct.unpack_from(
        "<qddddqiq", hst, 148
    )
    assert stamp == int(frame.index[0].timestamp())
    assert (open_, high, low, close, volume) == (1.1, 1.13, 1.09, 1.12, 10)
