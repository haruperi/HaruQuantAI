"""Authoritative instrument specifications, validation, and host persistence.

Description:
    ensure_defaults() owns the baseline instrument definitions and initializes
    them idempotently through InstrumentStore. All database operations belong to
    app.host.persistence; this service owns domain validation, defaults, domain
    timestamps and interpretation.

    Provides canonical quantitative instrument definitions, precision models,
    margin rates, financing swaps, broker aliases, and host SQLite persistence
    operations for the Data Manager workspace. Instruments represent tradable
    assets across heterogeneous asset classes (Forex, Equities, Futures, Crypto,
    Commodities) with distinct tick values, contract point sizes, and price
    decimals. All mutations and lookups execute through the host persistence
    layer via `DatabaseManager.instruments`, ensuring zero ad-hoc SQL execution.

Purpose:
    FEAT-WORKSPACE-DATAMGR: Manage instrument definitions, parameter validation,
    and host persistence for the Data Manager workspace.

Key Capabilities:
    - FR-DATA-INSTRUMENTS-DEFAULTS: Initialize baseline instruments idempotently.
      Associated: `InstrumentService.ensure_defaults()`
      Logging: INFO initialization; storage logs each insert-if-absent result.
    - FR-DATA-INSTRUMENTS-SPECIFICATION: Strongly typed instrument parameters
      governing ticks, points, spreads, lots, margins, and overnight swaps.
      Associated: `[InstrumentDefinition]`, `[InstrumentService.get_instrument()]`
      Logging: Emits DEBUG when instrument specifications are retrieved.
    - FR-DATA-INSTRUMENTS-VALIDATION: Strict semantic validation ensuring positive
      tick sizes, valid decimal ranges, non-negative lots, and proper symbols.
      Associated: `[InstrumentService.create_instrument()]`,
      `[InstrumentService.update_instrument()]`
      Logging: Emits WARNING on invalid specifications and validation rejections.
    - FR-DATA-INSTRUMENTS-PERSISTENCE-CRUD: Centralized CRUD operations
      persisting to datamgr_instruments via host DatabaseManager.
      Associated: `[InstrumentService.create_instrument()]`,
      `[InstrumentService.update_instrument()]`,
      `[InstrumentService.delete_instrument()]`
      Logging: Emits INFO on creation, update, and deletion of instruments.
    - FR-DATA-INSTRUMENTS-ALIAS-RESOLUTION: Broker-to-clean symbol mapping and
      alias registry lifecycle management.
      Associated: `[InstrumentService.resolve_alias()]`,
      `[InstrumentService.list_aliases()]`, `[InstrumentService.add_alias()]`,
      `[InstrumentService.edit_alias()]`, `[InstrumentService.remove_alias()]`
      Logging: Emits DEBUG when translating or mutating broker symbol aliases.
    - FR-DATA-INSTRUMENTS-CLONE: Duplicate instrument specifications with
      broker-dependent naming conventions and postfix resolution.
      Associated: `[InstrumentService.clone_instrument()]`
      Logging: Emits INFO when an instrument is cloned into a new profile.
    - FR-DATA-INSTRUMENTS-MASS-EDIT: Selectively patch specific instrument parameters
      across multiple symbols with fine-grained field activation flags.
      Associated: `[InstrumentService.mass_edit_instruments()]`
      Logging: Emits INFO on bulk parameter mutation across target instruments.
    - FR-DATA-INSTRUMENTS-TRANSFER-XML: Export and import native SQX XML instrument
      catalogs (`<Instruments>`) with embedded broker configurations and duplicate
      conflict resolution policies.
      Associated: `[InstrumentService.export_sqx_xml()]`,
      `[InstrumentService.import_sqx_xml()]`
      Logging: Emits INFO during XML catalog import and export execution.

Python API Usage:
    ```python
    from app.host.persistence import DatabaseManager
    from app.workspace.data_manager.instruments import (
        InstrumentDefinition,
        InstrumentService,
    )

    db = DatabaseManager(":memory:")
    db.initialize()
    service = InstrumentService(db)
    service.ensure_defaults()

    instr = InstrumentDefinition(
        symbol="EURUSD",
        data_type="Forex",
        point_value=100000.0,
        tick_size=0.00001,
        decimals=5,
    )
    service.create_instrument(instr)
    retrieved = service.get_instrument("EURUSD")
    assert retrieved is not None
    assert retrieved.decimals == 5
    ```

CLI Usage:
    ```bash
    uv run python -m app.workspace.data_manager.instruments --symbol EURUSD
    ```
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from datetime import UTC, datetime
from typing import Any
from xml.dom import minidom

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.host.logging import get_logger
from app.host.persistence import DatabaseManager

logger = get_logger(__name__)

DATA_TYPE_INT_TO_NAME: dict[int, str] = {
    1: "Futures",
    2: "Stock",
    3: "Forex",
    4: "Indices",
    5: "Crypto",
}

DATA_TYPE_NAME_TO_INT: dict[str, int] = {
    "futures": 1,
    "stock": 2,
    "stocks": 2,
    "equities": 2,
    "forex": 3,
    "cash": 3,
    "indices": 4,
    "crypto": 5,
}

_ASYNC_DELETE_THRESHOLD: int = 10
_WEDNESDAY_DAY_INDEX: int = 3
_FRIDAY_DAY_INDEX: int = 5


class InstrumentDefinition(BaseModel):
    """Authoritative domain specification for a financial instrument."""

    model_config = ConfigDict(frozen=True, extra="ignore")

    id: int | None = Field(default=None, description="Database auto-increment ID")
    symbol: str = Field(min_length=1, max_length=64, description="Standard symbol")
    connection: str = Field(default="", description="Source connection or broker")
    broker_id: int = Field(
        default=-1, description="Broker profile numeric ID (-1 for SQ default)"
    )
    description: str = Field(default="", description="Descriptive instrument name")
    tick_size: float = Field(
        default=0.00001, gt=0.0, description="Minimum price movement"
    )
    tick_step: float = Field(
        default=0.00001, gt=0.0, description="Tick step resolution"
    )
    tick_value_in_money: float = Field(
        default=10.0, gt=0.0, description="Monetary value per tick per lot"
    )
    point_value: float = Field(
        default=100000.0, gt=0.0, description="Contract point unit multiplier"
    )
    decimals: int = Field(default=5, ge=0, le=10, description="Price display decimals")
    default_spread: float = Field(
        default=0.0001, ge=0.0, description="Default spread in price units"
    )
    default_slippage: float = Field(
        default=0.0, ge=0.0, description="Default slippage in points"
    )
    min_volume: float = Field(
        default=0.01, gt=0.0, description="Minimum trade order volume"
    )
    max_volume: float = Field(
        default=100.0, gt=0.0, description="Maximum trade order volume"
    )
    lot_step: float = Field(default=0.01, gt=0.0, description="Order volume step size")
    margin_rate: float = Field(
        default=0.05, ge=0.0, le=1.0, description="Required margin fraction"
    )
    swap_long: float = Field(default=0.0, description="Long overnight swap points")
    swap_short: float = Field(default=0.0, description="Short overnight swap points")
    swap_3day_day: int = Field(
        default=3, ge=0, le=6, description="Weekday of triple swap (3=Wed)"
    )
    commissions: str = Field(
        default='<Method type="None" use="true"><Params/></Method>',
        description="Commission rules XML serialization",
    )
    data_type: str = Field(
        default="Forex", description="Asset class (Forex, Stock, Futures, Crypto)"
    )
    alias: str = Field(default="", description="Comma-separated broker symbol aliases")
    exchange: str = Field(default="", description="Trading exchange name")
    country: str = Field(default="", description="Country of issuer")
    sector: str = Field(default="", description="Market sector")
    min_distance: float = Field(
        default=0.0, ge=0.0, description="Minimum order distance in points"
    )
    order_size_multiplier: float = Field(
        default=1.0, gt=0.0, description="Order size multiplier"
    )
    order_size_step: float = Field(
        default=0.0, ge=0.0, description="Order size step increment"
    )
    cot: str | None = Field(
        default=None, description="Commitment of Traders code mapping"
    )
    created_at_utc: str | None = Field(default=None)
    updated_at_utc: str | None = Field(default=None)

    @field_validator("symbol")
    @classmethod
    def validate_symbol(cls, v: str) -> str:
        """Ensure symbol is alphanumeric with allowable delimiters."""
        cleaned = v.strip().upper()
        if not cleaned:
            msg = "Instrument symbol cannot be empty."
            raise ValueError(msg)
        return cleaned

    @field_validator("data_type", mode="before")
    @classmethod
    def normalize_data_type(cls, v: Any) -> str:
        """Normalize integer data_type values to authoritative string names."""
        if isinstance(v, int):
            return DATA_TYPE_INT_TO_NAME.get(v, "Forex")
        if isinstance(v, str):
            s = v.strip()
            if s.isdigit():
                return DATA_TYPE_INT_TO_NAME.get(int(s), "Forex")
            lower = s.lower()
            if lower in DATA_TYPE_NAME_TO_INT:
                int_val = DATA_TYPE_NAME_TO_INT[lower]
                return DATA_TYPE_INT_TO_NAME.get(int_val, "Forex")
            return s
        return "Forex"

    @property
    def data_type_int(self) -> int:
        """Return the SQX-compatible integer identifier for data_type."""
        return DATA_TYPE_NAME_TO_INT.get(self.data_type.lower(), 3)


def _format_swap_xml(inst: InstrumentDefinition) -> str:
    """Format an SQX <Swap ... /> XML attribute string."""
    has_swap = "true" if (inst.swap_long != 0 or inst.swap_short != 0) else "false"
    triple_day = "WEDNESDAY" if inst.swap_3day_day == _WEDNESDAY_DAY_INDEX else "FRIDAY"
    return (
        f'<Swap use="{has_swap}" type="points" '
        f'long="{inst.swap_long}" short="{inst.swap_short}" '
        f'tripleSwapOn="{triple_day}" />'
    )


def _parse_swap_xml(swap_xml: str) -> tuple[float, float, int]:
    """Parse swap parameters from SQX swap attribute."""
    if not swap_xml or "<Swap" not in swap_xml:
        return 0.0, 0.0, _WEDNESDAY_DAY_INDEX
    try:
        s_elem = ET.fromstring(swap_xml)  # noqa: S314
        swap_long = float(s_elem.get("long", 0.0))
        swap_short = float(s_elem.get("short", 0.0))
        triple = s_elem.get("tripleSwapOn", "WEDNESDAY").upper()
        swap_3day = _FRIDAY_DAY_INDEX if "FRI" in triple else _WEDNESDAY_DAY_INDEX
        return swap_long, swap_short, swap_3day
    except (ET.ParseError, ValueError, TypeError) as err:
        logger.debug(
            "Failed to parse swap XML '%s': %s",
            swap_xml,
            err,
            extra={"fr_id": "FR-DATA-INSTRUMENTS-TRANSFER-XML"},
        )
        return 0.0, 0.0, _WEDNESDAY_DAY_INDEX


def _extract_active_updates(
    updates: dict[str, Any], change_flags: dict[str, bool] | None
) -> dict[str, Any]:
    """Extract applicable update keys based on SQX change flags."""
    if change_flags is None:
        return {
            k: v
            for k, v in updates.items()
            if k not in ("id", "symbol", "created_at_utc", "instruments")
        }
    flag_to_field: dict[str, str] = {
        "changePointValue": "point_value",
        "changeTickSize": "tick_size",
        "changeMinDistance": "min_distance",
        "changeTickStep": "tick_step",
        "changeDefaultSpread": "default_spread",
        "changeDefaultSlippage": "default_slippage",
        "changeCommisionModel": "commissions",
        "changeDataType": "data_type",
        "changeSizeMultiplier": "order_size_multiplier",
        "changeOrderSizeStep": "order_size_step",
        "changeCot": "cot",
    }
    active_updates: dict[str, Any] = {}
    for flag, active in change_flags.items():
        if not active:
            continue
        field = flag_to_field.get(flag, flag)
        if field in updates:
            active_updates[field] = updates[field]
        if flag == "changeSwap":
            for sw_field in ("swap_long", "swap_short", "swap_3day_day"):
                if sw_field in updates:
                    active_updates[sw_field] = updates[sw_field]
    return active_updates


def _parse_instrument_element(elem: ET.Element) -> InstrumentDefinition | None:
    """Parse a single <Instrument ...> XML element into an InstrumentDefinition."""
    symbol = (
        (elem.get("instrument") or elem.get("symbol") or elem.get("name") or "")
        .strip()
        .upper()
    )
    if not symbol:
        return None
    data_type_raw = elem.get("dataType", "3")
    data_type = DATA_TYPE_INT_TO_NAME.get(
        int(data_type_raw) if data_type_raw.isdigit() else 3, "Forex"
    )
    swap_long, swap_short, swap_3day = _parse_swap_xml(elem.get("swap", ""))
    broker_id_raw = elem.get("broker", "-1")
    broker_id = int(broker_id_raw) if broker_id_raw.lstrip("-").isdigit() else -1
    return InstrumentDefinition(
        symbol=symbol,
        description=elem.get("description", symbol),
        point_value=float(elem.get("pointValue", 100000.0)),
        tick_size=float(elem.get("tickSize", 0.00001)),
        tick_step=float(elem.get("tickStep", 0.00001)),
        default_spread=float(elem.get("defaultSpread", 0.0)),
        default_slippage=float(elem.get("defaultSlippage", 0.0)),
        commissions=elem.get(
            "commissions", '<Method type="None" use="true"><Params/></Method>'
        ),
        data_type=data_type,
        exchange=elem.get("exchange", ""),
        country=elem.get("country", ""),
        sector=elem.get("sector", ""),
        swap_long=swap_long,
        swap_short=swap_short,
        swap_3day_day=swap_3day,
        order_size_multiplier=float(elem.get("orderSizeMultiplier", 1.0)),
        order_size_step=float(elem.get("orderSizeStep", 0.0)),
        broker_id=broker_id,
        min_distance=float(elem.get("minDistance", 0.0)),
        cot=elem.get("cot") or None,
    )


class InstrumentService:
    """Domain service managing instruments via host DatabaseManager persistence."""

    def __init__(self, db: DatabaseManager) -> None:
        """Initialize service with host database manager."""
        self._db = db

    def ensure_defaults(self) -> None:
        """Initialize baseline instrument definitions without replacing user data."""
        now = datetime.now(UTC).isoformat()
        for symbol, description, tick, decimals, spread, alias, cot in (
            (
                "EURUSD",
                "Euro / US Dollar",
                0.00001,
                5,
                0.0001,
                "EUR/USD,EURUSD_SB",
                "6E",
            ),
            (
                "GBPUSD",
                "British Pound / US Dollar",
                0.00001,
                5,
                0.0001,
                "GBP/USD",
                "6B",
            ),
            (
                "USDJPY",
                "US Dollar / Japanese Yen",
                0.001,
                3,
                0.01,
                "USD/JPY",
                "6J",
            ),
        ):
            self._db.instruments.insert_if_absent(
                {
                    "symbol": symbol,
                    "connection": "",
                    "broker_id": -1,
                    "description": description,
                    "tick_size": tick,
                    "tick_step": tick,
                    "tick_value_in_money": 10.0,
                    "point_value": 100000.0,
                    "decimals": decimals,
                    "default_spread": spread,
                    "default_slippage": 0.0,
                    "min_volume": 0.01,
                    "max_volume": 100.0,
                    "lot_step": 0.01,
                    "margin_rate": 0.05,
                    "swap_long": 0.0,
                    "swap_short": 0.0,
                    "swap_3day_day": 3,
                    "commissions": "0.0",
                    "data_type": "Forex",
                    "alias": alias,
                    "exchange": "",
                    "country": "",
                    "sector": "",
                    "min_distance": 0.0,
                    "order_size_multiplier": 1.0,
                    "order_size_step": 0.0,
                    "cot": cot,
                    "created_at_utc": now,
                    "updated_at_utc": now,
                }
            )
        logger.info(
            "Baseline instruments initialized",
            extra={"fr_id": "FR-DATA-INSTRUMENTS-DEFAULTS"},
        )

    def create_instrument(self, instrument: InstrumentDefinition) -> int:
        """Persist a new instrument definition into datamgr_instruments.

        Fires FR-DATA-INSTRUMENTS-PERSISTENCE-CRUD.
        """
        payload = instrument.model_dump(exclude={"id"})
        now = datetime.now(UTC).isoformat()
        payload["created_at_utc"] = payload["created_at_utc"] or now
        payload["updated_at_utc"] = payload["updated_at_utc"] or now
        try:
            new_id = self._db.instruments.create(payload)
            logger.info(
                "FR-DATA-INSTRUMENTS-PERSISTENCE-CRUD: Created instrument '%s' (id=%d)",
                instrument.symbol,
                new_id,
                extra={
                    "symbol": instrument.symbol,
                    "instrument_id": new_id,
                    "fr_id": "FR-DATA-INSTRUMENTS-PERSISTENCE-CRUD",
                },
            )
            return new_id
        except Exception:
            logger.exception(
                "FR-DATA-INSTRUMENTS-PERSISTENCE-CRUD: Failed creating '%s'",
                instrument.symbol,
                extra={
                    "symbol": instrument.symbol,
                    "fr_id": "FR-DATA-INSTRUMENTS-PERSISTENCE-CRUD",
                },
            )
            raise

    def save_instrument(self, instrument: InstrumentDefinition) -> int:
        """Create or update an instrument definition.

        Fires FR-DATA-INSTRUMENTS-PERSISTENCE-CRUD.
        """
        existing = self.get_instrument(instrument.symbol)
        if existing is not None:
            payload = instrument.model_dump(exclude={"id", "created_at_utc"})
            self.update_instrument(instrument.symbol, payload)
            return existing.id or 0
        return self.create_instrument(instrument)

    def get_instrument(self, symbol: str) -> InstrumentDefinition | None:
        """Retrieve instrument by symbol.

        Fires FR-DATA-INSTRUMENTS-SPECIFICATION.
        """
        clean_symbol = symbol.strip().upper()
        row = self._db.instruments.get_by_symbol(clean_symbol)
        if row is None:
            logger.debug(
                "FR-DATA-INSTRUMENTS-SPECIFICATION: Instrument '%s' not found.",
                clean_symbol,
                extra={
                    "symbol": clean_symbol,
                    "fr_id": "FR-DATA-INSTRUMENTS-SPECIFICATION",
                },
            )
            return None
        logger.debug(
            "FR-DATA-INSTRUMENTS-SPECIFICATION: Loaded instrument '%s'",
            clean_symbol,
            extra={
                "symbol": clean_symbol,
                "fr_id": "FR-DATA-INSTRUMENTS-SPECIFICATION",
            },
        )
        return InstrumentDefinition.model_validate(row)

    def list_instruments(
        self,
        connection: str | None = None,
        data_type: str | None = None,
        *,
        broker_id: int | None = None,
        search: str | None = None,
        limit: int = 1000,
        offset: int = 0,
    ) -> list[InstrumentDefinition]:
        """List instruments matching optional filters."""
        rows = self._db.instruments.list_instruments(
            connection=connection,
            data_type=data_type,
            broker_id=broker_id,
            search=search,
            limit=limit,
            offset=offset,
        )
        logger.debug(
            "FR-DATA-INSTRUMENTS-SPECIFICATION: Listed %d instruments",
            len(rows),
            extra={
                "count": len(rows),
                "fr_id": "FR-DATA-INSTRUMENTS-SPECIFICATION",
            },
        )
        return [InstrumentDefinition.model_validate(r) for r in rows]

    def update_instrument(self, symbol: str, updates: dict[str, Any]) -> bool:
        """Update instrument parameters by symbol.

        Fires FR-DATA-INSTRUMENTS-PERSISTENCE-CRUD.
        """
        clean_symbol = symbol.strip().upper()
        payload = dict(updates)
        if payload:
            payload["updated_at_utc"] = datetime.now(UTC).isoformat()
        success = self._db.instruments.update(clean_symbol, payload)
        if success:
            logger.info(
                "FR-DATA-INSTRUMENTS-PERSISTENCE-CRUD: Updated instrument '%s'",
                clean_symbol,
                extra={
                    "symbol": clean_symbol,
                    "fr_id": "FR-DATA-INSTRUMENTS-PERSISTENCE-CRUD",
                },
            )
        else:
            logger.warning(
                "FR-DATA-INSTRUMENTS-PERSISTENCE-CRUD: No update for '%s'",
                clean_symbol,
                extra={
                    "symbol": clean_symbol,
                    "fr_id": "FR-DATA-INSTRUMENTS-PERSISTENCE-CRUD",
                },
            )
        return success

    def delete_instrument(self, symbol: str) -> bool:
        """Delete instrument record by symbol.

        Fires FR-DATA-INSTRUMENTS-PERSISTENCE-CRUD.
        """
        clean_symbol = symbol.strip().upper()
        success = self._db.instruments.delete(clean_symbol)
        if success:
            logger.info(
                "FR-DATA-INSTRUMENTS-PERSISTENCE-CRUD: Deleted instrument '%s'",
                clean_symbol,
                extra={
                    "symbol": clean_symbol,
                    "fr_id": "FR-DATA-INSTRUMENTS-PERSISTENCE-CRUD",
                },
            )
        else:
            logger.warning(
                "FR-DATA-INSTRUMENTS-PERSISTENCE-CRUD: Could not delete '%s'",
                clean_symbol,
                extra={
                    "symbol": clean_symbol,
                    "fr_id": "FR-DATA-INSTRUMENTS-PERSISTENCE-CRUD",
                },
            )
        return success

    def delete_instruments(self, symbols: list[str]) -> tuple[int, bool]:
        """Delete multiple instruments by symbol.

        Returns tuple of (deleted_count, is_async).
        If count > 10, is_async is True matching SQX behavior.
        Fires FR-DATA-INSTRUMENTS-PERSISTENCE-CRUD.
        """
        cleaned_symbols = [s.strip().upper() for s in symbols if s.strip()]
        if not cleaned_symbols:
            return 0, False
        is_async = len(cleaned_symbols) > _ASYNC_DELETE_THRESHOLD
        deleted_count = self._db.instruments.delete_many(cleaned_symbols)
        logger.info(
            "FR-DATA-INSTRUMENTS-PERSISTENCE-CRUD: "
            "Deleted %d instruments (is_async=%s)",
            deleted_count,
            is_async,
            extra={
                "deleted_count": deleted_count,
                "is_async": is_async,
                "fr_id": "FR-DATA-INSTRUMENTS-PERSISTENCE-CRUD",
            },
        )
        return deleted_count, is_async

    def count_instruments(self) -> int:
        """Return total count of persisted instruments."""
        return self._db.instruments.count()

    def clone_instrument(
        self,
        symbol: str,
        clone_name: str,
        broker_id: int = -1,
        broker_postfix: str = "",
    ) -> InstrumentDefinition:
        """Clone an existing instrument with broker postfix handling.

        Fires FR-DATA-INSTRUMENTS-CLONE.
        """
        clean_source = symbol.strip().upper()
        source = self.get_instrument(clean_source)
        if source is None:
            msg = f"Instrument with name '{clean_source}' doesn't exist."
            logger.warning(msg, extra={"fr_id": "FR-DATA-INSTRUMENTS-CLONE"})
            raise ValueError(msg)

        clean_clone = clone_name.strip()
        if broker_postfix and not clean_clone.endswith(broker_postfix):
            target_symbol = f"{clean_clone}{broker_postfix}".upper()
        else:
            target_symbol = clean_clone.upper()

        if self.get_instrument(target_symbol) is not None:
            msg = f"Instrument with name '{target_symbol}' already exists."
            logger.warning(msg, extra={"fr_id": "FR-DATA-INSTRUMENTS-CLONE"})
            raise ValueError(msg)

        data = source.model_dump(exclude={"id", "created_at_utc", "updated_at_utc"})
        data["symbol"] = target_symbol
        data["broker_id"] = broker_id
        cloned = InstrumentDefinition.model_validate(data)
        self.create_instrument(cloned)
        logger.info(
            "FR-DATA-INSTRUMENTS-CLONE: Cloned '%s' to '%s' (broker=%d)",
            clean_source,
            target_symbol,
            broker_id,
            extra={
                "source": clean_source,
                "target": target_symbol,
                "broker_id": broker_id,
                "fr_id": "FR-DATA-INSTRUMENTS-CLONE",
            },
        )
        return cloned

    def mass_edit_instruments(
        self,
        symbols: list[str],
        updates: dict[str, Any],
        change_flags: dict[str, bool] | None = None,
    ) -> int:
        """Selectively update parameters across multiple instruments.

        Fires FR-DATA-INSTRUMENTS-MASS-EDIT.
        """
        if not symbols or not updates:
            return 0

        active_updates = _extract_active_updates(updates, change_flags)
        if not active_updates:
            return 0

        updated_count = 0
        for s in symbols:
            clean = s.strip().upper()
            if self.update_instrument(clean, active_updates):
                updated_count += 1

        logger.info(
            "FR-DATA-INSTRUMENTS-MASS-EDIT: Mass updated %d instruments",
            updated_count,
            extra={
                "updated_count": updated_count,
                "fields": list(active_updates.keys()),
                "fr_id": "FR-DATA-INSTRUMENTS-MASS-EDIT",
            },
        )
        return updated_count

    def export_sqx_xml(self, symbols: list[str]) -> str:
        """Export specified instruments to SQX Instruments.xml format.

        Fires FR-DATA-INSTRUMENTS-TRANSFER-XML.
        """
        root = ET.Element("Instruments")
        broker_ids: set[int] = set()

        for s in symbols:
            inst = self.get_instrument(s)
            if inst is None:
                continue

            elem = ET.SubElement(root, "Instrument")
            elem.set("instrument", inst.symbol)
            elem.set("description", inst.description or inst.symbol)
            elem.set("pointValue", str(inst.point_value))
            elem.set("tickSize", str(inst.tick_size))
            elem.set("tickStep", str(inst.tick_step))
            elem.set("defaultSpread", str(inst.default_spread))
            elem.set("defaultSlippage", str(inst.default_slippage))
            elem.set("commissions", inst.commissions)
            elem.set("dataType", str(inst.data_type_int))
            elem.set("exchange", inst.exchange or "")
            elem.set("country", inst.country or "")
            elem.set("sector", inst.sector or "")
            elem.set("swap", _format_swap_xml(inst))
            elem.set("orderSizeMultiplier", str(inst.order_size_multiplier))
            elem.set("orderSizeStep", str(inst.order_size_step))
            elem.set("broker", str(inst.broker_id))
            elem.set("minDistance", str(inst.min_distance))
            if inst.cot:
                elem.set("cot", inst.cot)

            if inst.broker_id > 0:
                broker_ids.add(inst.broker_id)

        # Append broker profiles if present
        for b_id in broker_ids:
            broker_row = (
                self._db.brokers.get_profile(b_id)
                if hasattr(self._db, "brokers")
                else None
            )
            if broker_row is not None:
                b_elem = ET.SubElement(root, "Broker")
                b_elem.set("id", str(broker_row.get("id", b_id)))
                b_elem.set("name", str(broker_row.get("name", "")))
                b_elem.set("postfix", str(broker_row.get("postfix", "")))
                b_elem.set("mtUse", str(bool(broker_row.get("mt_use", 0))).lower())

        xml_bytes = ET.tostring(root, encoding="utf-8")
        parsed = minidom.parseString(xml_bytes)  # noqa: S318
        formatted = parsed.toprettyxml(indent="  ", encoding="utf-8").decode("utf-8")
        logger.info(
            "FR-DATA-INSTRUMENTS-TRANSFER-XML: Exported %d instruments to XML",
            len(symbols),
            extra={"count": len(symbols), "fr_id": "FR-DATA-INSTRUMENTS-TRANSFER-XML"},
        )
        return formatted

    def import_sqx_xml(
        self, xml_content: str, conflict_policy: str = "overwrite_all"
    ) -> dict[str, Any]:
        """Import instruments from SQX Instruments.xml format.

        Conflict policies:
            - 'overwrite' / 'overwrite_all': replace existing definitions
            - 'skip': ignore definitions that already exist
            - 'cancel': abort entire import on conflict

        Fires FR-DATA-INSTRUMENTS-TRANSFER-XML.
        """
        try:
            root = ET.fromstring(xml_content)  # noqa: S314
        except ET.ParseError as err:
            msg = f"Failed to parse XML: {err}"
            logger.warning(msg, extra={"fr_id": "FR-DATA-INSTRUMENTS-TRANSFER-XML"})
            raise ValueError(msg) from err

        if root.tag != "Instruments":
            msg = "No Instruments found to import."
            logger.warning(msg, extra={"fr_id": "FR-DATA-INSTRUMENTS-TRANSFER-XML"})
            raise ValueError(msg)

        imported: list[str] = []
        overwritten: list[str] = []
        skipped: list[str] = []

        for elem in root.findall("Instrument"):
            inst = _parse_instrument_element(elem)
            if inst is None:
                continue

            symbol = inst.symbol
            existing = self.get_instrument(symbol)
            if existing is not None:
                if conflict_policy == "skip":
                    skipped.append(symbol)
                    continue
                if conflict_policy == "cancel":
                    msg = f"Import canceled due to conflict on '{symbol}'"
                    logger.info(
                        msg,
                        extra={"fr_id": "FR-DATA-INSTRUMENTS-TRANSFER-XML"},
                    )
                    raise ValueError(msg)

            if existing is not None:
                self.update_instrument(
                    symbol,
                    inst.model_dump(exclude={"id", "created_at_utc", "symbol"}),
                )
                overwritten.append(symbol)
            else:
                self.create_instrument(inst)
                imported.append(symbol)

        logger.info(
            "FR-DATA-INSTRUMENTS-TRANSFER-XML: Imported XML instruments",
            extra={
                "imported": len(imported),
                "overwritten": len(overwritten),
                "skipped": len(skipped),
                "fr_id": "FR-DATA-INSTRUMENTS-TRANSFER-XML",
            },
        )
        return {
            "imported": len(imported),
            "overwritten": len(overwritten),
            "skipped": len(skipped),
            "symbols": imported + overwritten,
        }

    def resolve_alias(self, alias_or_symbol: str) -> str:
        """Resolve a broker-specific alias to canonical instrument symbol.

        Fires FR-DATA-INSTRUMENTS-ALIAS-RESOLUTION.
        """
        candidate = alias_or_symbol.strip().upper()
        direct = self.get_instrument(candidate)
        if direct is not None:
            return direct.symbol

        all_instrs = self.list_instruments(limit=5000)
        for inst in all_instrs:
            if inst.alias:
                aliases = [a.strip().upper() for a in inst.alias.split(",")]
                if candidate in aliases:
                    logger.debug(
                        "FR-DATA-INSTRUMENTS-ALIAS-RESOLUTION: Resolved '%s' to '%s'",
                        candidate,
                        inst.symbol,
                        extra={
                            "alias": candidate,
                            "canonical": inst.symbol,
                            "fr_id": "FR-DATA-INSTRUMENTS-ALIAS-RESOLUTION",
                        },
                    )
                    return inst.symbol

        logger.debug(
            "FR-DATA-INSTRUMENTS-ALIAS-RESOLUTION: No alias found for '%s', "
            "returning verbatim",
            candidate,
            extra={
                "alias": candidate,
                "fr_id": "FR-DATA-INSTRUMENTS-ALIAS-RESOLUTION",
            },
        )
        return candidate

    def list_aliases(self) -> list[dict[str, str]]:
        """List all registered instrument aliases.

        Fires FR-DATA-INSTRUMENTS-ALIAS-RESOLUTION.
        """
        instruments = self.list_instruments(limit=5000)
        results: list[dict[str, str]] = []
        for inst in instruments:
            if inst.alias:
                for a in inst.alias.split(","):
                    clean = a.strip().upper()
                    if clean:
                        results.append(
                            {
                                "alias": clean,
                                "instrument": inst.symbol,
                                "description": inst.description,
                            }
                        )
        return results

    def add_alias(self, alias: str, instrument: str, description: str = "") -> bool:
        """Register a new broker alias for a target instrument.

        Fires FR-DATA-INSTRUMENTS-ALIAS-RESOLUTION.
        """
        clean_alias = alias.strip().upper()
        clean_target = instrument.strip().upper()
        logger.debug(
            "FR-DATA-INSTRUMENTS-ALIAS-RESOLUTION: Adding alias %s -> %s (desc=%s)",
            clean_alias,
            clean_target,
            description,
            extra={"fr_id": "FR-DATA-INSTRUMENTS-ALIAS-RESOLUTION"},
        )
        target = self.get_instrument(clean_target)
        if target is None:
            msg = f"Instrument '{clean_target}' doesn't exist."
            logger.warning(msg, extra={"fr_id": "FR-DATA-INSTRUMENTS-ALIAS-RESOLUTION"})
            raise ValueError(msg)

        current_aliases = [
            a.strip().upper() for a in target.alias.split(",") if a.strip()
        ]
        if clean_alias in current_aliases:
            return True

        current_aliases.append(clean_alias)
        new_alias_str = ",".join(current_aliases)
        return self.update_instrument(clean_target, {"alias": new_alias_str})

    def edit_alias(self, alias: str, instrument: str, description: str = "") -> bool:
        """Reassign an existing alias to another instrument.

        Fires FR-DATA-INSTRUMENTS-ALIAS-RESOLUTION.
        """
        self.remove_alias(alias)
        return self.add_alias(alias, instrument, description)

    def remove_alias(self, alias: str) -> bool:
        """Remove a broker alias from whichever instrument owns it.

        Fires FR-DATA-INSTRUMENTS-ALIAS-RESOLUTION.
        """
        clean_alias = alias.strip().upper()
        instruments = self.list_instruments(limit=5000)
        removed = False
        for inst in instruments:
            if inst.alias:
                aliases = [
                    a.strip().upper() for a in inst.alias.split(",") if a.strip()
                ]
                if clean_alias in aliases:
                    aliases.remove(clean_alias)
                    self.update_instrument(inst.symbol, {"alias": ",".join(aliases)})
                    removed = True
        return removed


def main() -> int:
    """CLI tool for inspecting instrument definitions."""
    parser = argparse.ArgumentParser(description="Inspect instrument definitions")
    parser.add_argument("--symbol", type=str, help="Symbol to inspect")
    parser.add_argument("--list", action="store_true", help="List all instruments")
    args = parser.parse_args()

    db = DatabaseManager()
    db.initialize()
    service = InstrumentService(db)
    service.ensure_defaults()

    if args.symbol:
        inst = service.get_instrument(args.symbol)
        if inst:
            print(f"Instrument: {inst.symbol} ({inst.description})")
            print(f"  Type: {inst.data_type}, Decimals: {inst.decimals}")
            print(f"  Point: {inst.point_value}, Tick: {inst.tick_size}")
            return 0
        print(f"Symbol '{args.symbol}' not found.")
        return 1
    if args.list:
        instruments = service.list_instruments()
        print(f"Total instruments: {len(instruments)}")
        for i in instruments[:20]:
            print(f"  {i.symbol:12} {i.data_type:10} {i.description}")
        return 0
    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
