"""Authoritative Agentic migration manifest and execution boundary."""

from __future__ import annotations

from typing import Any

from app.agentic.migrations.experiment import AGENTIC_EXPERIMENT_MIGRATION_STEPS
from app.agentic.migrations.lifecycle import AGENTIC_LIFECYCLE_MIGRATION_STEPS
from app.agentic.migrations.memory import AGENTIC_MEMORY_MIGRATION_STEPS
from app.agentic.migrations.operations import AGENTIC_OPERATIONS_MIGRATION_STEPS
from app.agentic.migrations.workflow import AGENTIC_MIGRATION_STEPS
from app.services.data import build_migration_request, run_domain_migrations
from app.utils import get_logger

logger = get_logger(__name__)


def get_agentic_migrations() -> tuple[Any, ...]:
    """Return the complete ordered Agentic migration manifest.

    Returns:
        Immutable migration steps in their authoritative apply order.

    Raises:
        ValueError: If the assembled manifest contains duplicate identities.
    """
    steps: tuple[Any, ...] = (
        *AGENTIC_MIGRATION_STEPS,
        *AGENTIC_MEMORY_MIGRATION_STEPS,
        *AGENTIC_LIFECYCLE_MIGRATION_STEPS,
        *AGENTIC_OPERATIONS_MIGRATION_STEPS,
        *AGENTIC_EXPERIMENT_MIGRATION_STEPS,
    )
    migration_ids = tuple(str(step.migration_id) for step in steps)
    if len(migration_ids) != len(set(migration_ids)):
        raise ValueError("Agentic migration identities must be unique")
    return steps


def run_agentic_migrations(request_id: str) -> object:
    """Apply or verify the complete Agentic manifest through Data.

    Data owns ledger verification, write locking, checksum enforcement, and
    transactional execution. Agentic supplies only its immutable definitions.

    Args:
        request_id: Bounded migration trace identity.

    Returns:
        Data-owned structured migration response.
    """
    logger.info("Running the authoritative Agentic migration manifest")
    response = run_domain_migrations(
        build_migration_request(
            domain="agentic",
            steps=get_agentic_migrations(),
            request_id=request_id,
            complete_manifest=True,
        )
    )
    if getattr(response, "status", None) != "success":
        logger.error("Agentic migration manifest failed closed")
    else:
        logger.info("Agentic migration manifest verified")
    return response


__all__ = ("get_agentic_migrations", "run_agentic_migrations")
