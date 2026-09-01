"""Fail-closed branch coverage for Strategy event and vectorized runners."""

from datetime import timedelta
from types import SimpleNamespace
from typing import Any
from unittest.mock import patch

import pytest
from app.composition.logging import get_logger
from app.services.strategy import (
    get_strategy_timing_policy,
    run_event_strategy_hook,
    run_vectorized_strategy_signals,
)

from tests.strategy.unit.test_event_runner import Evaluator as EventEvaluator
from tests.strategy.unit.test_models import (
    HASH,
    make_config,
    make_context,
    make_decision,
    make_event,
    make_market,
    make_ref,
)
from tests.strategy.unit.test_vectorized_runner import Evaluator as VectorEvaluator

logger = get_logger(__name__)
_VECTOR_TIMING = get_strategy_timing_policy("BAR_OPEN_PREVIOUS_CLOSE")
_ONE_BAR = (("1.1000", "1.1010", "1.0990", "1.1005"),)


class _VectorResultEvaluator(VectorEvaluator):
    """Vector evaluator returning or raising one controlled result."""

    def __init__(self, result: object) -> None:
        """Store the controlled evaluator result."""
        self._result = result

    def evaluate_vectorized(
        self,
        market: object,
        indicators: tuple[Any, ...],
        config: object,
        context: object,
        account_snapshot: object,
    ) -> object:
        """Return or raise the controlled result."""
        del market, indicators, config, context, account_snapshot
        if isinstance(self._result, BaseException):
            raise self._result
        return self._result


class _EventResultEvaluator(EventEvaluator):
    """Event evaluator returning or raising one controlled result."""

    def __init__(self, result: object) -> None:
        """Store the controlled evaluator result."""
        self._result = result

    def on_bar(
        self,
        ref: object,
        config: object,
        event: object,
        context: object,
        account_snapshot: object = None,
        local_state: object = None,
    ) -> object:
        """Return or raise the controlled result."""
        del ref, event, config, context, local_state, account_snapshot
        if isinstance(self._result, BaseException):
            raise self._result
        return self._result


def _run_vectorized(
    evaluator: object,
    *,
    ref: Any | None = None,
    config: Any | None = None,
    market: Any | None = None,
    context: Any | None = None,
    account_snapshot: object | None = None,
) -> Any:
    """Run one bounded vectorized case with complete default evidence."""
    return run_vectorized_strategy_signals(
        ref or make_ref(timing=_VECTOR_TIMING),
        config or make_config(),
        market or make_market(_ONE_BAR),
        (),
        context or make_context(timing=_VECTOR_TIMING),
        evaluator,
        account_snapshot,
    )


def _run_event(
    evaluator: object,
    *,
    ref: Any | None = None,
    config: Any | None = None,
    event: Any | None = None,
    context: Any | None = None,
    local_state: object | None = None,
    account_snapshot: object | None = None,
) -> Any:
    """Run one bounded event case with complete default evidence."""
    return run_event_strategy_hook(
        ref or make_ref(),
        config or make_config(),
        event or make_event(),
        context or make_context(),
        evaluator,
        account_snapshot=account_snapshot,
        local_state=local_state,
    )


@pytest.mark.parametrize(
    "outcome",
    [
        lambda: _run_vectorized(
            VectorEvaluator(),
            config=make_config().model_copy(update={"strategy_id": "other"}),
        ),
        lambda: _run_vectorized(
            VectorEvaluator(),
            market=make_market(_ONE_BAR).model_copy(update={"records": ()}),
        ),
        lambda: _run_vectorized(
            VectorEvaluator(),
            ref=make_ref(timing=_VECTOR_TIMING).model_copy(
                update={
                    "manifest": make_ref(timing=_VECTOR_TIMING).manifest.model_copy(
                        update={"max_batch_records": 1}
                    )
                }
            ),
            market=make_market(_ONE_BAR * 2),
        ),
        lambda: _run_vectorized(
            VectorEvaluator(),
            ref=make_ref(timing=_VECTOR_TIMING).model_copy(
                update={
                    "manifest": make_ref(timing=_VECTOR_TIMING).manifest.model_copy(
                        update={"required_indicators": ("rsi",)}
                    )
                }
            ),
        ),
        lambda: _run_vectorized(
            VectorEvaluator(),
            ref=make_ref(timing=_VECTOR_TIMING).model_copy(
                update={
                    "manifest": make_ref(timing=_VECTOR_TIMING).manifest.model_copy(
                        update={"requires_account_snapshot": True}
                    )
                }
            ),
        ),
    ],
)
def test_vectorized_readiness_rejections(outcome) -> None:
    """Verify independent vectorized readiness defects fail before evaluation."""
    assert outcome().status == "error"


def test_vectorized_evaluator_and_result_failures() -> None:
    """Verify evaluator, ordering, state, and digest failures are atomic."""
    assert _run_vectorized(_VectorResultEvaluator(RuntimeError("failed"))).status == (
        "error"
    )

    future = make_decision(action="NEUTRAL").model_copy(
        update={"valid_from": make_context().decision_timestamp + timedelta(seconds=1)}
    )
    assert _run_vectorized(_VectorResultEvaluator((future,))).status == "error"

    first = make_decision(action="NEUTRAL").model_copy(
        update={"candidate_local_state": {"first": 1}}
    )
    second = first.model_copy(
        update={
            "decision_id": "decision-2",
            "sequence": 1,
            "candidate_local_state": {"second": 2},
        }
    )
    assert _run_vectorized(_VectorResultEvaluator((first, second))).status == "error"

    unordered = (second, first)
    assert _run_vectorized(_VectorResultEvaluator(unordered)).status == "error"

    with patch(
        "app.services.strategy.vectorized.runner.canonical_digest",
        side_effect=ValueError("invalid input"),
    ):
        assert _run_vectorized(VectorEvaluator()).status == "error"

    with patch(
        "app.services.strategy.vectorized.runner.canonical_digest",
        side_effect=(HASH, HASH, ValueError("invalid result")),
    ):
        assert _run_vectorized(VectorEvaluator()).status == "error"


@pytest.mark.parametrize(
    "outcome",
    [
        lambda: _run_event(
            EventEvaluator(),
            config=make_config().model_copy(update={"strategy_id": "other"}),
        ),
        lambda: _run_event(
            EventEvaluator(),
            event=make_event().model_copy(
                update={"occurred_at": make_context().decision_timestamp + timedelta(1)}
            ),
        ),
        lambda: _run_event(
            EventEvaluator(),
            context=make_context().model_copy(
                update={"dependency_status": {"last_event_sequence": 1}}
            ),
        ),
        lambda: _run_event(
            EventEvaluator(),
            ref=make_ref().model_copy(
                update={
                    "manifest": make_ref().manifest.model_copy(
                        update={"max_local_state_bytes": 1}
                    )
                }
            ),
            local_state={"counter": 1},
        ),
        lambda: _run_event(
            EventEvaluator(),
            ref=make_ref().model_copy(
                update={
                    "manifest": make_ref().manifest.model_copy(
                        update={"requires_account_snapshot": True}
                    )
                }
            ),
        ),
        lambda: _run_event(
            EventEvaluator(),
            account_snapshot=SimpleNamespace(
                snapshot_at=make_context().decision_timestamp + timedelta(seconds=1),
                expires_at=make_context().decision_timestamp + timedelta(minutes=1),
            ),
        ),
    ],
)
def test_event_readiness_rejections(outcome) -> None:
    """Verify independent event readiness defects fail before evaluation."""
    assert outcome().status == "error"


def test_event_evaluator_and_result_failures() -> None:
    """Verify event evaluator, state, ordering, and digest failures are atomic."""
    assert _run_event(_EventResultEvaluator(RuntimeError("failed"))).status == "error"

    first = make_decision(action="NEUTRAL").model_copy(
        update={"candidate_local_state": {"first": 1}}
    )
    second = first.model_copy(
        update={
            "decision_id": "decision-2",
            "sequence": 1,
            "candidate_local_state": {"second": 2},
        }
    )
    assert _run_event(_EventResultEvaluator((first, second))).status == "error"
    assert _run_event(_EventResultEvaluator((second, first))).status == "error"

    tiny_ref = make_ref().model_copy(
        update={
            "manifest": make_ref().manifest.model_copy(
                update={"max_local_state_bytes": 1}
            )
        }
    )
    assert (
        _run_event(
            _EventResultEvaluator((first,)),
            ref=tiny_ref,
        ).status
        == "error"
    )

    with patch(
        "app.services.strategy.event.runner.canonical_digest",
        side_effect=ValueError("invalid result"),
    ):
        assert _run_event(EventEvaluator()).status == "error"
