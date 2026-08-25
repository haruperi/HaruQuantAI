"""Portfolio domain capability keys."""

from typing import TYPE_CHECKING

from app.kernel.capability import CapabilityKey

if TYPE_CHECKING:
    from app.contracts.portfolio.ports import (
        AnalyzeCorrelationCapability,
        AnalyzePortfolioRiskCapability,
        ComposePortfoliosCapability,
        ExtendPortfolioMethodsCapability,
        MergePortfoliosCapability,
        OptimizeMarkowitzCapability,
        SearchPortfoliosCapability,
        SimulatePortfoliosCapability,
    )

COMPOSE_PORTFOLIOS_CAPABILITY: CapabilityKey[ComposePortfoliosCapability] = (
    CapabilityKey(
        name="portfolio.compose-portfolios",
        major=1,
    )
)

ANALYZE_CORRELATION_CAPABILITY: CapabilityKey[AnalyzeCorrelationCapability] = (
    CapabilityKey(
        name="portfolio.analyze-correlation",
        major=1,
    )
)

SIMULATE_PORTFOLIOS_CAPABILITY: CapabilityKey[SimulatePortfoliosCapability] = (
    CapabilityKey(
        name="portfolio.simulate-portfolios",
        major=1,
    )
)

SEARCH_PORTFOLIOS_CAPABILITY: CapabilityKey[SearchPortfoliosCapability] = CapabilityKey(
    name="portfolio.search-portfolios",
    major=1,
)

ANALYZE_PORTFOLIO_RISK_CAPABILITY: CapabilityKey[AnalyzePortfolioRiskCapability] = (
    CapabilityKey(
        name="portfolio.analyze-portfolio-risk",
        major=1,
    )
)

OPTIMIZE_MARKOWITZ_CAPABILITY: CapabilityKey[OptimizeMarkowitzCapability] = (
    CapabilityKey(
        name="portfolio.optimize-markowitz",
        major=1,
    )
)

MERGE_PORTFOLIOS_CAPABILITY: CapabilityKey[MergePortfoliosCapability] = CapabilityKey(
    name="portfolio.merge-portfolios",
    major=1,
)

EXTEND_PORTFOLIO_METHODS_CAPABILITY: CapabilityKey[ExtendPortfolioMethodsCapability] = (
    CapabilityKey(
        name="portfolio.extend-portfolio-methods",
        major=1,
    )
)
