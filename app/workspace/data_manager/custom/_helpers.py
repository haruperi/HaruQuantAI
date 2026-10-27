"""Validation and bounded file helpers for custom indicators."""

from __future__ import annotations

import csv
import io
import json
import math
import re
import tempfile
import zipfile
from collections.abc import Callable, Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

import httpx

from app.host.persistence import HostPersistence
from app.host.response import ErrorCode

_DEFINITIONS = "datamgr_custom"
_OBSERVATIONS = "datamgr_custom_values"
_FORMATS = "datamgr_custom_formats"
_BATCH = 1000
_MAX_OUTPUTS = 5
_MAX_NAME = 100
_ASCII_SPACE = 32
_MAX_FILE_BYTES = 100 * 1024 * 1024
_MAX_ROWS = 1_000_000
_FIRST_COT_YEAR = 1986
_COT_COLUMNS = {
    "CommercialLong": "Comm_Positions_Long_All",
    "CommercialShort": "Comm_Positions_Short_All",
    "NonCommercialLong": "NonComm_Positions_Long_All",
    "NonCommercialShort": "NonComm_Positions_Short_All",
    "OpenInterest": "Open_Interest_All",
}


class CustomDataError(ValueError):
    """Validate or transform custom-indicator data at the service boundary."""

    def __init__(self, message: str, code: ErrorCode = ErrorCode.VALIDATION) -> None:
        super().__init__(message)
        self.code = code


def response_data(response: dict[str, Any]) -> Any:
    """Validate or transform custom-indicator data at the service boundary."""
    if not response["success"]:
        error = response.get("error") or {}
        raise CustomDataError(
            error.get("message", "Storage operation failed"),
            ErrorCode(error.get("code", "internal")),
        )
    return response["data"]


def read_all(
    gateway: HostPersistence, table: str, filters: Any = None
) -> list[dict[str, Any]]:
    """Validate or transform custom-indicator data at the service boundary."""
    rows: list[dict[str, Any]] = []
    offset: int | None = 0
    while offset is not None:
        page = response_data(
            gateway.read_records(table, filters=filters, limit=_BATCH, offset=offset)
        )
        rows.extend(page["records"])
        offset = page["pagination"]["next_offset"]
    return rows


def validate_name(value: Any) -> str:
    """Validate or transform custom-indicator data at the service boundary."""
    if (
        not isinstance(value, str)
        or not value.strip()
        or len(value.strip()) > _MAX_NAME
    ):
        raise CustomDataError("Names must contain 1-100 characters")
    if any(ord(char) < _ASCII_SPACE for char in value):
        raise CustomDataError("Names cannot contain control characters")
    return value.strip()


def _targets(values: str | Sequence[str]) -> list[str]:
    items = [values] if isinstance(values, str) else values
    if not isinstance(items, (list, tuple)) or not items:
        raise CustomDataError("Select at least one indicator")
    return list(
        {validate_name(item).casefold(): validate_name(item) for item in items}.values()
    )


def validate_outputs(values: Any) -> list[dict[str, str]]:
    """Validate or transform custom-indicator data at the service boundary."""
    if not isinstance(values, list) or not 1 <= len(values) <= _MAX_OUTPUTS:
        raise CustomDataError("Specify one to five named value columns")
    result: list[dict[str, str]] = []
    for item in values:
        if not isinstance(item, dict) or set(item) - {"name", "mt4", "mt5", "el"}:
            raise CustomDataError("Invalid output definition")
        name = validate_name(item.get("name"))
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9]*", name):
            raise CustomDataError(
                "Output names require a leading letter and only letters or digits"
            )
        output = {"name": name}
        for platform in ("mt4", "mt5", "el"):
            mapping = item.get(platform)
            mapping = "" if mapping is None else mapping
            if not isinstance(mapping, str):
                raise CustomDataError("Platform mappings must be strings")
            output[platform] = mapping
        result.append(output)
    if len({item["name"].casefold() for item in result}) != len(result):
        raise CustomDataError("Output names must be unique")
    return result


def timestamp(value: Any, date_format: str | None = None) -> str:
    """Validate or transform custom-indicator data at the service boundary."""
    if not isinstance(value, str) or not value.strip():
        raise CustomDataError("An observation requires a date")
    text = value.strip()
    parsed = (
        datetime.strptime(text, date_format)  # noqa: DTZ007 - UTC assigned below
        if date_format
        else datetime.fromisoformat(text)
    )
    return (
        parsed.replace(tzinfo=UTC).isoformat()
        if parsed.tzinfo is None
        else parsed.astimezone(UTC).isoformat()
    )


def read_text(path: str | Path) -> str:
    """Validate or transform custom-indicator data at the service boundary."""
    with Path(path).open("rb") as stream:
        raw = stream.read(_MAX_FILE_BYTES + 1)
    if len(raw) > _MAX_FILE_BYTES:
        raise CustomDataError("File exceeds the 100 MiB limit")
    return raw.decode("utf-8-sig")


def atomic_text(path: str | Path, content: str) -> None:
    """Validate or transform custom-indicator data at the service boundary."""
    destination = Path(path)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", newline="", dir=destination.parent, delete=False
        ) as stream:
            temporary = Path(stream.name)
            stream.write(content)
        temporary.replace(destination)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def normalize_format(config: Mapping[str, Any]) -> dict[str, Any]:
    """Validate or transform custom-indicator data at the service boundary."""
    allowed = {
        "separator",
        "date_format",
        "skip_rows",
        "skip_columns",
        "columns",
        "error_handling",
    }
    if not isinstance(config, Mapping) or set(config) - allowed:
        raise CustomDataError("Unknown import-format fields")
    result = {
        "separator": ",",
        "date_format": None,
        "skip_rows": 0,
        "skip_columns": 0,
        "columns": [],
        "error_handling": "abort",
        **config,
    }
    if result["separator"] not in (",", ";", "\t", "|"):
        raise CustomDataError("Unsupported separator")
    for key in ("skip_rows", "skip_columns"):
        if (
            isinstance(result[key], bool)
            or not isinstance(result[key], int)
            or result[key] < 0
        ):
            raise CustomDataError("Skip counts must be non-negative integers")
    if result["date_format"] is not None and not isinstance(result["date_format"], str):
        raise CustomDataError("date_format must be a string or null")
    columns = result["columns"]
    if (
        not isinstance(columns, list)
        or not columns
        or any(not isinstance(column, str) for column in columns)
    ):
        raise CustomDataError(
            "Specify columns containing date, output names, or ignore"
        )
    if columns.count("date") != 1 or len([c for c in columns if c != "ignore"]) != len(
        {c for c in columns if c != "ignore"}
    ):
        raise CustomDataError(
            "Columns require exactly one date and unique output names"
        )
    if result["error_handling"] not in ("abort", "skip"):
        raise CustomDataError("error_handling must be abort or skip")
    return result


def fetch_cot(year: int) -> str:
    """Download the CFTC legacy futures-only annual CSV archive with bounds."""
    url = f"https://www.cftc.gov/files/dea/history/deacot{year}.zip"
    buffer = io.BytesIO()
    with httpx.stream("GET", url, timeout=60, follow_redirects=False) as response:
        response.raise_for_status()
        for chunk in response.iter_bytes():
            buffer.write(chunk)
            if buffer.tell() > _MAX_FILE_BYTES:
                raise CustomDataError("COT download exceeds the size limit")
    with zipfile.ZipFile(buffer) as archive:
        members = [
            item
            for item in archive.infolist()
            if item.filename.lower().endswith((".txt", ".csv"))
        ]
        if len(members) != 1 or members[0].file_size > _MAX_FILE_BYTES:
            raise CustomDataError("Unexpected COT archive contents")
        return archive.read(members[0]).decode("utf-8-sig")


def parse_csv_row(
    raw: list[str], config: dict[str, Any], seen: dict[str, Any]
) -> tuple[str, dict[str, float]]:
    """Normalize one dated numeric CSV observation."""
    columns = config["columns"]
    cells = raw[config["skip_columns"] :]
    if len(cells) != len(columns):
        raise CustomDataError("Column count does not match format")
    text = cells[columns.index("date")]
    pattern = config["date_format"]
    if pattern and "%" not in pattern:
        for old, new in (
            ("yyyy", "%Y"),
            ("MM", "%m"),
            ("dd", "%d"),
            ("HH", "%H"),
            ("mm", "%M"),
            ("ss", "%S"),
            ("SSS", "%f"),
        ):
            pattern = pattern.replace(old, new)
    if "time" in columns:
        clock = cells[columns.index("time")]
        text += " " + clock
        if pattern and "%H" not in pattern:
            pattern += (
                " %H:%M"
                + (":%S" if clock.count(":") > 1 else "")
                + (".%f" if "." in clock else "")
            )
    date = timestamp(text, pattern)
    values = {
        column: float(cell)
        for column, cell in zip(columns, cells, strict=True)
        if column not in {"date", "time", "ignore"}
    }
    if not all(math.isfinite(value) for value in values.values()):
        raise CustomDataError("Values must be finite numbers")
    if date in seen:
        raise CustomDataError("Duplicate observation timestamp")
    return date, values


def parse_cot_reports(
    selected: Sequence[int], fetcher: Callable[[int], str] | None
) -> dict[str, dict[str, dict[str, Any]]]:
    """Validate annual CFTC reports and group by stable contract code."""
    grouped: dict[str, dict[str, dict[str, Any]]] = {}
    for year in dict.fromkeys(selected):
        content = (fetcher or fetch_cot)(year)
        if not isinstance(content, str) or len(content) > _MAX_FILE_BYTES:
            raise CustomDataError("Invalid or oversized COT report")
        count = 0
        for raw in csv.DictReader(io.StringIO(content)):
            report = {str(key).strip(): value for key, value in raw.items()}
            code = report["CFTC_Contract_Market_Code"].strip()
            if not re.fullmatch(r"[A-Za-z0-9]+", code):
                raise CustomDataError("Invalid CFTC contract code")
            date = timestamp(report["As_of_Date_In_Form_YYYY-MM-DD"])
            values = {
                key: float(report[column].replace(",", ""))
                for key, column in _COT_COLUMNS.items()
            }
            if not all(math.isfinite(value) for value in values.values()):
                raise CustomDataError("COT report contains non-finite values")
            grouped.setdefault(f"COT{code}", {})[date] = {
                "timestamp": date,
                "values_json": json.dumps(values),
            }
            count += 1
            if count > _MAX_ROWS:
                raise CustomDataError("COT report exceeds one million rows")
        if not count:
            raise CustomDataError("Empty COT report")
    return grouped


def definition_file(path: str | Path, on_conflict: str) -> list[Any]:
    """Validate the versioned definition-transfer envelope."""
    payload = json.loads(read_text(path))
    if (
        not isinstance(payload, dict)
        or type(payload.get("version")) is not int
        or payload["version"] != 1
        or not isinstance(payload.get("indicators"), list)
        or on_conflict not in ("error", "skip", "overwrite")
    ):
        raise CustomDataError("Invalid definition file or conflict policy")
    return cast("list[Any]", payload["indicators"])


_MAX_ERRORS = 100

__all__ = [
    "_ASCII_SPACE",
    "_BATCH",
    "_COT_COLUMNS",
    "_DEFINITIONS",
    "_FIRST_COT_YEAR",
    "_FORMATS",
    "_MAX_ERRORS",
    "_MAX_FILE_BYTES",
    "_MAX_NAME",
    "_MAX_OUTPUTS",
    "_MAX_ROWS",
    "_OBSERVATIONS",
    "CustomDataError",
    "_targets",
    "atomic_text",
    "definition_file",
    "fetch_cot",
    "normalize_format",
    "parse_cot_reports",
    "parse_csv_row",
    "read_all",
    "read_text",
    "response_data",
    "timestamp",
    "validate_name",
    "validate_outputs",
]

_MAX_INLINE_OUTPUTS: int = 2
_MAX_DATE_LEN: int = 10


def _get(item: Any, key: str, default: Any = "") -> Any:
    from collections.abc import Mapping

    if isinstance(item, Mapping):
        return item.get(key, default)
    return getattr(item, key, default)


def format_custom_table(
    indicators: Sequence[Any] | Mapping[str, Any], limit: int | None = 50
) -> str:
    """Format ASCII table of external indicator catalog entries."""
    from collections.abc import Mapping

    items: Sequence[Any]
    if (
        isinstance(indicators, Mapping)
        and "data" in indicators
        and isinstance(indicators["data"], Sequence)
    ):
        items = cast("Any", indicators["data"])
    elif isinstance(indicators, Sequence):
        items = indicators
    else:
        items = ()
    count = len(items)
    lines: list[str] = [f"=== External Indicators Catalog ({count} items) ==="]
    header_fmt = (
        "| {name:<20} | {values:<16} | {dtype:<12} | {tf:<9} "
        "| {d_from:<12} | {d_to:<12} | {days:>6} | {recs:>10} |"
    )
    divider = (
        "|-"
        + "-|-".join(["-" * width for width in (20, 16, 12, 9, 12, 12, 6, 10)])
        + "-|"
    )
    lines.append(
        header_fmt.format(
            name="Name",
            values="Values",
            dtype="Data type",
            tf="Timeframe",
            d_from="Date from",
            d_to="Date to",
            days="Days",
            recs="Records",
        )
    )
    lines.append(divider)
    visible = items if limit is None else items[:limit]
    for item in visible:
        name = str(_get(item, "name", ""))
        vals = _get(item, "values", [])
        if isinstance(vals, list):
            val_names = [
                v.get("name", "") if isinstance(v, dict) else str(v) for v in vals
            ]
            val_str = (
                ", ".join(val_names)
                if len(val_names) <= _MAX_INLINE_OUTPUTS
                else f"{len(val_names)} outputs"
            )
        else:
            val_str = str(vals)
        dtype = str(_get(item, "data_type", "custom"))
        tf = str(_get(item, "timeframe", "D1"))
        d_from = str(_get(item, "date_from", "") or "-")
        if len(d_from) > _MAX_DATE_LEN:
            d_from = d_from[:_MAX_DATE_LEN]
        d_to = str(_get(item, "date_to", "") or "-")
        if len(d_to) > _MAX_DATE_LEN:
            d_to = d_to[:_MAX_DATE_LEN]
        days = _get(item, "total_days", 0)
        recs = f"{int(_get(item, 'total_records', 0)):,}"
        lines.append(
            header_fmt.format(
                name=name[:20],
                values=val_str[:16],
                dtype=dtype[:12],
                tf=tf[:9],
                d_from=d_from[:12],
                d_to=d_to[:12],
                days=days,
                recs=recs,
            )
        )
    if limit is not None and count > limit:
        lines.append(f"... and {count - limit} more items")
    return "\n".join(lines)


def format_review_table(records: Sequence[Any], columns: Sequence[str]) -> str:
    """Format ASCII table of dated observation records."""
    if not records:
        return "No observations recorded."
    header_cols = ["Timestamp", *columns]
    col_widths = [max(len(str(c)), 12) for c in header_cols]
    col_widths[0] = max(col_widths[0], 25)
    header_fmt = (
        "| " + " | ".join(f"{{{i}:<{w}}}" for i, w in enumerate(col_widths)) + " |"
    )
    divider = "|-" + "-|-".join("-" * w for w in col_widths) + "-|"
    lines = [
        header_fmt.format(*header_cols),
        divider,
    ]
    for row in records:
        ts = str(_get(row, "timestamp", ""))
        vals = _get(row, "values", {})
        cells = [
            ts[: col_widths[0]],
            *(
                str(vals.get(c, ""))[: col_widths[i + 1]]
                if isinstance(vals, dict)
                else ""
                for i, c in enumerate(columns)
            ),
        ]
        lines.append(header_fmt.format(*cells))
    return "\n".join(lines)


class CustomDataCLI:
    """Table formatters for Data Manager custom indicators."""

    format_custom_table = staticmethod(format_custom_table)
    format_review_table = staticmethod(format_review_table)
