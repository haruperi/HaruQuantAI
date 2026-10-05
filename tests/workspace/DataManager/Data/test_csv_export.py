"""Verify csv export boundaries and explicit semantics."""

import csv
from dataclasses import replace
from io import StringIO
from typing import Any

from app.workspace.DataManager.Data.contracts import TickRecord
from app.workspace.DataManager.Data.csv_export import export_csv


def test_bar_export_column_order_precision_and_inclusive_dates(dataset):
    writer = StringIO()
    result = export_csv(
        dataset, writer, precision=2, date_from_ms=60_000, date_to_ms=60_000
    ).unwrap()
    assert result.rows_written == 1
    assert list(csv.reader(StringIO(writer.getvalue()))) == [
        ["time_ms", "open", "high", "low", "close", "volume"],
        ["60000", "10.00", "11.00", "9.00", "10.00", "4.00"],
    ]
    assert "\r" not in writer.getvalue()
    assert not writer.closed


def test_tick_volume_and_custom_quoting(dataset):
    ticks = replace(
        dataset, symbol="FX:PAIR", timeframe="TICK", records=(TickRecord(0, 1, 2, 0.5),)
    )
    writer = StringIO()
    assert (
        export_csv(
            ticks,
            writer,
            separator=":",
            columns=("symbol", "volume", "bid"),
            precision=1,
            include_header=False,
        )
        .unwrap()
        .rows_written
        == 1
    )
    assert list(csv.reader(StringIO(writer.getvalue()), delimiter=":")) == [
        ["FX:PAIR", "0.5", "1.0"]
    ]
    assert ticks.records[0].volume == 0.5


def test_invalid_options_write_nothing(dataset):
    cases: list[tuple[dict[str, Any], str]] = [
        ({"precision": -1}, "INVALID_PRECISION"),
        ({"precision": 16}, "INVALID_PRECISION"),
        ({"precision": True}, "INVALID_PRECISION"),
        ({"separator": ""}, "INVALID_FORMAT"),
        ({"separator": "\n"}, "INVALID_FORMAT"),
        ({"include_header": 1}, "INVALID_FORMAT"),
        ({"date_from_ms": True}, "INVALID_DATES"),
        ({"date_from_ms": 1, "date_to_ms": 0}, "INVALID_DATES"),
        ({"columns": ()}, "INVALID_COLUMNS"),
        ({"columns": ("ask",)}, "INVALID_COLUMNS"),
        ({"columns": ("volume", "volume")}, "INVALID_COLUMNS"),
        ({"timeframe": "H1"}, "UNSUPPORTED_TIMEFRAME"),
    ]
    for kwargs, code in cases:
        writer = StringIO()
        assert export_csv(dataset, writer, **kwargs).error_code == code
        assert writer.getvalue() == ""


def test_empty_and_date_exclusions(dataset):
    writer = StringIO()
    assert (
        export_csv(dataset, writer, date_to_ms=-1, include_header=False)
        .unwrap()
        .rows_written
        == 0
    )
    assert writer.getvalue() == ""
    assert export_csv(replace(dataset, records=()), writer).unwrap().rows_written == 0


def test_writer_failure_reports_partial_output_without_exception(dataset):
    class FailingWriter(StringIO):
        def __init__(self) -> None:
            super().__init__()
            self.calls = 0

        def write(self, value: str) -> int:
            self.calls += 1
            if self.calls == 3:
                raise OSError("private endpoint and credential")
            return super().write(value)

    writer = FailingWriter()
    result = export_csv(dataset, writer)
    assert result.error_code == "CSV_WRITE_FAILED"
    assert (
        result.metadata.side_effects and result.metadata.extensions["rows_written"] == 1
    )
    assert "private endpoint" not in str(result)
