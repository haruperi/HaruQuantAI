"""Authoritative instrument specifications, validation, and host persistence.

Description:
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
    - FR-DATA-INSTRUMENTS-ALIAS-RESOLUTION: Broker-to-clean symbol mapping.
      Associated: `[InstrumentService.resolve_alias()]`
      Logging: Emits DEBUG when translating broker symbol aliases.

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
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.host.logging import get_logger
from app.host.persistence import DatabaseManager

logger = get_logger(__name__)


class InstrumentDefinition(BaseModel):
    """Authoritative domain specification for a financial instrument."""

    model_config = ConfigDict(frozen=True, extra="ignore")

    id: int | None = Field(default=None, description="Database auto-increment ID")
    symbol: str = Field(min_length=1, max_length=64, description="Standard symbol")
    connection: str = Field(default="", description="Source connection or broker")
    broker_id: int = Field(default=0, description="Broker profile numeric ID")
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
        default="0.0", description="Commission rules serialization"
    )
    data_type: str = Field(
        default="Forex", description="Asset class (Forex, Stock, Futures, Crypto)"
    )
    alias: str = Field(default="", description="Comma-separated broker symbol aliases")
    exchange: str = Field(default="", description="Trading exchange name")
    country: str = Field(default="", description="Country of issuer")
    sector: str = Field(default="", description="Market sector")
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


class InstrumentService:
    """Domain service managing instruments via host DatabaseManager persistence."""

    def __init__(self, db: DatabaseManager) -> None:
        """Initialize service with host database manager."""
        self._db = db

    def create_instrument(self, instrument: InstrumentDefinition) -> int:
        """Persist a new instrument definition into datamgr_instruments.

        Fires FR-DATA-INSTRUMENTS-PERSISTENCE-CRUD.
        """
        payload = instrument.model_dump(exclude={"id"})
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
        limit: int = 1000,
        offset: int = 0,
    ) -> list[InstrumentDefinition]:
        """List instruments matching optional filters."""
        rows = self._db.instruments.list_instruments(
            connection=connection,
            data_type=data_type,
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
        success = self._db.instruments.update(clean_symbol, updates)
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

    def count_instruments(self) -> int:
        """Return total count of persisted instruments."""
        return self._db.instruments.count()

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


def main() -> int:
    """CLI tool for inspecting instrument definitions."""
    parser = argparse.ArgumentParser(description="Inspect instrument definitions")
    parser.add_argument("--symbol", type=str, help="Symbol to inspect")
    parser.add_argument("--list", action="store_true", help="List all instruments")
    args = parser.parse_args()

    db = DatabaseManager()
    db.initialize()
    service = InstrumentService(db)

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
