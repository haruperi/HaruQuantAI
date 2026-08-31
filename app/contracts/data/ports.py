"""Public capability protocols (ports) for Data capabilities."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from app.contracts.common.events import DomainEvent
    from app.contracts.data.errors import DataFailure
    from app.contracts.data.models import (
        AggregateBarsRequest,
        AggregateBarsSuccess,
        AlignSeriesRequest,
        AlignSeriesSuccess,
        BindRunDataRequest,
        BindRunDataSuccess,
        GenerateScenariosRequest,
        GenerateScenariosSuccess,
        ImportIndicatorsRequest,
        ImportIndicatorsSuccess,
        ImportQuantdataRequest,
        ImportQuantdataSuccess,
        IngestHistoryRequest,
        IngestHistorySuccess,
        ManageRetentionRequest,
        ManageRetentionSuccess,
        NormalizeTicksRequest,
        NormalizeTicksSuccess,
        PrepareProfilesRequest,
        PrepareProfilesSuccess,
        ResolveQualityRequest,
        ResolveQualitySuccess,
        StreamMarketEventsRequest,
        StreamMarketEventsSubscription,
        StreamMarketEventsSuccess,
        SyncConnectorsRequest,
        SyncConnectorsSuccess,
        TrackMarketNewsRequest,
        TrackMarketNewsSuccess,
    )


@runtime_checkable
class IngestHistoryCapability(Protocol):
    """Capability protocol for historical data ingestion operations."""

    async def ingest_history(
        self,
        request: IngestHistoryRequest,
    ) -> IngestHistorySuccess | DataFailure:
        """Register connections, import files, and export data series.

        Args:
            request: Operation-discriminated historical ingestion request.

        Returns:
            The registered connection, import receipt, published series
            version, or export artifact outcome on success, otherwise a
            structured data failure.
        """
        ...


@runtime_checkable
class SyncConnectorsCapability(Protocol):
    """Capability protocol for connector synchronization operations."""

    async def sync_connectors(
        self,
        request: SyncConnectorsRequest,
    ) -> SyncConnectorsSuccess | DataFailure:
        """Plan, fetch, and commit incremental connector synchronizations.

        Args:
            request: Operation-discriminated connector synchronization
                request.

        Returns:
            The synchronization plan or page receipt on success,
            otherwise a structured data failure.
        """
        ...


@runtime_checkable
class ImportQuantdataCapability(Protocol):
    """Capability protocol for QuantDataManager import operations."""

    async def import_quantdata(
        self,
        request: ImportQuantdataRequest,
    ) -> ImportQuantdataSuccess | DataFailure:
        """Discover, decode, and sync governed QuantDataManager sources.

        Args:
            request: Operation-discriminated QuantDataManager request.

        Returns:
            The governed import specification and committed version
            identifiers on success, otherwise a structured data failure.
        """
        ...


@runtime_checkable
class NormalizeTicksCapability(Protocol):
    """Capability protocol for tick normalization operations."""

    async def normalize_ticks(
        self,
        request: NormalizeTicksRequest,
    ) -> NormalizeTicksSuccess | DataFailure:
        """Normalize raw tick batches with preserved fields and ordering.

        Args:
            request: Tick normalization request carrying the raw batch.

        Returns:
            The normalized series version identifier and findings on
            success, otherwise a structured data failure.
        """
        ...


@runtime_checkable
class ResolveQualityCapability(Protocol):
    """Capability protocol for data quality and resolution operations."""

    async def resolve_quality(
        self,
        request: ResolveQualityRequest,
    ) -> ResolveQualitySuccess | DataFailure:
        """Detect quality findings and resolve them explicitly.

        Args:
            request: Operation-discriminated data quality request.

        Returns:
            The detected findings and recorded decision on success,
            otherwise a structured data failure.
        """
        ...


@runtime_checkable
class AggregateBarsCapability(Protocol):
    """Capability protocol for bar aggregation operations."""

    async def aggregate_bars(
        self,
        request: AggregateBarsRequest,
    ) -> AggregateBarsSuccess | DataFailure:
        """Aggregate series across timeframes and validate custom ones.

        Args:
            request: Operation-discriminated bar aggregation request.

        Returns:
            The aggregation specification and derived version identifier
            on success, otherwise a structured data failure.
        """
        ...


@runtime_checkable
class ManageRetentionCapability(Protocol):
    """Capability protocol for retention management operations."""

    async def manage_retention(
        self,
        request: ManageRetentionRequest,
    ) -> ManageRetentionSuccess | DataFailure:
        """Define retention policies and collect unreachable artifacts.

        Args:
            request: Operation-discriminated retention request.

        Returns:
            The stored policy and collected artifact count on success,
            otherwise a structured data failure.
        """
        ...


@runtime_checkable
class AlignSeriesCapability(Protocol):
    """Capability protocol for external series alignment operations."""

    async def align_series(
        self,
        request: AlignSeriesRequest,
    ) -> AlignSeriesSuccess | DataFailure:
        """Align external series under point-in-time policies.

        Args:
            request: Operation-discriminated alignment request.

        Returns:
            The aligned series on success, otherwise a structured data
            failure.
        """
        ...


@runtime_checkable
class PrepareProfilesCapability(Protocol):
    """Capability protocol for volume-profile source validation."""

    async def prepare_profiles(
        self,
        request: PrepareProfilesRequest,
    ) -> PrepareProfilesSuccess | DataFailure:
        """Validate volume-profile source declarations.

        Args:
            request: Volume-profile source validation request.

        Returns:
            The validated source with sufficiency evidence on success,
            otherwise a structured data failure.
        """
        ...


@runtime_checkable
class ImportIndicatorsCapability(Protocol):
    """Capability protocol for external indicator series imports."""

    async def import_indicators(
        self,
        request: ImportIndicatorsRequest,
    ) -> ImportIndicatorsSuccess | DataFailure:
        """Import immutable external indicator series versions.

        Args:
            request: External indicator series import request.

        Returns:
            The imported version identifier and synchronization findings
            on success, otherwise a structured data failure.
        """
        ...


@runtime_checkable
class BindRunDataCapability(Protocol):
    """Capability protocol for run data binding operations."""

    async def bind_run_data(
        self,
        request: BindRunDataRequest,
    ) -> BindRunDataSuccess | DataFailure:
        """Bind committed series versions and validate run precision.

        Args:
            request: Operation-discriminated run data binding request.

        Returns:
            The validated binding on success, otherwise a structured
            data failure.
        """
        ...


@runtime_checkable
class GenerateScenariosCapability(Protocol):
    """Capability protocol for synthetic and scenario series operations."""

    async def generate_scenarios(
        self,
        request: GenerateScenariosRequest,
    ) -> GenerateScenariosSuccess | DataFailure:
        """Configure models, generate series, and transform scenarios.

        Args:
            request: Operation-discriminated synthetic and scenario
                request.

        Returns:
            The model specification and scenario version identifier on
            success, otherwise a structured data failure.
        """
        ...


@runtime_checkable
class TrackMarketNewsCapability(Protocol):
    """Capability protocol for economic calendar and news evidence."""

    async def track_market_news(
        self,
        request: TrackMarketNewsRequest,
    ) -> TrackMarketNewsSuccess | DataFailure:
        """Record observations, revise versions, and query point-in-time.

        Args:
            request: Operation-discriminated market news request.

        Returns:
            The recorded observation, revision, or point-in-time query
            results on success, otherwise a structured data failure.
        """
        ...


@runtime_checkable
class StreamMarketEventsCapability(Protocol):
    """Capability protocol for real-time market event operations."""

    async def stream_market_events(
        self,
        request: StreamMarketEventsRequest,
    ) -> StreamMarketEventsSuccess | DataFailure:
        """Bind feeds, observe feed state, and record bounded replays.

        Args:
            request: Operation-discriminated market event request.

        Returns:
            The feed state and replay reference on success, otherwise a
            structured data failure.
        """
        ...

    def subscribe_stream_market_events_events(
        self,
        request: StreamMarketEventsSubscription,
    ) -> AsyncIterator[DomainEvent]:
        """Deliver live normalized market events as domain events.

        Args:
            request: Owner-required subscription selector carrying the
                provider or feed binding, instrument filter, resume
                position, and bounded replay limit.

        Returns:
            An asynchronous iterator of normalized market events wrapped
            in the common domain event envelope.
        """
        ...
