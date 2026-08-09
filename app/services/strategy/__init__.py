"""Approved Strategy domain package-root public API.

Every cross-domain consumer must import standalone functions from
``app.services.strategy``. The public API surface consists exclusively of
standalone functions. Classes, dataclasses, pydantic models, enums, protocols,
and raw constants remain internal implementation details. Feature subpackages
are private implementation details.
"""

from app.services.strategy.checkpoints import (
    create_strategy_checkpoint,
    list_strategy_checkpoints,
    validate_strategy_checkpoint,
)
from app.services.strategy.checkpoints.factories import create_strategy_checkpoint_value
from app.services.strategy.contracts import (
    build_expectancy_reference,
    build_setup_evaluation,
    build_strategy_playbook,
    build_strategy_profile,
    evaluate_expectancy_reference,
    parse_expectancy_reference,
    parse_setup_evaluation,
    parse_strategy_playbook,
    parse_strategy_profile,
)
from app.services.strategy.contracts.factories import (
    create_strategy_config,
    create_strategy_decision,
    create_strategy_event,
    create_strategy_execution_context,
    create_strategy_execution_result,
    create_strategy_manifest,
    create_strategy_mutation_result,
    create_strategy_parameter_update_request,
    create_strategy_ref,
    create_strategy_registration_request,
    create_strategy_signal,
    create_strategy_signal_evidence,
    create_strategy_validation_policy,
    create_validated_strategy_config,
    create_validated_strategy_ref,
    get_strategy_environment,
    get_strategy_lifecycle_status,
    get_strategy_timing_policy,
)
from app.services.strategy.contracts.responses import unwrap_strategy_response
from app.services.strategy.diagnostics import (
    export_strategy_diagnostics,
    get_strategy_error_catalog,
)
from app.services.strategy.diagnostics.errors import get_strategy_error_code
from app.services.strategy.diagnostics.factories import create_strategy_diagnostics
from app.services.strategy.evaluators.factory import create_strategy_evaluator
from app.services.strategy.event import (
    commit_strategy_runtime_state,
    initialize_strategy_runtime_state,
    load_strategy_runtime_state,
    run_event_strategy_hook,
    run_persisted_event_strategy_hook,
)
from app.services.strategy.exit_plans import (
    build_exit_plan,
    build_exit_plan_handoff,
    parse_exit_plan,
)
from app.services.strategy.intents import (
    amend_trade_plan,
    build_trade_intent,
    build_trade_plan,
    parse_trade_plan,
    transition_trade_plan,
    validate_trade_plan_for_intent,
)
from app.services.strategy.intents.factories import create_trade_intent_value
from app.services.strategy.manual_plans import (
    build_manual_trade_plan,
    validate_manual_trade_plan,
)
from app.services.strategy.operating_envelope import (
    build_operating_envelope,
    evaluate_operating_envelope,
    parse_operating_envelope,
)
from app.services.strategy.proposal_intake import (
    bind_proposal_lineage,
    create_strategy_proposal_evaluation_request,
    create_strategy_proposal_evaluation_result,
    evaluate_automation_mode,
    evaluate_strategy_proposal,
    validate_strategy_proposal,
)
from app.services.strategy.registry import (
    adopt_approved_optimization_parameters,
    bootstrap_builtin_strategies,
    get_strategy_definition,
    govern_strategy_lifecycle,
    list_builtin_strategy_descriptors,
    list_strategy_configs,
    list_strategy_definitions,
    list_strategy_versions,
    register_strategy_version,
    resolve_strategy_config,
    update_strategy_parameters,
    validate_strategy_config,
    validate_strategy_ref,
)
from app.services.strategy.registry.runtime import (
    build_development_strategy_validation_policy,
)
from app.services.strategy.replay import create_strategy_replay_manifest
from app.services.strategy.replay.factories import create_strategy_replay_manifest_value
from app.services.strategy.signals import (
    evaluate_and_record_strategy_signals,
    evaluate_strategy_signals,
    list_strategy_signals,
    mark_strategy_signal_submitted,
    record_strategy_signals,
)
from app.services.strategy.vectorized import run_vectorized_strategy_signals

__all__ = (
    "adopt_approved_optimization_parameters",
    "amend_trade_plan",
    "bind_proposal_lineage",
    "bootstrap_builtin_strategies",
    "build_development_strategy_validation_policy",
    "build_exit_plan",
    "build_exit_plan_handoff",
    "build_expectancy_reference",
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
    "create_strategy_evaluator",
    "create_strategy_event",
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
    "get_strategy_environment",
    "get_strategy_error_catalog",
    "get_strategy_error_code",
    "get_strategy_lifecycle_status",
    "get_strategy_timing_policy",
    "govern_strategy_lifecycle",
    "initialize_strategy_runtime_state",
    "list_builtin_strategy_descriptors",
    "list_strategy_checkpoints",
    "list_strategy_configs",
    "list_strategy_definitions",
    "list_strategy_signals",
    "list_strategy_versions",
    "load_strategy_runtime_state",
    "mark_strategy_signal_submitted",
    "parse_exit_plan",
    "parse_expectancy_reference",
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
    "unwrap_strategy_response",
    "update_strategy_parameters",
    "validate_manual_trade_plan",
    "validate_strategy_checkpoint",
    "validate_strategy_config",
    "validate_strategy_proposal",
    "validate_strategy_ref",
    "validate_trade_plan_for_intent",
)
