"""Aggregate feature-local API migrations for canonical startup."""

from app.services.api.identity.migrations import get_identity_migration_steps
from app.services.api.workstation.watchlists.migrations import (
    get_watchlist_migration_steps,
)
from app.services.data import build_migration_request, run_domain_migrations
from app.utils import get_logger

logger = get_logger(__name__)


def get_api_migration_steps() -> tuple[object, ...]:
    """Return all immutable API feature migrations in ledger order.

    Returns:
        Ordered API migration steps.
    """
    identity_steps = get_identity_migration_steps()
    return (
        *identity_steps[:-1],
        *get_watchlist_migration_steps(),
        identity_steps[-1],
    )


def run_api_migrations(request_id: str) -> object:
    """Apply the complete API migration manifest through Data.

    Args:
        request_id: Canonical startup request identifier.

    Returns:
        Data-owned migration response.
    """
    logger.info("Running API feature-owned schema migrations")
    return run_domain_migrations(
        build_migration_request(
            domain="api",
            steps=get_api_migration_steps(),
            request_id=request_id,
            complete_manifest=True,
        )
    )


__all__ = ("get_api_migration_steps", "run_api_migrations")
