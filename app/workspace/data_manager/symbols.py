"""Data Manager symbols catalog service.

Description:
    Provides symbol / instrument definitions and specifications for the Data Manager
    workspace, reading catalog entries from the authoritative SQLite database
    (datamgr_instruments table). Exposes symbol specifications, lot sizes,
    trading hours, swap rates, margin rules, and commissions.

Purpose:
    FEAT-DATAMGR-SYMBOLS: Data Manager symbols catalog service.

Key Capabilities:
    - FR-DATAMGR-SYMBOLS-CATALOG: Symbols catalog (Symbols.list).

Python API Usage:
    ```python
    from app.workspace.data_manager.symbols import Symbols

    symbols_svc = Symbols()
    symbols = symbols_svc.list()
    ```

CLI Usage:
    ```bash
    uv run python -m app.workspace.data_manager.symbols
    ```
"""

from __future__ import annotations

import json
import time
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
    "SymbolInfo",
    "Symbols",
]

logger = get_logger(__name__)
persistence = HostPersistence()

SYMBOLS_CATALOG_FR = "FR-DATAMGR-SYMBOLS-CATALOG"


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
class SymbolInfo:
    """Symbol catalog record definition."""

    id: int = 0
    symbol: str = ""
    connection: str = ""
    broker_id: int = 0
    description: str = ""
    data_type: str = ""
    alias: str = ""
    exchange: str = ""
    country: str = ""
    sector: str = ""
    created_at_utc: str = ""
    updated_at_utc: str = ""
    cot: str | None = None
    swap: dict[str, Any] = field(default_factory=dict)
    margin: dict[str, Any] = field(default_factory=dict)
    volume: dict[str, Any] = field(default_factory=dict)
    spread: dict[str, Any] = field(default_factory=dict)
    trade: dict[str, Any] = field(default_factory=dict)
    price: dict[str, Any] = field(default_factory=dict)
    contract: dict[str, Any] = field(default_factory=dict)
    option: dict[str, Any] = field(default_factory=dict)
    sessions: dict[str, Any] = field(default_factory=dict)
    commissions: dict[str, Any] = field(default_factory=dict)
    order_size: dict[str, Any] = field(default_factory=dict)
    symbol_state: dict[str, Any] = field(default_factory=dict)
    specification_meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize SymbolInfo to a dictionary."""
        return asdict(self)

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> SymbolInfo:
        """Construct SymbolInfo from a database row."""
        return cls(
            id=int(row.get("id", 0)),
            symbol=str(row.get("symbol", "")),
            connection=str(row.get("connection", "")),
            broker_id=int(row.get("broker_id", 0)),
            description=str(row.get("description", "")),
            data_type=str(row.get("data_type", "")),
            alias=str(row.get("alias", "")),
            exchange=str(row.get("exchange", "")),
            country=str(row.get("country", "")),
            sector=str(row.get("sector", "")),
            created_at_utc=str(row.get("created_at_utc", "")),
            updated_at_utc=str(row.get("updated_at_utc", "")),
            cot=str(row["cot"]) if row.get("cot") is not None else None,
            swap=_parse_json_dict(row.get("swap")),
            margin=_parse_json_dict(row.get("margin")),
            volume=_parse_json_dict(row.get("volume")),
            spread=_parse_json_dict(row.get("spread")),
            trade=_parse_json_dict(row.get("trade")),
            price=_parse_json_dict(row.get("price")),
            contract=_parse_json_dict(row.get("contract")),
            option=_parse_json_dict(row.get("option")),
            sessions=_parse_json_dict(row.get("sessions")),
            commissions=_parse_json_dict(row.get("commissions")),
            order_size=_parse_json_dict(row.get("order_size")),
            symbol_state=_parse_json_dict(row.get("symbol_state")),
            specification_meta=_parse_json_dict(row.get("specification_meta")),
        )


class Symbols:
    """Service providing symbols catalog presentation."""

    def _read_symbols(self) -> list[dict[str, Any]]:
        """Read all symbol records from datamgr_instruments table."""
        rows: list[dict[str, Any]] = []
        offset: int | None = 0
        while offset is not None:
            response = persistence.read_records(
                "datamgr_instruments", limit=1000, offset=offset
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
        """Retrieve symbol catalog items wrapped in StandardResponse."""
        start = time.perf_counter()
        try:
            rows = self._read_symbols()
            symbols = [SymbolInfo.from_row(r) for r in rows]

            logger.debug(
                "%s: Retrieved %d symbol catalog items",
                SYMBOLS_CATALOG_FR,
                len(symbols),
                extra={"fr_id": SYMBOLS_CATALOG_FR, "count": len(symbols)},
            )
            return StandardResponse.success(
                message=f"Retrieved {len(symbols)} symbol catalog items",
                metadata=ResponseMetadata(
                    operation="symbols.list",
                    duration_ms=(time.perf_counter() - start) * 1000,
                ),
                data=symbols,
            )
        except (RuntimeError, ValueError, TypeError, KeyError, OSError) as error:
            logger.exception("%s: Failed to list symbols", SYMBOLS_CATALOG_FR)
            return StandardResponse.failure(
                message=str(error) or "Failed to retrieve symbols",
                metadata=ResponseMetadata(
                    operation="symbols.list",
                    duration_ms=(time.perf_counter() - start) * 1000,
                ),
                error=StandardError(
                    code=ErrorCode.INTERNAL,
                    message=str(error) or "Internal error listing symbols",
                ),
            )


if __name__ == "__main__":
    from app.workspace.data_manager.cli import format_symbol_table

    symbols_svc = Symbols()
    response = symbols_svc.list()
    if response["success"]:
        print(format_symbol_table(response))
    else:
        print(f"Failed: {response['message']}")
