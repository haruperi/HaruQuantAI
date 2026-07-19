"""Public contracts feature port for Analytics."""

from app.services.analytics.contracts.catalogs import (
    CONTRACT_COMPATIBILITY_MATRIX,
    EVIDENCE_CATALOG,
    METRIC_DEFINITION_CATALOG,
    validate_contract_version,
    validate_metric_catalog,
)
from app.services.analytics.contracts.errors import (
    AnalyticsError,
    AnalyticsValidationError,
    to_analytics_error_payload,
)
from app.services.analytics.contracts.evidence import (
    build_quality_flag,
    build_warning,
    to_report_json_safe,
)
from app.services.analytics.contracts.models import (
    ANALYTICS_SCHEMA_VERSION,
    AnalyticsRunConfig,
    AnalyticsWarning,
    ClosedTrade,
    DashboardPayload,
    Lineage,
    MetricEvidence,
    PerformanceReport,
    PortfolioAllocationEvidence,
    PortfolioPerformanceReport,
    QualityFlag,
    ReproducibilityHashes,
    RiskFreeRateEvidence,
    SectionEvidence,
    StatisticalValidationConfig,
    TradingResult,
)

__all__ = (
    "ANALYTICS_SCHEMA_VERSION",
    "CONTRACT_COMPATIBILITY_MATRIX",
    "EVIDENCE_CATALOG",
    "METRIC_DEFINITION_CATALOG",
    "AnalyticsError",
    "AnalyticsRunConfig",
    "AnalyticsValidationError",
    "AnalyticsWarning",
    "ClosedTrade",
    "DashboardPayload",
    "Lineage",
    "MetricEvidence",
    "PerformanceReport",
    "PortfolioAllocationEvidence",
    "PortfolioPerformanceReport",
    "QualityFlag",
    "ReproducibilityHashes",
    "RiskFreeRateEvidence",
    "SectionEvidence",
    "StatisticalValidationConfig",
    "TradingResult",
    "build_quality_flag",
    "build_warning",
    "to_analytics_error_payload",
    "to_report_json_safe",
    "validate_contract_version",
    "validate_metric_catalog",
)
