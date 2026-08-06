"""Tests for Strategy persistence update operations."""

from unittest.mock import patch

from app.services.strategy.persistence.update import (
    update_strategy_configuration_record,
    update_strategy_mutation_publication,
)

from tests.strategy.unit.test_models import (
    REQ,
    make_config,
    make_parameter_mutation,
    make_success_response,
)


def test_update_strategy_configuration_record() -> None:
    """Verify configuration update delegates to execution."""
    config = make_config()
    mutation = make_parameter_mutation()
    with patch(
        "app.services.strategy.persistence.update.execute_transaction"
    ) as mock_exec:
        mock_exec.return_value = make_success_response(data=None)
        update_strategy_configuration_record(config, mutation, "cmd-1", REQ)
        mock_exec.assert_called_once()
        tx_req = mock_exec.call_args[0][0]
        assert tx_req.plan.parameter_sets[0][2] == config.strategy_id
        assert tx_req.plan.parameter_sets[0][6] == config.model_dump_json()
        assert tx_req.plan.parameter_sets[1] == (
            "cmd-1",
            config.strategy_id,
            config.strategy_version,
            mutation.model_dump_json(),
            REQ,
        )


def test_update_strategy_mutation_publication() -> None:
    """Verify publication update delegates to execution."""
    mutation = make_parameter_mutation()
    with patch(
        "app.services.strategy.persistence.update.execute_transaction"
    ) as mock_exec:
        mock_exec.return_value = make_success_response(data=None)
        update_strategy_mutation_publication(mutation, "cmd-1")
        mock_exec.assert_called_once()
        tx_req = mock_exec.call_args[0][0]
        assert tx_req.plan.parameter_sets[0] == ("cmd-1",)
