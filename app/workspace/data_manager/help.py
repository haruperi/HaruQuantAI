"""Data Manager contextual help, tutorials, and documentation articles.

Description:
    Provides topic-based guidance, interactive tutorial steps, and links to
    external documentation for all Data Manager workspace features.
    Matches the StrategyQuant X DataManagerHelp donor plugin and powers the
    HelpTooltip UI component.

Key Capabilities:
    - Contextual topic help across all 11 workspace tabs
    - Donor help article links (MetaTrader 4/5 integration, tick precision)
    - Step-by-step tutorials with test IDs
    - Keyword search across documentation and tutorials
    - Optional thread-safe user notes per topic

Python API Usage:
    help_service = Help()
    guide = help_service.get_topic("overview")
    topics = help_service.list_topics()
    tutorials = help_service.list_tutorials()
    articles = help_service.list_articles()
"""

from __future__ import annotations

import time
from datetime import UTC, datetime
from threading import RLock
from typing import Any

from app.host.persistence import HostPersistence
from app.host.response import (
    ErrorCode,
    ResponseMetadata,
    StandardError,
    StandardResponse,
)

__all__ = ["Help"]

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
            "Up to five named output lines with MT4, MT5, and EasyLanguage",
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
        "title": "Import history data from MetaTrader 4",
        "url": (
            "https://strategyquant.com/doc/quantdatamanager/"
            "import-history-data-metatrader-4/"
        ),
        "topic": "import",
        "summary": (
            "Extracting historical price history from an existing MT4 terminal "
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
            "Define up to five named lines and platform codes (MT4/MT5/EL).",
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


class Help:
    """Contextual guidance, donor links, and tutorials for Data Manager."""

    def __init__(
        self,
        persistence: HostPersistence | None = None,
        *,
        logs: Any | None = None,
    ) -> None:
        self.gateway = persistence
        self.logs = logs
        self._user_notes: dict[str, dict[str, Any]] = {}
        self._lock = RLock()

    @staticmethod
    def _result(
        operation: str,
        started: float,
        data: Any = None,
        *,
        error: str = "",
        code: ErrorCode = ErrorCode.VALIDATION,
    ) -> dict[str, Any]:
        duration_ms = (time.perf_counter() - started) * 1000
        metadata = ResponseMetadata(
            operation=f"help.{operation}",
            duration_ms=duration_ms,
        )
        if error:
            return StandardResponse.failure(
                message=error,
                metadata=metadata,
                error=StandardError(code=code, message=error),
            )
        return StandardResponse.success(
            message="Data Manager help operation completed",
            metadata=metadata,
            data=data,
        )

    def get_topic(self, topic: str = _TOPIC_OVERVIEW) -> dict[str, Any]:
        """Return the contextual HelpGuidePayload for a given topic."""
        started = time.perf_counter()
        normalized = (topic or _TOPIC_OVERVIEW).strip().lower()
        if normalized not in _TOPICS:
            normalized = _TOPIC_OVERVIEW

        definition = _TOPICS[normalized]
        available_topics = list(_TOPICS.keys())

        tutorials = [
            t
            for t in _TUTORIALS
            if t.get("topic") == normalized or normalized == "overview"
        ]
        if not tutorials:
            tutorials = [t for t in _TUTORIALS if t.get("test_id")]

        articles = [
            a
            for a in _DONOR_ARTICLES
            if a.get("topic") == normalized or normalized == "overview"
        ]
        if not articles:
            articles = _DONOR_ARTICLES

        with self._lock:
            note_entry = self._user_notes.get(normalized)
            note = note_entry.get("note") if note_entry else None

        payload = {
            "topic": normalized,
            "title": definition["title"],
            "summary": definition["summary"],
            "tab": definition["tab"],
            "available_topics": available_topics,
            "key_capabilities": definition.get("key_capabilities", []),
            "tutorials": tutorials,
            "links": articles,
            "user_note": note,
        }
        return self._result("get_topic", started, data=payload)

    def list_topics(self) -> dict[str, Any]:
        """Return a catalog of all supported Data Manager topics."""
        started = time.perf_counter()
        items = [
            {
                "topic": key,
                "title": value["title"],
                "tab": value["tab"],
                "summary": value["summary"],
                "key_capabilities": value.get("key_capabilities", []),
            }
            for key, value in _TOPICS.items()
        ]
        return self._result(
            "list_topics", started, data={"topics": items, "count": len(items)}
        )

    def list_articles(self, topic: str | None = None) -> dict[str, Any]:
        """Return StrategyQuant X donor help articles, optionally filtered."""
        started = time.perf_counter()
        norm = topic.strip().lower() if topic else None
        articles = [
            a for a in _DONOR_ARTICLES if norm is None or a.get("topic") == norm
        ]
        return self._result(
            "list_articles",
            started,
            data={"articles": articles, "count": len(articles)},
        )

    def list_tutorials(self, topic: str | None = None) -> dict[str, Any]:
        """Return interactive tutorials, optionally filtered by topic."""
        started = time.perf_counter()
        norm = topic.strip().lower() if topic else None
        tutorials = [t for t in _TUTORIALS if norm is None or t.get("topic") == norm]
        return self._result(
            "list_tutorials",
            started,
            data={"tutorials": tutorials, "count": len(tutorials)},
        )

    def get_tutorial(self, tutorial_id: str) -> dict[str, Any]:
        """Return a single tutorial by ID."""
        started = time.perf_counter()
        clean_id = (tutorial_id or "").strip().lower()
        found = next((t for t in _TUTORIALS if t["id"].lower() == clean_id), None)
        if not found:
            return self._result(
                "get_tutorial",
                started,
                error=f"Tutorial '{tutorial_id}' not found.",
                code=ErrorCode.NOT_FOUND,
            )
        return self._result("get_tutorial", started, data=found)

    def search(self, query: str) -> dict[str, Any]:
        """Search across topics, summaries, tutorials, and articles."""
        started = time.perf_counter()
        clean = (query or "").strip().lower()
        if not clean:
            return self._result(
                "search",
                started,
                error="Search query cannot be empty.",
                code=ErrorCode.VALIDATION,
            )

        matched_topics = [
            {"topic": k, "title": v["title"], "summary": v["summary"]}
            for k, v in _TOPICS.items()
            if clean in k
            or clean in v["title"].lower()
            or clean in v["summary"].lower()
        ]

        matched_tutorials = [
            t
            for t in _TUTORIALS
            if clean in t["id"].lower()
            or clean in t["title"].lower()
            or clean in t["summary"].lower()
            or any(clean in step.lower() for step in t.get("steps", []))
        ]

        matched_articles = [
            a
            for a in _DONOR_ARTICLES
            if clean in a["title"].lower()
            or clean in a["summary"].lower()
            or clean in a["url"].lower()
        ]

        data = {
            "query": query,
            "topics": matched_topics,
            "tutorials": matched_tutorials,
            "articles": matched_articles,
            "total_matches": (
                len(matched_topics) + len(matched_tutorials) + len(matched_articles)
            ),
        }
        return self._result("search", started, data=data)

    def set_topic_note(self, topic: str, note: str) -> dict[str, Any]:
        """Persist a custom user note for a topic."""
        started = time.perf_counter()
        normalized = (topic or "").strip().lower()
        if normalized not in _TOPICS:
            return self._result(
                "set_topic_note",
                started,
                error=f"Topic '{topic}' is not a valid Data Manager topic.",
                code=ErrorCode.NOT_FOUND,
            )
        if len(note) > _MAX_NOTE_LENGTH:
            return self._result(
                "set_topic_note",
                started,
                error="Note cannot exceed 10,000 characters.",
                code=ErrorCode.VALIDATION,
            )

        now = datetime.now(UTC).isoformat()
        with self._lock:
            self._user_notes[normalized] = {"note": note, "updated_at": now}

        return self._result(
            "set_topic_note",
            started,
            data={"topic": normalized, "note": note, "updated_at": now},
        )

    def get_topic_note(self, topic: str) -> dict[str, Any]:
        """Retrieve the persisted user note for a topic."""
        started = time.perf_counter()
        normalized = (topic or "").strip().lower()
        with self._lock:
            entry = self._user_notes.get(normalized)
            note = entry.get("note") if entry else None

        return self._result(
            "get_topic_note", started, data={"topic": normalized, "note": note}
        )

    def reset_defaults(self, topic: str | None = None) -> dict[str, Any]:
        """Clear user notes and reset to built-in guidance."""
        started = time.perf_counter()
        norm = topic.strip().lower() if topic else None
        with self._lock:
            if norm:
                self._user_notes.pop(norm, None)
            else:
                self._user_notes.clear()

        return self._result(
            "reset_defaults",
            started,
            data={"topic": topic or "all", "status": "defaults_restored"},
        )
