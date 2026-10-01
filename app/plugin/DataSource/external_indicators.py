# ruff: noqa: INP001, N815, PLR2004 -- namespace, existing wire fields and limits.
"""External indicator metadata and real value imports.

Description:
    Validates custom indicator definitions and parses uploaded text under host
    jobs. Host settings retain metadata; market custody retains timestamped values.
Purpose:
    FEAT-DM-EXTERNAL_INDICATORS: Durable external indicator integration.
Key Capabilities:
    - FR-INDICATORS-DEFINITIONS: Immutable metadata validation; logs updates.
    - FR-INDICATORS-IMPORT: Real CSV value parsing; logs accepted and ignored rows.
    - FR-INDICATORS-CUSTODY: Producer-independent Parquet values; logs publication.
Python API Usage:
    contribution = await prepare(capabilities)
    state = await contribution.invoke("state.get", {})
CLI Usage:
    uv run pytest tests/plugin/DataSource/test_external_indicators.py --no-cov
"""

from __future__ import annotations

import asyncio
import csv
import io
import math
from datetime import UTC, datetime
from itertools import pairwise
from typing import Any, Literal, cast

import pandas as pd  # type: ignore[import-untyped]
import pyarrow as pa  # type: ignore[import-untyped]
from app.host.capabilities import (
    HostCapabilities,
    JobAccess,
    MarketAccess,
    SettingsAccess,
)
from app.host.contracts import Document
from app.host.jobs import Budget
from app.host.logging import get_logger
from app.host.packages import PreparedContribution
from pydantic import Field, JsonValue, model_validator

logger = get_logger(__name__)
PLUGIN = {
    "id": "plugin.data_manager.indicators",
    "kind": "plugin",
    "version": "1.0.0",
    "compatibility": "1",
    "owner_workspace_id": "workspace.data_manager",
    "slot_id": "data_source.acquisition",
    "contract_version": "1.0.0",
    "requires": [
        {"id": "host.market_data", "version": "1.0.0"},
        {"id": "host.jobs", "version": "1.0.0"},
        {"id": "host.settings", "version": "1.0.0"},
    ],
}


class Line(Document):
    """One optional named output and presentation expressions."""

    name: str = Field(max_length=500, pattern=r"^[A-Za-z0-9]*$")
    mt4: str = Field(max_length=500)
    mt5: str = Field(max_length=500)
    el: str = Field(max_length=500)


class ValueRecord(Document):
    """One finite ordered timestamped observation."""

    timestamp: int
    values: tuple[float, ...] = Field(min_length=1, max_length=3)


class Definition(Document):
    """Custom indicator metadata and explicit transfer observations."""

    name: str = Field(min_length=1, max_length=128)
    type: Literal[1, 2, 3, 10]
    values: tuple[Line, ...] = Field(min_length=3, max_length=3)
    timeframe: str = "—"
    dateFrom: str = ""
    dateTo: str = ""
    totalDays: int = 0
    records: tuple[ValueRecord, ...] = Field(default=(), max_length=200000)

    @model_validator(mode="after")
    def validate_values(self) -> Definition:
        """Reject duplicate names, nonfinite values and unordered observations."""
        names = [line.name for line in self.values if line.name]
        if not self.name.strip() or not names or len(names) != len(set(names)):
            raise ValueError("Indicator names must be nonempty and unique")
        previous = None
        for row in self.records:
            if (
                len(row.values) != len(names)
                or any(not math.isfinite(value) for value in row.values)
                or (previous is not None and row.timestamp <= previous)
            ):
                raise ValueError("Invalid indicator observations")
            previous = row.timestamp
        return self


class ImportFormat(Document):
    """Explicit column mapping and timestamp pattern."""

    name: str = Field(min_length=1, max_length=80)
    separator: Literal[",", ";", "\t", "|", " "]
    skipRows: int = Field(ge=0, le=1000)
    skipColumns: int = Field(ge=0, le=100)
    dateFormat: str = Field(min_length=1, max_length=80)
    columns: tuple[str, ...] = Field(max_length=100)
    predefined: bool = False


class State(Document):
    """One bounded explicit metadata transfer."""

    revision: int = Field(default=0, ge=0)
    definitions: tuple[Definition, ...] = Field(default=(), max_length=10000)
    formats: tuple[ImportFormat, ...] = Field(default=(), max_length=100)

    @model_validator(mode="after")
    def names(self) -> State:
        """Ensure transferred identities are case-insensitively unique."""
        for names in (
            [item.name.casefold() for item in self.definitions],
            [item.name.casefold() for item in self.formats],
        ):
            if len(names) != len(set(names)):
                raise ValueError("Duplicate indicator or format names")
        return self


class ImportRequest(Document):
    """Raw file content remains backend parsing input."""

    indicator: str
    text: str = Field(max_length=10 * 1024 * 1024)
    format: ImportFormat
    ignore_errors: bool = False


def parse(  # noqa: C901 -- mapped column and row error policies.
    text: str, import_format: ImportFormat, count: int, ignore_errors: bool
) -> tuple[list[dict[str, Any]], int]:
    """Parse mapped UTF-8 text with strict dates, finite values and duplicate policy."""
    used = [column for column in import_format.columns if column != "Unused"]
    if (
        not used
        or "" in used
        or len(used) != len(set(used))
        or ("Date" in used) == ("Date & Time" in used)
    ):
        raise ValueError("Map one Date or Date & Time column and unique value columns")
    if any(f"Value {index}" not in used for index in range(1, count + 1)):
        raise ValueError("Map every active indicator value")
    pattern = import_format.dateFormat
    for token, code in (
        ("yyyy", "%Y"),
        ("SSS", "%f"),
        ("MM", "%m"),
        ("dd", "%d"),
        ("HH", "%H"),
        ("mm", "%M"),
        ("ss", "%S"),
    ):
        pattern = pattern.replace(token, code)
    if any(part not in import_format.dateFormat for part in ("yyyy", "MM", "dd")):
        raise ValueError("Date pattern must specify year, month and day")
    positions = {name: index for index, name in enumerate(import_format.columns)}
    records: dict[int, list[float]] = {}
    ignored = 0
    rows = csv.reader(
        io.StringIO(text.lstrip("\ufeff")),
        delimiter=import_format.separator,
        strict=True,
    )
    for number, raw_cells in enumerate(rows):
        cells = raw_cells
        if number < import_format.skipRows or not any(cell.strip() for cell in cells):
            continue
        if number - import_format.skipRows >= 100000:
            raise ValueError("Indicator import exceeds 100000 rows")
        cells = cells[import_format.skipColumns :]
        try:
            stamp_text = cells[
                positions.get("Date & Time", positions.get("Date", 0))
            ].strip()
            if "Time" in positions:
                stamp_text += " " + cells[positions["Time"]].strip()
            selected_pattern = (
                pattern + " %H:%M:%S"
                if "Time" in positions and "%H" not in pattern
                else pattern
            )
            stamp = datetime.strptime(stamp_text, selected_pattern).replace(tzinfo=UTC)
            values = [
                float(cells[positions[f"Value {index}"]])
                for index in range(1, count + 1)
            ]
            if stamp.year < 1900 or any(not math.isfinite(value) for value in values):
                raise ValueError("Invalid date or value")  # noqa: TRY301 -- row error policy.
            records[int(stamp.timestamp() * 1000)] = values
        except ValueError, IndexError:
            if not ignore_errors:
                raise ValueError(f"Invalid indicator row {number + 1}") from None
            ignored += 1
    if not records:
        raise ValueError("No valid indicator records")
    return [
        {"timestamp": stamp, "values": records[stamp]} for stamp in sorted(records)
    ], ignored


class Runtime:
    """Own definitions, format metadata and real import jobs."""

    def __init__(
        self, market: MarketAccess, jobs: JobAccess, settings: SettingsAccess
    ) -> None:
        self.market, self.jobs, self.settings = market, jobs, settings
        self.progress: dict[str, dict[str, Any]] = {}

    def snapshot(self) -> dict[str, Any]:
        """Read metadata and current published values from host custody."""
        state = self.settings.get("indicator_state") or {
            "definitions": [],
            "formats": [],
        }
        result = {
            "revision": state.get("revision", 0),
            "definitions": [],
            "formats": state["formats"],
        }
        datasets = {row["underlying"]: row for row in self.market.source_definitions()}
        for original in state["definitions"]:
            item = {
                **original,
                "records": [],
                "dateFrom": "",
                "dateTo": "",
                "totalDays": 0,
            }
            dataset = datasets.get(item["name"])
            if dataset and dataset["bars"]:
                frame = self.market.read_source(dataset["id"]).to_pandas()
                stamps = pd.to_datetime(frame["DateTime"], utc=True)
                item["records"] = [
                    {
                        "timestamp": int(stamp.timestamp() * 1000),
                        "values": [float(value) for value in row],
                    }
                    for stamp, row in zip(
                        stamps, frame.drop(columns="DateTime").values, strict=True
                    )
                ]
                item.update(
                    timeframe=dataset["timeframe"],
                    dateFrom=stamps.iloc[0].date().isoformat(),
                    dateTo=stamps.iloc[-1].date().isoformat(),
                    totalDays=len(stamps.dt.date.unique()),
                )
            result["definitions"].append(item)
        return result

    def publish(
        self, definition: Definition, records: list[dict[str, Any]], timeframe: str
    ) -> None:
        """Publish complete indicator values with immutable source schema."""
        dataset_id = self.market.register_source(
            source="ExternalIndicator",
            symbol=definition.name,
            underlying=definition.name,
            instrument=definition.name,
            timeframe=timeframe,
            options={},
        )
        frame = pd.DataFrame(
            {
                "DateTime": pd.to_datetime(
                    [row["timestamp"] for row in records], unit="ms", utc=True
                ),
                **{
                    f"Value{index + 1}": [row["values"][index] for row in records]
                    for index in range(len(records[0]["values"]))
                },
            }
        )
        tables = {
            str(year): pa.Table.from_pandas(part, preserve_index=False)
            for year, part in frame.groupby(frame["DateTime"].dt.year)
        }
        self.market.replace_source(
            dataset_id,
            tables,
            expected_revisions=self.market.retained_revisions(dataset_id),
        )
        for old in self.market.source_definitions():
            if old["underlying"] == definition.name and old["id"] != dataset_id:
                self.market.remove_source(old["id"], clear_only=False)
        logger.info(
            "Indicator data published: name=%s rows=%d", definition.name, len(records)
        )

    async def invoke(  # noqa: C901, PLR0912 -- explicit operations.
        self, operation: str, payload: JsonValue
    ) -> JsonValue:
        """Handle explicit state and import requests with actual backend outcomes."""
        values = payload if isinstance(payload, dict) else {}
        logger.info("External indicators operation: %s", operation)
        if operation == "state.get":
            return cast("JsonValue", self.snapshot())
        if operation == "state.replace":
            state = State.model_validate(values)
            if any(
                self.jobs.status(job_id).state in ("queued", "running")
                for job_id in self.progress
            ):
                raise ValueError("Finish or cancel the active import before editing")
            snapshot = self.snapshot()
            if state.revision != snapshot["revision"]:
                raise ValueError("Indicator state changed; reload before editing")
            previous = {row["name"]: row for row in snapshot["definitions"]}
            names = {definition.name for definition in state.definitions}
            for definition in state.definitions:
                records = [row.model_dump(mode="json") for row in definition.records]
                if records and records != previous.get(definition.name, {}).get(
                    "records"
                ):
                    self.publish(definition, records, definition.timeframe)
                elif not records and previous.get(definition.name, {}).get("records"):
                    for dataset in self.market.source_definitions():
                        if dataset["underlying"] == definition.name:
                            self.market.remove_source(dataset["id"], clear_only=True)
            for dataset in self.market.source_definitions():
                if dataset["underlying"] not in names:
                    self.market.remove_source(dataset["id"], clear_only=False)
            self.settings.set(
                "indicator_state",
                {
                    "revision": state.revision + 1,
                    "definitions": [
                        {**item.model_dump(mode="json"), "records": []}
                        for item in state.definitions
                    ],
                    "formats": [item.model_dump(mode="json") for item in state.formats],
                },
            )
            return cast("JsonValue", self.snapshot())
        if operation == "import.start":
            request = ImportRequest.model_validate(values)
            target_definition = next(
                (
                    Definition.model_validate(row)
                    for row in self.snapshot()["definitions"]
                    if row["name"] == request.indicator
                ),
                None,
            )
            if target_definition is None:
                raise ValueError("Indicator definition unavailable")
            progress: dict[str, Any] = {"rows": 0, "ignored": 0}

            async def run() -> None:
                records, ignored = await self.jobs.offload(
                    parse,
                    request.text,
                    request.format,
                    len([line for line in target_definition.values if line.name]),
                    request.ignore_errors,
                )
                await asyncio.sleep(0)
                gaps = [
                    right["timestamp"] - left["timestamp"]
                    for left, right in pairwise(records)
                ]
                minutes = min(gaps) // 60000 if gaps else 0
                timeframe = {
                    1: "M1",
                    5: "M5",
                    15: "M15",
                    30: "M30",
                    60: "H1",
                    240: "H4",
                    1440: "D1",
                }.get(minutes, "Custom")
                self.publish(target_definition, records, timeframe)
                metadata = self.settings.get("indicator_state") or {}
                metadata["revision"] = metadata.get("revision", 0) + 1
                self.settings.set("indicator_state", metadata)
                progress.update(rows=len(records), ignored=ignored)

            job = self.jobs.submit(Budget(1, 256 * 1024 * 1024, 300), run)
            self.progress[job.id] = progress
            return {"job_id": job.id, "state": job.state}
        if operation in ("import.status", "import.cancel"):
            job_id = str(values.get("job_id", ""))
            if operation == "import.cancel":
                self.jobs.cancel(job_id)
            job = self.jobs.status(job_id)
            return cast("JsonValue", {"state": job.state, **self.progress[job.id]})
        raise ValueError("Unknown indicator operation")

    async def close(self) -> None:
        """Await the owner's import jobs."""
        await self.jobs.close()
        logger.info("External indicators closed")


async def prepare(context: HostCapabilities) -> PreparedContribution:
    """Bind explicit capabilities to one cohesive indicator contribution."""
    if context.market_data is None or context.jobs is None or context.settings is None:
        raise ValueError("Indicators require market data, jobs and settings")
    runtime = Runtime(context.market_data, context.jobs, context.settings)
    return PreparedContribution(
        (
            "state.get",
            "state.replace",
            "import.start",
            "import.status",
            "import.cancel",
        ),
        runtime.invoke,
        runtime.close,
    )
