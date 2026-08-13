# Account Watchlists

## Purpose

Owns `FEAT-API-11` account-watchlist orchestration and thin HTTP routes.

## Boundaries

- Persistence files remain in the documented API support package.
- Models are private; public consumers use function-only API root operations.
- Unit and isolated integration evidence never initializes broker transport.
- Runtime item additions read the exact symbol through Data's public metadata
  operation and persist the normalized class derived from MT5 `path` and
  currency metadata. Existing item classes are retained during reorder/removal.
- New symbols fail closed when source metadata is unavailable or cannot be
  classified; callers cannot submit an asset class.
- Runtime list reads treat legacy `Other` values as ambiguous, recheck only
  those entries through exact source metadata, and atomically persist any
  more-specific correction. Unavailable or genuinely inconclusive metadata
  preserves the readable watchlist and its existing `Other` value.
- Runtime list reads also inspect raw persistence for the empty class values
  introduced when `api-0008` upgraded older rows. Exact source metadata fills
  those values on the first successful read; temporary metadata failure leaves
  the row eligible for a later retry without making the watchlist unavailable.
