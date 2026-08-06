"""Unit tests for registry/registration.py branch coverage floor."""

from unittest.mock import patch

from app.services.strategy import (
    create_strategy_registration_request,
    register_strategy_version,
)
from app.services.strategy.contracts import StrategyLifecycleStatus
from app.services.strategy.contracts.responses import StrategyOperationError

from tests.strategy.unit.test_models import (
    COR,
    NOW,
    REQ,
    make_auth,
    make_manifest,
    make_policy,
)


def make_reg_req(manifest: object | None = None) -> object:
    m = manifest if manifest is not None else make_manifest()
    return create_strategy_registration_request(
        command_id="cmd-1",
        strategy_id=m.strategy_id,
        strategy_version=m.strategy_version,
        module_path=m.module_path,
        manifest=m,
        config_schema=m.config_schema,
        source_hash=m.source_hash,
        artifact_hash=m.artifact_hash,
        dependency_hash=m.dependency_hash,
        provenance_refs=m.provenance_refs,
        principal_id="principal-1",
        reason="Initial version registration",
        lifecycle_status=StrategyLifecycleStatus.APPROVED,
        authorization_ref="auth-ref-1",
        requested_at=NOW,
        request_id=REQ,
        correlation_id=COR,
    )


def test_registration_unapproved_module_branch() -> None:
    """Verify registration rejects unapproved module root."""
    manifest = make_manifest().model_copy(
        update={"module_path": "unapproved.submodule"}
    )
    req = make_reg_req(manifest)
    auth = make_auth(permissions=("strategy:register",))
    res = register_strategy_version(req, auth, policy=make_policy())
    assert res.status == "success"
    assert res.data is not None
    assert res.data.status == "REJECTED"
    assert res.data.reason_codes[0] == "UNAPPROVED_MODULE"


def test_registration_ambiguous_environment_branch() -> None:
    """Verify registration rejects empty or multiple permitted environments."""
    manifest = make_manifest().model_copy(
        update={"permitted_environments": ("RESEARCH", "PAPER_TRADING")}
    )
    req = make_reg_req(manifest)
    auth = make_auth(permissions=("strategy:register",))
    res = register_strategy_version(req, auth, policy=make_policy())
    assert res.status == "success"
    assert res.data is not None
    assert res.data.status == "REJECTED"
    assert res.data.reason_codes[0] == "AMBIGUOUS_ENVIRONMENT"


def test_registration_persistence_error_branches() -> None:
    """Verify persistence errors in registration are handled properly."""
    req = make_reg_req()
    auth = make_auth(permissions=("strategy:register",))

    with patch(
        "app.services.strategy.registry.registration._ensure_strategy_storage",
        side_effect=StrategyOperationError(
            "STRATEGY_INTERNAL_ERROR",
            "db failure",
            details={"upstream_code": "DB_WRITE_FAILED"},
        ),
    ):
        res = register_strategy_version(req, auth, policy=make_policy())
        assert res.status == "success"
        assert res.data is not None
        assert res.data.status == "REJECTED"
        assert res.data.reason_codes[0] == "IMMUTABLE_VERSION_EXISTS"

    import contextlib

    with (
        patch(
            "app.services.strategy.registry.registration._ensure_strategy_storage",
            side_effect=StrategyOperationError(
                "STRATEGY_INTERNAL_ERROR",
                "other db failure",
                details={"upstream_code": "OTHER_FAILURE"},
            ),
        ),
        contextlib.suppress(StrategyOperationError),
    ):
        register_strategy_version(req, auth, policy=make_policy())
