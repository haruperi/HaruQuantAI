# Watchlists

## Purpose

Owns account-watchlist presentation and interactions for `FEAT-UI-03`,
including the bounded in-memory source-symbol directory used for strict
autocomplete and exact provider-native selection.
The widget displays the class persisted by the backend from the selected MT5
symbol's metadata path; users do not manually select or bulk-add a class.
The backend boundary is the D-IFACE watchlist gateway
(`interfaces.operate-watchlists@1`, served at `GET/POST /api/v1/watchlists`
and `PATCH/DELETE /api/v1/watchlists/{id}`); watchlist policy and durable
state remain owned by the Workspace domain. An absent gateway (HTTP 503)
renders the explicit `unavailable` state and no lists are invented.

## D-UI feature shape (pipeline §4.8)

| Artifact | Responsibility |
| --- | --- |
| `manifest.ts` | Typed manifest: owning `FEAT-UI-03`, required `interfaces.operate-watchlists@1`, placement, dimensions, effects, accessibility, removal. |
| `config.ts` | Strict Zod configuration (refresh window, persisted-state schema version); unknown fields throw. |
| `feature.tsx` | Lifecycle adapter: strict configuration lifecycle and the explicit invalid-configuration response. |
| `WatchlistWidget.tsx` | Focused presentation and interactions, including the explicit gateway-unavailable state. |
| `index.ts` | Deliberate public exports only. |

## Public API

- `WatchlistsFeature` (lifecycle adapter) and `WatchlistWidget` through
  `index.ts`.

`symbolUniverse.ts` is private feature behavior. It walks the authenticated
Data symbol route once per browser document, shares concurrent loads, ranks
bounded suggestions, and never exposes a second UI public surface.
The same complete universe is the sole authority for the `NOT TRADABLE` tag;
the bounded Markets projection is not used as a membership directory.
Successful mutations emit one browser-local invalidation event so independently
mounted Markets widgets reload authoritative watchlist data and replace their
snapshot demand. The event contains no symbols or account data. A universe
failure never clobbers a primary list failure: it owns the alert only while
the list itself loaded successfully.

## Verification

- `WatchlistWidget.test.tsx` provides focused component evidence for loading,
  unavailable, suggestion, keyboard, exact-match, automatic class display,
  complete-universe tradability, removal of manual class controls, and mutation
  behavior.
- `feature.test.tsx` (lifecycle and availability), `manifest.test.ts`, and
  `config.test.ts` provide D-UI evidence.
