"""Built-in contextual documentation and user guide for Data Manager.

Description:
    Provides offline-ready contextual documentation, topic summaries, and
    step-by-step tutorials for market data acquisition, inspection, catalog
    governance, and multi-format export within the Data Manager workspace.

Purpose:
    FEAT-DATAMGR-HELP: Built-in documentation and user guide for Data Manager.

Key Capabilities:
    - FR-DATAMGR-HELP-GUIDE: Contextual help guide (DMHelp.help -> INFO/WARNING).

Python API Usage:
    ```python
    from app.workspace.data_manager.help import DMHelp, DMHelpCLI

    print(DMHelpCLI.format_help_guide(DMHelp().help("overview")))
    ```

CLI Usage:
    ```bash
    uv run python -m app.workspace.data_manager.help
    ```
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from app.host.logging import get_logger

__all__ = ["DMHelp", "DMHelpCLI"]

logger = get_logger(__name__)
GUIDE_FR = "FR-DATAMGR-HELP-GUIDE"

_TOPICS: dict[str, tuple[str, str]] = {
    "overview": ("Data Manager Overview", "Download, import, and export market data."),
    "data": ("Historical Data Sources", "Manage datasets and download market history."),
    "import": ("Data File Import", "Map file symbols and import CSV or tick data."),
    "export": ("Multi-Format Data Export", "Export selected datasets to target files."),
    "instruments": ("Instruments Catalog", "Configure point values, ticks, and costs."),
    "sessions": ("Trading Sessions", "Define session hours, breaks, and holidays."),
    "brokers": ("Broker Profiles", "Manage broker timezones and symbol postfixes."),
    "custom-data": ("External Indicators", "Register external indicators and series."),
    "stock-groups": ("Stock Groups & Baskets", "Organize stock groups and baskets."),
    "log": ("Operation Log & Progress", "Monitor download, import, and export status."),
    "chart": ("Recorded History Preview", "Inspect saved OHLCV bars in chart views."),
}


def _tut(tid: str, btn: str, title: str, info: str, *steps: str) -> dict[str, Any]:
    return {"id": tid, "test_id": btn, "title": title, "summary": info, "steps": steps}


_TUTORIALS: tuple[dict[str, Any], ...] = (
    _tut(
        "tick-precision-testing",
        "dm-help-openlink-btn",
        "Test strategies with tick precision",
        "Configure tick-level datasets and verify instrument spread rules.",
        "Select a tick or M1 dataset in Data sources.",
        "Verify point value, tick size, and decimals in Instruments.",
        "Export or link the dataset for high-precision evaluation.",
    ),
    _tut(
        "platform-data-export",
        "dm-help-openlink-btn-2",
        "Export data from Data Manager to external trading platforms",
        "Generate formatted bar and tick archives for external terminals.",
        "Select one or more saved datasets in the Data table.",
        "Open the Export ribbon tab and select the target format.",
        "Confirm date boundaries and download the exported artifacts.",
    ),
    _tut(
        "historical-data-import",
        "dm-help-openlink-btn-3",
        "Import historical bar and tick data from files",
        "Create a file symbol record and parse custom OHLCV CSV files.",
        "Add a symbol definition mapped to an existing Instrument.",
        "Choose Import data file and verify column and date formatting.",
        "Inspect the imported record count and preview bars in Chart.",
    ),
)


@dataclass(frozen=True)
class _Config:
    """Internal default configuration for Data Manager help guides."""

    default_topic: str = "overview"


class DMHelp:
    """Service providing contextual documentation and tutorials for Data Manager."""

    def help(self, topic: str = _Config.default_topic) -> dict[str, Any]:
        """Return contextual documentation and tutorials for the requested topic."""
        key = topic.strip().lower() if isinstance(topic, str) else ""
        if key not in _TOPICS:
            logger.warning("%s: Unknown topic", GUIDE_FR, extra={"fr_id": GUIDE_FR})
            raise ValueError(f"Unsupported Data Manager help topic: '{topic}'.")
        title, summary = _TOPICS[key]
        tutorials = [{**item, "steps": list(item["steps"])} for item in _TUTORIALS]
        logger.info("%s: Resolved help %s", GUIDE_FR, key, extra={"fr_id": GUIDE_FR})
        return {
            "topic": key,
            "title": title,
            "summary": summary,
            "available_topics": list(_TOPICS),
            "tutorials": tutorials,
        }


class DMHelpCLI:
    """CLI presentation adapter for Data Manager contextual help guides."""

    @staticmethod
    def format_help_guide(guide: Mapping[str, Any]) -> str:
        """Format a help guide payload into a human-readable CLI summary."""
        head = f"=== {guide.get('title', 'Help')} ({guide.get('topic', '')}) ==="
        items = [
            f"- {item.get('title', '')}: {item.get('summary', '')}"
            for item in guide.get("tutorials", [])
        ]
        return "\n".join([head, str(guide.get("summary", "")), *items])


def main() -> None:
    """Execute standalone DMHelp verification."""
    logger.info("%s", DMHelpCLI.format_help_guide(DMHelp().help()))


if __name__ == "__main__":
    main()
