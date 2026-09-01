"""Immutable Strategy registry persistence integration tests."""

# ruff: noqa: PT018
from pathlib import Path
from unittest.mock import patch

from app.composition.logging import get_logger
from app.services.strategy import (
    create_strategy_config,
    create_strategy_parameter_update_request,
    create_strategy_ref,
    get_strategy_environment,
    list_strategy_versions,
    register_strategy_version,
    update_strategy_parameters,
)

from tests.strategy.unit.test_catalog import make_registration, storage_context
from tests.strategy.unit.test_models import (
    COR,
    NOW,
    REQ,
    make_auth,
    make_config,
    make_policy,
    make_ref,
)

logger = get_logger(__name__)


def _parameter_update_kwargs() -> dict[str, object]:
    """Build public constructor arguments for one governed parameter update."""
    return {
        "command_id": "command-config-1",
        "strategy_id": "mean-reversion",
        "strategy_version": "1.0.0",
        "parameters": {"period": 7},
        "principal_id": "builder",
        "reason": "approved test configuration",
        "ref": create_strategy_ref(
            strategy_id="mean-reversion",
            exact_version="1.0.0",
            environment=get_strategy_environment("RESEARCH"),
            request_id=REQ,
            correlation_id=COR,
        ),
        "config": create_strategy_config(
            strategy_id="mean-reversion",
            strategy_version="1.0.0",
            config_schema_version="v1",
            parameters={"period": 7},
            request_id=REQ,
        ),
        "authorization_ref": "approval-config-1",
        "requested_at": NOW,
        "request_id": REQ,
        "correlation_id": COR,
    }


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


def test_multi_environment_manifest_requires_explicit_environment(
    tmp_path: Path,
) -> None:
    """Verify ambiguous environment declarations reject instead of defaulting."""
    logger.debug("Testing explicit Strategy registration environment")
    request = make_registration()
    ambiguous_manifest = request.manifest.model_copy(
        update={
            "permitted_environments": (
                get_strategy_environment("RESEARCH"),
                get_strategy_environment("DEMO"),
            )
        }
    )
    ambiguous = request.model_copy(update={"manifest": ambiguous_manifest})
    with storage_context(tmp_path):
        outcome = register_strategy_version(ambiguous, make_auth(), make_policy())
    assert outcome.data is not None
    assert outcome.data.status == "REJECTED"
    assert outcome.data.reason_codes == ("AMBIGUOUS_ENVIRONMENT",)
    assert outcome.data.validated_ref is None


def test_registration_rejects_authorization_and_unapproved_module() -> None:
    """Verify registration policy failures return explicit mutation truth."""
    request = make_registration()
    unauthorized = make_auth().model_copy(update={"permissions": ()})
    denied = register_strategy_version(request, unauthorized, make_policy())
    assert denied.data is not None
    assert denied.data.reason_codes == ("AUTHORIZATION_DENIED",)

    policy = make_policy().model_copy(update={"approved_module_roots": ("other",)})
    unapproved = register_strategy_version(request, make_auth(), policy)
    assert unapproved.data is not None
    assert unapproved.data.reason_codes == ("UNAPPROVED_MODULE",)


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
    request = create_strategy_parameter_update_request(**_parameter_update_kwargs())
    with storage_context(tmp_path):
        register_strategy_version(make_registration(), make_auth(), make_policy())
        outcome = update_strategy_parameters(request, make_auth())
        retry = update_strategy_parameters(request, make_auth())
    assert outcome.data is not None and outcome.data.validated_config is not None
    assert outcome.data.record_hash == outcome.data.validated_config.config_hash
    assert retry.data is not None and retry.data.status == "IDEMPOTENT"


def test_parameter_update_rejections_and_storage_failure() -> None:
    """Verify update authorization, registry, and storage failures fail closed."""
    request = create_strategy_parameter_update_request(**_parameter_update_kwargs())
    unauthorized = make_auth().model_copy(update={"permissions": ()})
    denied = update_strategy_parameters(request, unauthorized)
    assert denied.data is not None
    assert denied.data.reason_codes == ("AUTHORIZATION_DENIED",)

    with patch(
        "app.services.strategy.registry.parameters._load_policy",
        return_value=None,
    ):
        missing = update_strategy_parameters(request, make_auth())
    assert missing.data is not None
    assert missing.data.reason_codes == ("STRATEGY_NOT_FOUND",)

    with (
        patch(
            "app.services.strategy.registry.parameters._load_policy",
            return_value=make_policy(),
        ),
        patch(
            "app.services.strategy.registry.parameters.validate_strategy_ref",
            return_value=make_ref(),
        ),
        patch(
            "app.services.strategy.registry.parameters.validate_strategy_config",
            return_value=make_config(),
        ),
        patch(
            "app.services.strategy.registry.parameters._ensure_strategy_storage",
        ),
        patch(
            "app.services.strategy.registry.parameters._load_mutation",
            return_value=None,
        ),
        patch(
            "app.services.strategy.registry.parameters.update_strategy_configuration_record",
            side_effect=RuntimeError("database"),
        ),
        patch(
            "app.services.strategy.registry.parameters.is_data_error",
            return_value=True,
        ),
    ):
        failed = update_strategy_parameters(request, make_auth())
    assert failed.error is not None
    assert failed.error.code == "STRATEGY_INTERNAL_ERROR"
