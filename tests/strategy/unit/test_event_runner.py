"""Atomic event-driven Strategy runner tests."""

from app.services.strategy import run_event_strategy_hook
from app.services.strategy.contracts import StrategyExecutionResult
from app.services.strategy.contracts.responses import unwrap_strategy_response
from app.services.strategy.diagnostics import export_strategy_diagnostics
from app.services.strategy.event import EventStrategyEvaluator
from app.services.strategy.replay import create_strategy_replay_manifest
from app.utils import get_logger

from tests.strategy.unit.test_models import (
    HASH,
    make_config,
    make_context,
    make_decision,
    make_event,
    make_ref,
)

logger = get_logger(__name__)


class Evaluator:
    """Hash-bound deterministic event test evaluator."""

    strategy_id = "mean-reversion"
    strategy_version = "1.0.0"
    module_path = "approved.strategies.mean_reversion"
    source_hash = HASH
    artifact_hash = HASH
    dependency_hash = HASH

    def on_bar(
        self,
        ref,
        config,
        event,
        context,
        account_snapshot=None,
        local_state=None,
    ) -> StrategyExecutionResult:
        """Return one neutral decision for supplied event evidence."""
        logger.debug("Evaluating event Strategy test evidence")
        del event, local_state, account_snapshot
        diagnostics = unwrap_strategy_response(
            export_strategy_diagnostics(context, {"bars_seen": 1}),
            operation="export_diagnostics",
        )
        replay = unwrap_strategy_response(
            create_strategy_replay_manifest(
                ref=ref,
                config=config,
                context=context,
                data_checksum=HASH,
                indicator_manifest_hash=HASH,
                simulation_config_hash=HASH,
            ),
            operation="create_replay",
        )
        return StrategyExecutionResult(
            decisions=(make_decision(action="NEUTRAL"),),
            intents=(),
            diagnostics=diagnostics,
            replay_manifest=replay,
            local_state_update={"counter": 1},
            result_hash=HASH,
        )


def test_event_evaluator_identity_and_hook_are_verified() -> None:
    """Verify evaluator identity mismatches fail before invocation."""
    logger.debug("Testing event evaluator hook binding")
    evaluator = Evaluator()
    evaluator.strategy_id = "mismatched"
    res = run_event_strategy_hook(
        make_ref(), make_config(), make_event(), make_context(), evaluator
    )
    assert res.status == "error"


def test_event_result_commits_state_atomically() -> None:
    """Verify a validated local-state candidate appears only in success."""
    logger.debug("Testing atomic event Strategy local-state result")
    result = unwrap_strategy_response(
        run_event_strategy_hook(
            make_ref(), make_config(), make_event(), make_context(), Evaluator()
        ),
        operation="run_event_strategy_hook",
    )
    assert result.local_state_update == {"counter": 1}
    assert isinstance(Evaluator(), EventStrategyEvaluator)
