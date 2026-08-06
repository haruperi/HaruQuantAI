"""Tests for Strategy parameter registry."""

from datetime import UTC, datetime
from unittest.mock import patch

from app.services.strategy.contracts import (
    StrategyConfig,
    StrategyEnvironment,
    StrategyParameterUpdateRequest,
    StrategyRef,
)
from app.services.strategy.diagnostics.errors import StrategyErrorCode
from app.services.strategy.registry.parameters import update_strategy_parameters

from tests.strategy.unit.test_models import (
    make_auth,
    make_config,
    make_error_response,
    make_parameter_mutation,
    make_policy,
    make_ref,
    make_success_response,
)

NOW = datetime(2026, 1, 2, 12, tzinfo=UTC)


def _make_request() -> StrategyParameterUpdateRequest:
    config = StrategyConfig(
        strategy_id="mean-reversion",
        strategy_version="1.0.0",
        config_schema_version="v1",
        parameters={"period": 5},
        request_id="req-1",
    )
    ref = StrategyRef(
        strategy_id="mean-reversion",
        exact_version="1.0.0",
        environment=StrategyEnvironment.RESEARCH,
        request_id="req-1",
        correlation_id="cor-1",
    )
    return StrategyParameterUpdateRequest(
        command_id="cmd-1",
        strategy_id="mean-reversion",
        strategy_version="1.0.0",
        parameters={"period": 5},
        principal_id="builder",
        reason="test",
        ref=ref,
        config=config,
        authorization_ref="auth-1",
        requested_at=NOW,
        request_id="req-1",
        correlation_id="cor-1",
    )


def test_update_parameters_authorization_denied() -> None:
    """Verify parameters update rejects unauthorized requests."""
    req = _make_request()
    auth = make_auth(permissions=())
    result = update_strategy_parameters(req, auth)
    assert result.status == "success"
    assert result.data is not None
    assert result.data.status == "REJECTED"
    assert "AUTHORIZATION_DENIED" in result.data.reason_codes


def test_update_parameters_policy_not_found() -> None:
    """Verify parameters update rejects if policy is missing."""
    req = _make_request()
    auth = make_auth()
    with patch("app.services.strategy.registry.parameters._load_policy") as mock_policy:
        mock_policy.return_value = None
        result = update_strategy_parameters(req, auth)
        assert result.status == "success"
        assert result.data is not None
        assert result.data.status == "REJECTED"
        assert "STRATEGY_NOT_FOUND" in result.data.reason_codes


def test_update_parameters_config_validation_fails() -> None:
    """Verify parameters update rejects invalid config."""
    req = _make_request()
    auth = make_auth()
    validated_ref = make_ref()
    with (
        patch("app.services.strategy.registry.parameters._load_policy") as mock_policy,
        patch(
            "app.services.strategy.registry.parameters.validate_strategy_ref"
        ) as mock_val_ref,
        patch(
            "app.services.strategy.registry.parameters.validate_strategy_config"
        ) as mock_val_cfg,
    ):
        mock_policy.return_value = make_policy()
        mock_val_ref.return_value = make_success_response(data=validated_ref)
        mock_val_cfg.return_value = make_error_response(
            code=StrategyErrorCode.INVALID_CONFIG.value,
            message="Invalid config",
        )

        result = update_strategy_parameters(req, auth)
        assert result.status == "success"
        assert result.data is not None
        assert result.data.status == "REJECTED"
        assert "CONFIG_VALIDATION_FAILED" in result.data.reason_codes


def test_update_parameters_success() -> None:
    """Verify parameters update persists valid config."""
    req = _make_request()
    auth = make_auth()
    validated_ref = make_ref()
    validated_config = make_config()
    published_mutation = make_parameter_mutation()
    with (
        patch("app.services.strategy.registry.parameters._load_policy") as mock_policy,
        patch(
            "app.services.strategy.registry.parameters.validate_strategy_ref"
        ) as mock_val_ref,
        patch(
            "app.services.strategy.registry.parameters.validate_strategy_config"
        ) as mock_val_cfg,
        patch("app.services.strategy.registry.parameters._ensure_strategy_storage"),
        patch(
            "app.services.strategy.registry.parameters._load_mutation"
        ) as mock_load_mut,
        patch(
            "app.services.strategy.registry.parameters.update_strategy_configuration_record"
        ) as mock_update_rec,
        patch(
            "app.services.strategy.registry.parameters._publish_mutation"
        ) as mock_pub_mut,
    ):
        mock_policy.return_value = make_policy()
        mock_val_ref.return_value = make_success_response(data=validated_ref)
        mock_val_cfg.return_value = make_success_response(data=validated_config)
        mock_load_mut.return_value = None
        mock_pub_mut.return_value = published_mutation

        result = update_strategy_parameters(req, auth)
        assert result.status == "success"
        assert result.data == published_mutation
        mock_update_rec.assert_called_once()


def test_update_parameters_persistence_failure() -> None:
    """Verify parameters update returns error on persistence failure."""
    req = _make_request()
    auth = make_auth()
    validated_ref = make_ref()
    validated_config = make_config()
    with (
        patch("app.services.strategy.registry.parameters._load_policy") as mock_policy,
        patch(
            "app.services.strategy.registry.parameters.validate_strategy_ref"
        ) as mock_val_ref,
        patch(
            "app.services.strategy.registry.parameters.validate_strategy_config"
        ) as mock_val_cfg,
        patch(
            "app.services.strategy.registry.parameters._ensure_strategy_storage"
        ) as mock_ensure,
    ):
        mock_policy.return_value = make_policy()
        mock_val_ref.return_value = make_success_response(data=validated_ref)
        mock_val_cfg.return_value = make_success_response(data=validated_config)

        mock_ensure.side_effect = Exception("Database failure")

        result = update_strategy_parameters(req, auth)
        assert result.status == "error"
        assert result.error is not None
        assert result.error.code == StrategyErrorCode.INTERNAL_ERROR.value
