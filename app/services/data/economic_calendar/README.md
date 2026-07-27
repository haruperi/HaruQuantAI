# Economic Calendar — FEAT-DATA-11

Owns injected multi-site calendar acquisition, normalization, projection,
approved-root persistence, trusted local serialization, normalized provider
events, symbol relevance, refreshable event storage, and Risk-ready calendar
evidence.

- Production files: `normalization.py`, `parsing.py`, `scraper.py`, `events.py`,
  `profiling.py`, `providers.py`, `restriction.py`, `calendar_state.py`,
  `service.py`, and `store.py`.
- Requirements: `FR-DATA-095`–`FR-DATA-099` and
  `FR-DATA-123`–`FR-DATA-129`.
- Usage evidence: `tests/data/usage/11_economic_calendar.py`.
- Side effects: injected read-only provider calls, explicit approved-root
  writes, and bounded SQLite upserts through Data persistence.

Provider-specific rows never cross the normalized public boundary. Currency
and country filters represent alternative relevance dimensions for symbol
queries. Successful empty queries produce `calendar_state="open"`; unavailable
calendar evidence remains `unknown` so Risk applies its configured
missing-evidence policy. Risk alone interprets the state, and Trading consumes
only Risk decisions.
