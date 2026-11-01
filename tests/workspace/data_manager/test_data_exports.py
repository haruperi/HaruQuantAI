"""Exports contain actual fixture prices and independently checked binary records."""

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
