"""Focused economic-calendar acquisition and normalization.

Public surface composed of two layers:

1. The raw multi-site scrape pipeline declared by the legacy FEAT-DATA-11
   (`CalendarEvent`, `ScrapeOptions`, `ScrapeResult`, `scrape_economic_calendar`,
   `CalendarTransport`, `CALENDAR_SITES`) and its thin boundary helpers
   (
ormalize_calendar_number`, `parse_calendar_row`).
2. The normalized event/news-restriction surface that consumers outside Data
   depend on: `EconomicEvent`, `EventImpact`,
   `EconomicCalendarProvider`, `CalendarScrapeProvider`,
   `SymbolEventProfile`, `SYMBOL_EVENT_PROFILES`, `get_symbol_event_profile`,
   `get_economic_events`, `get_symbol_economic_events`, `is_news_restricted`,
   `derive_calendar_state`, `EconomicEventStore`, `from_row`.
"""

from app.services.data.economic_calendar.calendar_state import (
    DEFAULT_MINIMUM_IMPACT,
    CalendarStateResult,
    calendar_state_provenance,
    derive_calendar_state,
    populate_market_context_calendar,
)
from app.services.data.economic_calendar.events import EconomicEvent, EventImpact
from app.services.data.economic_calendar.profiling import (
    SYMBOL_EVENT_PROFILES,
    SymbolEventProfile,
    get_symbol_event_profile,
)
from app.services.data.economic_calendar.providers import (
    CalendarScrapeProvider,
    EconomicCalendarProvider,
)
from app.services.data.economic_calendar.restriction import (
    CALENDAR_STATE_BLACKOUT_AFTER,
    CALENDAR_STATE_BLACKOUT_BEFORE,
    CALENDAR_STATE_EVENT,
    CALENDAR_STATE_OPEN,
    CALENDAR_STATE_UNKNOWN,
    evaluate_calendar_state,
    is_news_restricted_events,
)
from app.services.data.economic_calendar.scraper import (
    CALENDAR_SITES,
    CalendarEvent,
    CalendarTransport,
    ScrapeOptions,
    ScrapeResult,
    deserialize_scrape_result,
    save_scrape_result,
    scrape_economic_calendar,
    scrape_result_to_dataframe,
    serialize_scrape_result,
)
from app.services.data.economic_calendar.service import (
    get_economic_events,
    get_persisted_events,
    get_symbol_economic_events,
    is_news_restricted,
)
from app.services.data.economic_calendar.store import (
    EconomicEventStore,
    from_row,
)

# Thin boundary helpers `normalize_calendar_number` and `parse_calendar_row`
# remain importable from their owning submodules
# (`economic_calendar.normalization` and `economic_calendar.parsing`) but are
# not re-exported here; the package-root API stays exactly the approved surface
# guarded by `tests/data/unit/test_api.py`.

__all__ = [
    "CALENDAR_SITES",
    "CALENDAR_STATE_BLACKOUT_AFTER",
    "CALENDAR_STATE_BLACKOUT_BEFORE",
    "CALENDAR_STATE_EVENT",
    "CALENDAR_STATE_OPEN",
    "CALENDAR_STATE_UNKNOWN",
    "DEFAULT_MINIMUM_IMPACT",
    "SYMBOL_EVENT_PROFILES",
    "CalendarEvent",
    "CalendarScrapeProvider",
    "CalendarStateResult",
    "CalendarTransport",
    "EconomicCalendarProvider",
    "EconomicEvent",
    "EconomicEventStore",
    "EventImpact",
    "ScrapeOptions",
    "ScrapeResult",
    "SymbolEventProfile",
    "calendar_state_provenance",
    "derive_calendar_state",
    "deserialize_scrape_result",
    "evaluate_calendar_state",
    "from_row",
    "get_economic_events",
    "get_persisted_events",
    "get_symbol_economic_events",
    "get_symbol_event_profile",
    "is_news_restricted",
    "is_news_restricted_events",
    "populate_market_context_calendar",
    "save_scrape_result",
    "scrape_economic_calendar",
    "scrape_result_to_dataframe",
    "serialize_scrape_result",
]
