"""Authoritative Portfolio migration-manifest runner."""

from __future__ import annotations

from app.composition.logging import get_logger
from app.services.data import (
    build_migration_request,
    run_domain_migrations,
)
from app.services.portfolio.migrations.definitions import get_portfolio_migrations

logger = get_logger(__name__)


def run_portfolio_migrations(request_id: str) -> object:
    """Apply or verify the complete Portfolio migration manifest.

    Data remains responsible for ledger verification, write-lock acquisition,
    checksum enforcement, and transactional execution.

    Args:
        request_id: Bounded request trace identity.

    Returns:
        Data-owned structured migration response.
    """
    logger.info("Running the authoritative Portfolio schema migration manifest")
    response = run_domain_migrations(
        build_migration_request(
            domain="portfolio",
            steps=get_portfolio_migrations(),
            request_id=request_id,
            complete_manifest=True,
        )
    )
    if getattr(response, "status", None) != "success":
        logger.error("Portfolio schema migration manifest failed closed")
    else:
        logger.info("Portfolio schema migration manifest verified")
    return response


__all__ = ("run_portfolio_migrations",)
