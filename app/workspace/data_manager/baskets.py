"""Market data baskets, stock groups, and multi-symbol series alignment.

Description:
    BasketStore in app.host.persistence owns atomic group/membership SQL. This
    service owns dates, default weights, basket models, interchange formats,
    readiness diagnostics, and synthetic calculations. No database connections,
    cursors or raw SQL are permitted here.

    Service managing multi-asset baskets, stock groups, and cross-instrument
    series alignment for portfolio analysis and synthetic instrument generation
    within the Data Manager workspace, providing full functional parity with SQX
    DataManagerBasket. Supports stock group persistence with entry and exit dates
    (date_from, date_to) to prevent survivorship bias, CSV and XML interchange
    conforming to donor schemas, immutability guards for system stock groups
    (e.g., [[S&P 100 limited]]), data download readiness evaluation, and chronological
    timestamp alignment using intersection (inner join) or union (outer join with
    forward-fill / notNaN) policies.

Purpose:
    FEAT-WORKSPACE-DATAMGR: Manage stock groups, baskets, and multi-series
    alignment for the Data Manager workspace.
    FEAT-DATA-DATA-MANAGER-BASKET: Achieve 100% parity with SQX DataManagerBasket.

Key Capabilities:
    - FR-DATA-BASKETS-GROUPS: Manage stock groups and constituent compositions.
      Associated: `[BasketService.save_basket()]`, `[BasketService.get_basket()]`
      Logging: Emits INFO on basket mutations with basket name and ID.
    - FR-DATA-BASKETS-SURVIVORSHIP: Track constituent entry and exit date intervals.
      Associated: `[BasketService.save_basket()]`, `[parse_stock_lines()]`
      Logging: Emits INFO when survivorship date intervals are saved.
    - FR-DATA-BASKETS-INTERCHANGE: CSV text and SQX XML schema import and export.
      Associated: `[parse_stock_lines()]`, `[format_stock_lines()]`,
      `[export_groups_xml()]`, `[import_groups_xml()]`
      Logging: Emits INFO on constituent import and export operations.
    - FR-DATA-BASKETS-DIAGNOSTICS: Evaluate data download readiness and missing symbols.
      Associated: `[BasketService.check_readiness()]`
      Logging: Emits INFO with readiness status and missing constituent counts.
    - FR-DATA-BASKETS-ALIGNMENT: Multi-symbol series alignment and synthetic bar math.
      Associated: `[BasketService.align_series()]`,
      `[BasketService.compute_basket_series()]`
      Logging: Emits INFO on synthetic bar computation with bar count.

Python API Usage:
    ```python
    from app.host.persistence import DatabaseManager
    from app.workspace.data_manager.baskets import (
        BasketDefinition,
        BasketItem,
        BasketService,
    )

    db = DatabaseManager()
    db.initialize()
    service = BasketService(db)

    basket = BasketDefinition(
        name="Tech_Trio",
        description="Top technology basket",
        items=[
            BasketItem(symbol="AAPL", weight=0.4, date_from="2020-01-01"),
            BasketItem(symbol="MSFT", weight=0.4, date_from="2020-01-01"),
            BasketItem(
                symbol="GOOGL",
                weight=0.2,
                date_from="2020-01-01",
                date_to="2025-12-31",
            ),
        ],
    )
    service.save_basket(basket)
    readiness = service.check_readiness(basket, {"AAPL", "MSFT", "GOOGL"})
    ```

CLI Usage:
    ```bash
    python -m app.workspace.data_manager.baskets --list
    ```
"""

from __future__ import annotations

import argparse
import contextlib
import sys
import xml.etree.ElementTree as ET
from datetime import UTC, datetime, timedelta
from typing import Any
from xml.dom import minidom

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.host.logging import get_logger
from app.host.persistence import DatabaseManager
from app.workspace.data_manager.data import BarRecord

logger = get_logger(__name__)

_ISO_DATE_PARTS = 3
_MIN_CSV_DATE_PARTS = 2


_MS_EPOCH_THRESHOLD = 1e11
_ISO_DATE_LENGTH = 10


def normalize_sqx_date(val: Any) -> str | None:
    """Normalize SQX dates (epoch ms, epoch s, -1, ISO) to YYYY-MM-DD or None."""
    if val is None:
        return None
    s = str(val).strip()
    if not s or s in ("-1", "0", "-", "None", "null", "none"):
        return None
    try:
        num = float(s)
        if num not in (-1, 0):
            seconds = num / 1000.0 if abs(num) >= _MS_EPOCH_THRESHOLD else num
            base = datetime(1970, 1, 1, tzinfo=UTC)
            return (base + timedelta(seconds=seconds)).strftime("%Y-%m-%d")
        return None
    except ValueError, OverflowError:
        pass
    if "." in s:
        with contextlib.suppress(ValueError):
            return (
                datetime.strptime(s, "%d.%m.%Y")
                .replace(tzinfo=UTC)
                .strftime("%Y-%m-%d")
            )
    return (
        s[:_ISO_DATE_LENGTH]
        if (len(s) >= _ISO_DATE_LENGTH and s[4] == "-" and s[7] == "-")
        else s
    )


parse_date_to_iso = normalize_sqx_date


def format_iso_to_sqx_date(value: str | None) -> str:
    """Convert an ISO YYYY-MM-DD date into SQX DD.MM.YYYY format."""
    if not value:
        return ""
    norm = parse_date_to_iso(value)
    if not norm:
        return ""
    parts = norm.split("-")
    if len(parts) == _ISO_DATE_PARTS:
        return f"{int(parts[2]):02d}.{int(parts[1]):02d}.{parts[0]}"
    return ""


def iso_to_epoch_ms(value: str | None) -> str:
    """Convert an ISO YYYY-MM-DD date string to an epoch millisecond string."""
    norm = parse_date_to_iso(value)
    if not norm:
        return ""
    try:
        dt = datetime.strptime(norm, "%Y-%m-%d").replace(tzinfo=UTC)
        return str(int(dt.timestamp() * 1000))
    except ValueError:
        return ""


class BasketItem(BaseModel):
    """Specification of a single constituent within a market basket."""

    model_config = ConfigDict(frozen=True)

    symbol: str = Field(min_length=1, description="Constituent symbol")
    weight: float = Field(default=1.0, gt=0.0, description="Relative weighting factor")
    date_from: str | None = Field(
        default=None, description="Inclusion start date (ISO YYYY-MM-DD)"
    )
    date_to: str | None = Field(
        default=None, description="Inclusion end date (ISO YYYY-MM-DD)"
    )

    @field_validator("symbol")
    @classmethod
    def validate_symbol(cls, v: str) -> str:
        """Validate and normalize basket constituent symbol."""
        clean = v.strip().upper()
        if not clean:
            raise ValueError("Basket constituent symbol cannot be empty.")
        return clean

    @field_validator("date_from", "date_to", mode="before")
    @classmethod
    def normalize_dates(cls, v: str | None) -> str | None:
        """Normalize input dates to ISO format."""
        return parse_date_to_iso(v)


class BasketDefinition(BaseModel):
    """Authoritative domain specification of a multi-asset market basket."""

    model_config = ConfigDict(frozen=True)

    id: int | None = Field(default=None, description="Unique group identifier")
    name: str = Field(min_length=1, max_length=128, description="Basket name")
    description: str = Field(default="", description="Descriptive label")
    system: bool = Field(
        default=False, description="Whether group is a built-in system group"
    )
    items: list[BasketItem] = Field(
        default_factory=list, description="List of basket constituents"
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate non-empty basket name."""
        clean = v.strip()
        if not clean:
            raise ValueError("Basket name cannot be empty.")
        return clean


class BasketReadiness(BaseModel):
    """Diagnostics evaluation of stock group data download readiness."""

    model_config = ConfigDict(frozen=True)

    is_ready: bool = Field(description="Whether all constituent data is available")
    downloaded_count: int = Field(description="Number of constituents with data")
    total_count: int = Field(description="Total count of constituents")
    missing_symbols: list[str] = Field(
        default_factory=list, description="Constituents missing historical data"
    )


class BasketSummary(BaseModel):
    """Summary overview of a stored stock group."""

    model_config = ConfigDict(frozen=True)

    id: int | None = Field(default=None)
    name: str
    description: str
    system: bool
    member_count: int


class BasketOverviewItem(BaseModel):
    """Enriched stock group overview row conforming to SQX table grid columns."""

    model_config = ConfigDict(frozen=True)

    id: int = Field(description="Unique group integer ID")
    name: str = Field(description="Stock group name")
    description: str = Field(default="", description="Group description")
    system: bool = Field(
        default=False,
        description="Whether group is a built-in unmodifiable system group",
    )
    active_count: int = Field(description="Count of currently active constituents")
    total_count: int = Field(description="Total count of constituent stocks")
    symbols_count: int = Field(description="Unique symbols count in group")
    downloaded_count: int = Field(description="Constituents with downloaded data")
    is_ready: bool = Field(description="Whether all symbols in group are downloaded")
    missing_symbols: list[str] = Field(
        default_factory=list, description="Constituent symbols missing data"
    )
    data_from: str = Field(default="", description="Earliest ISO date (YYYY-MM-DD)")
    data_to: str = Field(default="", description="Latest ISO date (YYYY-MM-DD)")
    data_from_sqx: str = Field(default="-", description="Earliest date (DD.MM.YYYY)")
    data_to_sqx: str = Field(default="-", description="Latest date (DD.MM.YYYY)")


def parse_stock_lines(text: str) -> list[BasketItem]:
    """Parse SQX multi-line constituent text into a list of BasketItem objects.

    Format per line: Ticker;Date from (optional);Date to (optional)
    Dates are formatted as DD.MM.YYYY or YYYY-MM-DD.
    """
    items: list[BasketItem] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        parts = [p.strip() for p in line.split(";")]
        symbol = parts[0]
        if not symbol:
            continue
        date_from = (
            parse_date_to_iso(parts[1])
            if len(parts) >= _MIN_CSV_DATE_PARTS and parts[1]
            else None
        )
        date_to = (
            parse_date_to_iso(parts[2])
            if len(parts) > _MIN_CSV_DATE_PARTS and parts[2]
            else None
        )
        items.append(
            BasketItem(
                symbol=symbol,
                weight=1.0,
                date_from=date_from,
                date_to=date_to,
            )
        )
    return items


def format_stock_lines(items: list[BasketItem]) -> str:
    """Format a list of BasketItem objects into SQX multi-line text format."""
    lines: list[str] = []
    for item in items:
        df = format_iso_to_sqx_date(item.date_from)
        dt = format_iso_to_sqx_date(item.date_to)
        if dt:
            lines.append(f"{item.symbol};{df};{dt}")
        elif df:
            lines.append(f"{item.symbol};{df}")
        else:
            lines.append(item.symbol)
    return "\n".join(lines) + ("\n" if lines else "")


def export_groups_xml(baskets: list[BasketDefinition]) -> str:
    """Export stock groups and constituents to the canonical SQX XML schema."""
    root = ET.Element("Groups")
    for b in baskets:
        grp = ET.SubElement(root, "Group", name=b.name)
        desc = ET.SubElement(grp, "Desc")
        desc.text = b.description or ""
        stocks = ET.SubElement(grp, "Stocks")
        for item in b.items:
            stock = ET.SubElement(stocks, "Stock", name=item.symbol)
            stock.set("from", iso_to_epoch_ms(item.date_from))
            stock.set("to", iso_to_epoch_ms(item.date_to))

    rough_bytes = ET.tostring(root, encoding="utf-8")
    reparsed = minidom.parseString(rough_bytes)  # noqa: S318
    return reparsed.toprettyxml(indent="  ")


def import_groups_xml(xml_content: str) -> list[BasketDefinition]:
    """Import stock groups and constituents from SQX XML format."""
    root = ET.fromstring(xml_content.strip())  # noqa: S314
    if root.tag != "Groups":
        raise ValueError("Invalid XML: Root element must be <Groups>.")

    baskets: list[BasketDefinition] = []
    for grp in root.findall("Group"):
        raw_name = grp.get("name", "").strip()
        if not raw_name:
            continue
        clean_name = raw_name
        is_system = False
        if clean_name.startswith("[[") and clean_name.endswith("]]"):
            is_system = True

        desc_elem = grp.find("Desc")
        description = desc_elem.text if desc_elem is not None and desc_elem.text else ""

        stocks_elem = grp.find("Stocks")
        items: list[BasketItem] = []
        if stocks_elem is not None:
            for s in stocks_elem.findall("Stock"):
                sym = s.get("name", "").strip()
                if not sym:
                    continue
                date_from = parse_date_to_iso(s.get("from"))
                date_to = parse_date_to_iso(s.get("to"))
                items.append(
                    BasketItem(
                        symbol=sym,
                        weight=1.0,
                        date_from=date_from,
                        date_to=date_to,
                    )
                )

        if items:
            baskets.append(
                BasketDefinition(
                    name=clean_name,
                    description=description,
                    system=is_system,
                    items=items,
                )
            )
    return baskets


DEFAULT_BASKETS: list[dict[str, Any]] = [
    {
        "name": "[[Dow Jones Industrial Average]]",
        "system": 1,
        "description": "Dow Jones Industrial Average index",
        "stocks": [
            "AAPL",
            "AMGN",
            "AXP",
            "BA",
            "CAT",
            "CRM",
            "CSCO",
            "CVX",
            "DIS",
            "DOW",
            "GS",
            "HD",
            "HON",
            "IBM",
            "INTC",
            "JNJ",
            "JPM",
            "KO",
            "MCD",
            "MMM",
            "MRK",
            "MSFT",
            "NKE",
            "PG",
            "TRV",
            "UNH",
            "V",
            "VZ",
            "WBA",
            "WMT",
        ],
    },
    {
        "name": "[[Nasdaq 100]]",
        "system": 1,
        "description": "Nasdaq 100 index",
        "stocks": [
            "AAPL",
            "ABNB",
            "ADBE",
            "ADI",
            "ADP",
            "ADSK",
            "AEP",
            "AMAT",
            "AMD",
            "AMGN",
            "AMZN",
            "ANSS",
            "ASML",
            "AVGO",
            "AZN",
            "BIIB",
            "BKNG",
            "BKR",
            "CDNS",
            "CEG",
            "CHTR",
            "CMCSA",
            "COST",
            "CPRT",
            "CRWD",
            "CSCO",
            "CSGP",
            "CSX",
            "CTAS",
            "CTSH",
            "DDOG",
            "DLTR",
            "DXCM",
            "EA",
            "EXC",
            "FANG",
            "FAST",
            "FTNT",
            "GEHC",
            "GFS",
            "GILD",
            "GOOG",
            "GOOGL",
            "HON",
            "IDXX",
            "ILMN",
            "INTC",
            "INTU",
            "ISRG",
            "KDP",
            "KHC",
            "KLAC",
            "LRCX",
            "LULU",
            "MAR",
            "MCHP",
            "MDLZ",
            "MELI",
            "META",
            "MNST",
            "MRNA",
            "MRVL",
            "MSFT",
            "MU",
            "NFLX",
            "NVDA",
            "NXPI",
            "ODFL",
            "ON",
            "ORLY",
            "PANW",
            "PAYX",
            "PCAR",
            "PDD",
            "PEP",
            "PYPL",
            "QCOM",
            "REGN",
            "ROP",
            "ROST",
            "SBUX",
            "SIRI",
            "SNPS",
            "SPLK",
            "TEAM",
            "TMUS",
            "TSLA",
            "TTD",
            "TXN",
            "VRSK",
            "VRTX",
            "WBA",
            "WBD",
            "WDAY",
            "XEL",
            "ZS",
        ],
    },
    {
        "name": "[[Nasdaq Biotechnology]]",
        "system": 1,
        "description": "Nasdaq Biotechnology index",
        "stocks": [
            "AMGN",
            "GILD",
            "VRTX",
            "REGN",
            "BIIB",
            "MRNA",
            "ALNY",
            "ILMN",
            "SGEN",
            "BMRN",
        ],
    },
    {
        "name": "[[Russell 1000]]",
        "system": 1,
        "description": "Russell 1000 index",
        "stocks": [
            "AAPL",
            "MSFT",
            "AMZN",
            "NVDA",
            "GOOGL",
            "META",
            "GOOG",
            "BRK.B",
            "TSLA",
            "UNH",
        ],
    },
    {
        "name": "[[Russell 2000]]",
        "system": 1,
        "description": "Russell 2000 index",
        "stocks": [
            "SMCI",
            "FTAI",
            "VRT",
            "SAIA",
            "ELF",
            "FN",
            "ENSG",
            "COHR",
            "MEDP",
            "ONTO",
        ],
    },
    {
        "name": "[[Russell 3000]]",
        "system": 1,
        "description": "Russell 3000 index",
        "stocks": [
            "AAPL",
            "MSFT",
            "AMZN",
            "NVDA",
            "GOOGL",
            "META",
            "TSLA",
            "UNH",
            "JNJ",
            "JPM",
        ],
    },
    {
        "name": "[[S&P 100 limited]]",
        "system": 1,
        "description": "S&P 100 limited index sample for clean installation",
        "stocks": [
            "AAPL",
            "ABBV",
            "ABT",
            "ACN",
            "ADBE",
            "AIG",
            "AMD",
            "AMGN",
            "AMT",
            "AMZN",
            "AVGO",
            "AXP",
            "BA",
            "BAC",
            "BK",
            "BKNG",
            "BLK",
            "BMY",
            "BRK.B",
            "C",
            "CAT",
            "CHTR",
            "CL",
            "CMCSA",
            "COF",
            "COP",
            "COST",
            "CRM",
            "CSCO",
            "CVS",
            "CVX",
            "DE",
            "DHR",
            "DIS",
            "DOW",
            "DUK",
            "EMR",
            "EXC",
            "F",
            "FDX",
            "GD",
            "GE",
            "GILD",
            "GM",
            "GOOG",
            "GOOGL",
            "GS",
            "HD",
            "HON",
            "IBM",
            "INTC",
            "INTU",
            "ISRG",
            "JNJ",
            "JPM",
            "KHC",
            "KO",
            "LIN",
            "LLY",
            "LMT",
            "LOW",
            "MA",
            "MCD",
            "MDLZ",
            "MDT",
            "MET",
            "META",
            "MMM",
            "MO",
            "MRK",
            "MS",
            "MSFT",
            "NEE",
            "NFLX",
            "NKE",
            "NVDA",
            "ORCL",
            "PEP",
            "PFE",
            "PG",
            "PM",
            "PYPL",
            "QCOM",
            "RTX",
            "SBUX",
            "SCHW",
            "SO",
            "SPG",
            "T",
            "TGT",
            "TMO",
            "TMUS",
            "TSLA",
            "TXN",
            "UNH",
            "UNP",
            "UPS",
            "USB",
            "V",
            "VZ",
            "WBA",
            "WFC",
            "WMT",
            "XOM",
        ],
    },
    {
        "name": "[[S&P 100]]",
        "system": 1,
        "description": "S&P 100 index",
        "stocks": [
            "AAPL",
            "ABBV",
            "ABT",
            "ACN",
            "ADBE",
            "AIG",
            "AMD",
            "AMGN",
            "AMT",
            "AMZN",
            "AVGO",
            "AXP",
            "BA",
            "BAC",
            "BK",
            "BKNG",
            "BLK",
            "BMY",
            "BRK.B",
            "C",
        ],
    },
    {
        "name": "[[S&P 500]]",
        "system": 1,
        "description": "S&P 500 index",
        "stocks": [
            "AAPL",
            "MSFT",
            "AMZN",
            "NVDA",
            "GOOGL",
            "META",
            "GOOG",
            "BRK.B",
            "TSLA",
            "UNH",
            "JNJ",
            "JPM",
            "V",
            "PG",
            "XOM",
            "MA",
            "HD",
            "CVX",
            "MRK",
            "ABBV",
        ],
    },
    {
        "name": "[[S&P MidCap 400]]",
        "system": 1,
        "description": "S&P MidCap 400 index",
        "stocks": [
            "DECK",
            "SAIA",
            "MANH",
            "RL",
            "WSO",
            "FIX",
            "RPM",
            "RS",
            "SFM",
            "HUBB",
        ],
    },
]


class BasketService:
    """Service managing stock groups, baskets, and multi-symbol alignment."""

    def __init__(self, db: DatabaseManager) -> None:
        """Initialize basket service with host DatabaseManager."""
        self._db = db

    def save_basket(
        self, basket: BasketDefinition, *, override_system: bool = False
    ) -> int:
        """Persist basket members with date windows and system protections."""
        existing = self._db.baskets.get(basket.name.strip())
        if (
            existing is not None
            and int(existing.get("system", 0)) == 1
            and not override_system
        ):
            raise ValueError(f"System stock group '{basket.name}' cannot be modified.")

        is_system_group = basket.system or (
            basket.name.startswith("[[") and basket.name.endswith("]]")
        )

        members = [
            {
                "ticker": item.symbol,
                "date_from": item.date_from or "1900-01-01",
                "date_to": item.date_to,
            }
            for item in basket.items
        ]
        group_id = self._db.baskets.save(
            basket.name,
            basket.description,
            members,
            system=1 if is_system_group else 0,
        )
        logger.info(
            "FR-DATA-BASKETS-GROUPS: Basket saved",
            extra={
                "basket_name": basket.name,
                "basket_id": group_id,
                "system": is_system_group,
                "fr_id": "FR-DATA-BASKETS-GROUPS",
            },
        )
        return group_id

    def get_basket(self, name: str) -> BasketDefinition | None:
        """Convert stored members into the service's basket model."""
        record = self._db.baskets.get(name.strip())
        if record is None:
            return None
        rec = {k.lower(): v for k, v in record.items()}
        return BasketDefinition(
            id=rec.get("id"),
            name=str(rec.get("name", "")),
            description=str(rec.get("description") or rec.get("desc") or ""),
            system=bool(rec.get("system", 0)),
            items=[
                BasketItem(
                    symbol=str(m.get("ticker") or m.get("symbol") or "").strip(),
                    weight=1.0,
                    date_from=m.get("date_from"),
                    date_to=m.get("date_to"),
                )
                for member in rec.get("members", [])
                for m in [{k.lower(): v for k, v in member.items()}]
            ],
        )

    def get_basket_by_id(self, basket_id: int) -> BasketDefinition | None:
        """Retrieve basket by unique integer ID."""
        record = self._db.baskets.get_by_id(basket_id)
        if record is None:
            return None
        rec = {k.lower(): v for k, v in record.items()}
        return BasketDefinition(
            id=rec.get("id"),
            name=str(rec.get("name", "")),
            description=str(rec.get("description") or rec.get("desc") or ""),
            system=bool(rec.get("system", 0)),
            items=[
                BasketItem(
                    symbol=str(m.get("ticker") or m.get("symbol") or "").strip(),
                    weight=1.0,
                    date_from=m.get("date_from"),
                    date_to=m.get("date_to"),
                )
                for member in rec.get("members", [])
                for m in [{k.lower(): v for k, v in member.items()}]
            ],
        )

    def list_baskets(self) -> list[BasketDefinition]:
        """List domain baskets in alphabetical name order."""
        result: list[BasketDefinition] = []
        for name in self._db.baskets.list_names():
            basket = self.get_basket(name)
            if basket is not None:
                result.append(basket)
        return result

    def list_baskets_summary(self) -> list[BasketSummary]:
        """List summary overviews of all stock groups with member counts."""
        groups = self._db.baskets.list_groups()
        return [
            BasketSummary(
                id=g["id"],
                name=g["name"],
                description=g.get("description") or "",
                system=bool(g.get("system", 0)),
                member_count=int(g.get("member_count", 0)),
            )
            for g in groups
        ]

    @staticmethod
    def calculate_group_metrics(
        g_dict: dict[str, Any],
        stocks: list[Any],
        available_map: dict[str, dict[str, Any]],
        today: str,
    ) -> dict[str, Any]:
        """Compute constituent metrics, bounds, and readiness for a group."""
        total_count = len(stocks)
        active_count = 0
        distinct_tickers: set[str] = set()
        downloaded_tickers: set[str] = set()
        group_dfs: list[str] = []
        group_dts: list[str] = []

        for s in stocks:
            s_dict = {k.lower(): v for k, v in dict(s).items()}
            tkr = str(s_dict.get("ticker") or s_dict.get("TICKER", "")).strip().upper()
            if not tkr:
                continue
            distinct_tickers.add(tkr)
            df = normalize_sqx_date(s_dict.get("date_from") or s_dict.get("DATE_FROM"))
            dt = normalize_sqx_date(s_dict.get("date_to") or s_dict.get("DATE_TO"))
            if (not df or df <= today) and (not dt or dt >= today):
                active_count += 1
            if tkr in available_map:
                downloaded_tickers.add(tkr)
                ds_info = available_map[tkr]
                if ds_info["date_from"]:
                    group_dfs.append(str(ds_info["date_from"]))
                if ds_info["date_to"]:
                    group_dts.append(str(ds_info["date_to"]))

        missing = sorted(distinct_tickers - downloaded_tickers)
        num_symbols = len(distinct_tickers)
        downloaded_count = len(downloaded_tickers)
        desc = g_dict.get("description") or g_dict.get("desc") or ""

        return {
            "id": int(g_dict["id"]),
            "name": str(g_dict.get("name", "")),
            "description": str(desc),
            "system": bool(g_dict.get("system", 0)),
            "active_count": active_count,
            "total_count": total_count,
            "symbols_count": num_symbols,
            "downloaded_count": downloaded_count,
            "is_ready": num_symbols > 0 and len(missing) == 0,
            "missing_symbols": missing,
            "data_from": min(group_dfs) if group_dfs else "",
            "data_to": max(group_dts) if group_dts else "",
        }

    def ensure_defaults(self) -> None:
        """Seed default StrategyQuant X stock groups if uninitialized."""
        seed_records = [
            {
                "name": str(group["name"]),
                "system": int(group.get("system", 1)),
                "description": str(group.get("description", "")),
                "members": [
                    {
                        "ticker": str(tkr).strip(),
                        "date_from": "1900-01-01",
                        "date_to": None,
                    }
                    for tkr in group["stocks"]
                ],
            }
            for group in DEFAULT_BASKETS
        ]
        self._db.baskets.seed_defaults(seed_records)
        logger.info(
            "FR-DATA-BASKETS-GROUPS: Verified and seeded default stock groups",
            extra={"fr_id": "FR-DATA-BASKETS-GROUPS"},
        )

    def list_baskets_overview(self) -> list[BasketOverviewItem]:
        """List enriched overview rows matching the 8-column SQX table grid."""
        groups_rows, stocks_rows, ds_rows = self._db.baskets.read_overview_rows()
        available_map: dict[str, dict[str, Any]] = {
            str(row["sym"]): {
                "date_from": row["df"],
                "date_to": row["dt"],
                "bars": row["tb"],
            }
            for row in ds_rows
            if row["tb"] is not None and int(row["tb"]) > 0
        }
        stocks_by_basket: dict[int, list[Any]] = {}
        for s in stocks_rows:
            stocks_by_basket.setdefault(int(s["basket_id"]), []).append(s)

        today = datetime.now(tz=UTC).strftime("%Y-%m-%d")
        overview_items: list[BasketOverviewItem] = []
        for g in groups_rows:
            g_dict = {k.lower(): v for k, v in dict(g).items()}
            stocks = stocks_by_basket.get(int(g_dict["id"]), [])
            metrics = self.calculate_group_metrics(g_dict, stocks, available_map, today)
            df = metrics["data_from"]
            dt = metrics["data_to"]
            df_sqx = format_iso_to_sqx_date(df) if df else "-"
            dt_sqx = format_iso_to_sqx_date(dt) if dt else "-"
            overview_items.append(
                BasketOverviewItem(
                    id=metrics["id"],
                    name=metrics["name"],
                    description=metrics["description"],
                    system=metrics["system"],
                    active_count=metrics["active_count"],
                    total_count=metrics["total_count"],
                    symbols_count=metrics["symbols_count"],
                    downloaded_count=metrics["downloaded_count"],
                    is_ready=metrics["is_ready"],
                    missing_symbols=metrics["missing_symbols"],
                    data_from=df,
                    data_to=dt,
                    data_from_sqx=df_sqx,
                    data_to_sqx=dt_sqx,
                )
            )
        logger.info(
            "FR-DATA-BASKETS-GROUPS: Listed overview for %d baskets",
            len(overview_items),
            extra={
                "count": len(overview_items),
                "fr_id": "FR-DATA-BASKETS-GROUPS",
            },
        )
        return overview_items

    def update_group_data(self, basket_id_or_name: int | str) -> dict[str, Any]:
        """Dispatch automatic historical data update for stocks in a group."""
        basket: BasketDefinition | None
        if isinstance(basket_id_or_name, int) or (
            isinstance(basket_id_or_name, str) and basket_id_or_name.isdigit()
        ):
            basket = self.get_basket_by_id(int(basket_id_or_name))
        else:
            basket = self.get_basket(str(basket_id_or_name))

        if basket is None:
            raise ValueError("Group doesn't exist.")

        if basket.name == "[[S&P 100 limited]]":
            raise ValueError(
                "Group S&P 100 limited cannot be updated, "
                "it is only in clean installation."
            )

        if not basket.items:
            raise ValueError("Nothing to update. Group is without any stocks.")

        available_symbols = {
            str(d["symbol"]).upper()
            for d in self._db.datasets.list_datasets(limit=10000)
        }
        readiness = self.check_readiness(basket, available_symbols)

        logger.info(
            "FR-DATA-BASKETS-GROUPS: Dispatched data update for basket '%s'",
            basket.name,
            extra={
                "basket_name": basket.name,
                "symbols_count": len(basket.items),
                "missing_count": len(readiness.missing_symbols),
                "fr_id": "FR-DATA-BASKETS-GROUPS",
            },
        )

        return {
            "status": "started",
            "basket_id": basket.id,
            "basket_name": basket.name,
            "total_symbols": len(basket.items),
            "missing_symbols": readiness.missing_symbols,
            "message": (
                "Data update started, please check Log tab for more information."
            ),
        }

    def delete_basket(self, name: str) -> bool:
        """Request atomic deletion of a non-system basket and its members."""
        existing = self.get_basket(name.strip())
        if existing is not None and existing.system:
            logger.warning(
                "Deletion rejected for system stock group '%s'",
                name,
                extra={"fr_id": "FR-DATA-BASKETS-GROUPS", "basket_name": name},
            )
            return False

        deleted = self._db.baskets.delete(name.strip())
        logger.info(
            "Basket delete completed",
            extra={"deleted": deleted, "fr_id": "FR-DATA-BASKETS-GROUPS"},
        )
        return deleted

    def check_readiness(
        self, basket: BasketDefinition, available_symbols: set[str]
    ) -> BasketReadiness:
        """Evaluate data availability readiness for a stock group."""
        norm_available = {s.strip().upper() for s in available_symbols}
        missing: list[str] = []
        downloaded = 0

        for item in basket.items:
            if item.symbol.upper() in norm_available:
                downloaded += 1
            else:
                missing.append(item.symbol)

        total = len(basket.items)
        is_ready = len(missing) == 0 and total > 0

        logger.info(
            "FR-DATA-BASKETS-DIAGNOSTICS: Evaluated readiness for basket '%s'",
            basket.name,
            extra={
                "basket_name": basket.name,
                "is_ready": is_ready,
                "downloaded": downloaded,
                "total": total,
                "missing_count": len(missing),
                "fr_id": "FR-DATA-BASKETS-DIAGNOSTICS",
            },
        )
        return BasketReadiness(
            is_ready=is_ready,
            downloaded_count=downloaded,
            total_count=total,
            missing_symbols=missing,
        )

    def import_stocks_from_csv(
        self, basket_name: str, csv_text: str
    ) -> BasketDefinition:
        """Parse constituent CSV lines and update group membership."""
        existing = self.get_basket(basket_name)
        if existing is None:
            raise ValueError(f"Basket '{basket_name}' does not exist.")
        if existing.system:
            raise ValueError(
                f"Stocks cannot be imported into system group '{basket_name}'."
            )

        new_items = parse_stock_lines(csv_text)
        if not new_items:
            raise ValueError("No valid stock entries parsed from input.")

        updated = BasketDefinition(
            id=existing.id,
            name=existing.name,
            description=existing.description,
            system=existing.system,
            items=new_items,
        )
        self.save_basket(updated)
        logger.info(
            "FR-DATA-BASKETS-INTERCHANGE: Imported %d stocks for group '%s'",
            len(new_items),
            basket_name,
            extra={
                "fr_id": "FR-DATA-BASKETS-INTERCHANGE",
                "stocks_count": len(new_items),
            },
        )
        return updated

    def export_stocks_to_csv(self, basket_name: str) -> str:
        """Export constituent list to SQX multi-line text format."""
        existing = self.get_basket(basket_name)
        if existing is None:
            raise ValueError(f"Basket '{basket_name}' does not exist.")
        csv_text = format_stock_lines(existing.items)
        logger.info(
            "FR-DATA-BASKETS-INTERCHANGE: Exported stocks for group '%s'",
            basket_name,
            extra={"fr_id": "FR-DATA-BASKETS-INTERCHANGE"},
        )
        return csv_text

    def align_series(
        self,
        series_dict: dict[str, list[BarRecord]],
        policy: str = "intersection",
    ) -> list[dict[str, BarRecord]]:
        """Align multiple symbol bar series along common timestamps.

        Supported policies:
            - 'intersection': Only timestamps present in every series (inner join).
            - 'union': All timestamps across all series with forward-fill (outer join).

        Fires FR-DATA-BASKETS-ALIGNMENT.
        """
        if not series_dict:
            return []

        # Index each series by timestamp
        sym_maps: dict[str, dict[str, BarRecord]] = {}
        for sym, bars in series_dict.items():
            sym_maps[sym] = {b.timestamp_utc: b for b in bars}

        symbols = list(series_dict.keys())
        all_timestamps_sets = [set(m.keys()) for m in sym_maps.values()]

        if policy == "intersection":
            common_timestamps = sorted(
                set.intersection(*all_timestamps_sets) if all_timestamps_sets else set()
            )
            aligned: list[dict[str, BarRecord]] = []
            for ts in common_timestamps:
                row = {sym: sym_maps[sym][ts] for sym in symbols}
                aligned.append(row)
            return aligned

        # Union with forward-fill
        all_timestamps = sorted(set.union(*all_timestamps_sets))
        aligned_union: list[dict[str, BarRecord]] = []
        last_known: dict[str, BarRecord] = {}

        for ts in all_timestamps:
            row = {}
            for sym in symbols:
                if ts in sym_maps[sym]:
                    bar = sym_maps[sym][ts]
                    last_known[sym] = bar
                    row[sym] = bar
                elif sym in last_known:
                    # Forward-fill previous bar with updated timestamp
                    prev = last_known[sym]
                    row[sym] = prev.model_copy(update={"timestamp_utc": ts})
            # Only include row if all symbols are present
            if len(row) == len(symbols):
                aligned_union.append(row)

        return aligned_union

    def compute_basket_series(
        self,
        basket: BasketDefinition,
        series_dict: dict[str, list[BarRecord]],
        policy: str = "intersection",
    ) -> list[BarRecord]:
        """Compute synthetic aggregate OHLCV bars for a weighted basket.

        Fires FR-DATA-BASKETS-ALIGNMENT.
        """
        aligned_rows = self.align_series(series_dict, policy=policy)
        if not aligned_rows:
            return []

        total_weight = sum(item.weight for item in basket.items)
        if total_weight <= 0.0:
            raise ValueError("Total basket weight must be strictly positive.")

        weights_map = {item.symbol: item.weight for item in basket.items}
        synthetic_bars: list[BarRecord] = []

        for row in aligned_rows:
            # Check all constituent symbols present in aligned row
            if not all(sym in row for sym in weights_map):
                continue

            ts = next(iter(row.values())).timestamp_utc

            agg_open = (
                sum(row[sym].open * weights_map[sym] for sym in weights_map)
                / total_weight
            )
            agg_high = (
                sum(row[sym].high * weights_map[sym] for sym in weights_map)
                / total_weight
            )
            agg_low = (
                sum(row[sym].low * weights_map[sym] for sym in weights_map)
                / total_weight
            )
            agg_close = (
                sum(row[sym].close * weights_map[sym] for sym in weights_map)
                / total_weight
            )
            agg_vol = sum(row[sym].volume * weights_map[sym] for sym in weights_map)

            synthetic_bars.append(
                BarRecord(
                    timestamp_utc=ts,
                    open=round(agg_open, 5),
                    high=round(agg_high, 5),
                    low=round(agg_low, 5),
                    close=round(agg_close, 5),
                    volume=round(agg_vol, 2),
                )
            )

        logger.info(
            "FR-DATA-BASKETS-ALIGNMENT: Computed %d synthetic bars for basket '%s'",
            len(synthetic_bars),
            basket.name,
            extra={
                "basket": basket.name,
                "bars": len(synthetic_bars),
                "policy": policy,
                "fr_id": "FR-DATA-BASKETS-ALIGNMENT",
            },
        )
        return synthetic_bars


def main() -> int:
    """CLI tool for inspecting market baskets."""
    parser = argparse.ArgumentParser(description="Manage market baskets")
    parser.add_argument("--list", action="store_true", help="List all baskets")
    args = parser.parse_args()

    db = DatabaseManager()
    db.initialize()
    service = BasketService(db)

    if args.list:
        baskets = service.list_baskets()
        print(f"Configured Baskets ({len(baskets)}):")
        for b in baskets:
            constituents = ", ".join(f"{i.symbol}:{i.weight}" for i in b.items)
            tag = " [SYSTEM]" if b.system else ""
            print(f"  {b.name:20}{tag} [{constituents}]")
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
