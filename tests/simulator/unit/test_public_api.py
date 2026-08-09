"""Unit tests pinning the documented Simulation public API surface."""

import importlib
import inspect
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from app.services.simulator import (
    create_simulation_handle,
    create_simulation_value,
    dump_simulation_value,
    execute_simulation_handle_operation,
    get_approved_tick_models,
    get_canonical_artifact_types,
    get_journal_policy,
    get_report_schema_version,
    get_same_tick_priority,
    get_simulation_error_catalog,
    get_simulation_migrations,
    get_simulation_value_field,
    get_simulation_value_fields,
    get_supported_asset_classes,
    get_supported_fill_policies,
    is_simulation_value,
)

_EXPECTED: dict[str, tuple[str, ...]] = {
    "app.services.simulator": (
        "branch_live_simulation",
        "branch_recovery_checkpoint",
        "build_artifact_manifest",
        "build_checklist_definition",
        "build_fill_model_provider",
        "build_injected_event",
        "build_json_report",
        "build_latency_profile",
        "build_markdown_report",
        "build_mission_definition",
        "build_queue_model",
        "build_replay_identity",
        "build_scenario_evidence_provider",
        "build_scenario_provider",
        "build_simulation_alert",
        "build_simulation_run_dependencies",
        "build_simulation_state_store",
        "build_tick_timeline",
        "bypass_simulation_checklist_step",
        "calculate_execution_costs",
        "calculate_margin",
        "calculate_portfolio_backtest_config_hash",
        "calculate_simulation_backtest_config_hash",
        "close_live_simulation_session",
        "complete_simulation_mission",
        "convert_fx_amount",
        "create_live_simulation_session",
        "create_recovery_checkpoint",
        "create_simulation_handle",
        "create_simulation_session",
        "create_simulation_value",
        "dump_simulation_value",
        "evaluate_emergency_controls",
        "evaluate_protective_exit",
        "evaluate_scenario_triggers",
        "evaluate_simulation_checklist",
        "execute_simulation_handle_operation",
        "execute_simulation_state_store_operation",
        "explicitly_rearm_simulation_session",
        "get_approved_tick_models",
        "get_canonical_artifact_types",
        "get_journal_policy",
        "get_report_schema_version",
        "get_same_tick_priority",
        "get_scenario_templates",
        "get_simulation_error_catalog",
        "get_simulation_migrations",
        "get_simulation_mode_policy",
        "get_simulation_result",
        "get_simulation_value_field",
        "get_simulation_value_fields",
        "get_supported_asset_classes",
        "get_supported_fill_policies",
        "group_simulation_alerts",
        "is_simulation_value",
        "load_recovery_checkpoints",
        "match_order",
        "normalize_volume",
        "order_injected_events",
        "persist_recovery_checkpoint",
        "persist_recovery_state",
        "price_order",
        "price_realistic_execution",
        "project_execution_views",
        "project_latency_timestamps",
        "read_live_simulation_state",
        "read_simulation_session",
        "replay_journal",
        "reset_live_simulation_sessions",
        "resolve_cancel_replace_race",
        "resolve_idempotent_run",
        "restore_simulation_session",
        "run_backtest",
        "run_fast_research",
        "run_portfolio_backtest",
        "run_simulator_migrations",
        "secure_simulation_session",
        "simulate_queue_fill",
        "start_simulation_checklist",
        "step_live_simulation",
        "stream_simulation_session_frames",
        "to_simulation_error_payload",
        "transition_simulation_alert",
        "unwrap_simulation_response",
        "validate_fx_evidence",
        "validate_intent_timing",
        "validate_market_data",
        "validate_phase_one_scope",
        "validate_run_inputs",
        "verify_recovery_checkpoints",
    ),
    "app.services.simulator.alerts": (
        "AlertEvent",
        "build_simulation_alert",
        "evaluate_emergency_controls",
        "group_simulation_alerts",
        "transition_simulation_alert",
    ),
    "app.services.simulator.checklists": (
        "ChecklistDefinition",
        "ChecklistRuntime",
        "ChecklistStepDefinition",
        "ChecklistStepRuntime",
        "MissionOutcome",
        "build_checklist_definition",
        "bypass_checklist_step",
        "complete_simulation_mission",
        "evaluate_checklist",
        "get_simulation_mode_policy",
        "parse_checklist_runtime",
        "start_checklist",
    ),
    "app.services.simulator.realism": (
        "LatencyProfile",
        "QueueFillResult",
        "QueueModel",
        "RealisticExecutionResult",
        "build_fill_model_provider",
        "build_latency_profile",
        "build_queue_model",
        "price_realistic_execution",
        "project_execution_views",
        "project_latency_timestamps",
        "resolve_cancel_replace_race",
        "simulate_queue_fill",
    ),
    "app.services.simulator.recovery": (
        "RecoveryCheckpoint",
        "ReplayIdentity",
        "branch_recovery_checkpoint",
        "build_replay_identity",
        "create_recovery_checkpoint",
        "explicitly_rearm_simulation_session",
        "load_recovery_checkpoints",
        "persist_recovery_checkpoint",
        "persist_recovery_state",
        "restore_simulation_session",
        "secure_simulation_session",
        "transition_recovery_state",
        "verify_recovery_checkpoints",
    ),
    "app.services.simulator.scenarios": (
        "InjectedEvent",
        "MissionDefinition",
        "build_injected_event",
        "build_mission_definition",
        "build_scenario_evidence_provider",
        "build_scenario_provider",
        "evaluate_scenario_triggers",
        "get_scenario_templates",
        "order_injected_events",
    ),
    "app.services.simulator.validation": (
        "SUPPORTED_ASSET_CLASSES",
        "validate_market_data",
        "validate_phase_one_scope",
        "validate_run_inputs",
    ),
    "app.services.simulator.timeline": (
        "APPROVED_TICK_MODELS",
        "Tick",
        "build_tick_timeline",
        "validate_intent_timing",
    ),
    "app.services.simulator.accounting": (
        "AccountLedger",
        "ExecutionCostInput",
        "ExecutionCostModel",
        "LedgerFill",
        "SymbolSpecification",
        "ValidatedFXConversionEvidence",
        "calculate_execution_costs",
        "calculate_margin",
        "convert_fx_amount",
        "normalize_volume",
        "validate_fx_evidence",
    ),
    "app.services.simulator.journal": (
        "JOURNAL_FORMAT",
        "JOURNAL_FSYNC_INTERVAL",
        "JOURNAL_SIDECAR_MODE",
        "JournalEvent",
        "JournalWriter",
        "replay_journal",
        "resolve_idempotent_run",
        "stream_journal_events",
    ),
    "app.services.simulator.state": (
        "SIMULATION_MIGRATIONS",
        "RunStatus",
        "SimulationStateStore",
        "branch_live_simulation",
        "build_simulation_state_store",
        "close_live_simulation_session",
        "create_live_simulation_session",
        "create_simulation_session",
        "read_live_simulation_state",
        "read_simulation_session",
        "reset_live_simulation_sessions",
        "step_live_simulation",
        "stream_simulation_session_frames",
    ),
    "app.services.simulator.execution": (
        "SAME_TICK_PRIORITY",
        "SUPPORTED_FILL_POLICIES",
        "EventDrivenExecutionEngine",
        "ExecutionProfile",
        "MatchResult",
        "SessionInterval",
        "SimTrader",
        "evaluate_protective_exit",
        "match_order",
        "price_order",
    ),
    "app.services.simulator.reporting": (
        "CANONICAL_ARTIFACT_TYPES",
        "REPORT_SCHEMA_VERSION",
        "AccountingSummary",
        "ArtifactEntry",
        "ArtifactManifest",
        "ClosedTradeRecord",
        "ComponentReturnSeries",
        "FastResearchResult",
        "PortfolioComponentResult",
        "PortfolioSimulationResult",
        "RealismDisclosure",
        "ReturnObservation",
        "RiskBudgetHistoryRow",
        "SimulationResult",
        "build_artifact_manifest",
        "build_json_report",
        "build_markdown_report",
    ),
    "app.services.simulator.run": (
        "PortfolioBacktestRequestV1",
        "PortfolioComponentRequest",
        "SimulationBacktestRequestV1",
        "SimulationRunDependencies",
        "build_simulation_run_dependencies",
        "run_backtest",
        "run_fast_research",
        "run_portfolio_backtest",
    ),
}


@pytest.mark.parametrize("module_name", sorted(_EXPECTED))
def test_feature_exports_match_documentation(module_name: str) -> None:
    """Prove each package exposes exactly its documented public symbols."""
    module = importlib.import_module(module_name)
    assert tuple(module.__all__) == _EXPECTED[module_name]


@pytest.mark.parametrize("module_name", sorted(_EXPECTED))
def test_every_exported_symbol_resolves(module_name: str) -> None:
    """Prove every declared export is importable from its package."""
    module = importlib.import_module(module_name)
    for name in module.__all__:
        assert hasattr(module, name)


def test_domain_root_exports_functions_only() -> None:
    """Prove the sole cross-domain boundary contains standalone functions only."""
    module = importlib.import_module("app.services.simulator")
    assert all(inspect.isfunction(getattr(module, name)) for name in module.__all__)


def test_public_getters_return_declared_simulation_policy() -> None:
    """Expose constants only through immutable function results."""
    assert "real" in get_approved_tick_models()
    assert "journal.jsonl" in get_canonical_artifact_types()
    assert get_journal_policy()["format"] == "jsonl-v1"
    assert get_report_schema_version() == "v1"
    assert get_same_tick_priority()[0] == "STOP_LOSS"
    assert "SIM_INVALID_CONFIG" in get_simulation_error_catalog()
    assert get_simulation_migrations()
    assert "FX" in get_supported_asset_classes()
    assert "FOK" in get_supported_fill_policies()


def test_opaque_value_helpers_validate_the_public_catalogue() -> None:
    """Create, inspect, project, and reject opaque public contract values."""
    tick = create_simulation_value(
        "Tick",
        symbol="EURUSD",
        timestamp=datetime(2025, 1, 1, tzinfo=UTC),
        bid=Decimal("1.1"),
        ask=Decimal("1.10002"),
        source_id="test",
        sequence=0,
        available_at=datetime(2025, 1, 1, tzinfo=UTC),
    )
    assert is_simulation_value(tick, "Tick")
    assert not is_simulation_value(tick, "Unknown")
    assert get_simulation_value_field(tick, "symbol") == "EURUSD"
    assert "symbol" in get_simulation_value_fields("Tick")
    assert dump_simulation_value(tick)["sequence"] == 0
    with pytest.raises(ValueError, match="unsupported"):
        create_simulation_value("Unknown")
    with pytest.raises(ValueError, match="unsupported"):
        get_simulation_value_fields("Unknown")
    with pytest.raises(ValueError, match="does not expose"):
        get_simulation_value_field(tick, "_private")
    with pytest.raises(TypeError, match="does not support"):
        dump_simulation_value(object())


def test_opaque_handle_helpers_reject_unknown_operations() -> None:
    """Reject unknown handle types, values, and operations deterministically."""
    with pytest.raises(ValueError, match="unsupported"):
        create_simulation_handle("Unknown")
    with pytest.raises(ValueError, match="unsupported"):
        execute_simulation_handle_operation(object(), "snapshot")
