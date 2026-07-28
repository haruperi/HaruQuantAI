"""Public Simulation domain port."""

from app.services.simulator.accounting import (
    AccountLedger,
    ExecutionCostInput,
    ExecutionCostModel,
    LedgerFill,
    SymbolSpecification,
    ValidatedFXConversionEvidence,
    calculate_execution_costs,
    calculate_margin,
    convert_fx_amount,
    normalize_volume,
    validate_fx_evidence,
)
from app.services.simulator.errors import (
    SIM_ERROR_CATALOG,
    SimulationError,
    guard_operation,
    to_simulation_error_payload,
    unwrap_simulation_response,
)
from app.services.simulator.execution import (
    SAME_TICK_PRIORITY,
    SUPPORTED_FILL_POLICIES,
    EventDrivenExecutionEngine,
    ExecutionProfile,
    MatchResult,
    SessionInterval,
    SimTrader,
    evaluate_protective_exit,
    match_order,
    price_order,
)
from app.services.simulator.journal import (
    JOURNAL_FORMAT,
    JOURNAL_FSYNC_INTERVAL,
    JOURNAL_SIDECAR_MODE,
    JournalEvent,
    JournalWriter,
    replay_journal,
    resolve_idempotent_run,
)
from app.services.simulator.reporting import (
    CANONICAL_ARTIFACT_TYPES,
    REPORT_SCHEMA_VERSION,
    AccountingSummary,
    ArtifactEntry,
    ArtifactManifest,
    ClosedTradeRecord,
    ComponentReturnSeries,
    FastResearchResult,
    PortfolioComponentResult,
    PortfolioSimulationResult,
    RealismDisclosure,
    ReturnObservation,
    RiskBudgetHistoryRow,
    SimulationResult,
    build_artifact_manifest,
    build_json_report,
    build_markdown_report,
)
from app.services.simulator.run import (
    PortfolioBacktestRequestV1,
    PortfolioComponentRequest,
    SimulationBacktestRequestV1,
    SimulationRunDependencies,
    run_backtest,
    run_fast_research,
    run_portfolio_backtest,
)
from app.services.simulator.state import (
    SIMULATION_MIGRATIONS,
    RunStatus,
    SimulationStateStore,
)
from app.services.simulator.timeline import (
    APPROVED_TICK_MODELS,
    Tick,
    build_tick_timeline,
    validate_intent_timing,
)
from app.services.simulator.validation import (
    SUPPORTED_ASSET_CLASSES,
    validate_market_data,
    validate_phase_one_scope,
    validate_run_inputs,
)
from app.services.simulator.validation.contracts import (
    MarketDataValidationContext,
    ValidatedMarketDataEvidence,
)
from app.utils import RiskLevel

# The package root is the sole supported public import surface. Feature
# subpackages remain raw implementation ports for Simulation's own orchestration.
calculate_execution_costs = guard_operation(  # type: ignore[assignment]
    calculate_execution_costs,
    operation="simulation.accounting.calculate_execution_costs",
    risk_level=RiskLevel.LOW,
    read_only=True,
)
calculate_margin = guard_operation(  # type: ignore[assignment]
    calculate_margin,
    operation="simulation.accounting.calculate_margin",
    risk_level=RiskLevel.LOW,
    read_only=True,
)
convert_fx_amount = guard_operation(  # type: ignore[assignment]
    convert_fx_amount,
    operation="simulation.accounting.convert_fx_amount",
    risk_level=RiskLevel.LOW,
    read_only=True,
)
normalize_volume = guard_operation(  # type: ignore[assignment]
    normalize_volume,
    operation="simulation.accounting.normalize_volume",
    risk_level=RiskLevel.LOW,
    read_only=True,
)
validate_fx_evidence = guard_operation(  # type: ignore[assignment]
    validate_fx_evidence,
    operation="simulation.accounting.validate_fx_evidence",
    risk_level=RiskLevel.LOW,
    read_only=True,
)
validate_run_inputs = guard_operation(  # type: ignore[assignment]
    validate_run_inputs,
    operation="simulation.validation.validate_run_inputs",
    risk_level=RiskLevel.LOW,
    read_only=True,
)
validate_market_data = guard_operation(  # type: ignore[assignment]
    validate_market_data,
    operation="simulation.validation.validate_market_data",
    risk_level=RiskLevel.LOW,
    read_only=True,
)
validate_phase_one_scope = guard_operation(  # type: ignore[assignment]
    validate_phase_one_scope,
    operation="simulation.validation.validate_phase_one_scope",
    risk_level=RiskLevel.LOW,
    read_only=True,
)
build_tick_timeline = guard_operation(  # type: ignore[assignment]
    build_tick_timeline,
    operation="simulation.timeline.build_tick_timeline",
    risk_level=RiskLevel.MEDIUM,
    read_only=True,
)
validate_intent_timing = guard_operation(  # type: ignore[assignment]
    validate_intent_timing,
    operation="simulation.timeline.validate_intent_timing",
    risk_level=RiskLevel.MEDIUM,
    read_only=True,
)
evaluate_protective_exit = guard_operation(  # type: ignore[assignment]
    evaluate_protective_exit,
    operation="simulation.execution.evaluate_protective_exit",
    risk_level=RiskLevel.MEDIUM,
    read_only=True,
)
match_order = guard_operation(  # type: ignore[assignment]
    match_order,
    operation="simulation.execution.match_order",
    risk_level=RiskLevel.MEDIUM,
    read_only=True,
)
price_order = guard_operation(  # type: ignore[assignment]
    price_order,
    operation="simulation.execution.price_order",
    risk_level=RiskLevel.MEDIUM,
    read_only=True,
)
replay_journal = guard_operation(  # type: ignore[assignment]
    replay_journal,
    operation="simulation.journal.replay_journal",
    risk_level=RiskLevel.MEDIUM,
    read_only=True,
)
resolve_idempotent_run = guard_operation(  # type: ignore[assignment]
    resolve_idempotent_run,
    operation="simulation.journal.resolve_idempotent_run",
    risk_level=RiskLevel.LOW,
    read_only=True,
)
build_artifact_manifest = guard_operation(  # type: ignore[assignment]
    build_artifact_manifest,
    operation="simulation.reporting.build_artifact_manifest",
    risk_level=RiskLevel.MEDIUM,
    read_only=True,
)
build_json_report = guard_operation(  # type: ignore[assignment]
    build_json_report,
    operation="simulation.reporting.build_json_report",
    risk_level=RiskLevel.LOW,
    read_only=True,
)
build_markdown_report = guard_operation(  # type: ignore[assignment]
    build_markdown_report,
    operation="simulation.reporting.build_markdown_report",
    risk_level=RiskLevel.LOW,
    read_only=True,
)
run_backtest = guard_operation(  # type: ignore[assignment]
    run_backtest,
    operation="simulation.run.run_backtest",
    risk_level=RiskLevel.MEDIUM,
    read_only=False,
    writes_file=True,
)
run_fast_research = guard_operation(  # type: ignore[assignment]
    run_fast_research,
    operation="simulation.run.run_fast_research",
    risk_level=RiskLevel.MEDIUM,
    read_only=False,
    modifies_database=True,
)
run_portfolio_backtest = guard_operation(  # type: ignore[assignment]
    run_portfolio_backtest,
    operation="simulation.run.run_portfolio_backtest",
    risk_level=RiskLevel.HIGH,
    read_only=False,
    writes_file=True,
    modifies_database=True,
)

__all__ = (
    "APPROVED_TICK_MODELS",
    "CANONICAL_ARTIFACT_TYPES",
    "JOURNAL_FORMAT",
    "JOURNAL_FSYNC_INTERVAL",
    "JOURNAL_SIDECAR_MODE",
    "REPORT_SCHEMA_VERSION",
    "SAME_TICK_PRIORITY",
    "SIMULATION_MIGRATIONS",
    "SIM_ERROR_CATALOG",
    "SUPPORTED_ASSET_CLASSES",
    "SUPPORTED_FILL_POLICIES",
    "AccountLedger",
    "AccountingSummary",
    "ArtifactEntry",
    "ArtifactManifest",
    "ClosedTradeRecord",
    "ComponentReturnSeries",
    "EventDrivenExecutionEngine",
    "ExecutionCostInput",
    "ExecutionCostModel",
    "ExecutionProfile",
    "FastResearchResult",
    "JournalEvent",
    "JournalWriter",
    "LedgerFill",
    "MarketDataValidationContext",
    "MatchResult",
    "PortfolioBacktestRequestV1",
    "PortfolioComponentRequest",
    "PortfolioComponentResult",
    "PortfolioSimulationResult",
    "RealismDisclosure",
    "ReturnObservation",
    "RiskBudgetHistoryRow",
    "RunStatus",
    "SessionInterval",
    "SimTrader",
    "SimulationBacktestRequestV1",
    "SimulationError",
    "SimulationResult",
    "SimulationRunDependencies",
    "SimulationStateStore",
    "SymbolSpecification",
    "Tick",
    "ValidatedFXConversionEvidence",
    "ValidatedMarketDataEvidence",
    "build_artifact_manifest",
    "build_json_report",
    "build_markdown_report",
    "build_tick_timeline",
    "calculate_execution_costs",
    "calculate_margin",
    "convert_fx_amount",
    "evaluate_protective_exit",
    "match_order",
    "normalize_volume",
    "price_order",
    "replay_journal",
    "resolve_idempotent_run",
    "run_backtest",
    "run_fast_research",
    "run_portfolio_backtest",
    "to_simulation_error_payload",
    "unwrap_simulation_response",
    "validate_fx_evidence",
    "validate_intent_timing",
    "validate_market_data",
    "validate_phase_one_scope",
    "validate_run_inputs",
)
