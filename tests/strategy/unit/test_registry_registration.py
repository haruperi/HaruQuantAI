"""Tests for Strategy version registration."""

from datetime import UTC, datetime
from unittest.mock import patch

from app.services.strategy.contracts import (
    StrategyLifecycleStatus,
    StrategyRegistrationRequest,
)
from app.services.strategy.contracts.responses import StrategyOperationError
from app.services.strategy.registry.registration import register_strategy_version

from tests.strategy.unit.test_models import (
    make_auth,
    make_manifest,
    make_policy,
    make_registration_mutation,
)

NOW = datetime(2026, 1, 2, 12, tzinfo=UTC)


def _make_reg_req() -> StrategyRegistrationRequest:
    manifest = make_manifest()
    return StrategyRegistrationRequest(
        command_id="cmd-1",
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
        reason="Initial registration",
        lifecycle_status=StrategyLifecycleStatus.APPROVED,
        authorization_ref="auth-1",
        requested_at=NOW,
        request_id="req-1",
        correlation_id="cor-1",
    )


def test_register_strategy_unauthorized() -> None:
    """Verify registration rejects unauthorized users."""
    req = _make_reg_req()
    auth = make_auth(permissions=())  # missing strategy:register
    policy = make_policy()
    result = register_strategy_version(req, auth, policy)
    assert result.status == "success"
    assert result.data is not None
    assert result.data.status == "REJECTED"
    assert "AUTHORIZATION_DENIED" in result.data.reason_codes
    assert result.data.validated_ref is None
    assert result.data.validated_config is None


def test_register_strategy_lifecycle_not_approved() -> None:
    """Verify registration requires APPROVED lifecycle."""
    req = _make_reg_req().model_copy(
        update={"lifecycle_status": StrategyLifecycleStatus.REVOKED}
    )
    auth = make_auth()
    policy = make_policy()
    result = register_strategy_version(req, auth, policy)
    assert result.status == "success"
    assert result.data is not None
    assert result.data.status == "REJECTED"
    assert "LIFECYCLE_NOT_APPROVED" in result.data.reason_codes
    assert result.data.validated_ref is None
    assert result.data.validated_config is None


def test_register_strategy_idempotent() -> None:
    """Verify registration handles idempotency correctly."""
    req = _make_reg_req()
    auth = make_auth()
    policy = make_policy()
    existing = make_registration_mutation(status="ACCEPTED")
    with (
        patch("app.services.strategy.registry.registration._ensure_strategy_storage"),
        patch(
            "app.services.strategy.registry.registration._load_mutation"
        ) as mock_load,
    ):
        mock_load.return_value = existing

        result = register_strategy_version(req, auth, policy)
        assert result.status == "success"
        assert result.data is not None
        assert result.data.status == "IDEMPOTENT"
        assert result.data.validated_ref == existing.validated_ref


def test_register_strategy_db_write_failed() -> None:
    """Verify registration catches db collision and returns REJECTED."""
    req = _make_reg_req()
    auth = make_auth()
    policy = make_policy()
    with (
        patch("app.services.strategy.registry.registration._ensure_strategy_storage"),
        patch(
            "app.services.strategy.registry.registration._load_mutation"
        ) as mock_load,
        patch(
            "app.services.strategy.registry.registration.create_strategy_version_record"
        ) as mock_create,
    ):
        mock_load.return_value = None
        mock_create.side_effect = StrategyOperationError(
            "DB_WRITE_FAILED", "Collision", details={"upstream_code": "DB_WRITE_FAILED"}
        )

        result = register_strategy_version(req, auth, policy)
        assert result.status == "success"
        assert result.data is not None
        assert result.data.status == "REJECTED"
        assert "IMMUTABLE_VERSION_EXISTS" in result.data.reason_codes
        assert result.data.validated_ref is None
        assert result.data.validated_config is None
