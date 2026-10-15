"""Contextual help topics and searchable FAQ catalog for the Data Manager.

Description:
    Provides domain-specific workflow guides, step-by-step instructions, and
    searchable FAQ answers for all features in the Data Manager workspace,
    including file import, tick vs M1 simulation, session calendars, broker
    profile management, external indicators, and multi-format exports.

Purpose:
    FEAT-DATAMGR-HELP: Contextual user assistance and documentation catalog.

Key Capabilities:
    - FR-DATAMGR-HELP-TOPICS: Retrieve structured help topics by section.
      Associated: `DataManagerHelpService.list_topics()`,
      `DataManagerHelpService.get_topic()`
      Logging: Emits DEBUG when retrieving help topics.
    - FR-DATAMGR-HELP-FAQ-SEARCH: Search FAQ entries by keyword query and tags.
      Associated: `DataManagerHelpService.search_faqs()`
      Logging: Emits DEBUG when searching FAQ entries with query terms.

Python API Usage:
    ```python
    from app.workspace.data_manager.help import DataManagerHelpService

    help_service = DataManagerHelpService()
    topics = help_service.list_topics(section="data")
    faqs = help_service.search_faqs(query="resampling")
    ```

CLI Usage:
    ```bash
    uv run python -m app.workspace.data_manager.help
    ```
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.host.logging import get_logger

__all__ = [
    "DataManagerHelpService",
    "HelpTopic",
]

logger = get_logger(__name__)

HELP_TOPICS_FR = "FR-DATAMGR-HELP-TOPICS"
HELP_FAQ_FR = "FR-DATAMGR-HELP-FAQ-SEARCH"


@dataclass(frozen=True)
class HelpTopic:
    """Represents a structured help topic for Data Manager views."""

    topic_id: str
    title: str
    section: str
    summary: str
    steps: list[str]

    def to_dict(self) -> dict[str, Any]:
        """Convert help topic to dictionary representation."""
        return {
            "topic_id": self.topic_id,
            "title": self.title,
            "section": self.section,
            "summary": self.summary,
            "steps": self.steps,
        }


@dataclass(frozen=True)
class HelpFaqItem:
    """Represents a searchable FAQ entry."""

    faq_id: str
    question: str
    answer: str
    tags: list[str]

    def to_dict(self) -> dict[str, Any]:
        """Convert FAQ item to dictionary representation."""
        return {
            "faq_id": self.faq_id,
            "question": self.question,
            "answer": self.answer,
            "tags": self.tags,
        }


_DEFAULT_TOPICS: tuple[HelpTopic, ...] = (
    HelpTopic(
        topic_id="importing-csv-data",
        title="Importing Historical CSV Data",
        section="data",
        summary=(
            "How to parse and load external ASCII / CSV market data into "
            "partitioned Parquet."
        ),
        steps=[
            "Navigate to Data tab and select 'Import Data'.",
            "Choose source file and verify delimiter, date format, and column mapping.",
            "Click Import to parse bars into the local catalog.",
            "Verify imported bar count and date range in the dataset list.",
        ],
    ),
    HelpTopic(
        topic_id="configuring-instruments",
        title="Configuring Instrument Specifications",
        section="instruments",
        summary=(
            "Adjusting point values, tick sizes, margin requirements, and "
            "commission schedules."
        ),
        steps=[
            "Select an instrument from the Instruments catalog.",
            "Set point value, tick size, and minimum volume.",
            "Configure default spread and commission rules.",
            "Save changes to update backtest simulation parameters.",
        ],
    ),
    HelpTopic(
        topic_id="trading-sessions-holidays",
        title="Custom Trading Sessions and Holidays",
        section="sessions",
        summary=(
            "Defining regular trading hours (RTH) and electronic trading hours (ETH)."
        ),
        steps=[
            "Select Sessions tab and click 'New Session' or choose a template.",
            "Define session windows for each day of the week.",
            "Add holiday exceptions to skip non-trading dates.",
            "Apply the session to relevant instruments or datasets.",
        ],
    ),
    HelpTopic(
        topic_id="stock-baskets-survivorship",
        title="Survivorship-Bias-Free Stock Groups",
        section="baskets",
        summary="Building dynamic composite baskets with constituent membership dates.",
        steps=[
            "Create a new Stock Group (e.g., S&P 500 Historical).",
            "Import constituent tickers with From and To dates.",
            "Check readiness overview to identify missing historical data.",
            "Trigger batch download for unready symbols.",
        ],
    ),
    HelpTopic(
        topic_id="data-quality-inspection",
        title="Running Data Quality Checks",
        section="review",
        summary=(
            "Detecting gaps, weekend bars, price spikes, and OHLC envelope violations."
        ),
        steps=[
            "Select dataset and open Quality Inspection tool.",
            "Run automated scan across chronological bar records.",
            "Inspect detected anomalies and quality score.",
            "Apply corrective edits or transforms as necessary.",
        ],
    ),
)

_DEFAULT_FAQS: tuple[HelpFaqItem, ...] = (
    HelpFaqItem(
        faq_id="faq-tick-vs-m1",
        question="What is the difference between Tick and M1 simulation?",
        answer=(
            "M1 simulation models intra-bar price movement using four bar ticks "
            "(open, high, low, close). Real tick simulation evaluates every "
            "price change, providing exact spread and slippage behavior at "
            "higher computational cost."
        ),
        tags=["simulation", "ticks", "timeframe"],
    ),
    HelpFaqItem(
        faq_id="faq-resampling",
        question="How does timeframe resampling work?",
        answer=(
            "Resampling aggregates lower timeframe bars (like M1) into higher "
            "timeframe bars (M5, H1, D1) by computing open=first, high=max, "
            "low=min, close=last, and volume=sum."
        ),
        tags=["transforms", "resample", "bars"],
    ),
    HelpFaqItem(
        faq_id="faq-nt8-import",
        question="Can I import NinjaTrader 8 session templates?",
        answer=(
            "Yes, the Sessions tool discovers and parses NinjaTrader 8 "
            "TradingHours XML definitions, extracting daily schedules and "
            "holiday calendars."
        ),
        tags=["sessions", "ninjatrader", "xml"],
    ),
    HelpFaqItem(
        faq_id="faq-custom-indicators",
        question="How do I load external indicators or COT data?",
        answer=(
            "Use the Custom Data view to import timestamped indicator values "
            "from CSV or recognize MetaTrader 4 .mq4 indicator buffer structures."
        ),
        tags=["indicators", "cot", "custom-data", "mq4"],
    ),
)


class DataManagerHelpService:
    """Service providing contextual documentation and FAQ search."""

    def __init__(self) -> None:
        """Initialize help service with built-in topics and FAQs."""
        self._topics: list[HelpTopic] = list(_DEFAULT_TOPICS)
        self._faqs: list[HelpFaqItem] = list(_DEFAULT_FAQS)

    def list_topics(self, section: str | None = None) -> list[HelpTopic]:
        """List help topics, optionally filtered by workspace section."""
        logger.debug(
            "%s: Listing help topics (section=%s)",
            HELP_TOPICS_FR,
            section,
            extra={"fr_id": HELP_TOPICS_FR, "section": section},
        )
        if not section:
            return list(self._topics)
        clean = section.strip().lower()
        return [t for t in self._topics if t.section.lower() == clean]

    def get_topic(self, topic_id: str) -> HelpTopic | None:
        """Retrieve a specific help topic by its identifier."""
        clean = topic_id.strip().lower()
        for t in self._topics:
            if t.topic_id.lower() == clean:
                return t
        return None

    def search_faqs(self, query: str | None = None) -> list[HelpFaqItem]:
        """Search FAQ entries by keyword query."""
        logger.debug(
            "%s: Searching FAQs with query='%s'",
            HELP_FAQ_FR,
            query,
            extra={"fr_id": HELP_FAQ_FR, "query": query},
        )
        if not query or not query.strip():
            return list(self._faqs)
        q = query.strip().lower()
        return [
            faq
            for faq in self._faqs
            if (
                q in faq.question.lower()
                or q in faq.answer.lower()
                or any(q in tag.lower() for tag in faq.tags)
            )
        ]


def main() -> None:
    """Execute real-usage demonstration of DataManagerHelpService."""
    service = DataManagerHelpService()
    topics = service.list_topics(section="data")
    print(f"Retrieved {len(topics)} topics for 'data' section")
    for t in topics:
        print(f" - {t.title}: {t.summary}")

    faqs = service.search_faqs(query="resampling")
    print(f"Found {len(faqs)} FAQs matching 'resampling':")
    for f in faqs:
        print(f" - Q: {f.question}")
        print(f"   A: {f.answer}")


if __name__ == "__main__":
    main()
