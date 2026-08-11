# Time and Sessions — FEAT-DATA-07

Owns UTC validation, timeframe definitions, venue-authoritative market hours,
exchange and configured weekly schedules, analytical named sessions, and pure gap
classification. Named liquidity sessions never establish whether a symbol is
tradable; only provider, venue, or explicit revisioned schedule evidence can do so.

- Production files: `contracts.py`, `exchange_calendar.py`, `gaps.py`,
  `market_hours.py`, `named_sessions.py`, `schedule.py`, `timeframes.py`, `utc.py`,
  and `weekly_schedule.py`.
- Requirements: `FR-DATA-034`, `FR-DATA-117` through `FR-DATA-122`.
- Usage evidence: `tests/data/usage/09_time_sessions.py`.
- Side effects: schedule operations may perform approved read-only source calls;
  named-session classification and configured-weekly expansion are pure.
- Dependencies: `exchange-calendars==4.12` for explicit exchange identifiers;
  Brokers' public `BrokerTradingSession` contract for broker-provided schedules.
- Failure boundary: absent, stale, conflicting, unbounded, or invalid schedule
  evidence fails closed. Ticker text is never used to infer a venue.
