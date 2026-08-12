# Account Watchlists

## Purpose

Owns `FEAT-API-11` account-watchlist orchestration and thin HTTP routes.

## Boundaries

- Persistence files remain in the documented API support package.
- Models are private; public consumers use function-only API root operations.
- Unit and isolated integration evidence never initializes broker transport.
