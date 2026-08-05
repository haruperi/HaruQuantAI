"""Immutable Strategy registry persistence tests."""

from contextlib import AbstractContextManager
from pathlib import Path

from app.services.data import build_data_settings, data_settings_context
from app.services.strategy.contracts import (
    StrategyLifecycleStatus,
    StrategyRegistrationRequest,
)
from app.utils import get_logger

from tests.strategy.unit.test_models import (
    COR,
    NOW,
    REQ,
    make_manifest,
)

logger = get_logger(__name__)


def storage_context(root: Path) -> AbstractContextManager[None]:
    """Build an isolated Data settings context.

    Args:
        root: Temporary storage directory.

    Returns:
        Context manager installing isolated SQLite settings.
    """
    logger.debug("Building isolated Strategy storage context")
    return data_settings_context(
        build_data_settings(
            database_url="sqlite:///strategy.sqlite3",
            data_dir=root,
            sqlite_busy_timeout_seconds=1.5,
            write_lock_lease_seconds=30,
        )
    )


def make_registration() -> StrategyRegistrationRequest:
    """Build one governed registration command.

    Returns:
        Complete registration request.
    """
    logger.debug("Building Strategy registration test request")
    manifest = make_manifest()
    return StrategyRegistrationRequest(
        command_id="command-register-1",
        strategy_id=manifest.strategy_id,
        strategy_version=manifest.strategy_version,
        module_path=manifest.module_path,
        manifest=manifest,
        config_schema=manifest.config_schema,
        source_hash=manifest.source_hash,
        artifact_hash=manifest.artifact_hash,
        dependency_hash=manifest.dependency_hash,
        provenance_refs=manifest.provenance_refs,
        principal_id="builder",
        reason="approved test registration",
        lifecycle_status=StrategyLifecycleStatus.APPROVED,
        authorization_ref="approval-1",
        requested_at=NOW,
        request_id=REQ,
        correlation_id=COR,
    )
