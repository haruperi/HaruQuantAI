"""Tests for Strategy version registration."""

from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

from app.services.strategy.contracts import (
    StrategyLifecycleStatus,
    StrategyRegistrationRequest,
)
from app.services.strategy.contracts.responses import StrategyOperationError
from app.services.strategy.registry.registration import register_strategy_version

from tests.strategy.unit.test_models import make_auth, make_manifest, make_policy

NOW = datetime(2026, 1, 2, 12, tzinfo=UTC)


def _make_reg_req() -> StrategyRegistrationRequest:
    return StrategyRegistrationRequest(
        command_id="cmd-1",
        manifest=make_manifest(),
        lifecycle_status=StrategyLifecycleStatus.APPROVED,
        principal_id="builder",
        requested_at=NOW,
        request_id="req-1",
        correlation_id="cor-1",
    )


def test_register_strategy_unauthorized() -> None:
    """Verify registration rejects unauthorized users."""
    req = _make_reg_req()
    auth = make_auth()
    auth.permissions = ()  # missing strategy:register
    policy = make_policy()
    result = register_strategy_version(req, auth, policy)
    assert result.status == "success"
    assert result.data.status == "REJECTED"
    assert "AUTHORIZATION_DENIED" in result.data.reason_codes


def test_register_strategy_lifecycle_not_approved() -> None:
    """Verify registration requires APPROVED lifecycle."""
    req = _make_reg_req()
    req.lifecycle_status = StrategyLifecycleStatus.STOPPED
    auth = make_auth()
    policy = make_policy()
    result = register_strategy_version(req, auth, policy)
    assert result.status == "success"
    assert result.data.status == "REJECTED"
    assert "LIFECYCLE_NOT_APPROVED" in result.data.reason_codes


def test_register_strategy_idempotent() -> None:
    """Verify registration handles idempotency correctly."""
    req = _make_reg_req()
    auth = make_auth()
    policy = make_policy()
    with (
        patch("app.services.strategy.registry.registration._ensure_strategy_storage"),
        patch(
            "app.services.strategy.registry.registration._load_mutation"
        ) as mock_load,
    ):
        existing = MagicMock()
        existing.model_copy.return_value = MagicMock(status="IDEMPOTENT")
        mock_load.return_value = existing

        result = register_strategy_version(req, auth, policy)
        assert result.status == "success"
        assert result.data.status == "IDEMPOTENT"


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
        assert result.data.status == "REJECTED"
        assert "IMMUTABLE_VERSION_EXISTS" in result.data.reason_codes
