"""Data Manager broker profiles catalog service.

Description:
    Provides broker profiles, connectivity metadata, timezones, and postfixes
    for the Data Manager workspace, reading catalog entries from the
    authoritative SQLite database (datamgr_broker table).

Purpose:
    FEAT-DATAMGR-BROKERS: Data Manager broker profiles catalog service.

Key Capabilities:
    - FR-DATAMGR-BROKERS-CATALOG: Brokers catalog (Brokers.list).

Python API Usage:
    ```python
    from app.workspace.data_manager.brokers import Brokers

    brokers_svc = Brokers()
    brokers = brokers_svc.list()
    ```

CLI Usage:
    ```bash
    uv run python -m app.workspace.data_manager.brokers
    ```
"""

from __future__ import annotations

import json
import time
from collections import defaultdict
from collections.abc import Mapping
from dataclasses import asdict, dataclass, field
from typing import Any

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
        return val
    if isinstance(val, str) and val.startswith(("{", "[")):
        try:
            parsed = json.loads(val)
            if isinstance(parsed, dict):
                return parsed
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
    clock_policy: dict[str, Any] = field(default_factory=dict)
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


class Brokers:
    """Service providing broker profile catalog presentation."""

    def _read_brokers(self) -> list[dict[str, Any]]:
        """Read all broker records from datamgr_broker table."""
        rows: list[dict[str, Any]] = []
        offset: int | None = 0
        while offset is not None:
            response = persistence.read_records(
                "datamgr_broker", limit=1000, offset=offset
            )
            if not response["success"]:
                err = response.get("error") or {}
                msg = (
                    err.get("message")
                    or response.get("message")
                    or "Database read failure"
                )
                raise RuntimeError(msg)
            data = response.get("data") or {}
            rows.extend(data.get("records") or [])
            pagination = data.get("pagination") or {}
            offset = pagination.get("next_offset")
        return rows

    def _read_broker_stocks_counts(self) -> dict[int, int]:
        """Read count of customized stocks per broker from datamgr_broker_stock."""
        counts: dict[int, int] = defaultdict(int)
        offset: int | None = 0
        while offset is not None:
            response = persistence.read_records(
                "datamgr_broker_stock", limit=1000, offset=offset
            )
            if not response["success"]:
                break
            data = response.get("data") or {}
            for rec in data.get("records") or []:
                b_id = int(rec.get("BROKER_ID") or rec.get("broker_id") or 0)
                if b_id > 0:
                    counts[b_id] += 1
            pagination = data.get("pagination") or {}
            offset = pagination.get("next_offset")
        return counts

    def _read_broker_instruments_counts(self) -> dict[int, int]:
        """Read count of customized instruments per broker from datamgr_instruments."""
        counts: dict[int, int] = defaultdict(int)
        offset: int | None = 0
        while offset is not None:
            response = persistence.read_records(
                "datamgr_instruments", limit=1000, offset=offset
            )
            if not response["success"]:
                break
            data = response.get("data") or {}
            for rec in data.get("records") or []:
                b_id = int(rec.get("broker_id") or rec.get("BROKER_ID") or 0)
                if b_id > 0:
                    counts[b_id] += 1
            pagination = data.get("pagination") or {}
            offset = pagination.get("next_offset")
        return counts

    def _read_broker_sessions_counts(self) -> dict[int, int]:
        """Read count of customized sessions per broker from datamgr_sessions."""
        counts: dict[int, int] = defaultdict(int)
        offset: int | None = 0
        while offset is not None:
            response = persistence.read_records(
                "datamgr_sessions", limit=1000, offset=offset
            )
            if not response["success"]:
                break
            data = response.get("data") or {}
            for rec in data.get("records") or []:
                b_id = int(rec.get("broker_id") or rec.get("BROKER_ID") or 0)
                if b_id > 0:
                    counts[b_id] += 1
            pagination = data.get("pagination") or {}
            offset = pagination.get("next_offset")
        return counts

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
    response = brokers_svc.list()
    if response["success"]:
        print(format_broker_table(response))
    else:
        print(f"Failed: {response['message']}")
