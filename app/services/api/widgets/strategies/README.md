# Strategy Gateway

Focused workstation API feature. It authenticates and authorizes requests,
delegates through verified owner-domain public contracts, translates bounded
errors, and performs no owner-domain or presentation calculations.

## Files

- `routes.py`: thin FastAPI transport boundary.
- `schemas.py`: feature-local request and response schemas.
- `orchestration.py`: dependency composition and owner delegation.

Additional focused route or persistence modules are listed here when required by
the feature's distinct resource lifecycle.

## Requirements

- FR-API-025.

## Dependencies

Shared API contracts, Identity authorization, canonical Composition, and the
relevant owner-domain package-root public API.

## Evidence

- `tests/api/unit/test_strategy_routes.py and test_strategy_mutation_routes.py`
