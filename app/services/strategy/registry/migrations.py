"""Strategy-owned persistence migration definitions."""

import hashlib

from app.services.data.contracts import MigrationRequest, MigrationStep
from app.services.data.storage import run_domain_migrations
from app.utils import logger

_STATEMENTS = (
    """CREATE TABLE IF NOT EXISTS strategy_versions (
        strategy_id TEXT NOT NULL,
        strategy_version TEXT NOT NULL,
        manifest_json TEXT NOT NULL,
        lifecycle_status TEXT NOT NULL,
        policy_json TEXT NOT NULL,
        record_hash TEXT NOT NULL,
        request_id TEXT NOT NULL,
        correlation_id TEXT NOT NULL,
        PRIMARY KEY (strategy_id, strategy_version)
    )""",
    """CREATE TABLE IF NOT EXISTS strategy_configs (
        strategy_id TEXT NOT NULL,
        strategy_version TEXT NOT NULL,
        config_hash TEXT NOT NULL,
        config_json TEXT NOT NULL,
        policy_version TEXT NOT NULL,
        request_id TEXT NOT NULL,
        PRIMARY KEY (strategy_id, strategy_version, config_hash)
    )""",
    """CREATE TABLE IF NOT EXISTS strategy_checkpoints (
        checkpoint_id TEXT PRIMARY KEY,
        checkpoint_json TEXT NOT NULL,
        checksum TEXT NOT NULL,
        authorization_ref TEXT NOT NULL,
        request_id TEXT NOT NULL
    )""",
    """CREATE TABLE IF NOT EXISTS strategy_mutations (
        command_id TEXT PRIMARY KEY,
        mutation_json TEXT NOT NULL,
        publication_pending INTEGER NOT NULL
    )""",
)


def strategy_migration_steps() -> tuple[MigrationStep, ...]:
    """Return ordered immutable Strategy migration definitions.

    Returns:
        The complete ordered Strategy migration tuple.
    """
    logger.debug("Building Strategy migration definitions")
    material = "\n".join(_STATEMENTS).encode("utf-8")
    return (
        MigrationStep(
            domain="strategy",
            migration_id="0001_strategy_domain",
            checksum=hashlib.sha256(material).hexdigest(),
            statements=_STATEMENTS,
        ),
    )


def ensure_strategy_storage(request_id: str) -> None:
    """Apply Strategy migrations idempotently through Data.

    Args:
        request_id: Canonical request trace identifier.
    """
    logger.info("Ensuring Strategy-owned persistence schema")
    run_domain_migrations(
        MigrationRequest(
            domain="strategy",
            steps=strategy_migration_steps(),
            request_id=request_id,
        )
    )


__all__: list[str] = []
