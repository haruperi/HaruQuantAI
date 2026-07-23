"""Strategy public export contract tests."""

from importlib import import_module

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
        "SignalEvaluator",
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


def test_feature_exports_are_exact() -> None:
    """Verify every feature package exposes exactly its documented API."""
    logger.debug("Testing exact Strategy feature exports")
    expected = {
        "contracts": {
            "StrategyConfig",
            "StrategyDecision",
            "StrategyEnvironment",
            "StrategyError",
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
            "StrategySignal",
            "StrategySignalEvidence",
            "StrategyTimingPolicy",
            "StrategyValidationPolicy",
            "ValidatedStrategyConfig",
            "ValidatedStrategyRef",
        },
        "diagnostics": {
            "StrategyDiagnostics",
            "StrategyErrorCode",
            "export_strategy_diagnostics",
        },
        "registry": {
            "list_strategy_versions",
            "register_strategy_version",
            "update_strategy_parameters",
            "validate_strategy_config",
            "validate_strategy_ref",
        },
        "intents": {"TradeIntent", "build_trade_intent"},
        "replay": {
            "StrategyReplayManifest",
            "create_strategy_replay_manifest",
        },
        "checkpoints": {
            "StrategyCheckpoint",
            "create_strategy_checkpoint",
            "validate_strategy_checkpoint",
        },
        "vectorized": {
            "VectorizedStrategyEvaluator",
            "run_vectorized_strategy_signals",
        },
        "event": {"EventStrategyEvaluator", "run_event_strategy_hook"},
        "signals": {"SignalEvaluator", "evaluate_strategy_signals"},
        "evaluators": {
            "DecomposingTradeEvaluator",
            "HarrietHedgingEvaluator",
            "MarketStructureEvaluator",
            "NaiveMATrendEvaluator",
            "RandomWalkEvaluator",
            "SQXBreakoutAtrTrailingEvaluator",
            "WhiteFairyEvaluator",
        },
    }
    for feature, names in expected.items():
        module = import_module(f"app.services.strategy.{feature}")
        assert set(module.__all__) == names, feature


def test_migration_helpers_are_private() -> None:
    """Verify Strategy migration definitions expose no public surface."""
    logger.debug("Testing private Strategy migration surface")
    module = import_module("app.services.strategy.registry.migrations")
    assert module.__all__ == []
    public = {name for name in vars(module) if not name.startswith("_")}
    assert not public & {"strategy_migration_steps", "ensure_strategy_storage"}
