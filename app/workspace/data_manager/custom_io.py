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
from typing import Any

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
    date = timestamp(cells[columns.index("date")], config["date_format"])
    values = {
        column: float(cell)
        for column, cell in zip(columns, cells, strict=True)
        if column not in {"date", "ignore"}
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
    return payload["indicators"]
