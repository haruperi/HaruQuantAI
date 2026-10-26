"""Data Manager broker profiles catalog service.

Description:
    Provides broker profiles, connectivity metadata, timezones, and postfixes
    for the Data Manager workspace, reading catalog entries from the
    authoritative SQLite database (datamgr_broker table).

Purpose:
    FEAT-DATAMGR-BROKERS: Data Manager broker profiles catalog service.

Key Capabilities:
    - Broker catalog listing, creation, bulk edits/deletes, and JSON import/export.

Python API Usage:
    ```python
    from app.workspace.data_manager.brokers import Brokers

    brokers_svc = Brokers()
    brokers = brokers_svc.list()
    created = brokers_svc.add("Example", server_timezone="UTC")
    edited = brokers_svc.edit("Example", enabled=False)
    saved = brokers_svc.save("brokers.json")
    deleted = brokers_svc.delete("Example")
    loaded = brokers_svc.load("brokers.json")
    ```

CLI Usage:
    ```bash
    uv run python -m app.cli data-manager broker list
    uv run python -m app.cli data-manager broker add --name Demo --mt-use
    uv run python -m app.cli data-manager broker edit Demo --no-enabled
    uv run python -m app.cli data-manager broker save brokers.json
    uv run python -m app.cli data-manager broker delete Demo
    uv run python -m app.cli data-manager broker load brokers.json
    ```
"""

from __future__ import annotations

import json
import tempfile
import time
from collections import defaultdict
from collections.abc import Callable, Mapping, Sequence
from contextlib import AbstractContextManager, nullcontext
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.host.logging import get_logger
from app.host.persistence import HostPersistence
from app.host.response import (
    ErrorCode,
    ResponseMetadata,
    StandardError,
    StandardResponse,
)

__all__ = [
    "BrokerInfo",
    "Brokers",
]

logger = get_logger(__name__)
persistence = HostPersistence()

BROKERS_CATALOG_FR = "FR-DATAMGR-BROKERS-CATALOG"


def _parse_json_dict(val: Any) -> dict[str, Any]:
    """Parse JSON string into dictionary or return empty dict."""
    if isinstance(val, dict):
        return cast("dict[str, Any]", val)
    if isinstance(val, str) and val.startswith(("{", "[")):
        try:
            parsed = json.loads(val)
            if isinstance(parsed, dict):
                return cast("dict[str, Any]", parsed)
        except json.JSONDecodeError, TypeError:
            return {}
    return {}


@dataclass(slots=True)
class BrokerInfo:
    """Broker profile catalog record definition."""

    id: int = 0
    name: str = ""
    is_system: bool = False
    description: str = ""
    stockpicker_use: bool = False
    mt_use: bool = False
    server_timezone: str = "UTC"
    postfix: str = ""
    enabled: bool = True
    created_at_utc: str = ""
    updated_at_utc: str = ""
    clock_policy: dict[str, Any] = field(default_factory=dict[str, Any])
    clock_policy_revision: int = 0
    customized_stocks: int = 0
    customized_instruments: int = 0
    customized_sessions: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Serialize BrokerInfo to a dictionary."""
        return asdict(self)

    @classmethod
    def from_row(
        cls,
        row: Mapping[str, Any],
        *,
        customized_stocks: int | None = None,
        customized_instruments: int | None = None,
        customized_sessions: int | None = None,
    ) -> BrokerInfo:
        """Construct BrokerInfo from a database row."""
        c_stocks = (
            customized_stocks
            if customized_stocks is not None
            else int(
                row.get("customized_stocks")
                or row.get("stocks_count")
                or len(row.get("stocks", []))
                or 0
            )
        )
        c_insts = (
            customized_instruments
            if customized_instruments is not None
            else int(
                row.get("customized_instruments") or row.get("total_instruments") or 0
            )
        )
        c_sess = (
            customized_sessions
            if customized_sessions is not None
            else int(row.get("customized_sessions") or row.get("total_sessions") or 0)
        )
        return cls(
            id=int(row.get("id", 0)),
            name=str(row.get("name", "")),
            is_system=bool(row.get("is_system", 0)),
            description=str(row.get("description", "")),
            stockpicker_use=bool(row.get("stockpicker_use", 0)),
            mt_use=bool(row.get("mt_use", 0)),
            server_timezone=str(row.get("server_timezone", "UTC")),
            postfix=str(row.get("postfix", "")),
            enabled=bool(row.get("enabled", 1)),
            created_at_utc=str(row.get("created_at_utc", "")),
            updated_at_utc=str(row.get("updated_at_utc", "")),
            clock_policy=_parse_json_dict(row.get("clock_policy_json", "{}")),
            clock_policy_revision=int(row.get("clock_policy_revision", 0)),
            customized_stocks=c_stocks,
            customized_instruments=c_insts,
            customized_sessions=c_sess,
        )


class _BrokerError(ValueError):
    def __init__(self, message: str, code: ErrorCode = ErrorCode.VALIDATION) -> None:
        super().__init__(message)
        self.code = code


def _error_code(error: Exception) -> ErrorCode:
    if isinstance(error, _BrokerError):
        return error.code
    return ErrorCode.INTERNAL


def _records(response: dict[str, Any]) -> list[dict[str, Any]]:
    if not response["success"]:
        error: dict[str, Any] = response.get("error") or {}
        raise _BrokerError(
            response.get("message") or "Broker storage failed",
            ErrorCode(error.get("code", "internal")),
        )
    return cast("list[dict[str, Any]]", response["data"]["records"])


def _names(names: str | Sequence[str]) -> list[str]:
    values: list[object] = [names] if isinstance(names, str) else list(names)
    if not values:
        raise _BrokerError("At least one non-empty broker name is required")
    normalized: list[str] = []
    for value in values:
        if not isinstance(value, str) or not value.strip():
            raise _BrokerError("At least one non-empty broker name is required")
        normalized.append(value.strip())
    return list(dict.fromkeys(normalized))


_FIELDS = {
    "name",
    "description",
    "is_system",
    "stockpicker_use",
    "mt_use",
    "server_timezone",
    "postfix",
    "enabled",
    "clock_policy",
    "clock_policy_revision",
}


def _policy_json(policy: Any) -> str:
    if not isinstance(policy, dict):
        raise _BrokerError("clock_policy must be an object")
    try:
        return json.dumps(policy, allow_nan=False)
    except (TypeError, ValueError) as error:
        raise _BrokerError("clock_policy must contain valid JSON values") from error


def _row(values: Mapping[str, Any]) -> dict[str, Any]:
    unknown = values.keys() - _FIELDS
    if unknown:
        raise _BrokerError(f"Unknown broker fields: {', '.join(sorted(unknown))}")
    data = dict(values)
    for key, default in (
        ("name", ""),
        ("description", ""),
        ("server_timezone", "UTC"),
        ("postfix", ""),
    ):
        value = data.get(key, default)
        if not isinstance(value, str):
            raise _BrokerError(f"{key} must be a string")
        data[key] = value.strip() if key in {"name", "server_timezone"} else value
    if not data["name"]:
        raise _BrokerError("Broker name is required")
    try:
        if data["server_timezone"] != "EETUS":
            ZoneInfo(data["server_timezone"])
    except (ZoneInfoNotFoundError, ValueError) as error:
        raise _BrokerError("Unknown broker timezone") from error
    for key in ("is_system", "stockpicker_use", "mt_use", "enabled"):
        value = data.get(key, key == "enabled")
        if not isinstance(value, bool):
            raise _BrokerError(f"{key} must be a boolean")
        data[key] = int(value)
    revision = data.get("clock_policy_revision", 0)
    if isinstance(revision, bool) or not isinstance(revision, int) or revision < 0:
        raise _BrokerError("clock_policy_revision must be a non-negative integer")
    data["clock_policy_revision"] = revision
    data["clock_policy_json"] = _policy_json(data.pop("clock_policy", {}))
    return data


def _editable(row: Mapping[str, Any]) -> dict[str, Any]:
    values = BrokerInfo.from_row(row).to_dict()
    return {key: values[key] for key in _FIELDS}


def _lookup(gateway: HostPersistence, name: str) -> dict[str, Any]:
    rows = _records(
        gateway.read_records("datamgr_broker", filters={"name": name}, limit=1)
    )
    if not rows:
        raise _BrokerError(f"Broker '{name}' not found", ErrorCode.NOT_FOUND)
    return rows[0]


class Brokers:
    """Broker catalog with atomic mutations and JSON import/export."""

    def __init__(
        self,
        gateway: HostPersistence | None = None,
        *,
        manage_transactions: bool = True,
    ) -> None:
        """Use a gateway; disable transaction ownership only within a caller's scope."""
        self.gateway = gateway if gateway is not None else persistence
        self.manage_transactions = manage_transactions

    def _transaction(self) -> AbstractContextManager[HostPersistence]:
        return (
            self.gateway.transaction()
            if self.manage_transactions
            else nullcontext(self.gateway)
        )

    def _read_brokers(
        self, gateway: HostPersistence | None = None
    ) -> list[dict[str, Any]]:
        """Read all broker records from datamgr_broker table."""
        gateway = gateway if gateway is not None else self.gateway
        rows: list[dict[str, Any]] = []
        offset: int | None = 0
        while offset is not None:
            response = gateway.read_records("datamgr_broker", limit=1000, offset=offset)
            if not response["success"]:
                err: dict[str, Any] = response.get("error") or {}
                msg = (
                    err.get("message")
                    or response.get("message")
                    or "Database read failure"
                )
                raise RuntimeError(msg)
            data: dict[str, Any] = response.get("data") or {}
            page_records: list[dict[str, Any]] = data.get("records") or []
            rows.extend(page_records)
            pagination: dict[str, Any] = data.get("pagination") or {}
            offset = pagination.get("next_offset")
        return rows

    def _read_broker_stocks_counts(self) -> dict[int, int]:
        """Read count of customized stocks per broker from datamgr_broker_stock."""
        counts: dict[int, int] = defaultdict(int)
        offset: int | None = 0
        while offset is not None:
            response = self.gateway.read_records(
                "datamgr_broker_stock", limit=1000, offset=offset
            )
            if not response["success"]:
                break
            data: dict[str, Any] = response.get("data") or {}
            page_records: list[dict[str, Any]] = data.get("records") or []
            for rec in page_records:
                b_id = int(rec.get("BROKER_ID") or rec.get("broker_id") or 0)
                if b_id > 0:
                    counts[b_id] += 1
            pagination: dict[str, Any] = data.get("pagination") or {}
            offset = pagination.get("next_offset")
        return counts

    def _read_broker_instruments_counts(self) -> dict[int, int]:
        """Read count of customized instruments per broker from datamgr_symbols."""
        counts: dict[int, int] = defaultdict(int)
        offset: int | None = 0
        while offset is not None:
            response = self.gateway.read_records(
                "datamgr_symbols", limit=1000, offset=offset
            )
            if not response["success"]:
                break
            data: dict[str, Any] = response.get("data") or {}
            page_records: list[dict[str, Any]] = data.get("records") or []
            for rec in page_records:
                b_id = int(rec.get("broker_id") or rec.get("BROKER_ID") or 0)
                if b_id > 0:
                    counts[b_id] += 1
            pagination: dict[str, Any] = data.get("pagination") or {}
            offset = pagination.get("next_offset")
        return counts

    def _read_broker_sessions_counts(self) -> dict[int, int]:
        """Read count of customized sessions per broker from datamgr_sessions."""
        counts: dict[int, int] = defaultdict(int)
        offset: int | None = 0
        while offset is not None:
            response = self.gateway.read_records(
                "datamgr_sessions", limit=1000, offset=offset
            )
            if not response["success"]:
                break
            data: dict[str, Any] = response.get("data") or {}
            page_records: list[dict[str, Any]] = data.get("records") or []
            for rec in page_records:
                b_id = int(rec.get("broker_id") or rec.get("BROKER_ID") or 0)
                if b_id > 0:
                    counts[b_id] += 1
            pagination: dict[str, Any] = data.get("pagination") or {}
            offset = pagination.get("next_offset")
        return counts

    def _run(self, operation: str, action: Callable[[], Any]) -> dict[str, Any]:
        start = time.perf_counter()
        try:
            data = action()
            return StandardResponse.success(
                message=f"Completed brokers.{operation}",
                metadata=ResponseMetadata(
                    operation=f"brokers.{operation}",
                    duration_ms=(time.perf_counter() - start) * 1000,
                ),
                data=data,
            )
        except (RuntimeError, ValueError, TypeError, KeyError, OSError) as error:
            return StandardResponse.failure(
                message=str(error) or "Broker operation failed",
                metadata=ResponseMetadata(
                    operation=f"brokers.{operation}",
                    duration_ms=(time.perf_counter() - start) * 1000,
                ),
                error=StandardError(
                    code=_error_code(error),
                    message=str(error) or "Broker operation failed",
                ),
            )

    def add(self, name: str = "", **kwargs: Any) -> dict[str, Any]:
        """Create a named broker with connectivity and clock metadata."""

        def action() -> BrokerInfo:
            row = _row({"name": name, **kwargs})
            now = datetime.now(UTC).isoformat()
            row.update(created_at_utc=now, updated_at_utc=now)
            records = _records(self.gateway.create_records("datamgr_broker", row))
            return BrokerInfo.from_row(records[0])

        return self._run("add", action)

    def edit(
        self,
        brokers: str | Sequence[str],
        updates: Mapping[str, Any] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Atomically edit brokers; name changes require one target."""

        def action() -> list[BrokerInfo]:
            names = _names(brokers)
            changes = {**(updates or {}), **kwargs}
            if not changes:
                raise _BrokerError("At least one field to edit is required")
            if "name" in changes and len(names) != 1:
                raise _BrokerError("Rename requires exactly one broker")
            result: list[BrokerInfo] = []
            with self._transaction() as tx:
                for name in names:
                    row = _row({**_editable(_lookup(tx, name)), **changes})
                    row["updated_at_utc"] = datetime.now(UTC).isoformat()
                    records = _records(
                        tx.update_record("datamgr_broker", row, filters={"name": name})
                    )
                    result.append(BrokerInfo.from_row(records[0]))
            return result

        return self._run("edit", action)

    def delete(self, brokers: str | Sequence[str]) -> dict[str, Any]:
        """Delete one or more named brokers atomically."""

        def action() -> list[BrokerInfo]:
            names = _names(brokers)
            result: list[BrokerInfo] = []
            with self._transaction() as tx:
                for name in names:
                    _lookup(tx, name)
                    records = _records(
                        tx.delete_record("datamgr_broker", filters={"name": name})
                    )
                    result.extend(BrokerInfo.from_row(row) for row in records)
            return result

        return self._run("delete", action)

    def load(self, json_path: str | Path) -> dict[str, Any]:
        """Atomically import a JSON array of brokers, rejecting duplicate names."""

        def action() -> list[BrokerInfo]:
            try:
                data = json.loads(Path(json_path).read_text(encoding="utf-8-sig"))
            except json.JSONDecodeError as error:
                raise _BrokerError("Invalid brokers JSON") from error
            if not isinstance(data, list):
                raise _BrokerError("Brokers JSON must be an array of objects")
            items = cast("list[object]", data)
            rows: list[dict[str, Any]] = []
            for item in items:
                if not isinstance(item, dict):
                    raise _BrokerError("Brokers JSON must be an array of objects")
                source = cast("dict[str, Any]", item)
                # Exported identifiers are local to the source database.
                values = {
                    k: v
                    for k, v in source.items()
                    if k
                    not in {
                        "id",
                        "created_at_utc",
                        "updated_at_utc",
                        "customized_stocks",
                        "customized_instruments",
                        "customized_sessions",
                    }
                }
                row = _row(values)
                now = datetime.now(UTC).isoformat()
                row.update(created_at_utc=now, updated_at_utc=now)
                rows.append(row)
            result: list[BrokerInfo] = []
            with self._transaction() as tx:
                for start in range(0, len(rows), 1000):
                    records = _records(
                        tx.create_records("datamgr_broker", rows[start : start + 1000])
                    )
                    result.extend(BrokerInfo.from_row(row) for row in records)
            return result

        return self._run("load", action)

    def save(self, json_path: str | Path) -> dict[str, Any]:
        """Export all brokers to a UTF-8 JSON array using atomic replacement."""

        def action() -> dict[str, Any]:
            with self._transaction() as tx:
                brokers = self._read_brokers(tx)
            data = [_editable(row) for row in brokers]
            target = Path(json_path)
            temporary = None
            try:
                with tempfile.NamedTemporaryFile(
                    mode="w",
                    encoding="utf-8",
                    dir=target.parent,
                    prefix=f".{target.name}.",
                    suffix=".tmp",
                    delete=False,
                ) as stream:
                    temporary = Path(stream.name)
                    json.dump(
                        data, stream, ensure_ascii=False, indent=2, allow_nan=False
                    )
                    stream.write("\n")
                Path(temporary).replace(target)
            finally:
                if temporary is not None:
                    temporary.unlink(missing_ok=True)
            return {"path": str(target), "count": len(data)}

        return self._run("save", action)

    def list(self) -> dict[str, Any]:
        """Retrieve broker profile items wrapped in StandardResponse."""
        start = time.perf_counter()
        try:
            rows = self._read_brokers()
            stock_counts = self._read_broker_stocks_counts()
            inst_counts = self._read_broker_instruments_counts()
            sess_counts = self._read_broker_sessions_counts()

            brokers = [
                BrokerInfo.from_row(
                    r,
                    customized_stocks=stock_counts.get(int(r.get("id", 0)), 0),
                    customized_instruments=inst_counts.get(int(r.get("id", 0)), 0),
                    customized_sessions=sess_counts.get(int(r.get("id", 0)), 0),
                )
                for r in rows
            ]

            logger.debug(
                "%s: Retrieved %d broker catalog items",
                BROKERS_CATALOG_FR,
                len(brokers),
                extra={"fr_id": BROKERS_CATALOG_FR, "count": len(brokers)},
            )
            return StandardResponse.success(
                message=f"Retrieved {len(brokers)} broker catalog items",
                metadata=ResponseMetadata(
                    operation="brokers.list",
                    duration_ms=(time.perf_counter() - start) * 1000,
                ),
                data=brokers,
            )
        except (RuntimeError, ValueError, TypeError, KeyError, OSError) as error:
            logger.exception("%s: Failed to list brokers", BROKERS_CATALOG_FR)
            return StandardResponse.failure(
                message=str(error) or "Failed to retrieve brokers",
                metadata=ResponseMetadata(
                    operation="brokers.list",
                    duration_ms=(time.perf_counter() - start) * 1000,
                ),
                error=StandardError(
                    code=ErrorCode.INTERNAL,
                    message=str(error) or "Internal error listing brokers",
                ),
            )


if __name__ == "__main__":
    from app.workspace.data_manager.cli import format_broker_table

    brokers_svc = Brokers()
    catalog_response = brokers_svc.list()
    if catalog_response["success"]:
        print(format_broker_table(catalog_response))
    else:
        print(f"Failed: {catalog_response['message']}")
