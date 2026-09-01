# Sessions and Calendars

**Feature ID:** `FEAT-CAT-DEFINE_SESSIONS`

## Domain

`catalogue`

## Purpose

Provide the `catalogue.define-sessions@1` capability for defining, versioning, retaining, and previewing trading sessions and market calendars.

## Provides

`catalogue.define-sessions@1`

## Required Capabilities

None.

## Optional Capabilities

None.

## Configuration

| Key | Type | Required | Description |
|---|---|---|---|
| `database_path` | string or null | No | Optional SQLite database path for persistent storage; defaults to in-memory SQLite. |

## Persistent State

`catalogue.sessions` schema version 1 retains `trading_sessions` and `market_calendars` in the configured SQLite database. Retention policy is `retain`: feature unloading or uninstallation preserves immutable session and calendar version definitions.

## Runtime Effects

Mount resolves no external dependencies through `FeatureContext` and stages `catalogue.define-sessions@1`. Scoped SQLite connections are opened per operation and closed in all execution paths.

## Operations

- `GET`: Retrieve the latest trading session definition by session reference ID.
- `UPSERT_SESSION`: Store versioned trading session definition and publish `catalogue.trading-session-changed`.
- `UPSERT_CALENDAR`: Store versioned market calendar definition and publish `catalogue.market-calendar-changed`.
- `PREVIEW`: Compute effective UTC tradable intervals across the requested date window, accounting for weekday schedules, overnight spans, calendar holidays, early closes, and DST transitions.

## Failure Behavior

- Unknown session reference IDs return `CATALOGUE_NOT_FOUND`.
- Invalid overlapping intervals within a session or duplicate holiday dates within a calendar are rejected at wire model validation time.

## Removal Behavior

Removing this feature withdraws its scoped `catalogue.define-sessions@1` provider. Existing session and calendar definitions remain retained; subsequent requests fail closed with `CAPABILITY_UNAVAILABLE`.

## Evidence

Run `uv run python -m app.services.catalogue.session_calendar.session_calendar` for the executable scenario harness. Automated tests live in `tests/services/catalogue/session_calendar/`.
