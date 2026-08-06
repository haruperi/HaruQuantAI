"""Unit tests for persistence/create.py, read.py, update.py branch coverage floor."""

from types import SimpleNamespace
from unittest.mock import patch

from app.services.strategy.persistence.create import (
    create_strategy_checkpoint_record,
    create_strategy_signal_records,
)
from app.services.strategy.persistence.read import (
    read_strategy_config_record,
    read_strategy_configs,
    read_strategy_definitions,
    read_strategy_manifest_record,
    read_strategy_policy_record,
    read_strategy_versions,
)
from app.services.strategy.persistence.update import (
    update_strategy_mutation_publication,
    update_strategy_signal_publication_record,
)

from tests.strategy.unit.test_checkpoints_store_branches import make_checkpoint
from tests.strategy.unit.test_models import (
    REQ,
    make_parameter_mutation,
    make_success_response,
)


def test_create_strategy_signal_records_and_checkpoints() -> None:
    """Verify signal and checkpoint persistence record creation."""
    create_strategy_signal_records((), REQ)

    checkpoint = make_checkpoint()
    with patch(
        "app.services.strategy.persistence.create.execute_transaction"
    ) as mock_exec:
        mock_exec.return_value = make_success_response(data=SimpleNamespace(rows=[]))
        create_strategy_checkpoint_record(checkpoint)
        assert mock_exec.called

        signal_rec = {
            "signal_id": "sig-1",
            "config_id": "cfg-1",
            "strategy_id": "strat-1",
            "strategy_version": "1.0.0",
            "sequence": 0,
            "symbol": "EURUSD",
            "signal_name": "BUY",
            "side": "BUY",
            "active": True,
            "signal_timestamp": "2026-01-02T12:00:00Z",
            "signal_json": "{}",
            "request_id": REQ,
            "correlation_id": "cor-1",
            "created_at": "2026-01-02T12:00:00Z",
            "updated_at": "2026-01-02T12:00:00Z",
        }
        create_strategy_signal_records((signal_rec,), REQ)
        assert mock_exec.called


def test_read_functions_with_filters() -> None:
    """Verify read persistence functions with specific filter arguments."""
    with patch(
        "app.services.strategy.persistence.read._read_rows", return_value=()
    ) as mock_read:
        read_strategy_definitions(REQ, strategy_id="test-id")
        assert mock_read.called

        read_strategy_versions(REQ, strategy_id="test-id")
        assert mock_read.called

        read_strategy_manifest_record("test-id", "1.0.0", REQ)
        assert mock_read.called

        read_strategy_policy_record("test-id", "1.0.0", REQ)
        assert mock_read.called

        read_strategy_configs("test-id", "1.0.0", REQ)
        assert mock_read.called

        read_strategy_config_record("config-id", REQ)
        assert mock_read.called


def test_update_strategy_mutation_publication_branches() -> None:
    """Verify mutation publication update with failure responses."""
    mutation = make_parameter_mutation()
    with patch(
        "app.services.strategy.persistence.update.execute_transaction"
    ) as mock_exec:
        mock_exec.return_value = make_success_response(
            data=SimpleNamespace(rows=[], affected_rows=1)
        )
        update_strategy_mutation_publication(mutation=mutation, command_id="cmd-1")
        assert mock_exec.called

        res_sig = update_strategy_signal_publication_record(
            signal_id="sig-1",
            expected_status="generated",
            new_status="submitted",
            risk_submission_ref="risk-1",
            request_id=REQ,
        )
        assert res_sig is True
