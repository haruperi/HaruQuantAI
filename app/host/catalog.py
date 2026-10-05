"""Authoritative host symbol and instrument catalog service.

Description:
    This module provides the authoritative market instrument and symbol catalog service
    for the HaruQuantAI platform. It manages read-only access to persisted financial
    contracts, futures commodities, equity tickers, and OTC instrument specifications
    stored within the SQLite database (`data/database/haruquantai.db`). Subsystems,
    quantitative pipelines, and broker plugins query this service to dynamically
    resolve contract specifications (tick sizes, point values, contract sizes, and
    precision) without hardcoding asset dictionaries or executing raw SQL queries
    in plugin code.

Purpose:
    FEAT-HOST-CATALOG: Authoritative symbol and instrument catalog query service for
    host services and broker plugins.

Key Capabilities:
    - FR-HOST-CATALOG-COMMODITY-LOOKUP: Query commodity and futures contract
      specifications by code or continuous symbol alias.
      Associated: `CatalogService.get_commodity()`
      Logging: Emits DEBUG telemetry with lookup code and resolution outcome.
    - FR-HOST-CATALOG-COMMODITY-LIST: Retrieve all registered commodity specifications
      with optional exchange filtering.
      Associated: `CatalogService.list_commodities()`
      Logging: Emits DEBUG telemetry with matched commodity record count.
    - FR-HOST-CATALOG-INSTRUMENT-LOOKUP: Query comprehensive instrument specifications
      from the central instruments store.
      Associated: `CatalogService.get_instrument()`
      Logging: Emits DEBUG telemetry with instrument symbol and resolution status.
    - FR-HOST-CATALOG-STOCK-LOOKUP: Query equity stock specifications and basket
      memberships.
      Associated: `CatalogService.get_stock()`
      Logging: Emits DEBUG telemetry with ticker code and resolution status.
    - FR-HOST-CATALOG-FALLBACK: Safely handle uninitialized or offline database
      environments without raising unhandled exceptions.
      Associated: `CatalogService._get_connection()`
      Logging: Emits WARNING telemetry when catalog database is offline or unreadable.

Python API Usage:
    ```python
    from app.host.catalog import get_catalog_service

    catalog = get_catalog_service()

    # Query futures contract spec (normalizes '@ES' -> 'ES')
    es_spec = catalog.get_commodity("@ES")
    if es_spec:
        print(es_spec.name, es_spec.point_value, es_spec.tick_size)

    # Query general instrument spec
    eurusd = catalog.get_instrument("EURUSD")
    if eurusd:
        print(eurusd.decimals, eurusd.tick_size)
    ```

CLI Usage:
    Catalog queries are accessed programmatically by broker plugins and quantitative
    tools during data ingestion or trading sessions:
    ```bash
    uv run python scripts/test_all_brokers.py
    ```
"""

from __future__ import annotations

import functools
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from app.host.logging import get_logger

__all__ = [
    "DEFAULT_DATABASE_PATH",
    "CatalogService",
    "CommodityRecord",
    "InstrumentRecord",
    "StockRecord",
    "get_catalog_service",
    "normalize_commodity_code",
]

logger = get_logger(__name__)

DEFAULT_DATABASE_PATH: Final[Path] = (
    Path(__file__).resolve().parents[2] / "data" / "database" / "haruquantai.db"
)
BUSY_TIMEOUT_SECONDS: Final[float] = 5.0


def normalize_commodity_code(symbol: str) -> str:
    """Normalize a commodity/futures symbol code for database lookup.

    Strips StrategyQuant continuous contract prefix ('@') and surrounding whitespace,
    converting the resulting string to uppercase.

    Args:
        symbol: Raw symbol identifier (e.g. '@ES', 'es', 'CL').

    Returns:
        Clean uppercase commodity identifier (e.g. 'ES', 'CL').
    """
    cleaned = symbol.strip().upper()
    if cleaned.startswith("@"):
        cleaned = cleaned.lstrip("@")
    return cleaned


@dataclass(frozen=True, slots=True)
class CommodityRecord:
    """Immutable specification for a commodity or futures contract.

    Attributes:
        code: Normalized exchange commodity code (e.g. 'ES', 'NQ', 'CL').
        name: Full descriptive name of the commodity contract.
        point_value: Cash value multiplier per full price point.
        tick_step: Minimum price increment step.
        tick_size: Minimum tick quotation size.
        order_size_multi: Order size lot multiplier.
        order_size_step: Minimum order volume increment step.
        exchange: Primary exchange code or name (e.g. 'CME', 'NYMEX').
    """

    code: str
    name: str
    point_value: float
    tick_step: float
    tick_size: float
    order_size_multi: float
    order_size_step: float
    exchange: str


@dataclass(frozen=True, slots=True)
class InstrumentRecord:
    """Immutable metadata and trading terms for an instrument.

    Attributes:
        symbol: Canonical instrument symbol (e.g. 'EURUSD', 'BTCUSD').
        description: Descriptive instrument name.
        tick_size: Minimum tick quote increment.
        tick_step: Minimum allowable quote movement step.
        tick_value_in_money: Monetary value of one minimum tick.
        point_value: Notional contract or unit multiplier.
        decimals: Number of decimal places in price quotes.
        default_spread: Typical spread in price points.
        data_type: Asset class category (e.g. 'Forex', 'Crypto', 'CFD').
        exchange: Exchange or market venue.
    """

    symbol: str
    description: str
    tick_size: float
    tick_step: float
    tick_value_in_money: float
    point_value: float
    decimals: int
    default_spread: float
    data_type: str
    exchange: str


@dataclass(frozen=True, slots=True)
class StockRecord:
    """Immutable metadata for an equity stock ticker.

    Attributes:
        ticker: Canonical stock ticker symbol (e.g. 'AAPL', 'MSFT').
        basket_id: Numerical group or basket identifier, if assigned.
        date_from: Earliest recorded data date.
        date_to: Latest recorded data date.
    """

    ticker: str
    basket_id: int | None = None
    date_from: str | None = None
    date_to: str | None = None


class CatalogService:
    """Authoritative host catalog lookup service backed by SQLite."""

    def __init__(self, db_path: Path | str | None = None) -> None:
        """Initialize catalog service with designated database path.

        Args:
            db_path: Path to SQLite database file. Defaults to DEFAULT_DATABASE_PATH.
        """
        self.db_path = Path(db_path) if db_path else DEFAULT_DATABASE_PATH

    def _get_connection(self) -> sqlite3.Connection | None:
        """Create a read-only SQLite connection, or None if the database is missing.

        Returns:
            sqlite3.Connection if accessible, otherwise None.
        """
        if not self.db_path.exists():
            logger.warning(
                "Catalog database file not found at '%s'. Catalog lookups disabled.",
                self.db_path,
            )
            return None

        try:
            conn = sqlite3.connect(
                self.db_path,
                timeout=BUSY_TIMEOUT_SECONDS,
                check_same_thread=False,
            )
            conn.row_factory = sqlite3.Row
            return conn
        except sqlite3.Error as exc:
            logger.warning(
                "Failed to open catalog database at '%s': %s",
                self.db_path,
                exc,
            )
            return None

    def get_commodity(self, code: str) -> CommodityRecord | None:
        """Retrieve commodity/futures specification by symbol or code.

        Normalizes StrategyQuant continuous contracts ('@ES' -> 'ES') and case.

        Args:
            code: Symbol identifier (e.g. '@ES', 'NQ', 'CL').

        Returns:
            CommodityRecord if found in database, otherwise None.
        """
        norm_code = normalize_commodity_code(code)
        conn = self._get_connection()
        if conn is None:
            return None

        query = """
            SELECT code, name, point_value, tick_step, tick_size,
                   order_size_multi, order_size_step, exchange
            FROM datamgr_commodities
            WHERE code = ?
            LIMIT 1
        """
        try:
            with conn:
                row = conn.execute(query, (norm_code,)).fetchone()
            if row is not None:
                record = CommodityRecord(
                    code=str(row["code"]),
                    name=str(row["name"] or ""),
                    point_value=float(row["point_value"] or 0.0),
                    tick_step=float(row["tick_step"] or 0.0),
                    tick_size=float(row["tick_size"] or 0.0),
                    order_size_multi=float(row["order_size_multi"] or 1.0),
                    order_size_step=float(row["order_size_step"] or 0.0),
                    exchange=str(row["exchange"] or ""),
                )
                logger.debug(
                    "FR-HOST-CATALOG-COMMODITY-LOOKUP: Resolved '%s' -> '%s' "
                    "(point_value=%s, tick_size=%s)",
                    code,
                    record.name,
                    record.point_value,
                    record.tick_size,
                )
                return record

            logger.debug(
                "FR-HOST-CATALOG-COMMODITY-LOOKUP: Commodity '%s' "
                "(normalized '%s') not found in database",
                code,
                norm_code,
            )
            return None
        except sqlite3.Error as exc:
            logger.warning(
                "FR-HOST-CATALOG-COMMODITY-LOOKUP: Error looking up commodity '%s': %s",
                code,
                exc,
            )
            return None
        finally:
            conn.close()

    def list_commodities(
        self, exchange: str | None = None, filter_str: str | None = None
    ) -> list[CommodityRecord]:
        """Retrieve all registered commodity specifications.

        Args:
            exchange: Optional exchange filter (e.g. 'CME').
            filter_str: Optional substring to match against code or name.

        Returns:
            List of matching CommodityRecord instances.
        """
        conn = self._get_connection()
        if conn is None:
            return []

        query = """
            SELECT code, name, point_value, tick_step, tick_size,
                   order_size_multi, order_size_step, exchange
            FROM datamgr_commodities
            WHERE 1=1
        """
        params: list[str] = []
        if exchange:
            query += " AND UPPER(exchange) = ?"
            params.append(exchange.upper().strip())
        if filter_str:
            query += " AND (UPPER(code) LIKE ? OR UPPER(name) LIKE ?)"
            pat = f"%{filter_str.upper().strip()}%"
            params.extend([pat, pat])

        query += " ORDER BY code ASC"

        try:
            with conn:
                rows = conn.execute(query, params).fetchall()
            results = [
                CommodityRecord(
                    code=str(r["code"]),
                    name=str(r["name"] or ""),
                    point_value=float(r["point_value"] or 0.0),
                    tick_step=float(r["tick_step"] or 0.0),
                    tick_size=float(r["tick_size"] or 0.0),
                    order_size_multi=float(r["order_size_multi"] or 1.0),
                    order_size_step=float(r["order_size_step"] or 0.0),
                    exchange=str(r["exchange"] or ""),
                )
                for r in rows
            ]
            logger.debug(
                "FR-HOST-CATALOG-COMMODITY-LIST: Listed %d commodities from catalog",
                len(results),
            )
            return results
        except sqlite3.Error as exc:
            logger.warning(
                "FR-HOST-CATALOG-COMMODITY-LIST: Failed to list commodities: %s",
                exc,
            )
            return []
        finally:
            conn.close()

    def get_instrument(self, symbol: str) -> InstrumentRecord | None:
        """Retrieve general instrument specification by symbol.

        Args:
            symbol: Clean instrument identifier (e.g. 'EURUSD', 'XAUUSD').

        Returns:
            InstrumentRecord if found in database, otherwise None.
        """
        norm_sym = symbol.strip().upper()
        conn = self._get_connection()
        if conn is None:
            return None

        query = """
            SELECT symbol, description, tick_size, tick_step, tick_value_in_money,
                   point_value, decimals, default_spread, data_type, exchange
            FROM datamgr_instruments
            WHERE UPPER(symbol) = ?
            LIMIT 1
        """
        try:
            with conn:
                row = conn.execute(query, (norm_sym,)).fetchone()
            if row is not None:
                record = InstrumentRecord(
                    symbol=str(row["symbol"]),
                    description=str(row["description"] or ""),
                    tick_size=float(row["tick_size"] or 0.00001),
                    tick_step=float(row["tick_step"] or 0.00001),
                    tick_value_in_money=float(row["tick_value_in_money"] or 10.0),
                    point_value=float(row["point_value"] or 100000.0),
                    decimals=int(row["decimals"] or 5),
                    default_spread=float(row["default_spread"] or 0.0),
                    data_type=str(row["data_type"] or ""),
                    exchange=str(row["exchange"] or ""),
                )
                logger.debug(
                    "FR-HOST-CATALOG-INSTRUMENT-LOOKUP: Resolved instrument '%s' "
                    "(decimals=%s, tick_size=%s)",
                    symbol,
                    record.decimals,
                    record.tick_size,
                )
                return record

            logger.debug(
                "FR-HOST-CATALOG-INSTRUMENT-LOOKUP: Instrument '%s' not found",
                norm_sym,
            )
            return None
        except sqlite3.Error as exc:
            logger.warning(
                "FR-HOST-CATALOG-INSTRUMENT-LOOKUP: Error looking up '%s': %s",
                symbol,
                exc,
            )
            return None
        finally:
            conn.close()

    def list_instruments(self, data_type: str | None = None) -> list[InstrumentRecord]:
        """Retrieve list of registered instruments, optionally filtered by asset class.

        Args:
            data_type: Optional asset class filter (e.g. 'Forex', 'Crypto', 'CFD').

        Returns:
            List of matching InstrumentRecord instances.
        """
        conn = self._get_connection()
        if conn is None:
            return []

        query = """
            SELECT symbol, description, tick_size, tick_step, tick_value_in_money,
                   point_value, decimals, default_spread, data_type, exchange
            FROM datamgr_instruments
            WHERE 1=1
        """
        params: list[str] = []
        if data_type:
            query += " AND UPPER(data_type) = ?"
            params.append(data_type.upper().strip())

        query += " ORDER BY symbol ASC"

        try:
            with conn:
                rows = conn.execute(query, params).fetchall()
            return [
                InstrumentRecord(
                    symbol=str(r["symbol"]),
                    description=str(r["description"] or ""),
                    tick_size=float(r["tick_size"] or 0.00001),
                    tick_step=float(r["tick_step"] or 0.00001),
                    tick_value_in_money=float(r["tick_value_in_money"] or 10.0),
                    point_value=float(r["point_value"] or 100000.0),
                    decimals=int(r["decimals"] or 5),
                    default_spread=float(r["default_spread"] or 0.0),
                    data_type=str(r["data_type"] or ""),
                    exchange=str(r["exchange"] or ""),
                )
                for r in rows
            ]
        except sqlite3.Error as exc:
            logger.warning("Failed to list instruments: %s", exc)
            return []
        finally:
            conn.close()

    def get_stock(self, ticker: str) -> StockRecord | None:
        """Retrieve equity stock record by ticker.

        Args:
            ticker: Stock ticker identifier (e.g. 'AAPL', 'MSFT').

        Returns:
            StockRecord if found, otherwise None.
        """
        norm_ticker = ticker.strip().upper()
        conn = self._get_connection()
        if conn is None:
            return None

        query = """
            SELECT TICKER, BASKET_ID, DATE_FROM, DATE_TO
            FROM datamgr_stock
            WHERE UPPER(TICKER) = ?
            LIMIT 1
        """
        try:
            with conn:
                row = conn.execute(query, (norm_ticker,)).fetchone()
            if row is not None:
                basket_raw = row["BASKET_ID"]
                record = StockRecord(
                    ticker=str(row["TICKER"]),
                    basket_id=int(basket_raw) if basket_raw is not None else None,
                    date_from=str(row["DATE_FROM"]) if row["DATE_FROM"] else None,
                    date_to=str(row["DATE_TO"]) if row["DATE_TO"] else None,
                )
                logger.debug(
                    "FR-HOST-CATALOG-STOCK-LOOKUP: Resolved stock ticker '%s'",
                    norm_ticker,
                )
                return record

            logger.debug(
                "FR-HOST-CATALOG-STOCK-LOOKUP: Stock ticker '%s' not found in database",
                norm_ticker,
            )
            return None
        except sqlite3.Error as exc:
            logger.warning(
                "FR-HOST-CATALOG-STOCK-LOOKUP: Error looking up stock '%s': %s",
                ticker,
                exc,
            )
            return None
        finally:
            conn.close()

    def list_stocks(
        self, filter_str: str | None = None, limit: int = 100
    ) -> list[StockRecord]:
        """Retrieve list of stock records with optional matching.

        Args:
            filter_str: Optional prefix or substring to filter tickers.
            limit: Maximum count of records to return.

        Returns:
            List of StockRecord instances.
        """
        conn = self._get_connection()
        if conn is None:
            return []

        query = """
            SELECT TICKER, BASKET_ID, DATE_FROM, DATE_TO
            FROM datamgr_stock
            WHERE 1=1
        """
        params: list[object] = []
        if filter_str:
            query += " AND UPPER(TICKER) LIKE ?"
            params.append(f"%{filter_str.upper().strip()}%")

        query += " ORDER BY TICKER ASC LIMIT ?"
        params.append(limit)

        try:
            with conn:
                rows = conn.execute(query, params).fetchall()
            results: list[StockRecord] = []
            for r in rows:
                b_raw = r["BASKET_ID"]
                results.append(
                    StockRecord(
                        ticker=str(r["TICKER"]),
                        basket_id=int(b_raw) if b_raw is not None else None,
                        date_from=str(r["DATE_FROM"]) if r["DATE_FROM"] else None,
                        date_to=str(r["DATE_TO"]) if r["DATE_TO"] else None,
                    )
                )
            return results
        except sqlite3.Error as exc:
            logger.warning("Failed to list stocks: %s", exc)
            return []
        finally:
            conn.close()


@functools.lru_cache(maxsize=1)
def _get_default_catalog_service() -> CatalogService:
    """Return cached default catalog service instance."""
    return CatalogService()


def get_catalog_service(db_path: Path | str | None = None) -> CatalogService:
    """Retrieve or create the host catalog service instance.

    Args:
        db_path: Optional custom database path. If omitted, returns global singleton.

    Returns:
        CatalogService instance.
    """
    if db_path is not None:
        return CatalogService(db_path)
    return _get_default_catalog_service()
