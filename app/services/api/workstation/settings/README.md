# Settings Boundary

Focused workstation API feature. It owns externally provisioned bootstrap
configuration, API-wide boundary limits, authenticated user/global settings,
and write-only credential-status routes. Bootstrap values are available before
the database opens; persisted settings activate only after canonical startup.

## Files

- `routes.py`: thin FastAPI transport boundary.
- `schemas.py`: feature-local request and response schemas.
- `orchestration.py`: dependency composition and owner delegation.
- `bootstrap.py`: validated pre-database process configuration and cache.
- `limits.py`: immutable pagination, timeout, retention, error, visibility, and
  rate-limit defaults consumed by API features.

Additional focused route or persistence modules are listed here when required by
the feature's distinct resource lifecycle.

## Requirements

- FR-API-023, bootstrap support for FR-API-035 through FR-API-036, and the
  route portion of FR-API-077.

## Dependencies

Shared API contracts, Identity authorization, canonical Composition, and the
relevant owner-domain package-root public API.

## Evidence

- `tests/api/integration/test_auth_settings.py`
- `tests/api/unit/test_application.py`
- `tests/api/contracts/test_pagination_contract.py`
