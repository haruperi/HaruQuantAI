"""Unit tests for event/runner.py branch coverage floor."""

from unittest.mock import patch

from app.services.strategy import (
    commit_strategy_runtime_state,
    initialize_strategy_runtime_state,
    load_strategy_runtime_state,
    run_persisted_event_strategy_hook,
)

from tests.strategy.unit.test_models import (
    NOW,
    REQ,
    make_config,
    make_context,
    make_event,
    make_ref,
)


def test_initialize_and_load_strategy_runtime_state() -> None:
    """Verify initialize and load runtime state functions."""
    with patch(
        "app.services.strategy.persistence.read_strategy_state_record",
        return_value=(),
    ):
        res_init = initialize_strategy_runtime_state("cfg-1", REQ, "cor-1")
        assert res_init.status == "success"
        assert res_init.data is not None

        res_load = load_strategy_runtime_state("cfg-1")
        assert res_load.status == "success"
        assert res_load.data is None


def test_commit_strategy_runtime_state_failure() -> None:
    """Verify optimistic concurrency commit failure."""
    with patch(
        "app.services.strategy.persistence.update_strategy_runtime_state_record",
        return_value=False,
    ):
        res = commit_strategy_runtime_state(
            "cfg-1",
            expected_state_version=0,
            evaluation_status="ready",
            bars_processed=1,
            last_evidence_at=NOW,
            request_id=REQ,
            correlation_id="cor-1",
        )
        assert res.status == "error"
        assert res.error is not None
        assert res.error.code == "STRATEGY_INTERNAL_ERROR"


def test_run_persisted_event_strategy_hook_flow() -> None:
    """Verify run_persisted_event_strategy_hook loads state, executes, and commits."""
    ref = make_ref()
    config = make_config()
    event = make_event()
    context = make_context()
    from tests.strategy.unit.test_event_runner import Evaluator

    evaluator = Evaluator()

    from tests.strategy.unit.test_models import make_success_response

    with (
        patch(
            "app.services.strategy.event.runner.load_strategy_runtime_state"
        ) as mock_load,
        patch(
            "app.services.strategy.persistence.update_strategy_runtime_state_record",
            return_value=True,
        ),
    ):
        mock_load.return_value = make_success_response(
            data={"state_version": 1, "bars_processed": 5, "local_state": {}}
        )
        res = run_persisted_event_strategy_hook(
            ref, config, "cfg-1", event, context, evaluator
        )
        assert res.status == "success"
        assert res.data is not None
