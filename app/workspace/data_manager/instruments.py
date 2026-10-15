"""Instrument specifications, trading cost models, and symbol catalogs.

Description:
    Provides domain logic for financial instrument specifications (`InstrumentInfo`),
    tick size/step rounding, contract sizing, commission and swap models, symbol
    aliases, and StrategyQuant X XML import/export. Governs the `datamgr_instruments`
    relational catalog and `host_entities` alias mappings with zero direct `sqlite3`
    calls and non-silent requirement logging.

Purpose:
    FEAT-DATAMGR-INSTRUMENTS: Instrument catalog and financial specification.

Key Capabilities:
    - FR-DATAMGR-INSTRUMENTS-MODEL: Specification model with tick rounding and
      SymbolSpec conversion.
      Associated: `InstrumentInfo.round_to_tick_size()`,
      `InstrumentInfo.to_symbol_spec()`
      Logging: Emits DEBUG on price rounding and symbol conversion.
    - FR-DATAMGR-INSTRUMENTS-CATALOG-CRUD: Manage instrument records in
      `datamgr_instruments`.
      Associated: `InstrumentsCatalogService.list_instruments()`,
      `InstrumentsCatalogService.save_instrument()`,
      `InstrumentsCatalogService.delete_instrument()`
      Logging: Emits INFO on creation, update, cloning, mass edit, and deletion.
    - FR-DATAMGR-INSTRUMENTS-XML-AND-ALIASES: SQX XML import/export and alias
      management.
      Associated: `InstrumentsCatalogService.export_xml()`,
      `InstrumentsCatalogService.import_xml()`,
      `InstrumentsCatalogService.save_alias()`
      Logging: Emits INFO on XML import/export and alias mutation.

Python API Usage:
    ```python
    from app.workspace.data_manager.instruments import InstrumentsCatalogService

    service = InstrumentsCatalogService()
    instrument = service.get_instrument("EURUSD")
    if instrument:
        rounded_price = instrument.round_to_tick_size(1.085427)
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
from app.services.trading import SymbolSpec
from app.workspace.data_manager.log import DataManagerLogService

__all__ = [
    "InstrumentAliasRecord",
    "InstrumentInfo",
    "InstrumentsCatalogService",
]

logger = get_logger(__name__)

INSTRUMENTS_MODEL_FR = "FR-DATAMGR-INSTRUMENTS-MODEL"
CATALOG_CRUD_FR = "FR-DATAMGR-INSTRUMENTS-CATALOG-CRUD"
XML_ALIASES_FR = "FR-DATAMGR-INSTRUMENTS-XML-AND-ALIASES"


@dataclass
class InstrumentInfo:
    """Represents a financial instrument's specification and trading costs."""

    id: int | None = None
    symbol: str = ""
    connection: str = ""
    broker_id: int = 0
    description: str = ""
    tick_size: float = 0.00001
    tick_step: float = 0.00001
    tick_value_in_money: float = 10.0
    point_value: float = 100000.0
    decimals: int = 5
    default_spread: float = 0.0001
    default_slippage: float = 0.0
    min_volume: float = 0.01
    max_volume: float = 100.0
    lot_step: float = 0.01
    margin_rate: float = 0.05
    swap_long: float = 0.0
    swap_short: float = 0.0
    swap_3day_day: int = 3
    commissions: str = "0.0"
    data_type: str = "Forex"
    alias: str = ""
    exchange: str = ""
    country: str = ""
    sector: str = ""
    min_distance: float = 0.0
    order_size_multiplier: float = 1.0
    order_size_step: float = 0.0
    cot: str | None = None
    created_at_utc: str = ""
    updated_at_utc: str = ""

    def round_to_tick_size(self, price: float) -> float:
        """Round a price to the instrument's minimum tick size."""
        step = self.tick_size if self.tick_size > 0.0 else 0.0001
        rounded = round(round(price / step) * step, self.decimals)
        logger.debug(
            "%s: Rounded price %f to %f (step=%f)",
            INSTRUMENTS_MODEL_FR,
            price,
            rounded,
            step,
            extra={
                "fr_id": INSTRUMENTS_MODEL_FR,
                "price": price,
                "rounded": rounded,
            },
        )
        return rounded

    def to_symbol_spec(self) -> SymbolSpec:
        """Convert specification to the Tier 2 SymbolSpec domain model."""
        logger.debug(
            "%s: Converting instrument %s to SymbolSpec",
            INSTRUMENTS_MODEL_FR,
            self.symbol,
            extra={"fr_id": INSTRUMENTS_MODEL_FR, "symbol": self.symbol},
        )
        return SymbolSpec(
            name=self.symbol,
            digits=self.decimals,
            point=self.tick_size,
            trade_tick_size=self.tick_size,
            trade_tick_value=self.tick_value_in_money,
            trade_contract_size=self.point_value,
            volume_min=self.min_volume,
            volume_max=self.max_volume,
            volume_step=self.lot_step,
            margin_initial=self.margin_rate,
            swap_long=self.swap_long,
            swap_short=self.swap_short,
            swap_rollover3days=self.swap_3day_day,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert specification to dictionary representation."""
        return {
            "id": self.id,
            "symbol": self.symbol,
            "connection": self.connection,
            "broker_id": self.broker_id,
            "description": self.description,
            "tick_size": self.tick_size,
            "tick_step": self.tick_step,
            "tick_value_in_money": self.tick_value_in_money,
            "point_value": self.point_value,
            "decimals": self.decimals,
            "default_spread": self.default_spread,
            "default_slippage": self.default_slippage,
            "min_volume": self.min_volume,
            "max_volume": self.max_volume,
            "lot_step": self.lot_step,
            "margin_rate": self.margin_rate,
            "swap_long": self.swap_long,
            "swap_short": self.swap_short,
            "swap_3day_day": self.swap_3day_day,
            "commissions": self.commissions,
            "data_type": self.data_type,
            "alias": self.alias,
            "exchange": self.exchange,
            "country": self.country,
            "sector": self.sector,
            "min_distance": self.min_distance,
            "order_size_multiplier": self.order_size_multiplier,
            "order_size_step": self.order_size_step,
            "cot": self.cot,
            "created_at_utc": self.created_at_utc,
            "updated_at_utc": self.updated_at_utc,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> InstrumentInfo:
        """Construct InstrumentInfo from row or dictionary data."""
        return cls(
            id=data.get("id"),
            symbol=str(data.get("symbol", "")),
            connection=str(data.get("connection", "")),
            broker_id=int(data.get("broker_id", -1)),
            description=str(data.get("description", "")),
            tick_size=float(data.get("tick_size", 0.0001)),
            tick_step=float(data.get("tick_step", 0.00001)),
            tick_value_in_money=float(data.get("tick_value_in_money", 10.0)),
            point_value=float(data.get("point_value", 100000.0)),
            decimals=int(data.get("decimals", 5)),
            default_spread=float(data.get("default_spread", 1.0)),
            default_slippage=float(data.get("default_slippage", 0.0)),
            min_volume=float(data.get("min_volume", 0.01)),
            max_volume=float(data.get("max_volume", 100.0)),
            lot_step=float(data.get("lot_step", 0.01)),
            margin_rate=float(data.get("margin_rate", 0.05)),
            swap_long=float(data.get("swap_long", 0.0)),
            swap_short=float(data.get("swap_short", 0.0)),
            swap_3day_day=int(data.get("swap_3day_day", 3)),
            commissions=str(data.get("commissions", "0.0")),
            data_type=str(data.get("data_type", "Forex")),
            alias=str(data.get("alias", "")),
            exchange=str(data.get("exchange", "")),
            country=str(data.get("country", "")),
            sector=str(data.get("sector", "")),
            min_distance=float(data.get("min_distance", 0.0)),
            order_size_multiplier=float(data.get("order_size_multiplier", 1.0)),
            order_size_step=float(data.get("order_size_step", 0.01)),
            cot=str(data["cot"]) if data.get("cot") is not None else None,
            created_at_utc=str(data.get("created_at_utc", "")),
            updated_at_utc=str(data.get("updated_at_utc", "")),
        )


@dataclass(frozen=True)
class InstrumentAliasRecord:
    """Represents a symbol alias mapping."""

    alias: str
    instrument: str
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert alias record to dictionary representation."""
        return {
            "alias": self.alias,
            "instrument": self.instrument,
            "description": self.description,
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


class InstrumentsCatalogService:
    """Service governing instrument specifications, CRUD, and XML transfer."""

    def __init__(
        self,
        db_path: Path | str | None = None,
        log_service: DataManagerLogService | None = None,
    ) -> None:
        """Initialize instruments service with optional DB path and logger."""
        self.db_path = Path(db_path) if db_path is not None else None
        self.log_service = log_service

    def ensure_default_instruments(self) -> int:
        """Seed default canonical instruments if catalog is empty."""
        with resolve_connection(self.db_path) as conn:
            existing = count_rows(conn, "datamgr_instruments")
            if existing > 0:
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
            CATALOG_CRUD_FR,
            seeded,
            extra={"fr_id": CATALOG_CRUD_FR, "seeded": seeded},
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
        if not rows:
            return None
        return InstrumentInfo.from_dict(rows[0])

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
            CATALOG_CRUD_FR,
            result.symbol,
            result.id,
            extra={
                "fr_id": CATALOG_CRUD_FR,
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
        return self.save_instrument(data)

    def delete_instrument(self, symbol: str) -> bool:
        """Delete an instrument specification by symbol."""
        inst = self.get_instrument(symbol)
        if inst is None or inst.id is None:
            return False

        with resolve_connection(self.db_path) as conn:
            deleted = delete_row_by_pk(conn, "datamgr_instruments", {"id": inst.id}) > 0

        logger.info(
            "%s: Deleted instrument symbol=%s deleted=%s",
            CATALOG_CRUD_FR,
            symbol,
            deleted,
            extra={
                "fr_id": CATALOG_CRUD_FR,
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
        return self.save_instrument(data)

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
            CATALOG_CRUD_FR,
            count,
            extra={"fr_id": CATALOG_CRUD_FR, "count": count},
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
            CATALOG_CRUD_FR,
            deleted_count,
            extra={"fr_id": CATALOG_CRUD_FR, "deleted_count": deleted_count},
        )
        return {"deleted_count": deleted_count, "is_async": False}

    def export_xml(self, symbols: Sequence[str] | None = None) -> str:
        """Export instrument specifications to StrategyQuant X XML format."""
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
            "%s: Exported %d instruments to SQX XML",
            XML_ALIASES_FR,
            len(root),
            extra={"fr_id": XML_ALIASES_FR, "count": len(root)},
        )
        return str(xml_str)

    def import_xml(
        self, xml_content: str, conflict_policy: str = "overwrite_all"
    ) -> dict[str, Any]:
        """Safely import SQX Instruments XML using defusedxml."""
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
            XML_ALIASES_FR,
            imported,
            overwritten,
            skipped,
            extra={
                "fr_id": XML_ALIASES_FR,
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
                    XML_ALIASES_FR,
                    exc,
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
            XML_ALIASES_FR,
            clean_alias,
            clean_inst,
            extra={
                "fr_id": XML_ALIASES_FR,
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
            XML_ALIASES_FR,
            clean_alias,
            removed,
            extra={
                "fr_id": XML_ALIASES_FR,
                "alias": clean_alias,
                "removed": removed,
            },
        )
        return removed


def main() -> None:
    """Execute real-usage demonstration of InstrumentsCatalogService."""
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
        db_file = Path(temp_dir) / "test_instruments.db"
        with resolve_connection(db_file) as conn:
            create_schema(conn)

        service = InstrumentsCatalogService(db_path=db_file)
        seeded = service.ensure_default_instruments()
        print(f"Seeded {seeded} instruments")

        eur = service.get_instrument("EURUSD")
        if eur:
            print(f"Loaded EURUSD: decimals={eur.decimals}, tick={eur.tick_size}")
            rounded = eur.round_to_tick_size(1.085427)
            print(f"EURUSD rounded price 1.085427 -> {rounded}")
            spec = eur.to_symbol_spec()
            print(f"Generated SymbolSpec: {spec.name} contract={spec.contract_size}")

        cloned = service.clone_instrument("EURUSD", "EURUSD_ECN")
        print(f"Cloned instrument: {cloned.symbol}")

        alias = service.save_alias("EUR.USD", "EURUSD", "Broker symbol format")
        print(f"Saved alias: {alias.alias} -> {alias.instrument}")

        xml_out = service.export_xml(["EURUSD", "EURUSD_ECN"])
        print(f"Exported XML snippet:\n{xml_out[:180]}...")


if __name__ == "__main__":
    main()
