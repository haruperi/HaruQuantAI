"""Strategy public export contract tests."""

from importlib import import_module

from app.services import strategy
from app.utils import get_logger

logger = get_logger(__name__)


def test_root_and_feature_exports_are_exact() -> None:
    """Verify root exports exactly match the documented public API.

    Args:
        None.

    Returns:
        None.
    """
    logger.debug("Testing exact Strategy root exports")
    expected_functions = {
        "adopt_approved_optimization_parameters",
        "amend_trade_plan",
        "bind_proposal_lineage",
        "bootstrap_builtin_strategies",
        "build_development_strategy_validation_policy",
        "build_expectancy_reference",
        "build_exit_plan",
        "build_exit_plan_handoff",
        "build_manual_trade_plan",
        "build_operating_envelope",
        "build_setup_evaluation",
        "build_strategy_playbook",
        "build_strategy_profile",
        "build_trade_intent",
        "build_trade_plan",
        "commit_strategy_runtime_state",
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
        "create_strategy_signal",
        "create_strategy_signal_evidence",
        "create_strategy_validation_policy",
        "create_trade_intent_value",
        "create_validated_strategy_config",
        "create_validated_strategy_ref",
        "evaluate_and_record_strategy_signals",
        "evaluate_automation_mode",
        "evaluate_expectancy_reference",
        "evaluate_operating_envelope",
        "evaluate_strategy_proposal",
        "evaluate_strategy_signals",
        "export_strategy_diagnostics",
        "get_strategy_definition",
        "govern_strategy_lifecycle",
        "get_strategy_environment",
        "get_strategy_error_catalog",
        "get_strategy_error_code",
        "get_strategy_lifecycle_status",
        "get_strategy_timing_policy",
        "initialize_strategy_runtime_state",
        "list_builtin_strategy_descriptors",
        "list_strategy_checkpoints",
        "list_strategy_configs",
        "list_strategy_definitions",
        "list_strategy_signals",
        "list_strategy_versions",
        "load_strategy_runtime_state",
        "mark_strategy_signal_submitted",
        "parse_expectancy_reference",
        "parse_exit_plan",
        "parse_operating_envelope",
        "parse_setup_evaluation",
        "parse_strategy_playbook",
        "parse_strategy_profile",
        "parse_trade_plan",
        "record_strategy_signals",
        "register_strategy_version",
        "resolve_strategy_config",
        "run_event_strategy_hook",
        "run_persisted_event_strategy_hook",
        "run_vectorized_strategy_signals",
        "transition_trade_plan",
        "update_strategy_parameters",
        "unwrap_strategy_response",
        "validate_strategy_checkpoint",
        "validate_strategy_config",
        "validate_strategy_proposal",
        "validate_strategy_ref",
        "validate_manual_trade_plan",
        "validate_trade_plan_for_intent",
    }
    assert set(strategy.__all__) == expected_functions
    for name in strategy.__all__:
        assert callable(getattr(strategy, name)), f"{name} must be a callable function"


def test_feature_subpackages_are_not_additional_public_boundaries() -> None:
    """Verify concrete evaluator classes are absent from all public facades.

    Args:
        None.

    Returns:
        None.
    """
    logger.debug("Testing Strategy package-root-only public boundary")
    assert import_module("app.services.strategy.evaluators").__all__ == ()


def test_migration_helpers_are_private() -> None:
    """Verify Strategy migration definitions expose no public surface.

    Args:
        None.

    Returns:
        None.
    """
    logger.debug("Testing private Strategy migration surface")
    module = import_module("app.services.strategy.migrations.definitions")
    assert module.__all__ == []
    public = {name for name in vars(module) if not name.startswith("_")}
    assert not public & {"strategy_migration_steps", "ensure_strategy_storage"}
