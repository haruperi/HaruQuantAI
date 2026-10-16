"""Instrument specifications, financial attributes, and symbol catalog management.

Description:
    Provides domain logic for financial instrument specifications, catalog viewing,
    editing, cloning, deletion, and canonical JSON specification import and export.
    Operates strictly via host persistence layer functions (`list_datamgr_instruments`,
    `get_datamgr_instrument`, `create_datamgr_instrument`, `update_datamgr_instrument`,
    `delete_datamgr_instrument`) with zero direct database queries and non-silent
    requirement logging.

Purpose:
    FEAT-DATAMGR-INSTRUMENTS: Instrument catalog and financial specification.

Key Capabilities:
    - FR-DATAMGR-INSTRUMENTS-VIEW: Retrieve and filter catalog instruments.
      Associated: `Instruments.view()`
      Logging: Emits INFO on listed count and query parameters.
    - FR-DATAMGR-INSTRUMENTS-ADD: Add an instrument specification to the catalog.
      Associated: `Instruments.add()`
      Logging: Emits INFO on added instrument symbol and id.
    - FR-DATAMGR-INSTRUMENTS-EDIT: Edit one or multiple existing instrument records.
      Associated: `Instruments.edit()`
      Logging: Emits INFO on edited instrument(s) and updated count.
    - FR-DATAMGR-INSTRUMENTS-CLONE: Duplicate instrument under a new symbol name.
      Associated: `Instruments.clone()`
      Logging: Emits INFO on source and cloned target symbol.
    - FR-DATAMGR-INSTRUMENTS-DELETE: Delete instrument specifications from catalog.
      Associated: `Instruments.delete()`
      Logging: Emits INFO on deleted symbol(s) and count.
    - FR-DATAMGR-INSTRUMENTS-IMPORT: Load instruments from a JSON file or payload.
      Associated: `Instruments.import_()`
      Logging: Emits INFO on imported, overwritten, and skipped instrument counts.
    - FR-DATAMGR-INSTRUMENTS-EXPORT: Save instruments to a JSON file or structure.
      Associated: `Instruments.export()`
      Logging: Emits INFO on exported instrument count and target path.
    - FR-DATAMGR-INSTRUMENTS-CLI: Headless CLI interface for instruments catalog.
      Associated: `InstrumentsCLI.dispatch()`
      Logging: Emits INFO on headless command dispatch and parameter evaluation.

Python API Usage:
    ```python
    from app.workspace.data_manager.instruments import Instruments, InstrumentsCLI

    service = Instruments()
    instruments = service.view()
    print(InstrumentsCLI.format_instruments_table(instruments))
    ```

CLI Usage:
    ```bash
    uv run python -m app.cli instrument action=list
    uv run python -m app.cli instrument action=add instrument=EURUSD
    uv run python -m app.cli instrument action=list csv=true
    ```
"""

from __future__ import annotations

import csv
import io
import json
import tempfile
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.host.logging import get_logger
from app.host.persistence.create import create_datamgr_instrument, create_schema
from app.host.persistence.delete import delete_datamgr_instrument
from app.host.persistence.read import (
    get_datamgr_instrument,
    list_datamgr_instruments,
    resolve_connection,
)
from app.host.persistence.update import update_datamgr_instrument
from app.services.include.contracts import SymbolInfo

from .log import DataManagerLogService

__all__ = [
    "Instruments",
    "InstrumentsCLI",
]

logger = get_logger(__name__)

VIEW_FR = "FR-DATAMGR-INSTRUMENTS-VIEW"
ADD_FR = "FR-DATAMGR-INSTRUMENTS-ADD"
EDIT_FR = "FR-DATAMGR-INSTRUMENTS-EDIT"
CLONE_FR = "FR-DATAMGR-INSTRUMENTS-CLONE"
DELETE_FR = "FR-DATAMGR-INSTRUMENTS-DELETE"
IMPORT_FR = "FR-DATAMGR-INSTRUMENTS-IMPORT"
EXPORT_FR = "FR-DATAMGR-INSTRUMENTS-EXPORT"
CLI_FR = "FR-DATAMGR-INSTRUMENTS-CLI"


@dataclass(frozen=True)
class _Config:
    """Internal module configuration and execution parameters."""

    db_path: Path | None = None
    default_data_type: str = "Forex"

    def to_dict(self) -> dict[str, Any]:
        """Convert internal config to standard dictionary."""
        return {
            "db_path": str(self.db_path) if self.db_path else None,
            "default_data_type": self.default_data_type,
        }


_VALID_INSTRUMENT_COLS: frozenset[str] = frozenset(
    {
        "connection",
        "broker_id",
        "description",
        "tick_size",
        "tick_step",
        "tick_value_in_money",
        "point_value",
        "decimals",
        "default_spread",
        "default_slippage",
        "min_volume",
        "max_volume",
        "lot_step",
        "margin_rate",
        "swap_long",
        "swap_short",
        "swap_3day_day",
        "commissions",
        "data_type",
        "alias",
        "exchange",
        "country",
        "sector",
        "min_distance",
        "order_size_multiplier",
        "order_size_step",
        "cot",
        "updated_at_utc",
    }
)

_FIELD_ALIASES: dict[str, str] = {
    "defaultspread": "default_spread",
    "defaultslippage": "default_slippage",
    "pointvalue": "point_value",
    "ticksize": "tick_size",
    "tickstep": "tick_step",
    "datatype": "data_type",
    "broker": "broker_id",
    "mindistance": "min_distance",
    "ordersizemultiplier": "order_size_multiplier",
    "ordersizestep": "order_size_step",
}


def _parse_json_payload(
    file_path_or_content: str | Path | Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Parse JSON file path, string, or mapping into a list of instrument dicts."""
    if isinstance(file_path_or_content, Mapping):
        raw: Any = dict(file_path_or_content)
    else:
        target = Path(file_path_or_content)
        if target.is_file():
            raw = json.loads(target.read_text(encoding="utf-8"))
        else:
            raw = json.loads(str(file_path_or_content))

    if isinstance(raw, dict):
        return list(raw.get("instruments", []))
    if isinstance(raw, list):
        return list(raw)
    return []


class Instruments:
    """Service governing instrument specifications via host persistence CRUD."""

    def __init__(
        self,
        db_path: Path | str | None = None,
        log_service: DataManagerLogService | None = None,
        config: _Config | None = None,
    ) -> None:
        """Initialize instruments service with optional DB path and logger."""
        resolved_db = Path(db_path) if db_path is not None else None
        self._config = config or _Config(db_path=resolved_db)
        self.log_service = log_service

    @property
    def db_path(self) -> Path | None:
        """Return configured database file path."""
        return self._config.db_path

    def view(
        self,
        broker_id: int | None = None,
        search: str | None = None,
        data_type: str | None = None,
        connection: str | None = None,
    ) -> list[dict[str, Any]]:
        """Return instruments in datamgr_instruments matching filter criteria."""
        rows = list_datamgr_instruments(
            self._config.db_path,
            broker_id=broker_id if broker_id is not None and broker_id >= 0 else None,
        )
        results: list[dict[str, Any]] = []
        q = search.strip().lower() if search else None
        dt = data_type.strip().lower() if data_type else None
        conn_str = connection.strip().lower() if connection else None

        for r in rows:
            if dt and str(r.get("data_type", "")).strip().lower() != dt:
                continue
            if conn_str and str(r.get("connection", "")).strip().lower() != conn_str:
                continue
            if q:
                sym = str(r.get("symbol", "")).lower()
                desc = str(r.get("description", "")).lower()
                if q not in sym and q not in desc:
                    continue
            results.append(r)

        logger.info(
            "%s: Listed %d instruments",
            VIEW_FR,
            len(results),
            extra={
                "fr_id": VIEW_FR,
                "count": len(results),
                "broker_id": broker_id,
                "search": search,
                "data_type": data_type,
                "connection": connection,
            },
        )
        return results

    def add(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        """Add an instrument specification to datamgr_instruments."""
        clean_symbol = (
            str(payload.get("symbol", "") or payload.get("instrument", ""))
            .strip()
            .upper()
        )
        if not clean_symbol:
            raise ValueError("Instrument symbol is required.")

        now_iso = datetime.now(UTC).isoformat()
        existing = get_datamgr_instrument(self._config.db_path, clean_symbol)
        if existing is not None:
            updates = dict(payload)
            updates.pop("id", None)
            updates["symbol"] = clean_symbol
            updates["updated_at_utc"] = now_iso
            update_datamgr_instrument(self._config.db_path, clean_symbol, updates)
            res = get_datamgr_instrument(self._config.db_path, clean_symbol)
            result = res if res is not None else dict(payload)
        else:
            inserted_id = create_datamgr_instrument(
                self._config.db_path,
                symbol=clean_symbol,
                connection=str(payload.get("connection", "")),
                broker_id=int(payload.get("broker_id", 0)),
                description=str(
                    payload.get("description", "") or payload.get("name", "")
                ),
                tick_size=float(
                    payload.get("tick_size", payload.get("ticksize", 0.00001))
                ),
                tick_step=float(
                    payload.get("tick_step", payload.get("tickstep", 0.00001))
                ),
                tick_value_in_money=float(payload.get("tick_value_in_money", 10.0)),
                point_value=float(
                    payload.get("point_value", payload.get("pointvalue", 100000.0))
                ),
                decimals=int(payload.get("decimals", 5)),
                default_spread=float(
                    payload.get(
                        "default_spread",
                        payload.get("defaultspread", payload.get("spread", 0.0001)),
                    )
                ),
                default_slippage=float(
                    payload.get(
                        "default_slippage",
                        payload.get("defaultslippage", payload.get("slippage", 0.0)),
                    )
                ),
                min_volume=float(payload.get("min_volume", 0.01)),
                max_volume=float(payload.get("max_volume", 100.0)),
                lot_step=float(payload.get("lot_step", 0.01)),
                margin_rate=float(payload.get("margin_rate", 0.05)),
                swap_long=float(payload.get("swap_long", 0.0)),
                swap_short=float(payload.get("swap_short", 0.0)),
                swap_3day_day=int(payload.get("swap_3day_day", 3)),
                commissions=str(payload.get("commissions", "0.0")),
                data_type=str(
                    payload.get("data_type", payload.get("datatype", "Forex"))
                ),
                alias=str(payload.get("alias", "")),
                exchange=str(payload.get("exchange", "")),
                country=str(payload.get("country", "")),
                sector=str(payload.get("sector", "")),
                min_distance=float(
                    payload.get("min_distance", payload.get("minDistance", 0.0))
                ),
                order_size_multiplier=float(
                    payload.get(
                        "order_size_multiplier", payload.get("orderSizeMultiplier", 1.0)
                    )
                ),
                order_size_step=float(
                    payload.get("order_size_step", payload.get("orderSizeStep", 0.0))
                ),
                cot=str(payload.get("cot", "")) or None,
                created_at_utc=now_iso,
                updated_at_utc=now_iso,
            )
            res = get_datamgr_instrument(self._config.db_path, clean_symbol)
            result = (
                res if res is not None else {"id": inserted_id, "symbol": clean_symbol}
            )

        logger.info(
            "%s: Added instrument symbol=%s id=%s",
            ADD_FR,
            clean_symbol,
            result.get("id"),
            extra={"fr_id": ADD_FR, "symbol": clean_symbol, "id": result.get("id")},
        )
        return result

    def edit(
        self,
        symbol_or_symbols: str | Sequence[str],
        updates: Mapping[str, Any],
        change_flags: Mapping[str, bool] | None = None,
    ) -> dict[str, Any] | int:
        """Edit one or multiple instruments in datamgr_instruments."""
        filtered_updates: dict[str, Any] = {}
        for k, v in updates.items():
            norm_k = _FIELD_ALIASES.get(k.lower(), k)
            if (
                norm_k in _VALID_INSTRUMENT_COLS
                and norm_k not in ("id", "symbol", "created_at_utc")
                and (change_flags is None or change_flags.get(k, True))
            ):
                filtered_updates[norm_k] = v
        filtered_updates["updated_at_utc"] = datetime.now(UTC).isoformat()

        if isinstance(symbol_or_symbols, str):
            clean_sym = symbol_or_symbols.strip().upper()
            inst = get_datamgr_instrument(self._config.db_path, clean_sym)
            if inst is None:
                raise KeyError(f"Instrument '{clean_sym}' not found.")
            update_datamgr_instrument(self._config.db_path, clean_sym, filtered_updates)
            updated = get_datamgr_instrument(self._config.db_path, clean_sym)
            res = updated if updated is not None else dict(filtered_updates)
            logger.info(
                "%s: Edited instrument symbol=%s",
                EDIT_FR,
                clean_sym,
                extra={"fr_id": EDIT_FR, "symbol": clean_sym},
            )
            return res

        count = 0
        for sym in symbol_or_symbols:
            clean_sym = sym.strip().upper()
            if update_datamgr_instrument(
                self._config.db_path, clean_sym, filtered_updates
            ):
                count += 1
        logger.info(
            "%s: Edited %d instruments",
            EDIT_FR,
            count,
            extra={"fr_id": EDIT_FR, "count": count},
        )
        return count

    def clone(
        self,
        symbol: str,
        clone_name: str = "",
        broker_id: int = -1,
        broker_postfix: str = "",
    ) -> dict[str, Any]:
        """Copy one instrument to create a new instrument in datamgr_instruments."""
        clean_sym = symbol.strip().upper()
        source = get_datamgr_instrument(self._config.db_path, clean_sym)
        if source is None:
            raise KeyError(f"Source instrument '{clean_sym}' not found.")

        target_name = (
            clone_name.strip().upper()
            if clone_name
            else f"{source['symbol']}{broker_postfix}".strip().upper()
        )
        data = dict(source)
        data.pop("id", None)
        data["symbol"] = target_name
        data["broker_id"] = broker_id
        cloned = self.add(data)
        logger.info(
            "%s: Cloned instrument %s -> %s",
            CLONE_FR,
            clean_sym,
            target_name,
            extra={"fr_id": CLONE_FR, "source": clean_sym, "target": target_name},
        )
        return cloned

    def delete(self, symbol_or_symbols: str | Sequence[str]) -> bool | int:
        """Remove one or more instruments from datamgr_instruments."""
        if isinstance(symbol_or_symbols, str):
            clean_sym = symbol_or_symbols.strip().upper()
            deleted = delete_datamgr_instrument(self._config.db_path, clean_sym)
            logger.info(
                "%s: Deleted instrument symbol=%s status=%s",
                DELETE_FR,
                clean_sym,
                deleted,
                extra={"fr_id": DELETE_FR, "symbol": clean_sym, "deleted": deleted},
            )
            return deleted

        deleted_count = 0
        for sym in symbol_or_symbols:
            clean_sym = sym.strip().upper()
            if delete_datamgr_instrument(self._config.db_path, clean_sym):
                deleted_count += 1
        logger.info(
            "%s: Deleted %d instruments",
            DELETE_FR,
            deleted_count,
            extra={"fr_id": DELETE_FR, "deleted_count": deleted_count},
        )
        return deleted_count

    def import_(
        self,
        file_path_or_content: str | Path | Mapping[str, Any],
        conflict_policy: str = "overwrite_all",
    ) -> dict[str, Any]:
        """Add new instruments from a selected JSON file or structure."""
        items = _parse_json_payload(file_path_or_content)
        imported = 0
        overwritten = 0
        skipped = 0
        symbols_list: list[str] = []

        for item in items:
            sym = str(item.get("symbol", "")).strip().upper()
            if not sym:
                continue
            existing = get_datamgr_instrument(self._config.db_path, sym)
            if existing and conflict_policy == "skip":
                skipped += 1
                continue
            self.add(item)
            symbols_list.append(sym)
            if existing:
                overwritten += 1
            else:
                imported += 1

        logger.info(
            "%s: Imported instruments JSON (imported=%d, overwritten=%d, skipped=%d)",
            IMPORT_FR,
            imported,
            overwritten,
            skipped,
            extra={
                "fr_id": IMPORT_FR,
                "imported": imported,
                "overwritten": overwritten,
                "skipped": skipped,
            },
        )
        return {
            "imported": imported,
            "overwritten": overwritten,
            "skipped": skipped,
            "symbols": symbols_list,
        }

    # Programmatic aliases
    import_json = import_

    def export(
        self,
        file_path: str | Path | None = None,
        symbols: Sequence[str] | None = None,
    ) -> str | Path:
        """Save selected instruments to a JSON file or string."""
        all_inst = self.view()
        target_symbols = (
            {s.strip().upper() for s in symbols} if symbols is not None else None
        )
        exported = [
            i
            for i in all_inst
            if target_symbols is None
            or str(i.get("symbol", "")).upper() in target_symbols
        ]

        payload = {
            "version": 1,
            "kind": "instruments",
            "brokers": [],
            "instruments": exported,
        }
        json_content = json.dumps(payload, indent=2)

        if file_path is not None:
            p = Path(file_path)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(json_content, encoding="utf-8")
            logger.info(
                "%s: Exported %d instruments to file %s",
                EXPORT_FR,
                len(exported),
                str(p),
                extra={
                    "fr_id": EXPORT_FR,
                    "count": len(exported),
                    "path": str(p),
                },
            )
            return p

        logger.info(
            "%s: Exported %d instruments as JSON string",
            EXPORT_FR,
            len(exported),
            extra={"fr_id": EXPORT_FR, "count": len(exported)},
        )
        return json_content


# Bind import attribute to import_ method for dynamic call support
setattr(Instruments, "import", Instruments.import_)


def _resolve_raw_action(params: dict[str, Any]) -> str:
    """Resolve effective action from parameters or flag aliases."""
    raw = str(params.get("action", "")).strip().lower()
    if raw.startswith("action="):
        raw = raw.split("=", 1)[1].strip()
    if "=" in raw:
        k, v = raw.split("=", 1)
        params[k.lstrip("-").strip().lower()] = v.strip()
        raw = ""
    if raw:
        return raw

    action_map = {"il": "list", "ia": "add", "ie": "edit", "id": "delete"}
    for flag, act in action_map.items():
        if flag in params:
            return act
    return "list"


def _parse_cli_arguments(
    args: Sequence[str] | Mapping[str, Any],
) -> tuple[str, dict[str, Any]]:
    """Parse CLI argument list or mapping into an action name and parameter dict."""
    if isinstance(args, Mapping):
        params = dict(args)
    else:
        params = {}
        for item in args:
            if "=" in item:
                k, v = item.split("=", 1)
                params[k.lstrip("-").strip().lower()] = v.strip()
            elif item.startswith("-"):
                params[item.lstrip("-").strip().lower()] = True
            elif "action" not in params:
                params["action"] = item.strip().lower()

    raw_action = _resolve_raw_action(params)
    return raw_action, params


class InstrumentsCLI:
    """Headless CLI presentation and dispatcher for instrument catalog operations."""

    MAX_DESC_LEN: int = 28
    TRUNCATE_LEN: int = 26

    @classmethod
    def dispatch(
        cls,
        args: Sequence[str] | Mapping[str, Any],
        service: Instruments | None = None,
    ) -> dict[str, Any]:
        """Dispatch headless CLI instrument commands and flags."""
        svc = service or Instruments()
        raw_action, params = _parse_cli_arguments(args)

        logger.info(
            "%s: Executing CLI action '%s' with %d parameters",
            CLI_FR,
            raw_action,
            len(params),
            extra={"fr_id": CLI_FR, "action": raw_action, "params": params},
        )

        handlers: dict[str, Callable[[], dict[str, Any]]] = {
            "list": lambda: cls._handle_list(svc, params),
            "view": lambda: cls._handle_list(svc, params),
            "-il": lambda: cls._handle_list(svc, params),
            "add": lambda: cls._handle_add(svc, params),
            "-ia": lambda: cls._handle_add(svc, params),
            "edit": lambda: cls._handle_edit(svc, params),
            "-ie": lambda: cls._handle_edit(svc, params),
            "delete": lambda: cls._handle_delete(svc, params),
            "-id": lambda: cls._handle_delete(svc, params),
            "clone": lambda: cls._handle_clone(svc, params),
            "import": lambda: cls._handle_import(svc, params),
            "load": lambda: cls._handle_import(svc, params),
            "export": lambda: cls._handle_export(svc, params),
            "save": lambda: cls._handle_export(svc, params),
        }

        handler = handlers.get(raw_action)
        if handler is None:
            raise ValueError(f"Unsupported instrument action: '{raw_action}'")
        return handler()

    @classmethod
    def _handle_list(
        cls, svc: Instruments, params: Mapping[str, Any]
    ) -> dict[str, Any]:
        broker_id = int(params["broker_id"]) if "broker_id" in params else None
        instruments = svc.view(
            broker_id=broker_id,
            search=params.get("search"),
            data_type=params.get("datatype") or params.get("data_type"),
            connection=params.get("connection"),
        )
        as_csv = str(params.get("csv", "false")).lower() in ("true", "1", "yes")
        rendered = (
            cls.format_instruments_csv(instruments)
            if as_csv
            else cls.format_instruments_table(instruments)
        )
        return {
            "command": "instrument",
            "action": "list",
            "count": len(instruments),
            "rendered": rendered,
            "instruments": instruments,
        }

    @classmethod
    def _handle_add(cls, svc: Instruments, params: Mapping[str, Any]) -> dict[str, Any]:
        sym = params.get("instrument") or params.get("symbol")
        if not sym:
            raise ValueError("Parameter 'instrument' is required for action=add.")
        payload = {
            k: v
            for k, v in params.items()
            if k not in ("action", "instrument", "symbol", "ia", "ie", "il", "id")
        }
        payload["symbol"] = sym
        added = svc.add(payload)
        return {
            "command": "instrument",
            "action": "add",
            "rendered": f"Added instrument '{added.get('symbol')}'.",
            "instrument": added,
        }

    @classmethod
    def _handle_edit(
        cls, svc: Instruments, params: Mapping[str, Any]
    ) -> dict[str, Any]:
        sym = params.get("instrument") or params.get("symbol")
        if not sym:
            raise ValueError("Parameter 'instrument' is required for action=edit.")
        payload = {
            k: v
            for k, v in params.items()
            if k not in ("action", "instrument", "symbol", "ia", "ie", "il", "id")
        }
        edited = svc.edit(str(sym), payload)
        return {
            "command": "instrument",
            "action": "edit",
            "rendered": f"Edited instrument '{sym}'.",
            "instrument": edited,
        }

    @classmethod
    def _handle_delete(
        cls, svc: Instruments, params: Mapping[str, Any]
    ) -> dict[str, Any]:
        symbols_raw = (
            params.get("instruments")
            or params.get("instrument")
            or params.get("symbols")
            or params.get("symbol")
        )
        if not symbols_raw:
            raise ValueError("Parameter 'instruments' is required for action=delete.")
        sym_list = [s.strip() for s in str(symbols_raw).split(",") if s.strip()]
        if len(sym_list) == 1:
            deleted = svc.delete(sym_list[0])
            return {
                "command": "instrument",
                "action": "delete",
                "rendered": f"Deleted instrument '{sym_list[0]}' (status={deleted}).",
                "deleted": deleted,
            }
        count = svc.delete(sym_list)
        return {
            "command": "instrument",
            "action": "delete",
            "rendered": f"Deleted {count} instruments.",
            "deleted_count": count,
        }

    @classmethod
    def _handle_clone(
        cls, svc: Instruments, params: Mapping[str, Any]
    ) -> dict[str, Any]:
        sym = params.get("instrument") or params.get("symbol")
        if not sym:
            raise ValueError("Parameter 'instrument' is required for action=clone.")
        clone_name = str(
            params.get("clone_name")
            or params.get("clone_symbol")
            or params.get("new_symbol")
            or params.get("new_name", "")
        )
        broker_id = int(params.get("broker_id", -1))
        broker_postfix = str(params.get("broker_postfix", ""))
        cloned = svc.clone(
            str(sym),
            clone_name=clone_name,
            broker_id=broker_id,
            broker_postfix=broker_postfix,
        )
        return {
            "command": "instrument",
            "action": "clone",
            "rendered": f"Cloned instrument '{sym}' -> '{cloned.get('symbol')}'.",
            "instrument": cloned,
        }

    @classmethod
    def _handle_import(
        cls, svc: Instruments, params: Mapping[str, Any]
    ) -> dict[str, Any]:
        filepath = params.get("filepath") or params.get("file")
        if not filepath:
            raise ValueError("Parameter 'filepath' is required for action=import.")
        policy = str(params.get("conflict_policy", "overwrite_all"))
        report = svc.import_(filepath, conflict_policy=policy)
        return {
            "command": "instrument",
            "action": "import",
            "rendered": (
                f"Imported {report.get('imported', 0)} instruments "
                f"(overwritten={report.get('overwritten', 0)}, "
                f"skipped={report.get('skipped', 0)})."
            ),
            **report,
        }

    @classmethod
    def _handle_export(
        cls, svc: Instruments, params: Mapping[str, Any]
    ) -> dict[str, Any]:
        filepath = params.get("filepath") or params.get("file")
        syms_raw = params.get("instruments") or params.get("symbols")
        syms = (
            [s.strip() for s in str(syms_raw).split(",") if s.strip()]
            if syms_raw
            else None
        )
        output = svc.export(filepath, symbols=syms)
        rendered = f"Exported instruments to {output}" if filepath else str(output)
        return {
            "command": "instrument",
            "action": "export",
            "rendered": rendered,
            "output": str(output),
        }

    @classmethod
    def format_instruments_table(
        cls,
        instruments: Sequence[Mapping[str, Any] | SymbolInfo],
    ) -> str:
        """Format ASCII table of instrument records."""
        logger.debug("Formatting %d instruments as ASCII table", len(instruments))
        lines: list[str] = [f"=== Instruments Catalog ({len(instruments)} items) ==="]
        header = (
            "| {sym:<12} | {desc:<28} | {dtype:<10} | {tick:>10} "
            "| {point:>10} | {dec:>4} | {spread:>8} |"
        )
        divider = (
            "|-"
            + "-|-".join(
                [
                    "-" * 12,
                    "-" * 28,
                    "-" * 10,
                    "-" * 10,
                    "-" * 10,
                    "-" * 4,
                    "-" * 8,
                ]
            )
            + "-|"
        )
        lines.append(
            header.format(
                sym="Symbol",
                desc="Description",
                dtype="Data Type",
                tick="Tick Size",
                point="Point Val",
                dec="Dec",
                spread="Spread",
            )
        )
        lines.append(divider)
        for inst in instruments:
            sym = (
                inst.symbol
                if isinstance(inst, SymbolInfo)
                else str(inst.get("symbol", ""))
            )
            desc_val = (
                inst.description
                if isinstance(inst, SymbolInfo)
                else str(inst.get("description", ""))
            )
            dtype = (
                inst.data_type
                if isinstance(inst, SymbolInfo)
                else str(inst.get("data_type", "Forex"))
            )
            tick = (
                inst.tick_size
                if isinstance(inst, SymbolInfo)
                else float(inst.get("tick_size", 0.0001))
            )
            point = (
                inst.point_value
                if isinstance(inst, SymbolInfo)
                else float(inst.get("point_value", 100000.0))
            )
            dec = (
                inst.decimals
                if isinstance(inst, SymbolInfo)
                else int(inst.get("decimals", 5))
            )
            spread = (
                inst.default_spread
                if isinstance(inst, SymbolInfo)
                else float(inst.get("default_spread", 1.0))
            )

            desc = (
                desc_val[: cls.TRUNCATE_LEN] + ".."
                if len(desc_val) > cls.MAX_DESC_LEN
                else desc_val
            )
            lines.append(
                header.format(
                    sym=sym,
                    desc=desc,
                    dtype=dtype,
                    tick=f"{tick:.5f}",
                    point=f"{point:.1f}",
                    dec=str(dec),
                    spread=f"{spread:.1f}",
                )
            )
        return "\n".join(lines)

    @classmethod
    def format_instruments_csv(
        cls,
        instruments: Sequence[Mapping[str, Any] | SymbolInfo],
    ) -> str:
        """Format CSV string of instrument records."""
        logger.debug("Formatting %d instruments as CSV", len(instruments))
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(
            [
                "Symbol",
                "Description",
                "DataType",
                "TickSize",
                "PointValue",
                "Decimals",
                "DefaultSpread",
            ]
        )
        for inst in instruments:
            sym = (
                inst.symbol
                if isinstance(inst, SymbolInfo)
                else str(inst.get("symbol", ""))
            )
            desc = (
                inst.description
                if isinstance(inst, SymbolInfo)
                else str(inst.get("description", ""))
            )
            dtype = (
                inst.data_type
                if isinstance(inst, SymbolInfo)
                else str(inst.get("data_type", "Forex"))
            )
            tick = (
                inst.tick_size
                if isinstance(inst, SymbolInfo)
                else float(inst.get("tick_size", 0.0001))
            )
            point = (
                inst.point_value
                if isinstance(inst, SymbolInfo)
                else float(inst.get("point_value", 100000.0))
            )
            dec = (
                inst.decimals
                if isinstance(inst, SymbolInfo)
                else int(inst.get("decimals", 5))
            )
            spread = (
                inst.default_spread
                if isinstance(inst, SymbolInfo)
                else float(inst.get("default_spread", 1.0))
            )
            writer.writerow([sym, desc, dtype, tick, point, dec, spread])
        return buf.getvalue().strip()

    @classmethod
    def format_output(cls, data: Mapping[str, Any]) -> str:
        """Format data into human-readable terminal output."""
        logger.debug("Formatting instruments output")
        lines = [f"{k}: {v}" for k, v in data.items()]
        return "\n".join(lines)


if __name__ == "__main__":
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
        db_file = Path(temp_dir) / "test_instruments.db"
        with resolve_connection(db_file) as conn:
            create_schema(conn)

        service = Instruments(db_path=db_file)

        # 1. add()
        service.add(
            {
                "symbol": "EURUSD",
                "description": "Euro vs US Dollar",
                "data_type": "Forex",
                "tick_size": 0.00001,
                "point_value": 100000.0,
                "decimals": 5,
                "default_spread": 1.2,
            }
        )
        service.add(
            {
                "symbol": "GBPUSD",
                "description": "British Pound vs US Dollar",
                "data_type": "Forex",
                "tick_size": 0.00001,
                "point_value": 100000.0,
                "decimals": 5,
                "default_spread": 1.5,
            }
        )

        # 2. view()
        items = service.view()
        print(InstrumentsCLI.format_instruments_table(items))

        # 3. edit()
        edited = service.edit("EURUSD", {"default_spread": 2.0})
        if isinstance(edited, dict):
            print(f"Edited EURUSD: spread={edited.get('default_spread')}")

        # 4. clone()
        cloned = service.clone("EURUSD", "EURUSD_PRO")
        print(f"Cloned instrument: {cloned.get('symbol')}")

        # 5. export()
        json_file = Path(temp_dir) / "exported_instruments.json"
        service.export(json_file)
        print(f"Exported to {json_file}")

        # 6. delete()
        service.delete("EURUSD_PRO")
        print("Deleted EURUSD_PRO")

        # 7. import_()
        service.import_(json_file)
        print("Re-imported instruments")

        # CLI dispatch demo
        cli_res = InstrumentsCLI.dispatch(["action=list", "csv=true"], service=service)
        print(f"CLI list output:\n{cli_res['rendered']}")
