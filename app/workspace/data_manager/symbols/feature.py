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
import time
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.core.host.logging import get_logger
from app.core.host.persistence import HostPersistence, RecordFilter
from app.host.response import ErrorCode
from app.include.contracts import BridgeError, SymbolInfo

from ._helpers import (
    _MT5_UPDATE_LOCK,
    CSV_COLUMNS,
    _apply_field_updates,
    _build_row_dict,
    _fail,
    _mt5_bridge_failure,
    _mt5_refresh_or_import,
    _ok,
    _parse_csv_row,
    _parse_json_dict,
    _parse_json_list,
    _read_symbols,
    _row_to_csv_dict,
    _row_to_symbol_info,
    _to_sym_list,
    persistence,
)

logger = get_logger(__name__)

__all__ = ["Symbols"]


class Symbols:
    """Service providing symbols catalog presentation and mutations."""

    def __init__(self, gateway: HostPersistence | None = None) -> None:
        import sys

        symbols_pkg = sys.modules.get(__package__)

        self.gateway = (
            gateway
            if gateway is not None
            else getattr(symbols_pkg, "persistence", persistence)
        )

    def _read_symbols(self) -> list[dict[str, Any]]:
        return _read_symbols(self.gateway)

    _build_row_dict = staticmethod(_build_row_dict)

    def mt5update(self, symbols: str | Sequence[str] | None = None) -> dict[str, Any]:
        """Refresh named symbols, or import all MT5 symbols into an empty catalog."""
        start = time.perf_counter()
        names = (
            list(dict.fromkeys(_to_sym_list(symbols))) if symbols is not None else []
        )
        if symbols is not None and not names:
            return _fail(
                "symbols.mt5update",
                start,
                "At least one symbol is required",
                ErrorCode.VALIDATION,
            )
        import sys

        symbols_pkg = sys.modules.get(__package__)

        lock = getattr(symbols_pkg, "_MT5_UPDATE_LOCK", _MT5_UPDATE_LOCK)
        if not lock.acquire(blocking=False):
            return _fail(
                "symbols.mt5update",
                start,
                "Another MT5 update is running",
                ErrorCode.UNAVAILABLE,
            )
        try:
            for name in names:
                response = self.get(name)
                if not response["success"]:
                    return _fail(
                        "symbols.mt5update",
                        start,
                        "Requested catalog symbol was not found",
                        ErrorCode.NOT_FOUND,
                        {"symbol": name},
                    )
            updated = _mt5_refresh_or_import(self, names, symbols is None)
            return _ok(
                "symbols.mt5update",
                start,
                f"{'Imported' if symbols is None else 'Updated'} "
                f"{len(updated)} symbol(s) from MT5",
                data=updated,
                side_effects=("Database records changed",),
            )
        except BridgeError as error:
            return _mt5_bridge_failure(error, start)
        except OSError, RuntimeError, ValueError, TypeError, KeyError:
            return _fail(
                "symbols.mt5update",
                start,
                "MT5 symbol update failed; "
                "check bridge configuration and catalog storage",
                ErrorCode.UNAVAILABLE,
            )
        finally:
            lock.release()

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
                data_type=source.get("data_type", "Forex"),
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
            for start_idx in range(0, len(sym_names), 1000):
                batch = sym_names[start_idx : start_idx + 1000]
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
