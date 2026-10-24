"""Data Manager trading sessions catalog service.

Description:
    Provides trading session schedules, regular trading hours, and holiday
    calendars for the Data Manager workspace, reading catalog entries from
    the authoritative SQLite database (datamgr_sessions table).

Purpose:
    FEAT-DATAMGR-SESSIONS: Data Manager trading sessions catalog service.

Key Capabilities:
    - FR-DATAMGR-SESSIONS-CATALOG: Sessions catalog (Sessions.list).

Python API Usage:
    ```python
    from app.workspace.data_manager.sessions import Sessions

    sessions_svc = Sessions()
    sessions = sessions_svc.list()
    ```

CLI Usage:
    ```bash
    uv run python -m app.workspace.data_manager.sessions
    ```
"""

from __future__ import annotations

import time
from typing import Any

from app.host.logging import get_logger
from app.host.persistence import HostPersistence
from app.host.response import (
    ErrorCode,
    ResponseMetadata,
    StandardError,
    StandardResponse,
)
from app.include.contracts import TradingSession

__all__ = [
    "Sessions",
    "TradingSession",
]

logger = get_logger(__name__)
persistence = HostPersistence()

SESSIONS_CATALOG_FR = "FR-DATAMGR-SESSIONS-CATALOG"


class Sessions:
    """Service providing trading session calendar catalog presentation."""

    def _read_sessions(self) -> list[dict[str, Any]]:
        """Read all session catalog items from the datamgr_sessions table."""
        rows: list[dict[str, Any]] = []
        offset: int | None = 0
        while offset is not None:
            response = persistence.read_records(
                "datamgr_sessions", limit=1000, offset=offset
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

    def list(self) -> dict[str, Any]:
        """Retrieve trading session catalog items wrapped in StandardResponse."""
        start = time.perf_counter()
        try:
            rows = self._read_sessions()
            sessions = [TradingSession.from_dict(r) for r in rows]

            logger.debug(
                "%s: Retrieved %d trading session catalog items",
                SESSIONS_CATALOG_FR,
                len(sessions),
                extra={"fr_id": SESSIONS_CATALOG_FR, "count": len(sessions)},
            )
            return StandardResponse.success(
                message=f"Retrieved {len(sessions)} trading session catalog items",
                metadata=ResponseMetadata(
                    operation="sessions.list",
                    duration_ms=(time.perf_counter() - start) * 1000,
                ),
                data=sessions,
            )
        except (RuntimeError, ValueError, TypeError, KeyError, OSError) as error:
            logger.exception("%s: Failed to list sessions", SESSIONS_CATALOG_FR)
            return StandardResponse.failure(
                message=str(error) or "Failed to retrieve sessions",
                metadata=ResponseMetadata(
                    operation="sessions.list",
                    duration_ms=(time.perf_counter() - start) * 1000,
                ),
                error=StandardError(
                    code=ErrorCode.INTERNAL,
                    message=str(error) or "Internal error listing sessions",
                ),
            )


if __name__ == "__main__":
    from app.workspace.data_manager.cli import format_session_table

    sessions_svc = Sessions()
    response = sessions_svc.list()
    if response["success"]:
        print(format_session_table(response))
    else:
        print(f"Failed: {response['message']}")
