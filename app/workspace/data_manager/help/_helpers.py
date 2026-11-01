"""Data Manager contextual help topics, donor articles, and tutorial definitions."""

from __future__ import annotations

from typing import Any

_TOPIC_OVERVIEW = "overview"
_MAX_NOTE_LENGTH = 10_000

# The 11 Data Manager workspace topics
_TOPICS: dict[str, dict[str, Any]] = {
    "overview": {
        "title": "Data Manager Overview",
        "tab": "Home",
        "summary": (
            "Centralized market data management for historical testing, "
            "evaluation, and symbol setup."
        ),
        "key_capabilities": [
            "Download historical tick and bar data from high-quality sources",
            "Maintain symbol specifications, tick sizes, and sessions",
            "Export data to MetaTrader 4, MetaTrader 5, and standard CSV",
            "Manage custom indicators, COT reports, and stock groups",
        ],
    },
    "data": {
        "title": "Data Sources & Market Feeds",
        "tab": "Data sources",
        "summary": (
            "Connect, configure, and download historical data from multiple "
            "market data providers."
        ),
        "key_capabilities": [
            "Free and premium downloaders (Dukascopy, Yahoo, Crypto)",
            "Direct import from MetaTrader 4, MetaTrader 5, and file archives",
            "Automatic data updating and coverage inspection",
        ],
    },
    "import": {
        "title": "File & Feed Data Import",
        "tab": "Data sources",
        "summary": (
            "Import historical bars and ticks from custom CSV/TSV files and "
            "external sources."
        ),
        "key_capabilities": [
            "Configurable CSV column mapping, separator, and date format presets",
            "Header skipping and error handling options (abort or skip)",
            "Automatic timeframe and interval detection with preview",
        ],
    },
    "export": {
        "title": "Multi-Format Data Export",
        "tab": "Export",
        "summary": (
            "Generate export artifacts for external trading platforms and "
            "research tools."
        ),
        "key_capabilities": [
            "Export to MetaTrader 4 (HST bar files and FXT tick archives)",
            "Export to MetaTrader 5 (custom symbol tick data for 99% tests)",
            "Standard CSV/TSV export with customizable column order",
        ],
    },
    "symbols": {
        "title": "Symbol Specifications & Pip Rules",
        "tab": "Symbols",
        "summary": (
            "Define financial instrument contracts, pip sizes, point values, "
            "spreads, and margins."
        ),
        "key_capabilities": [
            "Support for Forex, Indices, Equities, Commodities, and Crypto",
            "Live update and synchronization from MetaTrader 5 terminals",
            "CSV catalog import, export, and symbol cloning",
        ],
    },
    "sessions": {
        "title": "Trading Sessions & Holidays",
        "tab": "Sessions",
        "summary": (
            "Configure trading hours, daily windows, and exchange holiday calendars."
        ),
        "key_capabilities": [
            "Weekly day-by-day active trading time intervals",
            "Exchange holiday exclusion schedules",
            "Timezone conversion and session cloning",
        ],
    },
    "brokers": {
        "title": "Broker Profiles & Server Clocks",
        "tab": "Broker profiles",
        "summary": (
            "Model broker-specific execution rules, timezone offsets, and "
            "symbol postfixes."
        ),
        "key_capabilities": [
            "Server clock policies and daylight saving time rules",
            "Symbol prefix/postfix mapping (e.g. .raw, _pro)",
            "Stock picker eligibility and custom symbol overrides",
        ],
    },
    "custom-data": {
        "title": "External Indicators & COT Data",
        "tab": "External indicators",
        "summary": (
            "Manage external indicator definitions, custom signals, and "
            "CFTC COT reports."
        ),
        "key_capabilities": [
            "Up to five named output lines with MT5 and EasyLanguage",
            "CFTC legacy futures Commitments of Traders (COT) annual reports",
            "MQL source recognition (#property indicator_label)",
            "Dated observation import, review, and JSON transfers",
        ],
    },
    "stock-groups": {
        "title": "Stock Groups & Baskets",
        "tab": "Stock groups",
        "summary": (
            "Organize equities into watchlists and index compositions with "
            "historical membership."
        ),
        "key_capabilities": [
            "Time-ranged stock membership (ticker, date from, date to)",
            "Automatic data updating for all basket members",
            "Membership CSV import/export and JSON group transfers",
        ],
    },
    "log": {
        "title": "Activity History & Task Progress",
        "tab": "Log",
        "summary": (
            "Monitor active and completed background downloads, imports, and updates."
        ),
        "key_capabilities": [
            "Real-time task progress and status tracking",
            "Detailed operational log history with error highlighting",
            "Log filtering, bounded memory retention, and clearing",
        ],
    },
    "chart": {
        "title": "History Inspection & Resampling",
        "tab": "Chart",
        "summary": (
            "Inspect historical price bars and volume charts across multiple "
            "timeframes."
        ),
        "key_capabilities": [
            "Candlestick and bar rendering with responsive zooming and panning",
            "Multi-timeframe dynamic resampling (M1, M5, H1, D1)",
            "Technical indicator overlays and inspection tools",
        ],
    },
}

# Donor documentation articles from SQX DataManagerHelp (help.html)
_DONOR_ARTICLES: list[dict[str, Any]] = [
    {
        "id": "tick-precision-testing",
        "test_id": "dm-help-openlink-btn",
        "title": "Test strategy in MetaTrader 4 with tick precision",
        "url": (
            "https://strategyquant.com/doc/quantdatamanager/"
            "test-strategy-metatrader-4-tick-precision/"
        ),
        "topic": "export",
        "summary": (
            "Guide on generating 99% tick-precision FXT files for "
            "MetaTrader 4 strategy evaluation."
        ),
    },
    {
        "id": "platform-data-export",
        "test_id": "dm-help-openlink-btn-2",
        "title": (
            "How to export data from Quant Data Manager and import to Metatrader 5"
        ),
        "url": (
            "https://strategyquant.com/doc/quantdatamanager/"
            "how-to-import-data-to-metatrader-5/"
        ),
        "topic": "export",
        "summary": (
            "Step-by-step export of high-resolution bar and tick data for "
            "MetaTrader 5 custom symbols."
        ),
    },
    {
        "id": "historical-data-import",
        "test_id": "dm-help-openlink-btn-3",
        "title": "Import history data from MetaTrader 5",
        "url": (
            "https://strategyquant.com/doc/quantdatamanager/"
            "import-history-data-metatrader-5/"
        ),
        "topic": "import",
        "summary": (
            "Extracting historical price history from an existing MT5 terminal "
            "installation into Data Manager."
        ),
    },
]

# Step-by-step tutorials matching DEFAULT_DM_TUTORIALS and domain extensions
_TUTORIALS: list[dict[str, Any]] = [
    {
        "id": "tick-precision-testing",
        "test_id": "dm-help-openlink-btn",
        "title": "Test strategies with tick precision",
        "topic": "export",
        "summary": "Configure tick-level datasets and verify symbol spread rules.",
        "steps": [
            "Select a tick or M1 dataset in Data sources.",
            "Verify point value, tick size, and decimals in Symbols.",
            "Export or link the dataset for high-precision evaluation.",
        ],
    },
    {
        "id": "platform-data-export",
        "test_id": "dm-help-openlink-btn-2",
        "title": "Export data from Data Manager to external trading platforms",
        "topic": "export",
        "summary": ("Generate formatted bar and tick archives for external terminals."),
        "steps": [
            "Select one or more saved datasets in the Data table.",
            "Open the Export ribbon tab and select the target format.",
            "Confirm date boundaries and download the exported artifacts.",
        ],
    },
    {
        "id": "historical-data-import",
        "test_id": "dm-help-openlink-btn-3",
        "title": "Import historical bar and tick data from files",
        "topic": "import",
        "summary": ("Create a file symbol record and parse custom OHLCV CSV files."),
        "steps": [
            "Add a symbol definition mapped to an existing Symbol.",
            "Choose Import data file and verify column and date formatting.",
            "Inspect the imported record count and preview bars in Chart.",
        ],
    },
    {
        "id": "symbol-setup",
        "title": "Set up a new trading instrument",
        "topic": "symbols",
        "summary": "Configure point values, pip sizes, spreads, and margins.",
        "steps": [
            "Navigate to the Symbols tab and click Add Symbol.",
            "Enter the instrument name, broker datasource suffix, and category.",
            "Configure point value, pip size, contract size, and margins.",
            "Save the specification to validate spread and sizing bounds.",
        ],
    },
    {
        "id": "external-indicator-setup",
        "title": "Import external indicator values",
        "topic": "custom-data",
        "summary": (
            "Define custom indicator output lines and import timestamped values."
        ),
        "steps": [
            "Navigate to External indicators and click Add new or Recognize.",
            "Define up to five named lines and platform codes (MT5/EL).",
            "Click Import indicator data and map date and line columns.",
            "Inspect observations using View & Analyze.",
        ],
    },
    {
        "id": "stock-basket-setup",
        "title": "Create a stock group and update data",
        "topic": "stock-groups",
        "summary": "Manage an equity watchlist and synchronize member data.",
        "steps": [
            "Navigate to Stock groups and click Add new.",
            "Enter a name and click Edit stocks to specify member tickers.",
            "Set date-from and date-to ranges for historical constituents.",
            "Click Update data in group to trigger automated member downloads.",
        ],
    },
]


__all__ = [
    "_DONOR_ARTICLES",
    "_MAX_NOTE_LENGTH",
    "_TOPICS",
    "_TOPIC_OVERVIEW",
    "_TUTORIALS",
]
