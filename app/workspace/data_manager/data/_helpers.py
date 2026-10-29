"""Helper constants, bounds validation, and shared gateway for Data service."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from app.core.host.logging import get_logger
from app.core.host.persistence import HostPersistence

logger = get_logger(__name__)
persistence = HostPersistence()

OVERVIEW_FR = "FR-DATAMGR-DATA-OVERVIEW"
DATASETS_CATALOG_FR = "FR-DATAMGR-DATA-CATALOG"

_MAX_CHART_ROWS = 10000


def _chart_bounds(limit: int, offset: int) -> None:
    if isinstance(limit, bool) or not 1 <= limit <= _MAX_CHART_ROWS or offset < 0:
        raise ValueError("Invalid chart pagination")


__all__ = [
    "DATASETS_CATALOG_FR",
    "OVERVIEW_FR",
    "_MAX_CHART_ROWS",
    "_chart_bounds",
    "logger",
    "persistence",
]


def validate_dataset_updates(values: Mapping[str, Any]) -> dict[str, Any]:
    """Build a canonical empty catalog entry from explicit registration values."""
    import json
    import math
    from datetime import UTC, datetime
    from pathlib import Path

    from app.include.market_storage import price_columns, safe_component

    from .storage import dataset_root

    source = safe_component(str(values.get("source") or "files").lower())
    symbol = safe_component(str(values.get("symbol") or "").strip())
    timeframe = str(values.get("timeframe") or "M1").upper()
    price_columns(timeframe)
    step = float(values.get("tick_size") or 0.00001)
    if not math.isfinite(step) or step <= 0:
        raise ValueError("Choose a positive price storage unit")
    now = datetime.now(UTC).isoformat()
    metadata = {
        key: values[key]
        for key in ("exchange", "expiry", "contract_code")
        if values.get(key)
    }
    if metadata.get("expiry"):
        datetime.fromisoformat(metadata["expiry"])
    return {
        "id": f"{source}:{symbol}:{timeframe}",
        "source": source,
        "symbol": symbol,
        "underlying": str(values.get("underlying") or symbol),
        "timeframe": timeframe,
        "broker": str(values.get("broker") or "SQ default"),
        "timezone": "UTC",
        "category": str(values.get("category") or "Forex"),
        "date_from": "",
        "date_to": "",
        "bars": 0,
        "created_at": now,
        "updated_at": now,
        "path": str(
            dataset_root(
                Path(values.get("market_root") or "data/market") / source,
                symbol,
                timeframe,
            )
        ),
        "data_kind": "ticks" if timeframe == "TICK" else "bars",
        "schema_version": 2,
        "symbol_definition_id": values.get("symbol_definition_id"),
        "session_id": values.get("session_id"),
        "lineage_json": json.dumps({"tick_size": step, "partitions": [], **metadata}),
    }


def resolve_dataset_links(gateway: Any, values: Mapping[str, Any]) -> None:
    """Validate catalog references and presentation metadata."""
    from zoneinfo import ZoneInfo

    from .storage import require_data

    for field, table in (
        ("symbol_definition_id", "datamgr_symbols"),
        ("session_id", "datamgr_sessions"),
    ):
        identifier = values.get(field)
        if identifier is None:
            continue
        if type(identifier) is not int or identifier < 1:
            raise ValueError(f"Invalid {field}")
        if not require_data(
            gateway.read_records(table, filters={"id": identifier}, limit=1)
        )["records"]:
            raise ValueError(f"Unknown {field}")
    if "timezone" in values:
        ZoneInfo(values["timezone"])
    for field in ("broker", "category"):
        if field in values and (
            not isinstance(values[field], str) or not values[field].strip()
        ):
            raise ValueError(f"Invalid {field}")
