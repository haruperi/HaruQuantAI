"""Fail-closed branch coverage for concrete Strategy signal evaluation."""

from datetime import timedelta
from typing import Any

import pytest
from app.composition.logging import get_logger
from app.services.strategy import create_strategy_evaluator, evaluate_strategy_signals
from app.services.strategy.signals._mechanics import (
    _SignalConfigError,
    _SignalDataError,
    _SignalIndicatorError,
)

from tests.strategy.unit.test_models import (
    HASH,
    make_context,
    make_market,
    make_ref,
    make_signal_config,
    make_signal_evidence,
)

logger = get_logger(__name__)


def _evaluator(**overrides: object) -> Any:
    """Build a registry-bound RandomWalk evaluator with optional identity changes."""
    values: dict[str, object] = {
        "strategy_id": "mean-reversion",
        "strategy_version": "1.0.0",
        "module_path": "approved.strategies.mean_reversion",
        "source_hash": HASH,
        "artifact_hash": HASH,
        "dependency_hash": HASH,
    }
    values.update(overrides)
    return create_strategy_evaluator("random_walk", **values)


def _arguments(evaluator: object) -> tuple[Any, ...]:
    """Build one complete public signal-evaluation argument tuple."""
    market = make_market((("1", "2", "0", "1"),))
    return (
        make_ref(),
        make_signal_config({"buy_magic_number": 10, "sell_magic_number": 20}),
        make_signal_evidence(market),
        (),
        make_context(),
        evaluator,
    )


@pytest.mark.parametrize(
    "evaluator",
    [
        _evaluator(module_path="unapproved.module"),
        _evaluator(dependency_hash="b" * 64),
    ],
)
def test_signal_evaluator_identity_mismatches_fail_closed(evaluator: object) -> None:
    """Verify module and dependency identity mismatches stop evaluation."""
    outcome = evaluate_strategy_signals(*_arguments(evaluator))
    assert outcome.status == "error"


def test_signal_configuration_and_market_identity_fail_closed() -> None:
    """Verify configuration and primary/related market defects are rejected."""
    ref, config, evidence, indicators, context, evaluator = _arguments(_evaluator())
    wrong_config = config.model_copy(update={"strategy_id": "other"})
    assert (
        evaluate_strategy_signals(
            ref,
            wrong_config,
            evidence,
            indicators,
            context,
            evaluator,
        ).status
        == "error"
    )

    invalid_primary = evidence.model_copy(
        update={
            "primary_market": evidence.primary_market.model_copy(update={"records": ()})
        }
    )
    assert (
        evaluate_strategy_signals(
            ref,
            config,
            invalid_primary,
            indicators,
            context,
            evaluator,
        ).status
        == "error"
    )

    invalid_related = evidence.model_copy(
        update={
            "related_markets": {
                "H1": evidence.primary_market.model_copy(update={"records": ()})
            }
        }
    )
    assert (
        evaluate_strategy_signals(
            ref,
            config,
            invalid_related,
            indicators,
            context,
            evaluator,
        ).status
        == "error"
    )

    future_features = evidence.model_copy(
        update={
            "feature_available_at": {
                "feature": evidence.primary_market.available_at + timedelta(seconds=1)
            }
        }
    )
    assert (
        evaluate_strategy_signals(
            ref,
            config,
            future_features,
            indicators,
            context,
            evaluator,
        ).status
        == "error"
    )


class _ResultEvaluator:
    """Registry-bound evaluator returning or raising one controlled result."""

    strategy_id = "mean-reversion"
    strategy_version = "1.0.0"
    module_path = "approved.strategies.mean_reversion"
    source_hash = HASH
    artifact_hash = HASH
    dependency_hash = HASH

    def __init__(self, result: object) -> None:
        """Store the result or exception for deterministic evaluation."""
        self._result = result

    def evaluate_signals(
        self,
        evidence: object,
        indicators: tuple[Any, ...],
        config: object,
        context: object,
    ) -> object:
        """Return the configured result or raise the configured exception."""
        del evidence, indicators, config, context
        if isinstance(self._result, BaseException):
            raise self._result
        return self._result


@pytest.mark.parametrize(
    "error",
    [
        _SignalConfigError("bad config"),
        _SignalDataError("bad data"),
        _SignalIndicatorError("bad indicator"),
        RuntimeError("unexpected"),
    ],
)
def test_signal_evaluator_exceptions_map_to_owned_errors(error: Exception) -> None:
    """Verify known and unexpected evaluator failures remain structured."""
    outcome = evaluate_strategy_signals(*_arguments(_ResultEvaluator(error)))
    assert outcome.status == "error"


def test_signal_output_batch_validation_rejects_invalid_shapes() -> None:
    """Verify empty, duplicate, and mismatched signal batches fail closed."""
    assert (
        evaluate_strategy_signals(*_arguments(_ResultEvaluator(()))).status == "error"
    )

    ref, config, evidence, indicators, context, evaluator = _arguments(_evaluator())
    response = evaluator.evaluate_signals(evidence, indicators, config, context)
    assert response.data is not None
    valid = response.data
    duplicate = _ResultEvaluator((valid[0], valid[0]))
    assert (
        evaluate_strategy_signals(
            ref,
            config,
            evidence,
            indicators,
            context,
            duplicate,
        ).status
        == "error"
    )

    mismatched = valid[0].model_copy(update={"strategy_id": "other"})
    assert (
        evaluate_strategy_signals(
            ref,
            config,
            evidence,
            indicators,
            context,
            _ResultEvaluator((mismatched,)),
        ).status
        == "error"
    )
