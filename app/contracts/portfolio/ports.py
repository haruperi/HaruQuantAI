"""Public capability protocols (ports) for Portfolio capabilities."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from app.contracts.portfolio.errors import PortfolioFailure
    from app.contracts.portfolio.models import (
        AnalyzeCorrelationRequest,
        AnalyzeCorrelationSuccess,
        AnalyzePortfolioRiskRequest,
        AnalyzePortfolioRiskSuccess,
        ComposePortfoliosRequest,
        ComposePortfoliosSuccess,
        ExtendPortfolioMethodsRequest,
        ExtendPortfolioMethodsSuccess,
        MergePortfoliosRequest,
        MergePortfoliosSuccess,
        OptimizeMarkowitzRequest,
        OptimizeMarkowitzSuccess,
        SearchPortfoliosRequest,
        SearchPortfoliosSuccess,
        SimulatePortfoliosRequest,
        SimulatePortfoliosSuccess,
    )


@runtime_checkable
class ComposePortfoliosCapability(Protocol):
    """Capability protocol for manual portfolio composition operations."""

    async def compose_portfolios(
        self,
        request: ComposePortfoliosRequest,
    ) -> ComposePortfoliosSuccess | PortfolioFailure:
        """Version, validate, edit, and promote portfolio versions.

        Args:
            request: Operation-discriminated portfolio composition request.

        Returns:
            The portfolio version and validation findings on success,
            otherwise a structured portfolio failure.
        """
        ...


@runtime_checkable
class AnalyzeCorrelationCapability(Protocol):
    """Capability protocol for correlation analysis operations."""

    async def analyze_correlation(
        self,
        request: AnalyzeCorrelationRequest,
    ) -> AnalyzeCorrelationSuccess | PortfolioFailure:
        """Version correlation inputs and compute correlation matrices.

        Args:
            request: Operation-discriminated correlation analysis request.

        Returns:
            The immutable correlation matrix on success, otherwise a
            structured portfolio failure.
        """
        ...


@runtime_checkable
class SimulatePortfoliosCapability(Protocol):
    """Capability protocol for aggregate portfolio simulation operations."""

    async def simulate_portfolios(
        self,
        request: SimulatePortfoliosRequest,
    ) -> SimulatePortfoliosSuccess | PortfolioFailure:
        """Simulate aggregate portfolios and convert portfolio currencies.

        Args:
            request: Operation-discriminated aggregate simulation request.

        Returns:
            The aggregate portfolio result on success, otherwise a
            structured portfolio failure.
        """
        ...


@runtime_checkable
class SearchPortfoliosCapability(Protocol):
    """Capability protocol for automatic portfolio search operations."""

    async def search_portfolios(
        self,
        request: SearchPortfoliosRequest,
    ) -> SearchPortfoliosSuccess | PortfolioFailure:
        """Plan, search, checkpoint, and resume portfolio searches.

        Args:
            request: Operation-discriminated portfolio search request.

        Returns:
            The search plan and evaluated candidates on success, otherwise
            a structured portfolio failure.
        """
        ...


@runtime_checkable
class AnalyzePortfolioRiskCapability(Protocol):
    """Capability protocol for portfolio results and risk operations."""

    async def analyze_portfolio_risk(
        self,
        request: AnalyzePortfolioRiskRequest,
    ) -> AnalyzePortfolioRiskSuccess | PortfolioFailure:
        """Report portfolio risk and define portfolio metrics.

        Args:
            request: Operation-discriminated portfolio risk request.

        Returns:
            The risk report or metric definition on success, otherwise a
            structured portfolio failure.
        """
        ...


@runtime_checkable
class OptimizeMarkowitzCapability(Protocol):
    """Capability protocol for Markowitz optimization operations."""

    async def optimize_markowitz(
        self,
        request: OptimizeMarkowitzRequest,
    ) -> OptimizeMarkowitzSuccess | PortfolioFailure:
        """Optimize Markowitz portfolios over an efficient frontier.

        Args:
            request: Operation-discriminated Markowitz optimization request.

        Returns:
            The efficient frontier on success, otherwise a structured
            portfolio failure.
        """
        ...


@runtime_checkable
class MergePortfoliosCapability(Protocol):
    """Capability protocol for portfolio merge and split operations."""

    async def merge_portfolios(
        self,
        request: MergePortfoliosRequest,
    ) -> MergePortfoliosSuccess | PortfolioFailure:
        """Plan and execute portfolio merges and splits.

        Args:
            request: Operation-discriminated portfolio merge request.

        Returns:
            The merge plan or split plan on success, otherwise a structured
            portfolio failure.
        """
        ...


@runtime_checkable
class ExtendPortfolioMethodsCapability(Protocol):
    """Capability protocol for research-method portfolio plugins."""

    async def extend_portfolio_methods(
        self,
        request: ExtendPortfolioMethodsRequest,
    ) -> ExtendPortfolioMethodsSuccess | PortfolioFailure:
        """Register experimental research-method portfolio plugins.

        Args:
            request: Operation-discriminated portfolio method extension
                request.

        Returns:
            The registered portfolio method descriptor on success, otherwise
            a structured portfolio failure.
        """
        ...
