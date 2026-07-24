"""Closed Strategy execution-result contract tests."""

from collections.abc import Mapping

import pytest
from app.services.strategy import (
    StrategyExecutionResult,
    StrategyTimingPolicy,
    run_vectorized_strategy_signals,
)
from app.utils import logger
from pydantic import ValidationError

from tests.strategy.unit.test_models import make_config, make_context, make_ref
from tests.strategy.unit.test_vectorized_runner import Evaluator, _dataset


def _result() -> StrategyExecutionResult:
    """Build one genuine closed execution result.

    Returns:
        Successful vectorized execution result.
    """
    logger.debug("Building closed Strategy execution-result fixture")
    timing = StrategyTimingPolicy.BAR_OPEN_PREVIOUS_CLOSE
    outcome = run_vectorized_strategy_signals(
        make_ref(timing=timing),
        make_config(),
        _dataset(),
        (),
        make_context(timing=timing),
        Evaluator(),
    )
    assert outcome.data is not None
    return outcome.data


def test_execution_result_rejects_untyped_boundary_values() -> None:
    """Reject raw objects at every typed result boundary."""
    logger.debug("Testing closed Strategy execution-result boundaries")
    result = _result()
    with pytest.raises(ValidationError):
        StrategyExecutionResult(
            decisions=result.decisions,
            intents=(object(),),
            diagnostics=result.diagnostics,
            replay_manifest=result.replay_manifest,
            result_hash=result.result_hash,
        )
    with pytest.raises(ValidationError):
        StrategyExecutionResult(
            decisions=result.decisions,
            intents=result.intents,
            diagnostics=object(),
            replay_manifest=result.replay_manifest,
            result_hash=result.result_hash,
        )
    with pytest.raises(ValidationError):
        StrategyExecutionResult(
            decisions=result.decisions,
            intents=result.intents,
            diagnostics=result.diagnostics,
            replay_manifest=object(),
            result_hash=result.result_hash,
        )


def test_execution_result_freezes_nested_local_state() -> None:
    """Freeze local state recursively at public construction."""
    logger.debug("Testing Strategy execution-result local-state immutability")
    result = _result()
    closed = StrategyExecutionResult(
        decisions=result.decisions,
        intents=result.intents,
        diagnostics=result.diagnostics,
        replay_manifest=result.replay_manifest,
        local_state_update={"nested": {"counter": 1}},
        result_hash=result.result_hash,
    )
    nested = closed.local_state_update
    assert isinstance(nested, Mapping)
    with pytest.raises(TypeError):
        nested["nested"] = {"counter": 2}  # type: ignore[index]
    child = nested["nested"]
    assert isinstance(child, Mapping)
    with pytest.raises(TypeError):
        child["counter"] = 2  # type: ignore[index]


def test_execution_result_round_trips_without_type_loss() -> None:
    """Rebuild exact nested contracts from the JSON representation."""
    logger.debug("Testing Strategy execution-result wire round trip")
    result = _result()
    rebuilt = StrategyExecutionResult.model_validate_json(result.model_dump_json())
    assert rebuilt == result
    assert type(rebuilt.diagnostics) is type(result.diagnostics)
    assert type(rebuilt.replay_manifest) is type(result.replay_manifest)
