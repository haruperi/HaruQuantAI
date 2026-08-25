"""Public capability protocols (ports) for Analytics capabilities."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from app.contracts.analytics.errors import AnalyticsFailure
    from app.contracts.analytics.models import (
        AnalyzeTradesRequest,
        AnalyzeTradesSuccess,
        BulkDatabankRequest,
        BulkDatabankSuccess,
        CustomPanelsRequest,
        CustomPanelsSuccess,
        DatabankMembershipRequest,
        DatabankMembershipSuccess,
        ExchangeResultsRequest,
        ExchangeResultsSuccess,
        InterpretResultsRequest,
        InterpretResultsSuccess,
        MatchResultsRequest,
        MatchResultsSuccess,
        QualifyOperationsRequest,
        QualifyOperationsSuccess,
        QueryResultsRequest,
        QueryResultsSuccess,
    )


@runtime_checkable
class DatabankMembershipCapability(Protocol):
    """Capability protocol for databank membership operations."""

    async def databank_membership(
        self,
        request: DatabankMembershipRequest,
    ) -> DatabankMembershipSuccess | AnalyticsFailure:
        """Create, rename, delete, and mutate databanks transactionally.

        Args:
            request: Operation-discriminated databank membership request.

        Returns:
            The databank version, item, or admission decision on success,
            otherwise a structured analytics failure.
        """
        ...


@runtime_checkable
class QueryResultsCapability(Protocol):
    """Capability protocol for result query operations."""

    async def query_results(
        self,
        request: QueryResultsRequest,
    ) -> QueryResultsSuccess | AnalyticsFailure:
        """Query result tables, save views, and bound chart series.

        Args:
            request: Operation-discriminated result query request.

        Returns:
            The result page, saved view, or chart specification on
            success, otherwise a structured analytics failure.
        """
        ...


@runtime_checkable
class InterpretResultsCapability(Protocol):
    """Capability protocol for result interpretation operations."""

    async def interpret_results(
        self,
        request: InterpretResultsRequest,
    ) -> InterpretResultsSuccess | AnalyticsFailure:
        """Apply result scopes to overviews, trades, metrics, and manifests.

        Args:
            request: Operation-discriminated result interpretation request.

        Returns:
            The scoped metric values, aligned comparison, or run manifest
            on success, otherwise a structured analytics failure.
        """
        ...


@runtime_checkable
class AnalyzeTradesCapability(Protocol):
    """Capability protocol for chart, benchmark, and trade analysis."""

    async def analyze_trades(
        self,
        request: AnalyzeTradesRequest,
    ) -> AnalyzeTradesSuccess | AnalyticsFailure:
        """Analyze trade timing, reconstruct charts, and compare benchmarks.

        Args:
            request: Operation-discriminated trade analysis request.

        Returns:
            The temporal trade analysis or benchmark comparison on
            success, otherwise a structured analytics failure.
        """
        ...


@runtime_checkable
class ExchangeResultsCapability(Protocol):
    """Capability protocol for result interchange operations."""

    async def exchange_results(
        self,
        request: ExchangeResultsRequest,
    ) -> ExchangeResultsSuccess | AnalyticsFailure:
        """Export rows, package artifacts, and import external results.

        Args:
            request: Operation-discriminated result interchange request.

        Returns:
            The interchange package or produced artifact identifier on
            success, otherwise a structured analytics failure.
        """
        ...


@runtime_checkable
class BulkDatabankCapability(Protocol):
    """Capability protocol for bulk databank operations."""

    async def bulk_databank(
        self,
        request: BulkDatabankRequest,
    ) -> BulkDatabankSuccess | AnalyticsFailure:
        """Pin selections and dry-run or execute bulk databank transfers.

        Args:
            request: Operation-discriminated bulk databank request.

        Returns:
            The pinned selection token or executed bulk command on
            success, otherwise a structured analytics failure.
        """
        ...


@runtime_checkable
class MatchResultsCapability(Protocol):
    """Capability protocol for result similarity operations."""

    async def match_results(
        self,
        request: MatchResultsRequest,
    ) -> MatchResultsSuccess | AnalyticsFailure:
        """Query result similarity by relative-tolerance fingerprints.

        Args:
            request: Operation-discriminated result similarity request.

        Returns:
            The similarity matches of the reference result on success,
            otherwise a structured analytics failure.
        """
        ...


@runtime_checkable
class CustomPanelsCapability(Protocol):
    """Capability protocol for custom analysis and result panels."""

    async def custom_panels(
        self,
        request: CustomPanelsRequest,
    ) -> CustomPanelsSuccess | AnalyticsFailure:
        """Run custom analyses and declare result panels.

        Args:
            request: Operation-discriminated custom panel request.

        Returns:
            The declared panel descriptor or analysis output artifact on
            success, otherwise a structured analytics failure.
        """
        ...


@runtime_checkable
class QualifyOperationsCapability(Protocol):
    """Capability protocol for operational journals and qualification."""

    async def qualify_operations(
        self,
        request: QualifyOperationsRequest,
    ) -> QualifyOperationsSuccess | AnalyticsFailure:
        """Build journals and qualify operators from immutable evidence.

        Args:
            request: Operation-discriminated operational analysis request.

        Returns:
            The journal artifact, qualification decision, profile version,
            or export artifact on success, otherwise a structured
            analytics failure.
        """
        ...
