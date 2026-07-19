"""Supported Simulation reporting API."""

from app.services.simulator.reporting.artifacts import build_artifact_manifest
from app.services.simulator.reporting.contracts import (
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
)
from app.services.simulator.reporting.reports import (
    build_json_report,
    build_markdown_report,
)

__all__ = [
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
]
