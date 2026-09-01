"""Point-in-time-safe external-series alignment for FEAT-DATA-ALIGN_SERIES.

The public v1 request names one source version and one alignment policy. It does not
carry a target timeline or target series. Consequently this implementation can
materialize only ``EXACT`` alignment without inventing timestamps. ``LAST_KNOWN`` and
``AGGREGATE`` require a target timeline to prove age, missingness, and no-lookahead;
they fail closed until a future contract version represents that target explicitly.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from app.contracts.common.models import ProblemDetails
from app.contracts.data.errors import DataFailure
from app.contracts.data.models import AlignedSeries, AlignSeriesRequest, AlignSeriesSuccess
from app.kernel.identity import generate_uuid7

if TYPE_CHECKING:
    from app.contracts.data.internal import DataSeriesStoreCapability, StoredSeriesSnapshot


def _failure(request_id: str, *, code: str, detail: str, status: int = 422) -> DataFailure:
    """Build a deterministic alignment failure.

    Args:
        request_id: Public request identity.
        code: Closed Data failure code.
        detail: Safe human-readable detail.
        status: HTTP-style problem status.

    Returns:
        Contract-native Data failure.
    """
    return DataFailure(
        request_id=request_id,
        code=code,  # type: ignore[arg-type]
        problem=ProblemDetails(
            status=status,
            code=code,
            detail=detail,
            request_id=request_id,
        ),
    )


class AlignSeriesService:
    """Capability implementation for immutable point-in-time alignment."""

    def __init__(self, store: DataSeriesStoreCapability) -> None:
        """Initialize with immutable Data-series storage.

        Args:
            store: Declared Data series-store capability.
        """
        self._store = store

    async def align_series(
        self,
        request: AlignSeriesRequest,
    ) -> AlignSeriesSuccess | DataFailure:
        """Validate an alignment policy or materialize an exact aligned version.

        Args:
            request: Operation-discriminated alignment request.

        Returns:
            Contract-native success or deterministic failure.
        """
        assert request.source_version_id is not None
        assert request.policy is not None
        source = await self._store.get_snapshot(request.source_version_id)
        if source is None:
            return _failure(
                request.request_id,
                code="DATA_NOT_FOUND",
                detail="Source series version is not available",
                status=404,
            )

        if request.operation == "DEFINE_POLICY":
            return AlignSeriesSuccess(request_id=request.request_id)

        if request.policy.direction != "EXACT":
            return _failure(
                request.request_id,
                code="DATA_ALIGNMENT_INCOMPATIBLE",
                detail=(
                    "The v1 alignment request has no target timeline; LAST_KNOWN and "
                    "AGGREGATE cannot be evaluated without inventing decision times"
                ),
            )

        aligned_version_id = generate_uuid7()
        copied = await self._copy_exact(source, aligned_version_id)
        if not copied:
            return _failure(
                request.request_id,
                code="DATA_ALIGNMENT_INCOMPATIBLE",
                detail="Stored source kind cannot be materialized by this alignment capability",
            )
        return AlignSeriesSuccess(
            request_id=request.request_id,
            aligned=AlignedSeries(
                alignment_id=generate_uuid7(),
                source_version_id=request.source_version_id,
                policy=request.policy,
                aligned_version_id=aligned_version_id,
            ),
        )

    async def _copy_exact(
        self,
        source: StoredSeriesSnapshot,
        aligned_version_id: str,
    ) -> bool:
        """Copy a source payload byte-semantically under a new immutable identity.

        Args:
            source: Immutable source metadata.
            aligned_version_id: New immutable aligned-series identity.

        Returns:
            True when the source kind was copied successfully.
        """
        if source.kind == "TICKS":
            ticks = await self._store.read_ticks(source.version_id)
            if ticks is None:
                return False
            await self._store.put_ticks(
                aligned_version_id,
                ticks,
                content_hash=source.content_hash,
            )
            return True
        if source.kind in {"BARS", "SCENARIO"}:
            bars = await self._store.read_bars(source.version_id)
            if bars is None or source.timeframe is None:
                return False
            await self._store.put_bars(
                aligned_version_id,
                bars,
                content_hash=source.content_hash,
                timeframe=source.timeframe,
                kind=source.kind,
            )
            return True
        payload = await self._store.read_opaque(source.version_id)
        if payload is None:
            return False
        await self._store.put_opaque(
            aligned_version_id,
            payload,
            content_hash=source.content_hash,
            kind=source.kind,
        )
        return True


async def _demo() -> None:
    """Demonstrate an explicit no-lookahead alignment-policy request."""
    from app.contracts.data.models import AlignmentPolicy

    request = AlignSeriesRequest(
        request_id=generate_uuid7(),
        capability_snapshot_id=generate_uuid7(),
        operation="DEFINE_POLICY",
        source_version_id=generate_uuid7(),
        policy=AlignmentPolicy(
            direction="EXACT",
            max_age_seconds=60,
            missing_policy="FAIL",
            timezone="UTC",
        ),
    )
    print(request.model_dump(mode="json"))


if __name__ == "__main__":
    asyncio.run(_demo())
