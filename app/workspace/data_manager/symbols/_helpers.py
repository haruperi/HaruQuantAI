"""Helper utilities, constants, and MT5 synchronization for the symbols catalog."""

from __future__ import annotations

import asyncio
import json
import time
from collections.abc import Mapping, Sequence
from dataclasses import asdict
from datetime import UTC, datetime
from threading import Lock
from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    from .feature import Symbols

from app.core.host.logging import get_logger
from app.host.persistence import HostPersistence, SQLiteValue
from app.host.response import (
    ErrorCode,
    ResponseMetadata,
    StandardError,
    StandardResponse,
)
from app.include.contracts import (
    BridgeError,
    SymbolInfo,
    SymbolMargin,
    SymbolPrice,
    SymbolSessionWindow,
    SymbolSpread,
    SymbolState,
    SymbolSwap,
    SymbolTrade,
    SymbolVolume,
    default_session_windows,
)
from app.workspace.brokers.metatrader import create_mt5_client

logger = get_logger(__name__)
persistence = HostPersistence()

_MT5_UPDATE_LOCK = Lock()

_MT5_SPEC_COLUMNS = (
    "description",
    "exchange",
    "data_type",
    "spread",
    "margin",
    "volume",
    "trade",
    "price",
    "swap",
    "session",
    "state",
)

CSV_COLUMNS: tuple[str, ...] = (
    "id",
    "name",
    "description",
    "exchange",
    "data_type",
    "spread",
    "margin",
    "volume",
    "trade",
    "price",
    "swap",
    "commission",
    "session",
    "state",
    "broker_id",
)
CSV_FIELDNAMES = CSV_COLUMNS

_SHORTCUTS: tuple[tuple[str, str, str, type], ...] = (
    ("default_spread", "spread", "default", float),
    ("pip_size", "price", "tick_size", float),
    ("pip_step", "price", "tick_step", float),
    ("point_value", "price", "contract_size", float),
    ("min_distance", "trade", "min_distance", float),
    ("order_size_multiplier", "volume", "min", float),
    ("order_size_step", "volume", "step", float),
    ("swap_long", "swap", "long", float),
    ("swap_short", "swap", "short", float),
)

__all__ = [
    "CSV_COLUMNS",
    "CSV_FIELDNAMES",
    "_MT5_SPEC_COLUMNS",
    "_MT5_UPDATE_LOCK",
    "_SHORTCUTS",
    "SymbolInfo",
    "SymbolMargin",
    "SymbolPrice",
    "SymbolSessionWindow",
    "SymbolSpread",
    "SymbolState",
    "SymbolSwap",
    "SymbolTrade",
    "SymbolVolume",
    "_apply_field_updates",
    "_apply_shortcuts",
    "_build_price_dict",
    "_build_row_dict",
    "_build_swap_dict",
    "_fail",
    "_mt5_bridge_failure",
    "_mt5_fields",
    "_mt5_import_all",
    "_mt5_persist",
    "_mt5_refresh_or_import",
    "_mt5_require_empty",
    "_mt5_snapshots",
    "_ok",
    "_parse_csv_row",
    "_parse_json_dict",
    "_parse_json_list",
    "_read_symbols",
    "_row_to_csv_dict",
    "_row_to_symbol_info",
    "_to_sym_list",
    "_update_direct_columns",
    "logger",
    "persistence",
]


def _fail(
    op: str,
    start: float,
    message: str,
    code: ErrorCode,
    details: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a StandardResponse failure dictionary."""
    err = (
        StandardError(code=code, message=message, details=details)
        if details is not None
        else StandardError(code=code, message=message)
    )
    return StandardResponse.failure(
        message=message,
        metadata=ResponseMetadata(
            operation=op, duration_ms=(time.perf_counter() - start) * 1000
        ),
        error=err,
    )


def _ok(
    op: str,
    start: float,
    message: str,
    data: Any = None,
    side_effects: tuple[str, ...] = (),
) -> dict[str, Any]:
    """Build a StandardResponse success dictionary."""
    return StandardResponse.success(
        message=message,
        metadata=ResponseMetadata(
            operation=op,
            duration_ms=(time.perf_counter() - start) * 1000,
            side_effects=side_effects,
        ),
        data=data,
    )


def _to_sym_list(symbols: str | Sequence[str]) -> list[str]:
    """Normalize symbol string or sequence to a stripped list."""
    if isinstance(symbols, str):
        return [symbols.strip()] if symbols.strip() else []
    return [s.strip() for s in symbols if s.strip()]


def _parse_json_dict(val: Any) -> dict[str, Any]:
    """Parse JSON string into dictionary or return empty dict."""
    if isinstance(val, dict):
        return val
    if isinstance(val, str) and val.strip().startswith(("{", "[")):
        try:
            parsed = json.loads(val)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError, TypeError:
            return {}
    return {}


def _parse_json_list(val: Any) -> list[dict[str, Any]]:
    """Parse JSON string into list of dicts."""
    if isinstance(val, list):
        return val
    if isinstance(val, str) and val.strip().startswith("["):
        try:
            parsed = json.loads(val)
            if isinstance(parsed, list):
                return parsed
        except json.JSONDecodeError, TypeError:
            return []
    return []


def _update_direct_columns(fields: Mapping[str, Any], updates: dict[str, Any]) -> None:
    for col in ("name", "description", "exchange", "data_type", "broker_id"):
        if col in fields:
            val = fields[col]
            updates[col] = val
    if "commission" in fields or "commission_value" in fields:
        raw_comm = fields.get("commission", fields.get("commission_value"))
        updates["commission"] = float(raw_comm or 0.0)


def _apply_shortcuts(
    comps: dict[str, dict[str, Any]], fields: Mapping[str, Any]
) -> None:
    """Keep scalar service edits and optional browser settings consistent."""
    for field_key, comp, prop, conv in _SHORTCUTS:
        if field_key in fields:
            comps[comp][prop] = conv(fields[field_key])
    for key in ("point_value", "pip_size"):
        if key in fields:
            comps["price"][key] = float(fields[key])
    if ("commission" in fields or "commission_value" in fields) and not (
        isinstance(fields.get("trade"), Mapping)
        and "commission_settings" in fields["trade"]
    ):
        comps["trade"]["commission_settings"] = None
    if any(
        key in fields
        for key in (
            "swap_long",
            "swap_short",
            "triple_swap_on",
            "swap_type",
            "swap_mode",
        )
    ):
        comps["swap"]["settings"] = None


def _apply_field_updates(
    existing: Mapping[str, Any], fields: Mapping[str, Any], now_utc: str
) -> dict[str, Any]:
    """Calculate database column updates for an instrument record."""
    updates: dict[str, Any] = {"updated_at_utc": now_utc}
    _update_direct_columns(fields, updates)
    comps = {
        col: _parse_json_dict(existing.get(col))
        for col in ("spread", "margin", "volume", "trade", "price", "swap", "state")
    }
    for comp_name, comp_d in comps.items():
        val = fields.get(comp_name)
        if isinstance(val, Mapping):
            comp_d.update(val)
    _apply_shortcuts(comps, fields)
    if "triple_swap_on" in fields:
        comps["swap"]["rollover3days"] = str(fields["triple_swap_on"]).capitalize()
    if "swap_type" in fields or "swap_mode" in fields:
        comps["swap"]["mode"] = str(fields.get("swap_mode") or fields.get("swap_type"))
    for col, d in comps.items():
        updates[col] = json.dumps(d)
    if "session" in fields:
        sess = fields["session"]
        updates["session"] = (
            json.dumps(sess) if isinstance(sess, (list, tuple)) else str(sess)
        )
    return updates


def _row_to_csv_dict(r: Mapping[str, Any]) -> dict[str, Any]:
    """Convert an authoritative database record into a CSV row dict."""
    return {
        col: (
            ""
            if r.get(col) is None
            else (
                json.dumps(r[col]) if isinstance(r.get(col), (dict, list)) else r[col]
            )
        )
        for col in CSV_COLUMNS
    }


def _parse_csv_row(row: Mapping[str, str]) -> tuple[str, str, dict[str, Any]]:
    """Extract (name, datasource, add_args) from a CSV record mapping."""
    name = (row.get("name") or row.get("symbol") or "").strip()
    if not name:
        raise ValueError("Missing instrument name in CSV row")
    ds = (row.get("datasource") or "").strip()
    if not ds:
        raw_name, raw_ds = name.rsplit("_", 1) if "_" in name else (name, "SQ default")
    else:
        raw_name, raw_ds = name.removesuffix(f"_{ds}"), ds
    comm_raw = row.get("commission", row.get("commission_value"))
    add_args: dict[str, Any] = {
        "name": raw_name,
        "datasource": raw_ds,
        "data_type": (row.get("data_type", "Forex") or "").strip(),
        "description": (row.get("description") or "").strip(),
        "exchange": (row.get("exchange") or "XCCY").strip(),
        "commission": float(comm_raw)
        if comm_raw is not None and comm_raw != ""
        else 0.0,
        "broker_id": int(float(row.get("broker_id") or 0)),
        "spread": _parse_json_dict(row.get("spread")),
        "margin": _parse_json_dict(row.get("margin")),
        "volume": _parse_json_dict(row.get("volume")),
        "trade": _parse_json_dict(row.get("trade")),
        "price": _parse_json_dict(row.get("price")),
        "swap": _parse_json_dict(row.get("swap")),
        "session": _parse_json_list(row.get("session")),
        "state": _parse_json_dict(row.get("state")),
    }
    return raw_name, raw_ds, add_args


def _read_symbols(gateway: HostPersistence | None = None) -> list[dict[str, Any]]:
    """Read all symbol records from datamgr_symbols table."""
    import sys

    symbols_pkg = sys.modules.get(__package__)

    gw: Any = (
        gateway
        if gateway is not None
        else getattr(symbols_pkg, "persistence", persistence)
    )
    rows: list[dict[str, Any]] = []
    offset: int | None = 0
    while offset is not None:
        response = gw.read_records("datamgr_symbols", limit=1000, offset=offset)
        if not response["success"]:
            err = response.get("error") or {}
            msg = (
                err.get("message") or response.get("message") or "Database read failure"
            )
            raise RuntimeError(msg)
        data = response.get("data") or {}
        rows.extend(data.get("records") or [])
        pagination = data.get("pagination") or {}
        offset = pagination.get("next_offset")
    return rows


def _row_to_symbol_info(r: Mapping[str, Any]) -> SymbolInfo:
    """Convert database row mapping to SymbolInfo dataclass."""
    session_l = _parse_json_list(r.get("session"))
    return SymbolInfo(
        name=str(r.get("name") or ""),
        description=str(r.get("description") or ""),
        exchange=str(r.get("exchange") or "XCCY"),
        data_type=str(r.get("data_type") or ""),
        spread=cast("SymbolSpread", _parse_json_dict(r.get("spread"))),
        margin=cast("SymbolMargin", _parse_json_dict(r.get("margin"))),
        volume=cast("SymbolVolume", _parse_json_dict(r.get("volume"))),
        trade=cast("SymbolTrade", _parse_json_dict(r.get("trade"))),
        price=cast("SymbolPrice", _parse_json_dict(r.get("price"))),
        swap=cast("SymbolSwap", _parse_json_dict(r.get("swap"))),
        commission=float(r.get("commission") or 0.0),
        session=cast(
            "list[SymbolSessionWindow]",
            session_l or default_session_windows(),
        ),
        state=cast("SymbolState", _parse_json_dict(r.get("state"))),
    )


def _build_price_dict(
    price: dict[str, Any] | None,
    pip_size: float | None,
    point_value: float | None,
    pip_step: float | None,
) -> dict[str, Any]:
    d = dict(price or {})
    if point_value is not None:
        d["point_value"] = float(point_value)
    if pip_size is not None:
        d["pip_size"] = float(pip_size)
    d["tick_size"] = (
        float(pip_size) if pip_size is not None else d.get("tick_size", 0.0001)
    )
    d["contract_size"] = (
        float(point_value)
        if point_value is not None
        else d.get("contract_size", 100000.0)
    )
    d["tick_step"] = (
        float(pip_step) if pip_step is not None else d.get("tick_step", 0.00001)
    )
    return d


def _build_swap_dict(
    swap: dict[str, Any] | None,
    swap_long: float | None,
    swap_short: float | None,
    triple_swap_on: str | None,
    swap_type: str | None,
) -> dict[str, Any]:
    d = dict(swap or {})
    if swap_long is not None:
        d["long"] = float(swap_long)
    if swap_short is not None:
        d["short"] = float(swap_short)
    d["rollover3days"] = (
        triple_swap_on.capitalize()
        if triple_swap_on is not None
        else d.get("rollover3days", "Wednesday")
    )
    d["mode"] = swap_type if swap_type is not None else d.get("mode", "Points")
    return d


def _build_row_dict(inst_name: str, now_utc: str, **kwargs: Any) -> dict[str, Any]:
    """Construct full dictionary ready for database insertion."""
    dt = kwargs.get("data_type")
    dt = "Forex" if dt is None else dt
    clean_dt = dt
    spread_d = dict(kwargs.get("spread") or {})
    def_spread = kwargs.get("default_spread")
    if def_spread is not None:
        spread_d["default"] = float(def_spread)
    elif "default" not in spread_d:
        spread_d["default"] = 1.0
    vol_d = dict(kwargs.get("volume") or {})
    vol_min = kwargs.get("order_size_multiplier", kwargs.get("min_volume"))
    if vol_min is not None:
        vol_d["min"] = float(vol_min)
    vol_step = kwargs.get("order_size_step", kwargs.get("lot_step"))
    if vol_step is not None:
        vol_d["step"] = float(vol_step)
    trade_d = dict(kwargs.get("trade") or {})
    if kwargs.get("min_distance") is not None:
        trade_d["min_distance"] = float(kwargs["min_distance"])
    trade_d.setdefault("calculation", clean_dt)
    price_d = _build_price_dict(
        kwargs.get("price"),
        kwargs.get("pip_size"),
        kwargs.get("point_value"),
        kwargs.get("pip_step"),
    )
    swap_d = _build_swap_dict(
        kwargs.get("swap"),
        kwargs.get("swap_long"),
        kwargs.get("swap_short"),
        kwargs.get("triple_swap_on"),
        kwargs.get("swap_type"),
    )
    comm = kwargs.get("commission", kwargs.get("commission_value", 0.0))
    session = kwargs.get("session")
    sess_val = (
        list(session)
        if session is not None
        else [asdict(w) for w in default_session_windows()]
    )
    info = SymbolInfo(
        name=inst_name,
        description=str(kwargs.get("description") or ""),
        exchange=str(kwargs.get("exchange") or "XCCY"),
        data_type=clean_dt,
        spread=cast("SymbolSpread", spread_d),
        margin=cast("SymbolMargin", kwargs.get("margin") or {}),
        volume=cast("SymbolVolume", vol_d),
        trade=cast("SymbolTrade", trade_d),
        price=cast("SymbolPrice", price_d),
        swap=cast("SymbolSwap", swap_d),
        commission=float(comm or 0.0),
        session=cast("list[SymbolSessionWindow]", sess_val),
        state=cast("SymbolState", kwargs.get("state") or {}),
    )
    d = asdict(info)
    row = {
        col: json.dumps(d[col]) if isinstance(d.get(col), (dict, list)) else d.get(col)
        for col in CSV_COLUMNS
        if col not in ("id", "broker_id")
    }
    row["broker_id"] = int(kwargs.get("broker_id") or 0)
    row["created_at_utc"] = now_utc
    row["updated_at_utc"] = now_utc
    return row


async def _mt5_snapshots(names: list[str] | None) -> dict[str, SymbolInfo]:
    import sys

    symbols_pkg = sys.modules.get(__package__)

    client_factory = getattr(symbols_pkg, "create_mt5_client", create_mt5_client)
    client = client_factory()
    try:
        await client.start()
        await client.wait_connected(timeout=client.bridge.command_timeout)
        available = await client.symbol.SymbolsGet()
        if not isinstance(available, list) or not all(
            isinstance(name, str) for name in available
        ):
            raise ValueError("Invalid MT5 symbol list")
        result: dict[str, SymbolInfo] = {}
        if not available:
            raise ValueError("MT5 returned an empty symbol list")
        for name in dict.fromkeys(available if names is None else names):
            candidates = [
                symbol
                for symbol in available
                if name == symbol or name.startswith(symbol + "_")
            ]
            if not candidates:
                raise BridgeError(
                    "Requested symbol was not found in MT5", code="SYMBOL_NOT_FOUND"
                )
            source = max(candidates, key=len)
            if not await client.symbol.Name(source):
                raise BridgeError(
                    "Requested symbol was not found in MT5", code="SYMBOL_NOT_FOUND"
                )
            snapshot = await client.symbol.SymbolInfo()
            if snapshot.name != source:
                raise ValueError("MT5 returned a different symbol")
            if not snapshot.path:
                raise BridgeError(
                    "Reload the updated PythonBridge Expert in MT5",
                    code="BRIDGE_OUTDATED",
                )
            result[name] = snapshot
        return result
    finally:
        await client.close()


def _mt5_fields(row: dict[str, Any], snapshot: SymbolInfo) -> dict[str, Any]:
    """Retain local configuration that MT5 does not supply."""
    data = asdict(snapshot)
    current = asdict(_row_to_symbol_info(row))
    data["spread"]["slippage"] = current["spread"]["slippage"]
    data["margin"]["rate"] = current["margin"]["rate"]
    raw = data["trade"].get("commission_settings")
    if raw:
        commissions = json.loads(raw)
        existing = json.loads(current["trade"].get("commission_settings") or "null")
        if (
            isinstance(commissions, dict)
            and isinstance(existing, dict)
            and "settings" in existing
        ):
            commissions["settings"] = existing["settings"]
            data["trade"]["commission_settings"] = json.dumps(commissions)
    return {
        key: json.dumps(data[key]) if isinstance(data[key], (dict, list)) else data[key]
        for key in _MT5_SPEC_COLUMNS
    }


def _mt5_persist(
    service: Symbols, names: list[str], snapshots: dict[str, SymbolInfo]
) -> list[SymbolInfo]:
    """Write the fetched specifications in one database transaction."""
    updated = []
    with service.gateway.transaction() as tx:
        for name in names:
            response = tx.read_records(
                "datamgr_symbols", filters={"name": name}, limit=1
            )
            records = (response.get("data") or {}).get("records") or []
            if not response["success"] or not records:
                raise ValueError("Catalog changed during the MT5 update")
            fields = _mt5_fields(records[0], snapshots[name])
            fields["updated_at_utc"] = datetime.now(UTC).isoformat()
            response = tx.update_record(
                "datamgr_symbols", fields, filters={"name": name}
            )
            if not response["success"]:
                raise ValueError("Unable to persist MT5 symbol specifications")
            updated.append(_row_to_symbol_info(response["data"]["records"][0]))
    return updated


def _mt5_require_empty(gateway: Any) -> None:
    response = gateway.read_records("datamgr_symbols", limit=1)
    if not response["success"]:
        raise ValueError("Unable to read catalog")
    if response["data"]["records"]:
        raise BridgeError(
            "Catalog is not empty; select symbols to update", code="CONFLICT"
        )


def _mt5_import_all(service: Symbols) -> list[SymbolInfo]:
    """Import the whole terminal catalog only when the local catalog is empty."""
    _mt5_require_empty(service.gateway)
    snapshots = asyncio.run(_mt5_snapshots(None))
    now = datetime.now(UTC).isoformat()
    rows: list[dict[str, SQLiteValue]] = []
    for name, snapshot in snapshots.items():
        data = asdict(snapshot)
        fields: dict[str, SQLiteValue] = {}
        for key in _MT5_SPEC_COLUMNS:
            value = data[key]
            fields[key] = (
                json.dumps(value) if isinstance(value, (dict, list)) else value
            )
        rows.append(
            {
                **fields,
                "name": name,
                "commission": snapshot.commission,
                "broker_id": 0,
                "created_at_utc": now,
                "updated_at_utc": now,
            }
        )
    imported: list[SymbolInfo] = []
    with service.gateway.transaction() as tx:
        _mt5_require_empty(tx)
        for start in range(0, len(rows), 1000):
            response = tx.create_records("datamgr_symbols", rows[start : start + 1000])
            if not response["success"]:
                raise ValueError("Unable to import MT5 catalog")
            imported.extend(
                _row_to_symbol_info(row) for row in response["data"]["records"]
            )
    return imported


def _mt5_refresh_or_import(
    service: Symbols, names: list[str], import_all: bool
) -> list[SymbolInfo]:
    if import_all:
        return _mt5_import_all(service)
    return _mt5_persist(service, names, asyncio.run(_mt5_snapshots(names)))


def _mt5_bridge_failure(error: BridgeError, start: float) -> dict[str, Any]:
    """Describe actionable bridge errors without exposing connection details."""
    if error.code == "BRIDGE_OUTDATED":
        return _fail(
            "symbols.mt5update",
            start,
            "Reload the updated PythonBridge Expert in MT5 before updating symbols",
            ErrorCode.UNAVAILABLE,
        )
    code = {
        "SYMBOL_NOT_FOUND": ErrorCode.NOT_FOUND,
        "CONFLICT": ErrorCode.CONFLICT,
    }.get(error.code, ErrorCode.UNAVAILABLE)
    return _fail(
        "symbols.mt5update",
        start,
        "Catalog is not empty; select symbols to update"
        if code == ErrorCode.CONFLICT
        else "MT5 update failed; check the terminal, bridge and symbol names",
        code,
    )


MAX_DESC_DISPLAY_LEN: int = 26
DESC_TRUNCATE_LEN: int = 24


def _get(item: Any, key: str, default: Any = "") -> Any:
    if isinstance(item, Mapping):
        return cast("Mapping[str, Any]", item).get(key, default)
    return getattr(item, key, default)


def _fmt_scalar(val: Any) -> str:
    """Format scalar number or string cleanly."""
    if isinstance(val, float):
        if val.is_integer():
            return str(int(val))
        return f"{val:g}"
    return str(val)


def _extract_field(item: Any, section: str, key: str, default: Any = 0) -> Any:
    """Extract nested dictionary or contract property safely."""
    sec = _get(item, section, {})
    if isinstance(sec, Mapping):
        return cast("Mapping[str, Any]", sec).get(key, default)
    return getattr(sec, key, default)


def _format_commission(item: Any) -> str:
    """Extract human-readable commission summary."""
    single_comm = _get(item, "commission")
    if single_comm is not None and isinstance(single_comm, (int, float)):
        return f"${_fmt_scalar(single_comm)}/lot"
    comm = _get(item, "commissions", {})
    if not isinstance(comm, Mapping):
        return "None"
    rules: Any = cast("Mapping[str, Any]", comm).get("rules") or []
    if isinstance(rules, list) and rules:
        first_rule = cast("Any", rules)[0]
        if isinstance(first_rule, Mapping):
            tiers: Any = cast("Mapping[str, Any]", first_rule).get("tiers") or []
            if isinstance(tiers, list) and tiers:
                tier = cast("Any", tiers)[0]
                if isinstance(tier, Mapping):
                    val = _fmt_scalar(cast("Mapping[str, Any]", tier).get("value", 0))
                    curr = str(
                        cast("Mapping[str, Any]", tier).get("currency", "")
                    ).strip()
                    return f"{val} {curr}".strip()
    return "None"


def _format_swap(item: Any) -> str:
    """Extract swap long/short representation."""
    swap = _get(item, "swap", {})
    if not isinstance(swap, Mapping):
        return "0 / 0"
    l_val = _fmt_scalar(cast("Mapping[str, Any]", swap).get("long", 0))
    s_val = _fmt_scalar(cast("Mapping[str, Any]", swap).get("short", 0))
    return f"{l_val} / {s_val}"


def _format_order_size(item: Any) -> str:
    """Extract order size multiplier and step."""
    ord_sz = _get(item, "order_size", {})
    if isinstance(ord_sz, Mapping) and ord_sz:
        mult = _fmt_scalar(cast("Mapping[str, Any]", ord_sz).get("multiplier", 1))
        step = _fmt_scalar(cast("Mapping[str, Any]", ord_sz).get("step", 0))
        return f"{mult} / {step}"
    vol = _get(item, "volume", {})
    if isinstance(vol, Mapping) and vol:
        mult = _fmt_scalar(cast("Mapping[str, Any]", vol).get("min", 1))
        step = _fmt_scalar(cast("Mapping[str, Any]", vol).get("step", 0))
        return f"{mult} / {step}"
    return "1 / 0"


def format_symbol_table(
    symbols: Sequence[Any] | Mapping[str, Any],
    *,
    limit: int | None = 50,
) -> str:
    """Format ASCII table of symbol catalog entries with StrategyQuant columns."""
    items: Sequence[Any]
    if (
        isinstance(symbols, Mapping)
        and "data" in symbols
        and isinstance(symbols["data"], Sequence)
    ):
        items = cast("Any", symbols["data"])
    elif isinstance(symbols, Sequence):
        items = symbols
    else:
        items = ()
    total_count = len(items)
    displayed_items = items[:limit] if limit is not None else items
    count = len(displayed_items)
    title = (
        f"=== Symbols Catalog (Showing {count} of {total_count} items) ==="
        if (limit is not None and total_count > count)
        else f"=== Symbols Catalog ({total_count} items) ==="
    )
    lines: list[str] = [title]
    header_fmt = (
        "| {sym:<10} | {desc:<26} | {brk:<14} | {pt:>12} | {ts:>10} "
        "| {tstep:>10} | {spd:>14} | {slip:>16} | {comm:<14} | {swap:<16} "
        "| {dtype:<14} | {ord_sz:<20} |"
    )
    divider = (
        "|-"
        + "-|-".join(
            ["-" * width for width in (10, 26, 14, 12, 10, 10, 14, 16, 14, 16, 14, 20)]
        )
        + "-|"
    )
    lines.append(
        header_fmt.format(
            sym="Symbol",
            desc="Description",
            brk="Broker Profile",
            pt="Point Value",
            ts="Tick Size",
            tstep="Tick Step",
            spd="Default Spread",
            slip="Default Slippage",
            comm="Commissions",
            swap="Swap (L/S)",
            dtype="Data Type",
            ord_sz="Order Size Mult/Step",
        )
    )
    lines.append(divider)
    for item in displayed_items:
        sym = str(_get(item, "name", "") or _get(item, "symbol", ""))
        desc = str(_get(item, "description", ""))
        if len(desc) > MAX_DESC_DISPLAY_LEN:
            desc = desc[:DESC_TRUNCATE_LEN] + ".."
        brk = str(_get(item, "broker_name") or _get(item, "broker") or "Default")
        pt_val = _extract_field(item, "price", "contract_size", None)
        if pt_val is None or pt_val == 0:
            pt_val = _extract_field(item, "contract", "point_value", 0)
        if isinstance(pt_val, (int, float)) and pt_val == int(pt_val) and pt_val > 0:
            pt_str = f"{int(pt_val):,}"
        else:
            pt_str = _fmt_scalar(pt_val)
        tick_sz = _fmt_scalar(_extract_field(item, "price", "tick_size", 0))
        tick_st = _fmt_scalar(_extract_field(item, "price", "tick_step", 0))
        def_spread = _fmt_scalar(_extract_field(item, "spread", "default", 0))
        def_slip = _fmt_scalar(_extract_field(item, "spread", "slippage", 0))
        comm_str = _format_commission(item)
        swap_str = _format_swap(item)
        dtype = str(_get(item, "data_type", ""))
        ord_sz_str = _format_order_size(item)
        lines.append(
            header_fmt.format(
                sym=sym,
                desc=desc,
                brk=brk,
                pt=pt_str,
                ts=tick_sz,
                tstep=tick_st,
                spd=def_spread,
                slip=def_slip,
                comm=comm_str,
                swap=swap_str,
                dtype=dtype,
                ord_sz=ord_sz_str,
            )
        )
    return "\n".join(lines)


class SymbolsCLI:
    """Table formatters for the Data Manager catalog."""

    format_symbol_table = staticmethod(format_symbol_table)
