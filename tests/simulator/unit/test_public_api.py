"""Unit tests pinning the documented Simulation public API surface."""
# ruff: noqa: INP001

import importlib

import pytest

_EXPECTED: dict[str, tuple[str, ...]] = {
    "app.services.simulator": (
        "SIM_ERROR_CATALOG",
        "ArtifactManifest",
        "ClosedTradeRecord",
        "FastResearchResult",
        "PortfolioBacktestRequestV1",
        "PortfolioComponentRequest",
        "PortfolioSimulationResult",
        "SimTrader",
        "SimulationBacktestRequestV1",
        "SimulationError",
        "SimulationResult",
        "SimulationRunDependencies",
        "run_backtest",
        "run_fast_research",
        "run_portfolio_backtest",
        "to_simulation_error_payload",
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
    ),
    "app.services.simulator.state": (
        "SIMULATION_MIGRATIONS",
        "RunStatus",
        "SimulationStateStore",
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
