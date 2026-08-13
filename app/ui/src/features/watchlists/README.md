# Watchlists

## Purpose

Owns account-watchlist presentation and interactions for `FEAT-UI-03`,
including the bounded in-memory source-symbol directory used for strict
autocomplete and exact provider-native selection.
The widget displays the class persisted by the backend from the selected MT5
symbol's metadata path; users do not manually select or bulk-add a class.
Backend watchlist policy remains in `app/services/api/workstation/watchlists/`.

## Public API

- `WatchlistWidget` through `index.ts`.

`symbolUniverse.ts` is private feature behavior. It walks the authenticated
Data symbol route once per browser document, shares concurrent loads, ranks
bounded suggestions, and never exposes a second UI public surface.
The same complete universe is the sole authority for the `NOT TRADABLE` tag;
the bounded Markets projection is not used as a membership directory.

## Verification

- `WatchlistWidget.test.tsx` provides focused component evidence for loading,
  unavailable, suggestion, keyboard, exact-match, automatic class display,
  complete-universe tradability, removal of manual class controls, and mutation
  behavior.
