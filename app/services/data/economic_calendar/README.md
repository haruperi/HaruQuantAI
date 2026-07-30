# Economic Calendar — FEAT-DATA-11

Owns licensed multi-site calendar acquisition, normalization, projection,
approved-root persistence, trusted local serialization, normalized provider
events, symbol relevance, refreshable event storage, and Risk-ready calendar
evidence.

- Production files: `firecrawl_transport.py`, `normalization.py`, `parsing.py`,
  `scraper.py`, `events.py`,
  `profiling.py`, `providers.py`, `restriction.py`, `calendar_state.py`,
  `service.py`, and `store.py`.
- Requirements: `FR-DATA-095`–`FR-DATA-099` and
  `FR-DATA-123`–`FR-DATA-129`.
- Usage evidence: `tests/data/usage/11_economic_calendar.py`.
- Side effects: licensed read-only provider calls, explicit approved-root
  writes, and bounded SQLite upserts through Data persistence.

The production transport uses bounded uncached Firecrawl HTTPS retrieval under
the owner's written Fair Economy copy permission. It verifies the final API host
and JSON media type, rejects oversized responses, applies enhanced-proxy and
concurrency limits, and never logs the API key or full provider payload. Missing
credentials or total provider failure fails closed. Unit and default integration
tests remain network-free; `tests/data/integration/test_economic_calendar_live.py`
is opt-in, while the numbered usage is the direct real-evidence program.

Public consumers use only functions re-exported by `app.services.data`, including
transport/options construction, scrape/DataFrame/serialization operations,
provider-neutral general and symbol queries, event/state projections, restriction
evaluation, approved persistence, and market-context population. Returned classes
are opaque values and handles.

Provider-specific rows never cross the normalized public boundary. Currency
and country filters represent alternative relevance dimensions for symbol
queries. Successful empty queries produce `calendar_state="open"`; unavailable
calendar evidence remains `unknown` so Risk applies its configured
missing-evidence policy. Risk alone interprets the state, and Trading consumes
only Risk decisions.
