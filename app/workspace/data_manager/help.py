"""Data Manager documentation, user guides, and format specifications.

Description:
    Provides structured help topics, file format specifications (CSV, NinjaTrader
    XML, MT4/MT5, CFTC COT), keyboard shortcuts, and quantitative guide
    references within the Data Manager workspace, mirroring SQX DataManagerHelp.

Purpose:
    FEAT-WORKSPACE-DATAMGR: Expose Data Manager help guides and format specs.

Key Capabilities:
    - FR-WORKSPACE-DATAMGR-HELP: Retrieve structured documentation and specs.
      Associated: `[DataManagerHelpService.get_topic()]`,
      `[DataManagerHelpService.list_topics()]`
      Logging: Emits DEBUG when help topics are retrieved.

Python API Usage:
    ```python
    from app.workspace.data_manager.help import DataManagerHelpService

    help_service = DataManagerHelpService()
    topics = help_service.list_topics()
    csv_spec = help_service.get_topic("csv-format")
    ```

CLI Usage:
    ```bash
    python -m app.workspace.data_manager.help --list
    ```
"""

from __future__ import annotations

import argparse
import sys

from pydantic import BaseModel, ConfigDict, Field

from app.host.logging import get_logger

logger = get_logger(__name__)


class HelpTopic(BaseModel):
    """Specification of a help article or format guide."""

    model_config = ConfigDict(frozen=True)

    topic_id: str = Field(description="Unique topic slug")
    title: str = Field(description="Human-readable title")
    category: str = Field(description="Category (e.g. Formats, Workflows, Hotkeys)")
    content_markdown: str = Field(description="Full article content in markdown")


HELP_TOPICS: list[HelpTopic] = [
    HelpTopic(
        topic_id="csv-format",
        title="CSV File Ingestion Format",
        category="Formats",
        content_markdown=(
            "# CSV Format Specifications\n\n"
            "Supported delimiters: `,`, `;`, `\t`, `|`.\n\n"
            "Header columns can be separate "
            "(Date, Time, Open, High, Low, Close, Volume) "
            "or combined (DateTime, Open, High, Low, Close, Volume).\n"
            "Timestamps are automatically converted to UTC."
        ),
    ),
    HelpTopic(
        topic_id="ninjatrader-sessions",
        title="NinjaTrader 8 TradingHours XML Import",
        category="Formats",
        content_markdown=(
            "# NinjaTrader 8 XML Import\n\n"
            "Data Manager can directly import `.xml` templates exported from "
            "NinjaTrader 8 TradingHours definitions. Day-of-week windows and "
            "holiday exclusions are preserved."
        ),
    ),
    HelpTopic(
        topic_id="cot-reports",
        title="CFTC Commitments of Traders (COT)",
        category="Workflows",
        content_markdown=(
            "# Commitments of Traders (COT)\n\n"
            "Computes Commercial Position Index (cpihedg), Commercial Trend Index "
            "(ctihedg), Speculator Position Index (cpispec), Speculator Trend Index "
            "(ctispec), and Small Trader Index (cpismall) based on weekly Tuesday "
            "positions released on Fridays."
        ),
    ),
    HelpTopic(
        topic_id="keyboard-shortcuts",
        title="Keyboard Shortcuts",
        category="Hotkeys",
        content_markdown=(
            "# Keyboard Shortcuts\n\n"
            "- `Ctrl+I`: Open file ingestion dialog\n"
            "- `Ctrl+D`: Open provider download dialog\n"
            "- `Ctrl+Shift+I`: Add new instrument\n"
            "- `Ctrl+Shift+S`: Add new trading session\n"
            "- `Ctrl+Shift+B`: Create synthetic basket\n"
        ),
    ),
]


class DataManagerHelpService:
    """Service providing Data Manager help articles and documentation."""

    def list_topics(self) -> list[HelpTopic]:
        """List all available help topics.

        Fires FR-WORKSPACE-DATAMGR-HELP.
        """
        logger.debug(
            "FR-WORKSPACE-DATAMGR-HELP: Listed %d help topics",
            len(HELP_TOPICS),
            extra={"count": len(HELP_TOPICS), "fr_id": "FR-WORKSPACE-DATAMGR-HELP"},
        )
        return list(HELP_TOPICS)

    def get_topic(self, topic_id: str) -> HelpTopic | None:
        """Find a help topic by slug ID.

        Fires FR-WORKSPACE-DATAMGR-HELP.
        """
        clean_id = topic_id.strip().lower()
        for t in HELP_TOPICS:
            if t.topic_id.lower() == clean_id:
                return t
        return None


def main() -> int:
    """CLI tool for reading Data Manager help topics."""
    parser = argparse.ArgumentParser(description="Data Manager help documentation")
    parser.add_argument("--list", action="store_true", help="List all help topics")
    parser.add_argument("--topic", type=str, help="Topic slug to read")
    args = parser.parse_args()

    service = DataManagerHelpService()
    if args.topic:
        top = service.get_topic(args.topic)
        if top:
            print(f"=== {top.title} ({top.category}) ===")
            print(top.content_markdown)
            return 0
        print(f"Topic '{args.topic}' not found.")
        return 1

    topics = service.list_topics()
    print(f"Data Manager Help Topics ({len(topics)}):")
    for t in topics:
        print(f"  [{t.topic_id:20}] {t.title} ({t.category})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
