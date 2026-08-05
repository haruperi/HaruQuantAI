"""Tests for Strategy persistence update operations."""

from unittest.mock import patch

from app.services.strategy.contracts.outcomes import StrategyMutationResult
from app.services.strategy.persistence.update import (
    update_strategy_configuration_record,
    update_strategy_mutation_publication,
)

from tests.strategy.unit.test_models import make_config


def test_update_strategy_configuration_record() -> None:
    """Verify configuration update delegates to execution."""
    config = make_config()
    mutation = StrategyMutationResult(
        mutation_id="mut-1",
        mutation_type="UPDATE_PARAMETERS",
        status="ACCEPTED",
        strategy_id=config.strategy_id,
        strategy_version=config.strategy_version,
        record_ref="ref",
        record_hash="hash",
        request_id=config.request_id,
        correlation_id="cor-1",
        workflow_id="wf-1",
    )
    with patch(
        "app.services.strategy.persistence.update.execute_transaction"
    ) as mock_exec:
        mock_exec.return_value = {"status": "success", "data": None}
        update_strategy_configuration_record(config, mutation, "cmd-1", "req-1")
        mock_exec.assert_called_once()


def test_update_strategy_mutation_publication() -> None:
    """Verify publication update delegates to execution."""
    mutation = StrategyMutationResult(
        mutation_id="mut-1",
        mutation_type="UPDATE_PARAMETERS",
        status="ACCEPTED",
        strategy_id="strat-1",
        strategy_version="1.0.0",
        record_ref="ref",
        record_hash="hash",
        request_id="req-1",
        correlation_id="cor-1",
        workflow_id="wf-1",
    )
    with patch(
        "app.services.strategy.persistence.update.execute_transaction"
    ) as mock_exec:
        mock_exec.return_value = {"status": "success", "data": None}
        update_strategy_mutation_publication(mutation, "cmd-1")
        mock_exec.assert_called_once()
