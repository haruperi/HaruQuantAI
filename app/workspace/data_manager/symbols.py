"""Data Manager symbols catalog service.

Description:
    Provides symbol / instrument definitions and specifications for the Data Manager
    workspace, reading catalog entries from and mutating the SQLite database
    (datamgr_symbols table). Exposes symbol specifications, lot sizes,
    trading hours, swap rates, margin rules, and commissions with full CRUD,
    cloning, and CSV import/export capabilities.
"""

from __future__ import annotations

import csv
import json
import time
from collections.abc import Mapping, Sequence
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

from app.host.logging import get_logger
from app.host.persistence import HostPersistence, RecordFilter
from app.host.response import (
    ErrorCode,
    ResponseMetadata,
    StandardError,
    StandardResponse,
)
from app.include.contracts import (
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

__all__ = [
    "CSV_COLUMNS",
    "CSV_FIELDNAMES",
    "SymbolInfo",
    "SymbolMargin",
    "SymbolPrice",
    "SymbolSessionWindow",
    "SymbolSpread",
    "SymbolState",
    "SymbolSwap",
    "SymbolTrade",
    "SymbolVolume",
    "Symbols",
]

logger = get_logger(__name__)
persistence = HostPersistence()

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
            if col == "data_type" and isinstance(val, str) and "\\" in val:
                val = val.split("\\", maxsplit=1)[0]
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
        "data_type": (row.get("data_type") or "Forex").strip(),
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
    gateway = gateway if gateway is not None else persistence
    rows: list[dict[str, Any]] = []
    offset: int | None = 0
    while offset is not None:
        response = gateway.read_records("datamgr_symbols", limit=1000, offset=offset)
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
        data_type=str(r.get("data_type") or "Forex"),
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
    dt = kwargs.get("data_type") or "Forex"
    clean_dt = dt.split("\\", maxsplit=1)[0] if "\\" in dt else dt
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
    trade_d["calculation"] = clean_dt
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


class Symbols:
    """Service providing symbols catalog presentation and mutations."""

    def __init__(self, gateway: HostPersistence | None = None) -> None:
        self.gateway = gateway if gateway is not None else persistence

    def _read_symbols(self) -> list[dict[str, Any]]:
        return _read_symbols(self.gateway)

    _build_row_dict = staticmethod(_build_row_dict)

    def list(self) -> dict[str, Any]:
        """Retrieve symbol catalog items wrapped in StandardResponse."""
        start = time.perf_counter()
        try:
            symbols = [_row_to_symbol_info(r) for r in self._read_symbols()]
            logger.debug("FR-DATAMGR-SYMBOLS-CATALOG: Retrieved %d items", len(symbols))
            return _ok(
                "symbols.list",
                start,
                f"Retrieved {len(symbols)} symbol catalog items",
                data=symbols,
            )
        except (RuntimeError, ValueError, TypeError, KeyError, OSError) as error:
            logger.exception("FR-DATAMGR-SYMBOLS-CATALOG: Failed to list symbols")
            return _fail(
                "symbols.list",
                start,
                str(error) or "Failed to retrieve symbols",
                ErrorCode.INTERNAL,
            )

    def get(self, symbol: str) -> dict[str, Any]:
        """Retrieve a single symbol catalog record by symbol/instrument name."""
        start = time.perf_counter()
        sym = symbol.strip()
        if not sym:
            return _fail(
                "symbols.get", start, "Symbol name is required", ErrorCode.VALIDATION
            )
        try:
            resp = self.gateway.read_records(
                "datamgr_symbols", filters={"name": sym}, limit=1
            )
            if not resp["success"]:
                return resp
            records = (resp.get("data") or {}).get("records") or []
            if not records:
                return _fail(
                    "symbols.get",
                    start,
                    f"Symbol '{sym}' not found",
                    ErrorCode.NOT_FOUND,
                )
            return _ok(
                "symbols.get",
                start,
                f"Retrieved symbol '{sym}'",
                data=_row_to_symbol_info(records[0]),
            )
        except (RuntimeError, ValueError, TypeError, KeyError, OSError) as error:
            logger.exception("Failed to get symbol %s", sym)
            return _fail(
                "symbols.get",
                start,
                str(error) or f"Failed to get symbol '{sym}'",
                ErrorCode.INTERNAL,
            )

    def add(
        self,
        name: str = "",
        datasource: str = "",
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Add a new symbol / instrument definition to the catalog."""
        start = time.perf_counter()
        inst_name = name.strip() or str(kwargs.get("symbol") or "").strip()
        broker_profile = datasource.strip()
        if not inst_name:
            return _fail(
                "symbols.add",
                start,
                "Instrument name ('name') is required",
                ErrorCode.VALIDATION,
            )
        if not broker_profile:
            return _fail(
                "symbols.add",
                start,
                "Broker profile ('datasource') is required",
                ErrorCode.VALIDATION,
            )
        suffix = f"_{broker_profile}"
        symbol_key = (
            inst_name if inst_name.endswith(suffix) else f"{inst_name}_{broker_profile}"
        )
        try:
            existing_check = self.gateway.read_records(
                "datamgr_symbols", filters={"name": symbol_key}, limit=1
            )
            records = (existing_check.get("data") or {}).get("records")
            if existing_check.get("success") and records:
                return _fail(
                    "symbols.add",
                    start,
                    f"Symbol '{symbol_key}' already exists",
                    ErrorCode.CONFLICT,
                )
            now_utc = datetime.now(UTC).isoformat()
            row_data = self._build_row_dict(symbol_key, now_utc, **kwargs)
            create_resp = self.gateway.create_records("datamgr_symbols", row_data)
            if not create_resp["success"]:
                err = create_resp.get("error") or {}
                return _fail(
                    "symbols.add",
                    start,
                    create_resp.get("message")
                    or f"Failed to add symbol '{symbol_key}'",
                    ErrorCode(err.get("code", "internal")),
                )
            records = (create_resp.get("data") or {}).get("records") or []
            created_info = (
                _row_to_symbol_info(records[0])
                if records
                else SymbolInfo(name=symbol_key)
            )
            logger.info("FR-DATAMGR-SYMBOLS-ADD: Added symbol '%s'", symbol_key)
            return _ok(
                "symbols.add",
                start,
                f"Added symbol '{symbol_key}'",
                data=created_info,
                side_effects=("Database records changed",),
            )
        except (RuntimeError, ValueError, TypeError, KeyError, OSError) as error:
            logger.exception(
                "FR-DATAMGR-SYMBOLS-ADD: Failed to add symbol '%s'", symbol_key
            )
            return _fail(
                "symbols.add",
                start,
                str(error) or f"Failed to add symbol '{symbol_key}'",
                ErrorCode.INTERNAL,
            )

    def edit(
        self,
        symbols: str | Sequence[str],
        updates: Mapping[str, Any] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Edit one or multiple symbols in the catalog."""
        start = time.perf_counter()
        sym_list = _to_sym_list(symbols)
        if not sym_list:
            return _fail(
                "symbols.edit",
                start,
                "At least one symbol must be specified to edit",
                ErrorCode.VALIDATION,
            )
        fields = dict(updates or {})
        fields.update(kwargs)
        if not fields:
            return _fail(
                "symbols.edit",
                start,
                "No fields provided to edit",
                ErrorCode.VALIDATION,
            )

        try:
            found: dict[str, dict[str, Any]] = {}
            for s in sym_list:
                r = self.gateway.read_records(
                    "datamgr_symbols", filters={"name": s}, limit=1
                )
                if r.get("success") and (r.get("data") or {}).get("records"):
                    found[s] = r["data"]["records"][0]

            if not found:
                return _fail(
                    "symbols.edit",
                    start,
                    f"None of the specified symbols were found: {sym_list}",
                    ErrorCode.NOT_FOUND,
                )

            updated: list[SymbolInfo] = []
            now_utc = datetime.now(UTC).isoformat()
            with self.gateway.transaction() as tx:
                for sym, row in found.items():
                    upds = _apply_field_updates(row, fields, now_utc)
                    res = tx.update_record(
                        "datamgr_symbols",
                        upds,
                        filters={"name": row.get("name") or sym},
                    )
                    if not res["success"]:
                        raise RuntimeError(  # noqa: TRY301
                            res.get("message") or f"Failed to update symbol '{sym}'"
                        )
                    updated.append(_row_to_symbol_info(res["data"]["records"][0]))

            logger.info(
                "FR-DATAMGR-SYMBOLS-EDIT: Successfully edited %d symbol(s)",
                len(updated),
            )
            return _ok(
                "symbols.edit",
                start,
                f"Successfully edited {len(updated)} symbol(s)",
                data=updated,
                side_effects=("Database records changed",),
            )
        except (RuntimeError, ValueError, TypeError, KeyError, OSError) as error:
            logger.exception("FR-DATAMGR-SYMBOLS-EDIT: Failed to edit symbols")
            return _fail(
                "symbols.edit",
                start,
                str(error) or "Internal error editing symbols",
                ErrorCode.INTERNAL,
            )

    def delete(self, symbols: str | Sequence[str]) -> dict[str, Any]:
        """Delete one or multiple symbols from the catalog."""
        start = time.perf_counter()
        sym_list = _to_sym_list(symbols)
        if not sym_list:
            return _fail(
                "symbols.delete",
                start,
                "At least one symbol must be specified to delete",
                ErrorCode.VALIDATION,
            )

        try:
            filter_val = (
                RecordFilter("name", "in", sym_list)
                if len(sym_list) > 1
                else {"name": sym_list[0]}
            )
            resp = self.gateway.delete_record(
                "datamgr_symbols",
                filters=[filter_val]
                if isinstance(filter_val, RecordFilter)
                else filter_val,
            )
            if not resp["success"]:
                err = resp.get("error") or {}
                if err.get("code") == "not_found":
                    return _fail(
                        "symbols.delete",
                        start,
                        f"None of specified symbols were found: {sym_list}",
                        ErrorCode.NOT_FOUND,
                    )
                return resp

            records = (resp.get("data") or {}).get("records") or []
            deleted_syms = [r.get("name") or r.get("symbol") for r in records]
            logger.info(
                "FR-DATAMGR-SYMBOLS-DELETE: Deleted %d symbol(s)", len(deleted_syms)
            )
            return _ok(
                "symbols.delete",
                start,
                f"Deleted {len(deleted_syms)} symbol(s)",
                data=deleted_syms,
                side_effects=("Database records changed",),
            )
        except (RuntimeError, ValueError, TypeError, KeyError, OSError) as error:
            logger.exception("FR-DATAMGR-SYMBOLS-DELETE: Failed to delete symbols")
            return _fail(
                "symbols.delete",
                start,
                str(error) or "Failed to delete symbols",
                ErrorCode.INTERNAL,
            )

    def clone(
        self,
        symbol: str,
        new_name: str,
        *,
        new_datasource: str | None = None,
        **overrides: Any,
    ) -> dict[str, Any]:
        """Clone an existing symbol with a new name by calling Symbols.add()."""
        start = time.perf_counter()
        src_sym, target_name = symbol.strip(), new_name.strip()
        if not src_sym or not target_name:
            return _fail(
                "symbols.clone",
                start,
                "Both source symbol and new symbol name are required",
                ErrorCode.VALIDATION,
            )

        try:
            resp = self.gateway.read_records(
                "datamgr_symbols", filters={"name": src_sym}, limit=1
            )
            records = (resp.get("data") or {}).get("records") or []
            if not resp["success"] or not records:
                return _fail(
                    "symbols.clone",
                    start,
                    f"Source symbol '{src_sym}' not found in datamgr_symbols",
                    ErrorCode.NOT_FOUND,
                )

            source = records[0]
            existing_name = str(source.get("name") or "")
            ds = new_datasource or (
                existing_name.rsplit("_", 1)[1]
                if "_" in existing_name
                else "SQ default"
            )
            inst_name = target_name.removesuffix(f"_{ds}")

            comp_keys = (
                "spread",
                "margin",
                "volume",
                "trade",
                "price",
                "swap",
                "state",
            )
            add_args: dict[str, Any] = {
                k: _parse_json_dict(source.get(k)) for k in comp_keys
            }
            add_args.update(
                name=inst_name,
                datasource=ds,
                data_type=source.get("data_type") or "Forex",
                description=source.get("description") or "",
                exchange=source.get("exchange") or "XCCY",
                broker_id=int(source.get("broker_id") or 0),
                commission=float(source.get("commission") or 0.0),
                session=_parse_json_list(source.get("session")),
            )
            add_args.update(overrides)

            add_resp = self.add(**add_args)
            if not add_resp["success"]:
                err = add_resp.get("error") or {}
                msg = f"Failed to clone symbol '{src_sym}': {add_resp.get('message')}"
                return _fail(
                    "symbols.clone", start, msg, ErrorCode(err.get("code", "internal"))
                )

            logger.info(
                "FR-DATAMGR-SYMBOLS-CLONE: Cloned symbol '%s' as '%s_%s'",
                src_sym,
                inst_name,
                ds,
            )
            return _ok(
                "symbols.clone",
                start,
                f"Cloned symbol '{src_sym}' as '{inst_name}_{ds}'",
                data=add_resp["data"],
                side_effects=("Database records changed",),
            )
        except (RuntimeError, ValueError, TypeError, KeyError, OSError) as error:
            logger.exception(
                "FR-DATAMGR-SYMBOLS-CLONE: Failed to clone symbol '%s'", src_sym
            )
            return _fail(
                "symbols.clone",
                start,
                str(error) or f"Failed to clone symbol '{src_sym}'",
                ErrorCode.INTERNAL,
            )

    def load(self, path: str | Path) -> dict[str, Any]:
        """Load symbols from a CSV file into the catalog."""
        start = time.perf_counter()
        try:
            file_path = Path(path).resolve()
            if not file_path.is_file():
                return _fail(
                    "symbols.load",
                    start,
                    f"CSV file '{file_path}' does not exist",
                    ErrorCode.NOT_FOUND,
                )

            with file_path.open(encoding="utf-8-sig", newline="") as fp:
                rows = list(csv.DictReader(fp))

            if not rows:
                return _fail(
                    "symbols.load",
                    start,
                    "CSV contains no records",
                    ErrorCode.VALIDATION,
                )

            loaded: list[dict[str, Any]] = []
            errors: list[dict[str, Any]] = []

            for idx, row in enumerate(rows):
                try:
                    raw_name, raw_ds, add_args = _parse_csv_row(row)
                except ValueError as val_err:
                    errors.append({"row": idx + 1, "error": str(val_err)})
                    continue

                if not raw_name:
                    errors.append({"row": idx + 1, "error": "Missing instrument name"})
                    continue

                res = self.add(**add_args)
                if res["success"]:
                    loaded.append(res["data"])
                else:
                    errors.append(
                        {
                            "row": idx + 1,
                            "symbol": f"{raw_name}_{raw_ds}",
                            "error": res.get("message") or "Failed to add symbol",
                        }
                    )

            if not loaded and errors:
                err_code = (
                    ErrorCode.CONFLICT
                    if all("already exists" in e["error"] for e in errors)
                    else ErrorCode.VALIDATION
                )
                return _fail(
                    "symbols.load",
                    start,
                    f"Failed to load symbols from '{file_path.name}'",
                    err_code,
                    details={"errors": errors},
                )

            logger.info(
                "FR-DATAMGR-SYMBOLS-LOAD: Loaded %d symbol(s) from '%s'",
                len(loaded),
                file_path.name,
            )
            msg = f"Loaded {len(loaded)} symbol(s) from '{file_path.name}'" + (
                f" ({len(errors)} skipped)" if errors else ""
            )
            return _ok(
                "symbols.load",
                start,
                msg,
                data={"loaded": loaded, "errors": errors, "total": len(rows)},
                side_effects=("Database records changed",) if loaded else (),
            )
        except (RuntimeError, ValueError, TypeError, KeyError, OSError) as error:
            logger.exception("FR-DATAMGR-SYMBOLS-LOAD: Failed to load symbols from CSV")
            return _fail(
                "symbols.load",
                start,
                str(error) or "Internal error loading symbols from CSV",
                ErrorCode.INTERNAL,
            )

    def save(
        self,
        symbols: Sequence[str | SymbolInfo | Mapping[str, Any]],
        path: str | Path,
    ) -> dict[str, Any]:
        """Save a list of symbols from the catalog to a CSV file."""
        start = time.perf_counter()
        if not symbols:
            return _fail(
                "symbols.save",
                start,
                "Symbols list cannot be empty",
                ErrorCode.VALIDATION,
            )

        try:
            names = [
                s.strip()
                if isinstance(s, str)
                else s.name
                if isinstance(s, SymbolInfo)
                else str(s.get("name") or s.get("symbol") or "").strip()
                for s in symbols
            ]
            sym_names = [n for n in names if n]
            if not sym_names:
                return _fail(
                    "symbols.save",
                    start,
                    "No valid symbol names extracted from symbols argument",
                    ErrorCode.VALIDATION,
                )

            file_path = Path(path).resolve()
            file_path.parent.mkdir(parents=True, exist_ok=True)

            sym_names = list(dict.fromkeys(sym_names))
            records: list[dict[str, Any]] = []
            for start in range(0, len(sym_names), 1000):
                batch = sym_names[start : start + 1000]
                resp = self.gateway.read_records(
                    "datamgr_symbols",
                    filters=[RecordFilter("name", "in", batch)],
                    limit=1000,
                )
                if not resp["success"]:
                    return resp
                data = resp.get("data") or {}
                records.extend(data.get("records") or [])
            if not records:
                return _fail(
                    "symbols.save",
                    start,
                    "Symbols not found in catalog",
                    ErrorCode.NOT_FOUND,
                )

            rows_to_write = [_row_to_csv_dict(r) for r in records]
            with file_path.open(mode="w", encoding="utf-8-sig", newline="") as fp:
                writer = csv.DictWriter(fp, fieldnames=list(CSV_COLUMNS))
                writer.writeheader()
                writer.writerows(rows_to_write)

            logger.info(
                "FR-DATAMGR-SYMBOLS-SAVE: Saved %d symbol(s) to '%s'",
                len(rows_to_write),
                file_path.name,
            )
            return _ok(
                "symbols.save",
                start,
                f"Saved {len(rows_to_write)} symbol(s) to '{file_path.name}'",
                data={
                    "path": str(file_path),
                    "count": len(rows_to_write),
                    "symbols": [r["name"] for r in rows_to_write],
                },
                side_effects=("File written",),
            )
        except (RuntimeError, ValueError, TypeError, KeyError, OSError) as error:
            logger.exception("FR-DATAMGR-SYMBOLS-SAVE: Failed to save symbols to CSV")
            return _fail(
                "symbols.save",
                start,
                str(error) or "Internal error saving symbols to CSV",
                ErrorCode.INTERNAL,
            )
