"""Tests for Strategy mutation registry."""

from unittest.mock import patch

import pytest
from app.services.strategy.contracts.outcomes import StrategyMutationResult
from app.services.strategy.contracts.responses import StrategyOperationError
from app.services.strategy.registry._mutations import (
    _load_mutation,
    _load_policy,
    _publish_mutation,
)

from tests.strategy.unit.test_models import make_auth, make_ref


def test_load_mutation() -> None:
    """Verify loading prior mutation works when mutation exists."""
    mutation_json = '{"mutation_id": "mut-1", "mutation_type": "REGISTER_VERSION", "status": "ACCEPTED", "strategy_id": "mean-reversion", "strategy_version": "1.0.0", "record_ref": "ref", "record_hash": "hash", "request_id": "req-1", "correlation_id": "cor-1", "workflow_id": "wf-1"}'
    with patch(
        "app.services.strategy.registry._mutations.read_strategy_mutation_record"
    ) as mock_read:
        mock_read.return_value = [{"mutation_json": mutation_json}]
        result = _load_mutation("cmd-1", "req-1")
        assert result is not None
        assert result.mutation_id == "mut-1"


def test_load_policy() -> None:
    """Verify loading policy returns policy when exists."""
    policy_json = '{"policy_version": "policy-v1", "approved_module_roots": ["approved.strategies"], "max_config_payload_bytes": 4096, "max_config_nesting_depth": 8, "max_config_string_length": 128, "max_config_collection_items": 64}'
    with (
        patch(
            "app.services.strategy.registry._mutations.read_strategy_policy_record"
        ) as mock_read,
        patch("app.services.strategy.registry._mutations._ensure_strategy_storage"),
    ):
        mock_read.return_value = [{"policy_json": policy_json}]
        ref = make_ref()
        result = _load_policy(ref, "req-1")
        assert result is not None
        assert result.policy_version == "policy-v1"


def test_publish_mutation_success() -> None:
    """Verify mutation publishing success."""
    mutation = StrategyMutationResult(
        mutation_id="mut-1",
        mutation_type="REGISTER_VERSION",
        status="ACCEPTED",
        strategy_id="strat-1",
        strategy_version="1.0.0",
        record_ref="ref",
        record_hash="hash",
        request_id="req-1",
        correlation_id="cor-1",
        workflow_id="wf-1",
        publication_pending=True,
    )
    auth = make_auth()
    with (
        patch(
            "app.services.strategy.registry._mutations.persist_audit_event"
        ) as mock_persist,
        patch(
            "app.services.strategy.registry._mutations.update_strategy_mutation_publication"
        ) as mock_update,
    ):
        mock_persist.return_value = {"status": "success", "data": None}
        result = _publish_mutation(mutation, "cmd-1", auth)
        assert result.publication_pending is False
        assert result.audit_event_ref is not None
        mock_update.assert_called_once()


def test_publish_mutation_handles_data_error() -> None:
    """Verify mutation publishing gracefully handles data errors."""
    mutation = StrategyMutationResult(
        mutation_id="mut-1",
        mutation_type="REGISTER_VERSION",
        status="ACCEPTED",
        strategy_id="strat-1",
        strategy_version="1.0.0",
        record_ref="ref",
        record_hash="hash",
        request_id="req-1",
        correlation_id="cor-1",
        workflow_id="wf-1",
        publication_pending=True,
    )
    auth = make_auth()
    with patch(
        "app.services.strategy.registry._mutations.persist_audit_event"
    ) as mock_persist:
        mock_persist.side_effect = StrategyOperationError(
            "DATA_ERROR", "Data failed", details={"upstream_code": "DB_FAILED"}
        )
        result = _publish_mutation(mutation, "cmd-1", auth)
        # Should return the original mutation which is still pending
        assert result.publication_pending is True


def test_publish_mutation_raises_non_data_error() -> None:
    """Verify mutation publishing raises non-data errors."""
    mutation = StrategyMutationResult(
        mutation_id="mut-1",
        mutation_type="REGISTER_VERSION",
        status="ACCEPTED",
        strategy_id="strat-1",
        strategy_version="1.0.0",
        record_ref="ref",
        record_hash="hash",
        request_id="req-1",
        correlation_id="cor-1",
        workflow_id="wf-1",
        publication_pending=True,
    )
    auth = make_auth()
    with patch(
        "app.services.strategy.registry._mutations.persist_audit_event"
    ) as mock_persist:
        mock_persist.side_effect = ValueError("Other error")
        with pytest.raises(ValueError, match="Other error"):
            _publish_mutation(mutation, "cmd-1", auth)
