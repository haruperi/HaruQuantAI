"""Large-input behaviour for Strategy digest bounding (STR-B05).

These tests prove the runners digest realistic dataset and batch sizes rather
than merely declaring a resource limit. Every prior fixture used <=20 bars, so
the unbounded ``canonical_json`` path that failed above ~660 records was never
exercised.
"""

# ruff: noqa: PT018

from datetime import timedelta

from app.services.strategy import (
    StrategyTimingPolicy,
    run_vectorized_strategy_signals,
)
from app.utils import canonical_digest, logger

from tests.strategy.unit.test_models import (
    NOW,
    make_config,
    make_context,
    make_decision,
    make_market,
    make_ref,
)
from tests.strategy.unit.test_vectorized_runner import Evaluator

_TIMING = StrategyTimingPolicy.BAR_OPEN_PREVIOUS_CLOSE
_SHA256_LENGTH = 64
_BAR = ("1.1000", "1.1010", "1.0990", "1.1005")


def _past_dataset(bar_count: int) -> object:
    """Build a point-in-time-safe dataset of ``bar_count`` bars ending before NOW.

    Args:
        bar_count: Number of bars to synthesize.

    Returns:
        An immutable dataset whose every record is available at or before the
        fixture decision clock, so it never trips the lookahead guard.
    """
    logger.debug("Building %d-bar large-input dataset", bar_count)
    base = make_market(tuple(_BAR for _ in range(bar_count)))
    step = timedelta(minutes=5)
    records = tuple(
        record.model_copy(
            update={
                "timestamp": NOW - step * (bar_count - index),
                "available_at": NOW - step * (bar_count - index),
            }
        )
        for index, record in enumerate(base.records)
    )
    quality = base.quality_report.model_copy(
        update={"generated_at": records[-1].available_at}
    )
    return base.model_copy(
        update={
            "records": records,
            "start": records[0].timestamp,
            "end": records[-1].timestamp,
            "available_at": records[-1].available_at,
            "quality_report": quality,
        }
    )


def test_vectorized_runner_digests_thousand_bar_dataset() -> None:
    """Verify a 1,000-bar dataset digests and succeeds without raising."""
    logger.debug("Testing 1000-bar vectorized digest")
    outcome = run_vectorized_strategy_signals(
        make_ref(timing=_TIMING),
        make_config(),
        _past_dataset(1_000),
        (),
        make_context(timing=_TIMING),
        Evaluator(),
    )
    assert outcome.status == "success"
    assert outcome.data is not None
    assert len(outcome.data.result_hash) == _SHA256_LENGTH


def test_vectorized_runner_digest_is_unchanged_across_bound() -> None:
    """Verify datasets just below and above the old ~660-record ceiling both run."""
    logger.debug("Testing vectorized digest across the former ceiling")
    for bar_count in (600, 700, 1_000):
        outcome = run_vectorized_strategy_signals(
            make_ref(timing=_TIMING),
            make_config(),
            _past_dataset(bar_count),
            (),
            make_context(timing=_TIMING),
            Evaluator(),
        )
        assert outcome.status == "success", bar_count
        assert outcome.data is not None and outcome.data.result_hash


def test_vectorized_runner_rejects_oversized_batch() -> None:
    """Verify the resource-limit guard still fires with a small batch bound."""
    logger.debug("Testing vectorized oversized-batch rejection")
    base = make_ref(timing=_TIMING)
    ref = base.model_copy(
        update={"manifest": base.manifest.model_copy(update={"max_batch_records": 1})}
    )

    class _TwoDecisionEvaluator(Evaluator):
        def evaluate_vectorized(
            self, market, indicators, config, context, account_snapshot
        ):
            """Return two decisions to exceed the one-record batch bound.

            Returns:
                Two neutral decisions.
            """
            del market, indicators, config, context, account_snapshot
            first = make_decision(action="NEUTRAL")
            second = first.model_copy(
                update={"decision_id": "decision-2", "sequence": 1}
            )
            return (first, second)

    outcome = run_vectorized_strategy_signals(
        ref,
        make_config(),
        _past_dataset(10),
        (),
        make_context(timing=_TIMING),
        _TwoDecisionEvaluator(),
    )
    assert outcome.status == "error"
    assert outcome.error is not None
    assert outcome.error.code == "STRATEGY_RESOURCE_LIMIT_EXCEEDED"


def test_result_digest_is_deterministic_and_order_sensitive() -> None:
    """Verify the shared canonical digest is stable and order-sensitive."""
    logger.debug("Testing canonical digest properties over batch material")
    records = tuple({"index": index, "close": f"1.{index:04d}"} for index in range(600))
    material = {"symbol": "EURUSD", "records": records}
    first = canonical_digest(material)
    assert first == canonical_digest(material)
    assert len(first) == _SHA256_LENGTH

    reordered = {"symbol": "EURUSD", "records": (records[1], records[0], *records[2:])}
    assert canonical_digest(reordered) != first

    changed_envelope = {"symbol": "GBPUSD", "records": records}
    assert canonical_digest(changed_envelope) != first
