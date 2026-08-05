# Economic Calendar — FEAT-DATA-11

Owns database-first calendar retrieval, licensed bounded historical acquisition,
current-week CSV synchronization, CSV bootstrap, permanent event-definition
discovery and specifications, normalization, projection,
approved-root persistence, explicit coverage, symbol relevance, and Risk-ready
calendar evidence.

- Production files: `firecrawl_transport.py`, `reader_transport.py`, `event_urls.py`, `ingestion.py`, `normalization.py`, `parsing.py`,
  `scraper.py`, `events.py`,
  `profiling.py`, `providers.py`, `restriction.py`, `calendar_state.py`,
  `service.py`, and `store.py`.
- Requirements: `FR-DATA-095`–`FR-DATA-099`, `FR-DATA-123`–`FR-DATA-129`,
  and `FR-DATA-168`–`FR-DATA-180`.
- Usage evidence: `tests/data/usage/11_economic_calendar.py`.
- Side effects: licensed read-only provider calls, explicit approved-root
  writes, and bounded SQLite upserts through Data persistence.

Multi-site live retrieval uses bounded uncached Firecrawl HTTPS under
the owner's written Fair Economy copy permission. It verifies the final API host
and JSON media type, rejects oversized responses, applies enhanced-proxy and
concurrency limits, and never logs the API key or full provider payload. Missing
credentials or total provider failure fails closed. Unit and default integration
tests remain network-free; `tests/data/integration/test_economic_calendar_live.py`
is opt-in. Historical Forex Factory backfill uses the credential-free Jina Reader
API with fixed hosts, weekly page bounds, America/Chicago-to-UTC conversion,
response-size limits, coverage-ledger resume, and bounded retry behavior.
Permanent definition discovery scans only an explicit numeric-ID interval at no
more than twenty Reader requests per minute. Definition pages provide canonical
URLs and nullable Source, latest-release, Measures, Usual Effect, Frequency,
Also Called, and Event Type values. Historical rows are linked only by an exact,
unique title/country match; the implementation never invents URL slugs or specs.

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
