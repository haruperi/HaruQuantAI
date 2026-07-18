"""Strategy public export contract tests."""

from app.services import strategy
from app.utils import logger


def test_root_and_feature_exports_are_exact() -> None:
    """Verify root exports exactly match the documented public API."""
    logger.debug("Testing exact Strategy root exports")
    assert set(strategy.__all__) == {
        "DecomposingTradeEvaluator",
        "EventStrategyEvaluator",
        "HarrietHedgingEvaluator",
        "MarketStructureEvaluator",
        "NaiveMATrendEvaluator",
        "RandomWalkEvaluator",
        "SQXBreakoutAtrTrailingEvaluator",
        "StrategyCheckpoint",
        "StrategyConfig",
        "StrategyDecision",
        "StrategyDiagnostics",
        "StrategyEnvironment",
        "StrategyError",
        "StrategyErrorCode",
        "StrategyEvent",
        "StrategyExecutionContext",
        "StrategyExecutionResult",
        "StrategyLifecycleStatus",
        "StrategyManifest",
        "StrategyMutationResult",
        "StrategyOutcome",
        "StrategyParameterUpdateRequest",
        "StrategyRef",
        "StrategyRegistrationRequest",
        "StrategyReplayManifest",
        "StrategySignal",
        "StrategySignalEvidence",
        "StrategyTimingPolicy",
        "StrategyValidationPolicy",
        "TradeIntent",
        "ValidatedStrategyConfig",
        "ValidatedStrategyRef",
        "VectorizedStrategyEvaluator",
        "WhiteFairyEvaluator",
        "build_trade_intent",
        "create_strategy_checkpoint",
        "create_strategy_replay_manifest",
        "evaluate_strategy_signals",
        "export_strategy_diagnostics",
        "list_strategy_versions",
        "register_strategy_version",
        "run_event_strategy_hook",
        "run_vectorized_strategy_signals",
        "update_strategy_parameters",
        "validate_strategy_checkpoint",
        "validate_strategy_config",
        "validate_strategy_ref",
    }
