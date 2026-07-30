"""Strategy public export contract tests."""

from importlib import import_module

from app.services import strategy
from app.utils import get_logger

logger = get_logger(__name__)


def test_root_and_feature_exports_are_exact() -> None:
    """Verify root exports exactly match the documented public API."""
    logger.debug("Testing exact Strategy root exports")
    expected_functions = {
        "adopt_approved_optimization_parameters",
        "bind_proposal_lineage",
        "build_trade_intent",
        "create_strategy_checkpoint",
        "create_strategy_checkpoint_value",
        "create_strategy_config",
        "create_strategy_decision",
        "create_strategy_diagnostics",
        "create_strategy_event",
        "create_strategy_evaluator",
        "create_strategy_execution_context",
        "create_strategy_execution_result",
        "create_strategy_manifest",
        "create_strategy_mutation_result",
        "create_strategy_parameter_update_request",
        "create_strategy_proposal_evaluation_request",
        "create_strategy_proposal_evaluation_result",
        "create_strategy_ref",
        "create_strategy_registration_request",
        "create_strategy_replay_manifest",
        "create_strategy_replay_manifest_value",
        "create_strategy_signal_evidence",
        "create_strategy_signal",
        "create_strategy_validation_policy",
        "create_trade_intent_value",
        "evaluate_strategy_proposal",
        "evaluate_strategy_signals",
        "export_strategy_diagnostics",
        "get_strategy_environment",
        "get_strategy_error_code",
        "get_strategy_error_catalog",
        "get_strategy_lifecycle_status",
        "get_strategy_timing_policy",
        "list_strategy_versions",
        "register_strategy_version",
        "run_event_strategy_hook",
        "run_vectorized_strategy_signals",
        "update_strategy_parameters",
        "validate_strategy_checkpoint",
        "validate_strategy_config",
        "validate_strategy_proposal",
        "validate_strategy_ref",
        "create_validated_strategy_config",
        "create_validated_strategy_ref",
    }
    assert set(strategy.__all__) == expected_functions
    for name in strategy.__all__:
        assert callable(getattr(strategy, name)), f"{name} must be a callable function"


def test_feature_subpackages_are_not_additional_public_boundaries() -> None:
    """Verify concrete evaluator classes are absent from all public facades."""
    logger.debug("Testing Strategy package-root-only public boundary")
    assert import_module("app.services.strategy.evaluators").__all__ == ()


def test_migration_helpers_are_private() -> None:
    """Verify Strategy migration definitions expose no public surface."""
    logger.debug("Testing private Strategy migration surface")
    module = import_module("app.services.strategy.migrations.definitions")
    assert module.__all__ == []
    public = {name for name in vars(module) if not name.startswith("_")}
    assert not public & {"strategy_migration_steps", "ensure_strategy_storage"}
