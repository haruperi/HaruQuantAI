"""Instrument specifications, financial attributes, and symbol catalog management.

Description:
    Provides domain logic for financial instrument specifications (`InstrumentInfo`),
    tick size/step rounding, contract sizing, commission and swap models, symbol
    aliases, and standard XML specification import/export. Governs the
    `datamgr_instruments` relational catalog and `host_entities` alias mappings with
    zero direct `sqlite3` calls and non-silent requirement logging.

Purpose:
    FEAT-DATAMGR-INSTRUMENTS: Instrument catalog and financial specification.

Key Capabilities:
    - FR-DATAMGR-INSTRUMENTS-SEED: Seed default canonical financial instruments.
      Associated: `Instruments.ensure_default_instruments()`
      Logging: Emits INFO on seeded instrument count.
    - FR-DATAMGR-INSTRUMENTS-LIST: List instrument specifications matching criteria.
      Associated: `Instruments.list_instruments()`
      Logging: Emits INFO on listed count and query parameters.
    - FR-DATAMGR-INSTRUMENTS-GET: Retrieve specification details by instrument symbol.
      Associated: `Instruments.get_instrument()`
      Logging: Emits DEBUG on retrieval outcome.
    - FR-DATAMGR-INSTRUMENTS-SAVE: Create or upsert an instrument specification.
      Associated: `Instruments.save_instrument()`
      Logging: Emits INFO on saved instrument symbol and id.
    - FR-DATAMGR-INSTRUMENTS-UPDATE: Update attributes of an existing instrument.
      Associated: `Instruments.update_instrument()`
      Logging: Emits INFO on updated instrument symbol.
    - FR-DATAMGR-INSTRUMENTS-DELETE: Delete an instrument specification by symbol.
      Associated: `Instruments.delete_instrument()`
      Logging: Emits INFO on deleted instrument symbol and status.
    - FR-DATAMGR-INSTRUMENTS-CLONE: Duplicate an instrument under a new target symbol.
      Associated: `Instruments.clone_instrument()`
      Logging: Emits INFO on source and cloned symbol names.
    - FR-DATAMGR-INSTRUMENTS-MASS-EDIT: Apply batch field updates across instruments.
      Associated: `Instruments.mass_edit_instruments()`
      Logging: Emits INFO on mass-edited count.
    - FR-DATAMGR-INSTRUMENTS-MASS-DELETE: Delete a collection of instruments by symbol.
      Associated: `Instruments.mass_delete_instruments()`
      Logging: Emits INFO on deleted instrument count.
    - FR-DATAMGR-INSTRUMENTS-EXPORT-XML: Export specifications to standard XML format.
      Associated: `Instruments.export_xml()`
      Logging: Emits INFO on exported instrument count.
    - FR-DATAMGR-INSTRUMENTS-IMPORT-XML: Parse and import specifications from XML.
      Associated: `Instruments.import_xml()`
      Logging: Emits INFO on imported, overwritten, and skipped counts.
    - FR-DATAMGR-INSTRUMENTS-LIST-ALIASES: List all registered symbol alias mappings.
      Associated: `Instruments.list_aliases()`
      Logging: Emits INFO on listed alias count.
    - FR-DATAMGR-INSTRUMENTS-SAVE-ALIAS: Create or update a symbol alias mapping.
      Associated: `Instruments.save_alias()`
      Logging: Emits INFO on saved alias and target instrument.
    - FR-DATAMGR-INSTRUMENTS-DELETE-ALIAS: Remove a symbol alias mapping.
      Associated: `Instruments.delete_alias()`
      Logging: Emits INFO on deleted alias name and removal status.

Python API Usage:
    ```python
    from app.workspace.data_manager.instruments import Instruments, InstrumentsCLI

    service = Instruments()
    instruments = service.list_instruments()
    print(InstrumentsCLI.format_instruments_table(instruments))
    ```

CLI Usage:
    ```bash
    uv run python -m app.workspace.data_manager.instruments
    ```
"""

from __future__ import annotations

import json
import tempfile
import xml.etree.ElementTree as ET
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import defusedxml.ElementTree as DefusedET  # type: ignore[import-untyped]
from app.host.logging import get_logger
from app.host.persistence.create import create_schema, insert_row
from app.host.persistence.delete import delete_row_by_pk, delete_rows
from app.host.persistence.read import count_rows, read_rows, resolve_connection
from app.host.persistence.update import update_row_by_pk

from ._common import InstrumentAliasRecord, InstrumentInfo
from .log import DataManagerLogService

__all__ = [
    "Instruments",
    "InstrumentsCLI",
]

logger = get_logger(__name__)

SEED_FR = "FR-DATAMGR-INSTRUMENTS-SEED"
LIST_FR = "FR-DATAMGR-INSTRUMENTS-LIST"
GET_FR = "FR-DATAMGR-INSTRUMENTS-GET"
SAVE_FR = "FR-DATAMGR-INSTRUMENTS-SAVE"
UPDATE_FR = "FR-DATAMGR-INSTRUMENTS-UPDATE"
DELETE_FR = "FR-DATAMGR-INSTRUMENTS-DELETE"
CLONE_FR = "FR-DATAMGR-INSTRUMENTS-CLONE"
MASS_EDIT_FR = "FR-DATAMGR-INSTRUMENTS-MASS-EDIT"
MASS_DELETE_FR = "FR-DATAMGR-INSTRUMENTS-MASS-DELETE"
EXPORT_XML_FR = "FR-DATAMGR-INSTRUMENTS-EXPORT-XML"
IMPORT_XML_FR = "FR-DATAMGR-INSTRUMENTS-IMPORT-XML"
LIST_ALIASES_FR = "FR-DATAMGR-INSTRUMENTS-LIST-ALIASES"
SAVE_ALIAS_FR = "FR-DATAMGR-INSTRUMENTS-SAVE-ALIAS"
DELETE_ALIAS_FR = "FR-DATAMGR-INSTRUMENTS-DELETE-ALIAS"


@dataclass(frozen=True)
class _Config:
    """Internal module configuration and execution parameters."""

    db_path: Path | None = None
    default_data_type: str = "Forex"

    def to_dict(self) -> dict[str, Any]:
        """Convert internal config or metrics to standard dictionary."""
        return {
            "db_path": str(self.db_path) if self.db_path else None,
            "default_data_type": self.default_data_type,
        }


_DEFAULT_SEEDED_INSTRUMENTS: tuple[dict[str, Any], ...] = (
    {
        "symbol": "EURUSD",
        "description": "Euro vs US Dollar",
        "data_type": "Forex",
        "tick_size": 0.00001,
        "tick_step": 0.00001,
        "tick_value_in_money": 10.0,
        "point_value": 100000.0,
        "decimals": 5,
        "default_spread": 1.2,
        "margin_rate": 0.033,
    },
    {
        "symbol": "GBPUSD",
        "description": "British Pound vs US Dollar",
        "data_type": "Forex",
        "tick_size": 0.00001,
        "tick_step": 0.00001,
        "tick_value_in_money": 10.0,
        "point_value": 100000.0,
        "decimals": 5,
        "default_spread": 1.5,
        "margin_rate": 0.033,
    },
    {
        "symbol": "USDJPY",
        "description": "US Dollar vs Japanese Yen",
        "data_type": "Forex",
        "tick_size": 0.001,
        "tick_step": 0.001,
        "tick_value_in_money": 9.1,
        "point_value": 100000.0,
        "decimals": 3,
        "default_spread": 1.4,
        "margin_rate": 0.033,
    },
    {
        "symbol": "XAUUSD",
        "description": "Gold vs US Dollar",
        "data_type": "Metals",
        "tick_size": 0.01,
        "tick_step": 0.01,
        "tick_value_in_money": 1.0,
        "point_value": 100.0,
        "decimals": 2,
        "default_spread": 2.5,
        "margin_rate": 0.05,
    },
    {
        "symbol": "SPY",
        "description": "SPDR S&P 500 ETF Trust",
        "data_type": "Equities",
        "tick_size": 0.01,
        "tick_step": 0.01,
        "tick_value_in_money": 1.0,
        "point_value": 1.0,
        "decimals": 2,
        "default_spread": 1.0,
        "margin_rate": 0.20,
    },
    {
        "symbol": "NQ",
        "description": "E-mini NASDAQ 100 Futures",
        "data_type": "Futures",
        "tick_size": 0.25,
        "tick_step": 0.25,
        "tick_value_in_money": 5.0,
        "point_value": 20.0,
        "decimals": 2,
        "default_spread": 0.5,
        "margin_rate": 0.10,
    },
    {
        "symbol": "BTCUSDT",
        "description": "Bitcoin vs Tether USD",
        "data_type": "Crypto",
        "tick_size": 0.01,
        "tick_step": 0.01,
        "tick_value_in_money": 1.0,
        "point_value": 1.0,
        "decimals": 2,
        "default_spread": 5.0,
        "margin_rate": 0.50,
    },
)


class Instruments:
    """Service governing instrument specifications, CRUD, and XML transfer."""

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
        """Return configured SQLite database file path."""
        return self._config.db_path

    def ensure_default_instruments(self) -> int:
        """Seed default canonical instruments if catalog is empty."""
        with resolve_connection(self.db_path) as conn:
            existing = count_rows(conn, "datamgr_instruments")
            if existing > 0:
                logger.debug(
                    "%s: Catalog already contains %d instruments",
                    SEED_FR,
                    existing,
                    extra={"fr_id": SEED_FR, "existing": existing},
                )
                return 0

            seeded = 0
            now_iso = datetime.now(UTC).isoformat()
            for item in _DEFAULT_SEEDED_INSTRUMENTS:
                data = dict(item)
                data["created_at_utc"] = now_iso
                data["updated_at_utc"] = now_iso
                insert_row(conn, "datamgr_instruments", data)
                seeded += 1

        logger.info(
            "%s: Seeded %d default instruments",
            SEED_FR,
            seeded,
            extra={"fr_id": SEED_FR, "seeded": seeded},
        )
        return seeded

    def list_instruments(
        self,
        connection: str | None = None,
        data_type: str | None = None,
        broker_id: int | None = None,
        search: str | None = None,
    ) -> list[InstrumentInfo]:
        """List instruments matching optional filter criteria."""
        where: dict[str, Any] = {}
        if connection:
            where["connection"] = connection.strip()
        if data_type:
            where["data_type"] = data_type.strip()
        if broker_id is not None and broker_id >= 0:
            where["broker_id"] = broker_id

        with resolve_connection(self.db_path) as conn:
            rows = read_rows(
                conn,
                "datamgr_instruments",
                where=where or None,
                order_by="symbol ASC",
            )

        results: list[InstrumentInfo] = []
        q = search.strip().lower() if search else None
        for r in rows:
            inst = InstrumentInfo.from_dict(r)
            if q and q not in inst.symbol.lower() and q not in inst.description.lower():
                continue
            results.append(inst)

        logger.info(
            "%s: Listed %d instruments",
            LIST_FR,
            len(results),
            extra={
                "fr_id": LIST_FR,
                "count": len(results),
                "connection": connection,
                "data_type": data_type,
            },
        )
        return results

    def get_instrument(self, symbol: str) -> InstrumentInfo | None:
        """Retrieve instrument specification by symbol."""
        clean = symbol.strip().upper()
        with resolve_connection(self.db_path) as conn:
            rows = read_rows(
                conn,
                "datamgr_instruments",
                where={"symbol": clean},
                limit=1,
            )
        result = InstrumentInfo.from_dict(rows[0]) if rows else None
        logger.debug(
            "%s: Retrieved instrument symbol=%s found=%s",
            GET_FR,
            clean,
            result is not None,
            extra={"fr_id": GET_FR, "symbol": clean, "found": result is not None},
        )
        return result

    def save_instrument(self, payload: Mapping[str, Any]) -> InstrumentInfo:
        """Create or upsert an instrument specification."""
        clean_symbol = str(payload.get("symbol", "")).strip().upper()
        if not clean_symbol:
            raise ValueError("Instrument symbol is required.")

        now_iso = datetime.now(UTC).isoformat()
        existing = self.get_instrument(clean_symbol)

        if existing is not None:
            merged = existing.to_dict()
            merged.update(payload)
            row_data = merged
            row_data["id"] = existing.id
        else:
            row_data = dict(payload)
            row_data.pop("id", None)
            row_data["created_at_utc"] = now_iso

        row_data["symbol"] = clean_symbol
        row_data["updated_at_utc"] = now_iso

        with resolve_connection(self.db_path) as conn:
            if existing is not None and existing.id is not None:
                update_row_by_pk(
                    conn, "datamgr_instruments", {"id": existing.id}, row_data
                )
            else:
                inserted = insert_row(conn, "datamgr_instruments", row_data)
                row_data["id"] = int(inserted)

        reloaded = self.get_instrument(clean_symbol)
        result = (
            reloaded if reloaded is not None else InstrumentInfo.from_dict(row_data)
        )
        logger.info(
            "%s: Saved instrument symbol=%s id=%s",
            SAVE_FR,
            result.symbol,
            result.id,
            extra={
                "fr_id": SAVE_FR,
                "symbol": result.symbol,
                "id": result.id,
            },
        )
        return result

    def update_instrument(
        self, symbol: str, updates: Mapping[str, Any]
    ) -> InstrumentInfo:
        """Update an existing instrument specification."""
        inst = self.get_instrument(symbol)
        if inst is None:
            raise KeyError(f"Instrument '{symbol}' not found.")

        data = inst.to_dict()
        data.update(updates)
        saved = self.save_instrument(data)
        logger.info(
            "%s: Updated instrument symbol=%s",
            UPDATE_FR,
            symbol,
            extra={"fr_id": UPDATE_FR, "symbol": symbol},
        )
        return saved

    def delete_instrument(self, symbol: str) -> bool:
        """Delete an instrument specification by symbol."""
        inst = self.get_instrument(symbol)
        if inst is None or inst.id is None:
            logger.debug(
                "%s: Instrument %s not found for deletion",
                DELETE_FR,
                symbol,
                extra={"fr_id": DELETE_FR, "symbol": symbol},
            )
            return False

        with resolve_connection(self.db_path) as conn:
            deleted = delete_row_by_pk(conn, "datamgr_instruments", {"id": inst.id}) > 0

        logger.info(
            "%s: Deleted instrument symbol=%s deleted=%s",
            DELETE_FR,
            symbol,
            deleted,
            extra={
                "fr_id": DELETE_FR,
                "symbol": symbol,
                "deleted": deleted,
            },
        )
        return deleted

    def clone_instrument(
        self,
        symbol: str,
        clone_name: str,
        broker_id: int = -1,
        broker_postfix: str = "",
    ) -> InstrumentInfo:
        """Clone an existing instrument specification with a new symbol name."""
        source = self.get_instrument(symbol)
        if source is None:
            raise KeyError(f"Source instrument '{symbol}' not found.")

        target_name = (
            clone_name.strip().upper()
            if clone_name
            else f"{source.symbol}{broker_postfix}".strip().upper()
        )
        data = source.to_dict()
        data["id"] = None
        data["symbol"] = target_name
        data["broker_id"] = broker_id
        cloned = self.save_instrument(data)
        logger.info(
            "%s: Cloned instrument %s -> %s",
            CLONE_FR,
            symbol,
            target_name,
            extra={"fr_id": CLONE_FR, "source": symbol, "target": target_name},
        )
        return cloned

    def mass_edit_instruments(
        self,
        symbols: Sequence[str],
        updates: Mapping[str, Any],
        change_flags: Mapping[str, bool] | None = None,
    ) -> int:
        """Mass-edit multiple instrument records with filtered field updates."""
        filtered_updates = {
            k: v
            for k, v in updates.items()
            if (change_flags is None or change_flags.get(k, True))
            and k not in ("id", "symbol", "created_at_utc")
        }

        if not filtered_updates or not symbols:
            return 0

        filtered_updates["updated_at_utc"] = datetime.now(UTC).isoformat()
        count = 0
        for sym in symbols:
            inst = self.get_instrument(sym)
            if inst is not None and inst.id is not None:
                with resolve_connection(self.db_path) as conn:
                    update_row_by_pk(
                        conn,
                        "datamgr_instruments",
                        {"id": inst.id},
                        filtered_updates,
                    )
                count += 1

        logger.info(
            "%s: Mass-edited %d instruments",
            MASS_EDIT_FR,
            count,
            extra={"fr_id": MASS_EDIT_FR, "count": count},
        )
        return count

    def mass_delete_instruments(self, symbols: Sequence[str]) -> dict[str, Any]:
        """Delete multiple instruments by symbol."""
        deleted_count = 0
        for sym in symbols:
            if self.delete_instrument(sym):
                deleted_count += 1

        logger.info(
            "%s: Mass-deleted %d instruments",
            MASS_DELETE_FR,
            deleted_count,
            extra={"fr_id": MASS_DELETE_FR, "deleted_count": deleted_count},
        )
        return {"deleted_count": deleted_count, "is_async": False}

    def export_xml(self, symbols: Sequence[str] | None = None) -> str:
        """Export instrument specifications to XML specification format."""
        all_inst = self.list_instruments()
        target_symbols = {s.strip().upper() for s in symbols} if symbols else None

        root = ET.Element("Instruments")
        for inst in all_inst:
            if target_symbols and inst.symbol not in target_symbols:
                continue
            item = ET.SubElement(root, "Instrument")
            item.set("symbol", inst.symbol)
            item.set("description", inst.description)
            item.set("dataType", inst.data_type)
            item.set("tickSize", str(inst.tick_size))
            item.set("tickStep", str(inst.tick_step))
            item.set("pointValue", str(inst.point_value))
            item.set("tickValueInMoney", str(inst.tick_value_in_money))
            item.set("decimals", str(inst.decimals))
            item.set("defaultSpread", str(inst.default_spread))
            item.set("defaultSlippage", str(inst.default_slippage))
            item.set("minVolume", str(inst.min_volume))
            item.set("maxVolume", str(inst.max_volume))
            item.set("lotStep", str(inst.lot_step))
            item.set("marginRate", str(inst.margin_rate))
            item.set("swapLong", str(inst.swap_long))
            item.set("swapShort", str(inst.swap_short))
            item.set("commissions", inst.commissions)
            item.set("alias", inst.alias)

        xml_str = ET.tostring(root, encoding="utf-8").decode("utf-8")
        logger.info(
            "%s: Exported %d instruments to XML",
            EXPORT_XML_FR,
            len(root),
            extra={"fr_id": EXPORT_XML_FR, "count": len(root)},
        )
        return str(xml_str)

    def import_xml(
        self, xml_content: str, conflict_policy: str = "overwrite_all"
    ) -> dict[str, Any]:
        """Safely import instruments XML using defusedxml."""
        root = DefusedET.fromstring(xml_content)
        imported = 0
        overwritten = 0
        skipped = 0
        symbols_list: list[str] = []

        for item in root.findall("Instrument"):
            symbol = item.get("symbol", "").strip().upper()
            if not symbol:
                continue

            existing = self.get_instrument(symbol)
            if existing and conflict_policy == "skip":
                skipped += 1
                continue

            payload: dict[str, Any] = {
                "symbol": symbol,
                "description": item.get("description", ""),
                "data_type": item.get("dataType", "Forex"),
                "tick_size": float(item.get("tickSize", 0.0001)),
                "tick_step": float(item.get("tickStep", 0.00001)),
                "point_value": float(item.get("pointValue", 100000.0)),
                "tick_value_in_money": float(item.get("tickValueInMoney", 10.0)),
                "decimals": int(item.get("decimals", 5)),
                "default_spread": float(item.get("defaultSpread", 1.0)),
                "default_slippage": float(item.get("defaultSlippage", 0.0)),
                "min_volume": float(item.get("minVolume", 0.01)),
                "max_volume": float(item.get("maxVolume", 100.0)),
                "lot_step": float(item.get("lotStep", 0.01)),
                "margin_rate": float(item.get("marginRate", 0.05)),
                "swap_long": float(item.get("swapLong", 0.0)),
                "swap_short": float(item.get("swapShort", 0.0)),
                "commissions": item.get("commissions", "0.0"),
                "alias": item.get("alias", ""),
            }
            self.save_instrument(payload)
            symbols_list.append(symbol)
            if existing:
                overwritten += 1
            else:
                imported += 1

        logger.info(
            "%s: Imported instruments XML (imported=%d, overwritten=%d, skipped=%d)",
            IMPORT_XML_FR,
            imported,
            overwritten,
            skipped,
            extra={
                "fr_id": IMPORT_XML_FR,
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

    def list_aliases(self) -> list[InstrumentAliasRecord]:
        """List all instrument symbol aliases stored in host_entities."""
        with resolve_connection(self.db_path) as conn:
            rows = read_rows(
                conn,
                "host_entities",
                where={"entity_type": "datamgr_instrument_alias"},
            )

        aliases: list[InstrumentAliasRecord] = []
        for r in rows:
            try:
                payload = json.loads(str(r.get("payload", "{}")))
                aliases.append(
                    InstrumentAliasRecord(
                        alias=str(r.get("entity_id", "")),
                        instrument=str(payload.get("instrument", "")),
                        description=str(payload.get("description", "")),
                    )
                )
            except (json.JSONDecodeError, TypeError, KeyError) as exc:
                logger.debug(
                    "%s: Skipping malformed alias record: %s",
                    LIST_ALIASES_FR,
                    exc,
                )

        logger.info(
            "%s: Listed %d instrument aliases",
            LIST_ALIASES_FR,
            len(aliases),
            extra={"fr_id": LIST_ALIASES_FR, "count": len(aliases)},
        )
        return aliases

    def save_alias(
        self, alias: str, instrument: str, description: str = ""
    ) -> InstrumentAliasRecord:
        """Create or update a symbol alias mapping in host_entities."""
        clean_alias = alias.strip().upper()
        clean_inst = instrument.strip().upper()
        now_iso = datetime.now(UTC).isoformat()
        payload_json = json.dumps(
            {"instrument": clean_inst, "description": description}
        )

        with resolve_connection(self.db_path) as conn:
            delete_rows(
                conn,
                "host_entities",
                where={
                    "entity_id": clean_alias,
                    "entity_type": "datamgr_instrument_alias",
                },
            )
            insert_row(
                conn,
                "host_entities",
                {
                    "entity_id": clean_alias,
                    "entity_type": "datamgr_instrument_alias",
                    "scope": "workspace",
                    "payload": payload_json,
                    "revision": 1,
                    "created_at_utc": now_iso,
                    "updated_at_utc": now_iso,
                },
            )

        rec = InstrumentAliasRecord(
            alias=clean_alias, instrument=clean_inst, description=description
        )
        logger.info(
            "%s: Saved symbol alias %s -> %s",
            SAVE_ALIAS_FR,
            clean_alias,
            clean_inst,
            extra={
                "fr_id": SAVE_ALIAS_FR,
                "alias": clean_alias,
                "instrument": clean_inst,
            },
        )
        return rec

    def delete_alias(self, alias: str) -> bool:
        """Delete a symbol alias from host_entities."""
        clean_alias = alias.strip().upper()
        with resolve_connection(self.db_path) as conn:
            count = delete_rows(
                conn,
                "host_entities",
                where={
                    "entity_id": clean_alias,
                    "entity_type": "datamgr_instrument_alias",
                },
            )
        removed = count > 0
        logger.info(
            "%s: Deleted alias %s removed=%s",
            DELETE_ALIAS_FR,
            clean_alias,
            removed,
            extra={
                "fr_id": DELETE_ALIAS_FR,
                "alias": clean_alias,
                "removed": removed,
            },
        )
        return removed


class InstrumentsCLI:
    """Headless CLI formatter and table presentation for Data Manager instruments."""

    MAX_DESC_LEN: int = 28
    TRUNCATE_LEN: int = 26

    @classmethod
    def format_instruments_table(
        cls,
        instruments: Sequence[InstrumentInfo],
    ) -> str:
        """Format ASCII table of instrument specification records."""
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
            desc = (
                inst.description[: cls.TRUNCATE_LEN] + ".."
                if len(inst.description) > cls.MAX_DESC_LEN
                else inst.description
            )
            lines.append(
                header.format(
                    sym=inst.symbol,
                    desc=desc,
                    dtype=inst.data_type,
                    tick=f"{inst.tick_size:.5f}",
                    point=f"{inst.point_value:.1f}",
                    dec=str(inst.decimals),
                    spread=f"{inst.default_spread:.1f}",
                )
            )
        return "\n".join(lines)

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
        seeded = service.ensure_default_instruments()
        print(f"Seeded {seeded} instruments")

        eur = service.get_instrument("EURUSD")
        if eur:
            print(f"Loaded EURUSD: decimals={eur.decimals}, tick={eur.tick_size}")
            rounded = eur.round_to_tick_size(1.085427)
            print(f"EURUSD rounded price 1.085427 -> {rounded}")
            spec = eur.to_symbol_info()
            print(
                f"Generated SymbolInfo: {spec.name} contract={spec.trade_contract_size}"
            )

        cloned = service.clone_instrument("EURUSD", "EURUSD_ECN")
        print(f"Cloned instrument: {cloned.symbol}")

        alias = service.save_alias("EUR.USD", "EURUSD", "Broker symbol format")
        print(f"Saved alias: {alias.alias} -> {alias.instrument}")

        xml_out = service.export_xml(["EURUSD", "EURUSD_ECN"])
        print(f"Exported XML snippet:\n{xml_out[:180]}...")

        insts = service.list_instruments()
        print(InstrumentsCLI.format_instruments_table(insts))
