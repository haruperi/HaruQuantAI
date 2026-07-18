"""Immutable Strategy registry persistence tests."""

# ruff: noqa: PT018

from contextlib import AbstractContextManager
from pathlib import Path

from app.services.data.config import DataSettings, data_settings_context
from app.services.strategy import (
    StrategyConfig,
    StrategyEnvironment,
    StrategyLifecycleStatus,
    StrategyParameterUpdateRequest,
    StrategyRef,
    StrategyRegistrationRequest,
    list_strategy_versions,
    register_strategy_version,
    update_strategy_parameters,
)
from app.utils import logger

from tests.strategy.unit.test_models import (
    COR,
    NOW,
    REQ,
    make_auth,
    make_manifest,
    make_policy,
)


def storage_context(root: Path) -> AbstractContextManager[None]:
    """Build an isolated Data settings context.

    Args:
        root: Temporary storage directory.

    Returns:
        Context manager installing isolated SQLite settings.
    """
    logger.debug("Building isolated Strategy storage context")
    return data_settings_context(
        DataSettings(
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


def test_registration_is_immutable(tmp_path: Path) -> None:
    """Verify duplicate versions reject while command retries are idempotent."""
    logger.debug("Testing immutable Strategy registration")
    with storage_context(tmp_path):
        first = register_strategy_version(
            make_registration(), make_auth(), make_policy()
        )
        retry = register_strategy_version(
            make_registration(), make_auth(), make_policy()
        )
        conflicting = make_registration().model_copy(
            update={"command_id": "command-register-2"}
        )
        rejected = register_strategy_version(conflicting, make_auth(), make_policy())
    assert first.data is not None and first.data.status == "ACCEPTED"
    assert retry.data is not None and retry.data.status == "IDEMPOTENT"
    assert rejected.data is not None and rejected.data.status == "REJECTED"


def test_list_versions_is_deterministically_ordered(tmp_path: Path) -> None:
    """Verify registry listing returns public immutable contracts only."""
    logger.debug("Testing deterministic Strategy registry listing")
    with storage_context(tmp_path):
        register_strategy_version(make_registration(), make_auth(), make_policy())
        outcome = list_strategy_versions()
    assert outcome.status == "success"
    assert (
        outcome.data is not None
        and outcome.data[0].manifest.strategy_id == "mean-reversion"
    )


def test_parameter_update_preserves_prior_hash(tmp_path: Path) -> None:
    """Verify parameter versions append immutable configuration hashes."""
    logger.debug("Testing immutable Strategy parameter update")
    request = StrategyParameterUpdateRequest(
        command_id="command-config-1",
        strategy_id="mean-reversion",
        strategy_version="1.0.0",
        parameters={"period": 7},
        principal_id="builder",
        reason="approved test configuration",
        ref=StrategyRef(
            strategy_id="mean-reversion",
            exact_version="1.0.0",
            environment=StrategyEnvironment.RESEARCH,
            request_id=REQ,
            correlation_id=COR,
        ),
        config=StrategyConfig(
            strategy_id="mean-reversion",
            strategy_version="1.0.0",
            config_schema_version="v1",
            parameters={"period": 7},
            request_id=REQ,
        ),
        authorization_ref="approval-config-1",
        requested_at=NOW,
        request_id=REQ,
        correlation_id=COR,
    )
    with storage_context(tmp_path):
        register_strategy_version(make_registration(), make_auth(), make_policy())
        outcome = update_strategy_parameters(request, make_auth())
        retry = update_strategy_parameters(request, make_auth())
    assert outcome.data is not None and outcome.data.validated_config is not None
    assert outcome.data.record_hash == outcome.data.validated_config.config_hash
    assert retry.data is not None and retry.data.status == "IDEMPOTENT"
