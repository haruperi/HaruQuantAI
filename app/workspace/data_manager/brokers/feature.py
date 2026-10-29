"""Broker profile catalog core service."""

from __future__ import annotations

import json
import sys
import tempfile
import time
from collections import defaultdict
from collections.abc import Callable, Mapping, Sequence
from contextlib import AbstractContextManager, nullcontext
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

from app.core.host.persistence import HostPersistence
from app.host.response import (
    ErrorCode,
    ResponseMetadata,
    StandardError,
    StandardResponse,
)

from ._helpers import (
    BROKERS_CATALOG_FR,
    BrokerInfo,
    _BrokerError,
    _editable,
    _error_code,
    _lookup,
    _names,
    _records,
    _row,
    logger,
    persistence,
)

__all__ = ["Brokers"]


class Brokers:
    """Broker catalog with atomic mutations and JSON import/export."""

    def __init__(
        self,
        gateway: HostPersistence | None = None,
        *,
        manage_transactions: bool = True,
    ) -> None:
        """Use a gateway; disable transaction ownership only within a caller's scope."""
        pkg = sys.modules.get(__package__ or "")
        gw = getattr(pkg, "persistence", persistence) if pkg else persistence
        self.gateway = gateway if gateway is not None else gw
        self.manage_transactions = manage_transactions
        response = self.gateway.ensure_broker_cost_schema()
        if not response["success"]:
            raise RuntimeError(response["message"])

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
