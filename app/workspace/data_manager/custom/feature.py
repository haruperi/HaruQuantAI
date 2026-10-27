"""External indicator definitions, dated values, CSV imports and JSON transfers.

CustomData uses HostPersistence exclusively. Its additive schema is installed on
first operation in an existing database. Imports validate before transactional
merge/replacement; optional host jobs support pause/resume/stop and activity logs.
Definitions contain one to five named outputs and MT4/MT5/EasyLanguage mappings.

Python API Usage:
    service = CustomData()
    service.add("Sentiment", values=[{"name": "Score"}])
    service.import_data("Sentiment", "sentiment.csv", columns=["date", "Score"])
    service.review_data("Sentiment")
    service.save("indicators.json")
"""

from __future__ import annotations

import builtins
import csv
import io
import json
import re
import sys
import time
import uuid
import zipfile
from collections.abc import Callable, Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

import httpx

from app.host.persistence import HostPersistence, RecordFilter
from app.host.response import (
    ErrorCode,
    ResponseMetadata,
    StandardError,
    StandardResponse,
)

if TYPE_CHECKING:
    from app.host.jobs import JobContext, JobManager
    from app.workspace.data_manager.logs import Logs

from ._helpers import (
    _BATCH,
    _COT_COLUMNS,
    _DEFINITIONS,
    _FIRST_COT_YEAR,
    _FORMATS,
    _MAX_ROWS,
    _OBSERVATIONS,
    _targets,
    definition_file,
    parse_cot_reports,
    parse_csv_row,
)
from ._helpers import (
    CustomDataError as _CustomError,
)
from ._helpers import (
    atomic_text as _atomic_text,
)
from ._helpers import (
    normalize_format as _format,
)
from ._helpers import (
    read_all as _read,
)
from ._helpers import (
    read_text as _text,
)
from ._helpers import (
    response_data as _data,
)
from ._helpers import (
    validate_name as _name,
)
from ._helpers import (
    validate_outputs as _outputs,
)

__all__ = ["CustomData"]
from ._helpers import _MAX_ERRORS


def _get_parse_cot_reports() -> Any:
    mod = sys.modules.get("app.workspace.data_manager.custom")
    if mod and hasattr(mod, "parse_cot_reports"):
        return mod.parse_cot_reports
    return parse_cot_reports


class CustomData:
    """Transactional custom indicator catalog with optional background imports."""

    def __init__(
        self,
        gateway: HostPersistence | None = None,
        *,
        jobs: JobManager | None = None,
        logs: Logs | None = None,
    ) -> None:
        self.gateway = gateway if gateway is not None else HostPersistence()
        self.jobs, self.logs = jobs, logs

    def _run(self, operation: str, action: Callable[[], Any]) -> dict[str, Any]:
        started = time.perf_counter()
        try:
            _data(self.gateway.ensure_custom_data_schema())
            result = action()
            return StandardResponse.success(
                message=f"Completed custom.{operation}",
                data=result,
                metadata=ResponseMetadata(
                    operation=f"custom.{operation}",
                    duration_ms=(time.perf_counter() - started) * 1000,
                ),
            )
        except (
            ValueError,
            TypeError,
            KeyError,
            OSError,
            RuntimeError,
            httpx.HTTPError,
            csv.Error,
            zipfile.BadZipFile,
        ) as error:
            code = (
                error.code
                if isinstance(error, _CustomError)
                else ErrorCode.UNAVAILABLE
                if isinstance(error, (OSError, RuntimeError, httpx.HTTPError))
                else ErrorCode.VALIDATION
            )
            message = str(error)[:1000] or "Custom data operation failed"
            return StandardResponse.failure(
                message=message,
                metadata=ResponseMetadata(
                    operation=f"custom.{operation}",
                    duration_ms=(time.perf_counter() - started) * 1000,
                ),
                error=StandardError(code=code, message=message),
            )

    @staticmethod
    def _lookup(gateway: HostPersistence, name: str) -> dict[str, Any]:
        target = _name(name)
        rows = _read(gateway, _DEFINITIONS, {"name": target})
        if not rows:
            raise _CustomError("Indicator not found", ErrorCode.NOT_FOUND)
        return rows[0]

    @staticmethod
    def _definition(
        name: str, values: Any, data_type: str, timeframe: str, system: bool
    ) -> dict[str, Any]:
        if not isinstance(system, bool):
            raise _CustomError("system must be boolean")
        return {
            "id": uuid.uuid4().hex,
            "name": _name(name),
            "data_type": _name(data_type),
            "timeframe": _name(timeframe),
            "values_json": json.dumps(_outputs(values)),
            "system": int(system),
            "updated_at": datetime.now(UTC).isoformat(),
        }

    @staticmethod
    def _public(row: dict[str, Any]) -> dict[str, Any]:
        return {key: value for key, value in row.items() if key != "values_json"} | {
            "values": json.loads(row["values_json"]),
            "system": bool(row["system"]),
        }

    def list(self) -> dict[str, Any]:
        """List definitions and authoritative observation date/count summaries."""

        def action() -> Any:
            with self.gateway.transaction() as tx:
                rows = _read(tx, _DEFINITIONS)
                observations = _read(tx, _OBSERVATIONS)
            dates: dict[str, builtins.list[str]] = {}
            for item in observations:
                dates.setdefault(item["indicator_id"], []).append(item["timestamp"])
            result = []
            for row in rows:
                history = sorted(dates.get(row["id"], []))
                result.append(
                    self._public(row)
                    | {
                        "total_records": len(history),
                        "date_from": history[0] if history else None,
                        "date_to": history[-1] if history else None,
                        "total_days": (
                            datetime.fromisoformat(history[-1])
                            - datetime.fromisoformat(history[0])
                        ).days
                        if history
                        else 0,
                    }
                )
            return result

        return self._run("list", action)

    def add(
        self,
        name: str,
        *,
        values: builtins.list[dict[str, Any]],
        data_type: str = "custom",
        timeframe: str = "D1",
        system: bool = False,
    ) -> dict[str, Any]:
        """Create a definition without observations; duplicate names conflict."""

        def action() -> Any:
            row = self._definition(name, values, data_type, timeframe, system)
            with self.gateway.transaction() as tx:
                if _read(tx, _DEFINITIONS, {"name": row["name"]}):
                    raise _CustomError(
                        "Indicator name already exists", ErrorCode.CONFLICT
                    )
                _data(tx.create_records(_DEFINITIONS, row))
            return self._public(row)

        return self._run("add", action)

    def edit(self, name: str, updates: Mapping[str, Any]) -> dict[str, Any]:
        """Edit one definition; structural changes require clearing observations."""

        def action() -> Any:
            if (
                not isinstance(updates, Mapping)
                or not updates
                or set(updates) - {"name", "values", "data_type", "timeframe"}
            ):
                raise _CustomError("Choose supported definition fields to edit")
            with self.gateway.transaction() as tx:
                row = self._lookup(tx, name)
                if row["system"]:
                    raise _CustomError(
                        "System indicator definitions cannot be edited",
                        ErrorCode.FORBIDDEN,
                    )
                public = self._public(row) | dict(updates)
                candidate = self._definition(
                    public["name"],
                    public["values"],
                    public["data_type"],
                    public["timeframe"],
                    public["system"],
                )
                existing = _read(tx, _DEFINITIONS, {"name": candidate["name"]})
                if existing and existing[0]["id"] != row["id"]:
                    raise _CustomError(
                        "Indicator name already exists", ErrorCode.CONFLICT
                    )
                structural = (
                    [item["name"] for item in json.loads(candidate["values_json"])]
                    != [item["name"] for item in json.loads(row["values_json"])]
                    or candidate["data_type"] != row["data_type"]
                    or candidate["timeframe"] != row["timeframe"]
                )
                if structural and _read(tx, _OBSERVATIONS, {"indicator_id": row["id"]}):
                    raise _CustomError(
                        "Clear observations before changing outputs, type or timeframe",
                        ErrorCode.CONFLICT,
                    )
                candidate.pop("id")
                _data(
                    tx.update_record(_DEFINITIONS, candidate, filters={"id": row["id"]})
                )
            return self._public(row | candidate)

        return self._run("edit", action)

    @staticmethod
    def _clear_values(tx: HostPersistence, identifier: str) -> int:
        rows = _read(tx, _OBSERVATIONS, {"indicator_id": identifier})
        for start in range(0, len(rows), _BATCH):
            _data(
                tx.delete_record(
                    _OBSERVATIONS,
                    filters=[
                        RecordFilter("indicator_id", "eq", identifier),
                        RecordFilter(
                            "timestamp",
                            "in",
                            [row["timestamp"] for row in rows[start : start + _BATCH]],
                        ),
                    ],
                )
            )
        return len(rows)

    def _remove(
        self, names: str | Sequence[str], *, definitions: bool
    ) -> dict[str, Any]:
        def action() -> Any:
            with self.gateway.transaction() as tx:
                rows = [self._lookup(tx, name) for name in _targets(names)]
                if definitions and any(row["system"] for row in rows):
                    raise _CustomError(
                        "System indicator definitions cannot be deleted",
                        ErrorCode.FORBIDDEN,
                    )
                count = 0
                for row in rows:
                    count += self._clear_values(tx, row["id"])
                    if definitions:
                        _data(tx.delete_record(_DEFINITIONS, filters={"id": row["id"]}))
            return {
                "names": [row["name"] for row in rows],
                "cleared_records": count,
                "deleted_count": len(rows) if definitions else 0,
            }

        return self._run("delete" if definitions else "clear", action)

    def delete(self, names: str | Sequence[str]) -> dict[str, Any]:
        """Atomically delete selected definitions and their observations."""
        return self._remove(names, definitions=True)

    def clear(self, names: str | Sequence[str]) -> dict[str, Any]:
        """Atomically clear observations, preserving selected definitions."""
        return self._remove(names, definitions=False)

    def review_data(
        self, name: str, *, limit: int = 100, offset: int = 0
    ) -> dict[str, Any]:
        """Return chronological observations in a bounded page."""

        def action() -> Any:
            if (
                isinstance(limit, bool)
                or not isinstance(limit, int)
                or not 1 <= limit <= _BATCH
                or isinstance(offset, bool)
                or not isinstance(offset, int)
                or offset < 0
            ):
                raise _CustomError("Invalid pagination")
            with self.gateway.transaction() as tx:
                row = self._lookup(tx, name)
                page = _data(
                    tx.read_records(
                        _OBSERVATIONS,
                        filters={"indicator_id": row["id"]},
                        limit=limit,
                        offset=offset,
                        order_by=["timestamp"],
                    )
                )
            return {
                "name": row["name"],
                "columns": [item["name"] for item in json.loads(row["values_json"])],
                "records": [
                    {
                        "timestamp": item["timestamp"],
                        "values": json.loads(item["values_json"]),
                    }
                    for item in page["records"]
                ],
                "pagination": page["pagination"],
            }

        return self._run("review_data", action)

    def save(
        self, json_path: str | Path, names: str | Sequence[str] | None = None
    ) -> dict[str, Any]:
        """Atomically save definitions only; observations use CSV export."""

        def action() -> Any:
            with self.gateway.transaction() as tx:
                rows = (
                    _read(tx, _DEFINITIONS)
                    if names is None
                    else [self._lookup(tx, name) for name in _targets(names)]
                )
            definitions = [
                {
                    key: value
                    for key, value in self._public(row).items()
                    if key not in {"id", "updated_at"}
                }
                for row in rows
            ]
            _atomic_text(
                json_path,
                json.dumps({"version": 1, "indicators": definitions}, indent=2),
            )
            return {"path": str(json_path), "count": len(rows)}

        return self._run("save", action)

    def load(
        self, json_path: str | Path, *, on_conflict: str = "error"
    ) -> dict[str, Any]:
        """Atomically load definitions; error/skip/overwrite handles existing names.

        Overwrite clears existing observations, matching donor load semantics.
        System flags cannot be elevated or overwritten by a definition transfer.
        """

        def action() -> Any:
            items = definition_file(json_path, on_conflict)
            candidates = []
            for item in items:
                if not isinstance(item, dict) or set(item) - {
                    "name",
                    "values",
                    "data_type",
                    "timeframe",
                    "system",
                }:
                    raise _CustomError("Invalid indicator definition")
                candidates.append(
                    self._definition(
                        item["name"],
                        item["values"],
                        item.get("data_type", "custom"),
                        item.get("timeframe", "D1"),
                        item.get("system", False),
                    )
                )
            for candidate in candidates:
                candidate["system"] = 0
            if len({row["name"].casefold() for row in candidates}) != len(candidates):
                raise _CustomError(
                    "Duplicate indicator names in file", ErrorCode.CONFLICT
                )
            loaded, skipped = [], []
            with self.gateway.transaction() as tx:
                for candidate in candidates:
                    existing = _read(tx, _DEFINITIONS, {"name": candidate["name"]})
                    if existing:
                        if on_conflict == "skip":
                            skipped.append(candidate["name"])
                            continue
                        if on_conflict == "error" or existing[0]["system"]:
                            raise _CustomError(
                                "Indicator already exists or is system-owned",
                                ErrorCode.CONFLICT,
                            )
                        self._clear_values(tx, existing[0]["id"])
                        candidate["id"] = existing[0]["id"]
                        _data(
                            tx.update_record(
                                _DEFINITIONS,
                                {
                                    key: value
                                    for key, value in candidate.items()
                                    if key != "id"
                                },
                                filters={"id": candidate["id"]},
                            )
                        )
                    else:
                        _data(tx.create_records(_DEFINITIONS, candidate))
                    loaded.append(self._public(candidate))
            return {"loaded": loaded, "skipped": skipped, "loaded_count": len(loaded)}

        return self._run("load", action)

    def recognize_from_file(self, file_path: str | Path) -> dict[str, Any]:
        """Recognize a JSON definition or labelled MQL indicator and add it.

        MQL source is inspected as text, never compiled or executed. Files without
        explicit indicator_label declarations require manual definition creation.
        """

        def action() -> Any:
            path, content = Path(file_path), _text(file_path)
            if path.suffix.lower() == ".json":
                item = json.loads(content)
                if not isinstance(item, dict) or set(item) - {
                    "name",
                    "values",
                    "data_type",
                    "timeframe",
                }:
                    raise _CustomError("Expected one indicator definition")
            elif path.suffix.lower() in (".mq4", ".mq5"):
                labels = re.findall(
                    r'^\s*#property\s+indicator_label(\d+)\s+"([A-Za-z][A-Za-z0-9]*)"',
                    content,
                    re.MULTILINE,
                )
                if not labels:
                    raise _CustomError("No supported indicator output labels found")
                platform = "mt4" if path.suffix.lower() == ".mq4" else "mt5"
                item = {
                    "name": path.stem,
                    "values": [
                        {"name": label, platform: str(int(index) - 1)}
                        for index, label in labels
                    ],
                }
            else:
                raise _CustomError("Recognition supports JSON, MQ4 and MQ5 text files")
            return _data(self.add(**item))

        return self._run("recognize_from_file", action)

    def _import_config(
        self, format_name: str | None, options: dict[str, Any]
    ) -> dict[str, Any]:
        config: dict[str, Any] = {}
        if format_name is not None:
            rows = _read(self.gateway, _FORMATS, {"name": _name(format_name)})
            if not rows:
                raise _CustomError("Import format not found", ErrorCode.NOT_FOUND)
            config = json.loads(rows[0]["config_json"])
        return _format(config | options)

    @staticmethod
    def _parse(
        content: str,
        config: dict[str, Any],
        outputs: builtins.list[str],
        context: Any = None,
    ) -> dict[str, Any]:
        columns = config["columns"]
        if set(columns) - {"date", "time", "ignore", *outputs} or set(outputs) != set(
            columns
        ) - {"date", "time", "ignore"}:
            raise _CustomError("Map each indicator output exactly once")
        reader = csv.reader(
            io.StringIO(content), delimiter=config["separator"], strict=True
        )
        records: dict[str, dict[str, Any]] = {}
        errors: builtins.list[dict[str, Any]] = []
        skipped = 0
        for number, raw in enumerate(reader, 1):
            if context is not None:
                context.wait_if_paused()
            if number <= config["skip_rows"] or not raw:
                continue
            if number > _MAX_ROWS:
                raise _CustomError("Import exceeds one million lines")
            try:
                timestamp, values = parse_csv_row(raw, config, records)
                records[timestamp] = {
                    "timestamp": timestamp,
                    "values_json": json.dumps(values, allow_nan=False),
                }
            except (ValueError, OverflowError) as error:
                if config["error_handling"] == "abort":
                    raise _CustomError(f"CSV line {number}: {error}") from error
                skipped += 1
                if len(errors) < _MAX_ERRORS:
                    errors.append({"line": number, "message": str(error)})
        if not records:
            raise _CustomError("No valid observations found")
        return {
            "records": sorted(records.values(), key=lambda row: row["timestamp"]),
            "skipped_rows": skipped,
            "errors": errors,
        }

    def import_preview(
        self,
        name: str,
        file_path: str | Path,
        *,
        format_name: str | None = None,
        limit: int = 20,
        **options: Any,
    ) -> dict[str, Any]:
        """Validate a file and return sample observations without writing values."""

        def action() -> Any:
            if (
                isinstance(limit, bool)
                or not isinstance(limit, int)
                or not 1 <= limit <= _BATCH
            ):
                raise _CustomError("Preview limit must be 1-1000")
            row = self._lookup(self.gateway, name)
            config = self._import_config(format_name, options)
            parsed = self._parse(
                _text(file_path),
                config,
                [item["name"] for item in json.loads(row["values_json"])],
            )
            return {
                "records": [
                    {
                        "timestamp": item["timestamp"],
                        "values": json.loads(item["values_json"]),
                    }
                    for item in parsed["records"][:limit]
                ],
                "total_records": len(parsed["records"]),
                "skipped_rows": parsed["skipped_rows"],
                "errors": parsed["errors"],
                "format": config,
            }

        return self._run("import_preview", action)

    def _write_values(
        self,
        tx: HostPersistence,
        definition: dict[str, Any],
        records: builtins.list[dict[str, Any]],
        replace: bool,
        context: Any = None,
    ) -> None:
        if replace:
            self._clear_values(tx, definition["id"])
        existing = {
            row["timestamp"]
            for row in _read(tx, _OBSERVATIONS, {"indicator_id": definition["id"]})
        }
        additions = []
        for record in records:
            if context is not None:
                context.raise_if_cancelled()
            row = {"indicator_id": definition["id"], **record}
            if row["timestamp"] in existing:
                _data(
                    tx.update_record(
                        _OBSERVATIONS,
                        {"values_json": row["values_json"]},
                        filters={
                            "indicator_id": definition["id"],
                            "timestamp": row["timestamp"],
                        },
                    )
                )
            else:
                additions.append(row)
        for start in range(0, len(additions), _BATCH):
            if context is not None:
                context.raise_if_cancelled()
            _data(tx.create_records(_OBSERVATIONS, additions[start : start + _BATCH]))
        _data(
            tx.update_record(
                _DEFINITIONS,
                {"updated_at": datetime.now(UTC).isoformat()},
                filters={"id": definition["id"]},
            )
        )

    def import_data(
        self,
        name: str,
        file_path: str | Path,
        *,
        format_name: str | None = None,
        replace: bool = False,
        **options: Any,
    ) -> dict[str, Any]:
        """Validate then merge/replace values atomically, optionally as a host job."""

        def action() -> Any:
            if not isinstance(replace, bool):
                raise _CustomError("replace must be boolean")
            row = self._lookup(self.gateway, name)
            config = self._import_config(format_name, options)
            content = _text(file_path)
            if self.jobs is not None:
                return self.jobs.submit_job(
                    self._import_job,
                    row,
                    content,
                    config,
                    replace,
                    owner="data-manager",
                    kind="custom.import",
                    executor_kind="thread",
                    pass_context=True,
                )
            return self._import_values(row, content, config, replace)

        return self._run("import_data", action)

    def _import_values(
        self,
        definition: dict[str, Any],
        content: str,
        config: dict[str, Any],
        replace: bool,
        context: Any = None,
    ) -> dict[str, Any]:
        parsed = self._parse(
            content,
            config,
            [item["name"] for item in json.loads(definition["values_json"])],
            context,
        )
        if context is not None:
            context.wait_if_paused()
            context.report_progress(90, "Committing validated observations")
        with self.gateway.transaction() as tx:
            current = self._lookup(tx, definition["name"])
            if any(
                current[key] != definition[key]
                for key in ("id", "values_json", "data_type", "timeframe")
            ):
                raise _CustomError(
                    "Indicator changed while import was preparing", ErrorCode.CONFLICT
                )
            self._write_values(tx, current, parsed["records"], replace, context)
            if context is not None:
                context.raise_if_cancelled()
        return {
            "name": definition["name"],
            "imported_count": len(parsed["records"]),
            "skipped_rows": parsed["skipped_rows"],
            "errors": parsed["errors"],
        }

    def _import_job(
        self,
        context: JobContext,
        definition: dict[str, Any],
        content: str,
        config: dict[str, Any],
        replace: bool,
    ) -> dict[str, Any]:
        task_id = context.job_id
        if self.logs is not None:
            self.logs.record_progress(
                task_id, progress=0, message=f"Importing {definition['name']}"
            )
        try:
            result = self._import_values(definition, content, config, replace, context)
        except Exception:
            if self.logs is not None:
                self.logs.record_progress(
                    task_id,
                    progress=-1,
                    message=f"Import ended for {definition['name']}",
                    level="error",
                )
            raise
        context.report_progress(100, "Import completed")
        if self.logs is not None:
            self.logs.record_progress(
                task_id, progress=100, message=f"Imported {definition['name']}"
            )
        return result

    def import_action(self, job_id: str, action: str) -> dict[str, Any]:
        """Pause, resume or stop only custom.import jobs owned by this manager."""

        def execute() -> Any:
            if self.jobs is None:
                raise _CustomError(
                    "No import job manager is configured", ErrorCode.UNAVAILABLE
                )
            job = self.jobs.get_job(job_id)
            if (
                job is None
                or job.kind != "custom.import"
                or job.owner != "data-manager"
            ):
                raise _CustomError("Custom import job not found", ErrorCode.NOT_FOUND)
            handlers = {
                "pause": self.jobs.pause_job,
                "resume": self.jobs.resume_job,
                "stop": self.jobs.cancel_job,
            }
            if action not in handlers:
                raise _CustomError("Import action must be pause, resume or stop")
            if not handlers[action](job_id):
                raise _CustomError(
                    "Import cannot perform that action", ErrorCode.CONFLICT
                )
            job = self.jobs.get_job(job_id)
            if job is None:
                raise _CustomError("Import job not found", ErrorCode.NOT_FOUND)
            return job.to_dict()

        return self._run("import_action", execute)

    def export_values(self, name: str, csv_path: str | Path) -> dict[str, Any]:
        """Atomically export dated numeric values as a UTF-8 CSV with header."""

        def action() -> Any:
            with self.gateway.transaction() as tx:
                definition = self._lookup(tx, name)
                rows = sorted(
                    _read(tx, _OBSERVATIONS, {"indicator_id": definition["id"]}),
                    key=lambda row: row["timestamp"],
                )
            columns = [item["name"] for item in json.loads(definition["values_json"])]
            stream = io.StringIO(newline="")
            writer = csv.writer(stream)
            writer.writerow(["date", *columns])
            for row in rows:
                values = json.loads(row["values_json"])
                writer.writerow(
                    [row["timestamp"], *(values[column] for column in columns)]
                )
            _atomic_text(csv_path, stream.getvalue())
            return {"path": str(csv_path), "count": len(rows)}

        return self._run("export_values", action)

    def import_get_info(self) -> dict[str, Any]:
        """Return reusable formats and supported import controls."""
        return self._run(
            "import_get_info",
            lambda: {
                "formats": [
                    {"name": row["name"], **json.loads(row["config_json"])}
                    for row in _read(self.gateway, _FORMATS)
                ],
                "separators": [",", ";", "\t", "|"],
                "date_formats": ["%Y-%m-%d", "%d.%m.%Y", "%Y-%m-%d %H:%M:%S"],
                "error_handling": ["abort", "skip"],
                "column_types": ["date", "ignore", "output name"],
                "encoding": "utf-8-sig",
            },
        )

    def _save_format(
        self, name: str, config: Mapping[str, Any], *, update: bool
    ) -> dict[str, Any]:
        def action() -> Any:
            target, normalized = _name(name), _format(config)
            with self.gateway.transaction() as tx:
                existing = _read(tx, _FORMATS, {"name": target})
                if bool(existing) != update:
                    raise _CustomError(
                        "Import format already exists"
                        if existing
                        else "Import format not found",
                        ErrorCode.CONFLICT if existing else ErrorCode.NOT_FOUND,
                    )
                if update:
                    _data(
                        tx.update_record(
                            _FORMATS,
                            {"config_json": json.dumps(normalized)},
                            filters={"name": target},
                        )
                    )
                else:
                    _data(
                        tx.create_records(
                            _FORMATS,
                            {"name": target, "config_json": json.dumps(normalized)},
                        )
                    )
            return {"name": target, **normalized}

        return self._run(
            "edit_import_format" if update else "add_import_format", action
        )

    def add_import_format(self, name: str, config: Mapping[str, Any]) -> dict[str, Any]:
        """Create a validated reusable import preset."""
        return self._save_format(name, config, update=False)

    def edit_import_format(
        self, name: str, config: Mapping[str, Any]
    ) -> dict[str, Any]:
        """Replace an existing import preset with validated settings."""
        return self._save_format(name, config, update=True)

    def delete_import_format(self, name: str) -> dict[str, Any]:
        """Delete an existing import preset without affecting imported values."""
        return self._run(
            "delete_import_format",
            lambda: _data(
                self.gateway.delete_record(_FORMATS, filters={"name": _name(name)})
            ),
        )

    def update_cot(
        self,
        *,
        years: Sequence[int] | None = None,
        fetcher: Callable[[int], str] | None = None,
    ) -> dict[str, Any]:
        """Merge CFTC legacy futures-only annual reports, atomically across years.

        Defaults to the current year. The injectable fetcher returns annual CSV
        text. Names use stable CFTC contract codes; five outputs track commercial
        and non-commercial long/short positions and total open interest.
        """

        def action() -> Any:
            selected = [datetime.now(UTC).year] if years is None else list(years)
            if not selected or any(
                isinstance(year, bool)
                or not isinstance(year, int)
                or not _FIRST_COT_YEAR <= year <= datetime.now(UTC).year
                for year in selected
            ):
                raise _CustomError(
                    "COT years must be between 1986 and the current year"
                )
            grouped = _get_parse_cot_reports()(selected, fetcher)
            with self.gateway.transaction() as tx:
                for name, records in grouped.items():
                    existing = _read(tx, _DEFINITIONS, {"name": name})
                    definition = self._definition(
                        name, [{"name": key} for key in _COT_COLUMNS], "cot", "W1", True
                    )
                    if existing:
                        if (
                            not existing[0]["system"]
                            or existing[0]["values_json"] != definition["values_json"]
                        ):
                            raise _CustomError(
                                "COT indicator conflicts with existing definition",
                                ErrorCode.CONFLICT,
                            )
                        definition = existing[0]
                    else:
                        _data(tx.create_records(_DEFINITIONS, definition))
                    self._write_values(tx, definition, list(records.values()), False)
            return {
                "updated_count": len(grouped),
                "records": sum(len(records) for records in grouped.values()),
                "years": selected,
            }

        return self._run("update_cot", action)
