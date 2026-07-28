"""WF-INDI-SEC: calculate and consume decision-time-qualified indicators."""

from __future__ import annotations

import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.indicators import ema
from app.services.strategy import (
    StrategyDecision,
    StrategyExecutionContext,
    StrategyTimingPolicy,
    run_vectorized_strategy_signals,
)
from tests.indicators.usage._support import unwrap_indicator_response
from tests.indicators.usage.workflows._support import live_bars
from tests.strategy.unit.test_models import (
    HASH,
    make_config,
    make_context,
    make_decision,
    make_ref,
)

WORKFLOW_ID = "WF-INDI-SEC"
STAGES = (
    "Accept current normalized Data evidence.",
    "Calculate the requested official indicator.",
    "Qualify values by source availability at decision time.",
    "Pass the typed IndicatorResult through Strategy's public boundary.",
    "Return the Strategy envelope or a documented domain error.",
)


class _CurrentNeutralEvaluator:
    """Hash-bound evaluator returning a decision valid at the current clock."""

    strategy_id = "mean-reversion"
    strategy_version = "1.0.0"
    module_path = "approved.strategies.mean_reversion"
    source_hash = HASH
    artifact_hash = HASH
    dependency_hash = HASH

    def evaluate_vectorized(
        self,
        market: object,
        indicators: object,
        config: object,
        context: StrategyExecutionContext,
        account_snapshot: object,
    ) -> tuple[StrategyDecision, ...]:
        """Return one neutral decision bound to the injected clock."""
        del market, indicators, config, account_snapshot
        return (
            make_decision(action="NEUTRAL").model_copy(
                update={
                    "valid_from": context.decision_timestamp - timedelta(seconds=1),
                    "expires_at": context.decision_timestamp + timedelta(seconds=1),
                }
            ),
        )


def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(
        f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}"
    )


def main() -> None:
    """Run the documented input-to-output workflow."""
    # Stage 1 — INPUT BOUNDARY: Data supplies a genuine MT5-backed MarketDataset.
    _stage(1)
    dataset = live_bars()
    print("Input available_at:", dataset.available_at)

    # Stage 2: Calculate official EMA values.
    _stage(2)
    indicator = unwrap_indicator_response(ema(dataset, period=5))
    print("Indicator rows:", indicator.manifest.row_count)

    # Stage 3: Establish the documented decision-time policy.
    _stage(3)
    timing = StrategyTimingPolicy.BAR_OPEN_PREVIOUS_CLOSE
    ref = make_ref(timing=timing)
    ref = ref.model_copy(
        update={
            "manifest": ref.manifest.model_copy(
                update={"required_indicators": ("ema",)}
            )
        }
    )
    print("Timing policy:", timing.value)

    # Stage 4: Consume only availability-qualified typed evidence.
    _stage(4)
    context = make_context(timing=timing).model_copy(
        update={"decision_timestamp": datetime.now(UTC)}
    )
    outcome = run_vectorized_strategy_signals(
        ref,
        make_config(),
        dataset,
        (indicator,),
        context,
        _CurrentNeutralEvaluator(),
    )
    print("Strategy status:", outcome.status)

    # Stage 5 — OUTPUT BOUNDARY: Return Strategy's canonical envelope.
    _stage(5)
    print("Output:", type(outcome).__name__, outcome.status)


if __name__ == "__main__":
    main()
