"""Volume-profile source validation for ``FEAT-DATA-PREPARE_PROFILES``.

The feature validates whether an already committed Data version has the precision
shape requested by a downstream volume/TPO calculation. It does not calculate the
profile itself and never fabricates volume or session coverage.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from app.contracts.common.models import ProblemDetails, ValidationIssue
from app.contracts.data.errors import DataFailure
from app.contracts.data.models import (
    PrepareProfilesRequest,
    PrepareProfilesSuccess,
    VolumeProfileSource,
)
from app.kernel.identity import generate_uuid7

if TYPE_CHECKING:
    from app.contracts.data.internal import DataSeriesStoreCapability


class PrepareProfilesService:
    """Capability implementation for profile-source sufficiency evidence."""

    def __init__(self, store: DataSeriesStoreCapability) -> None:
        """Initialize with the declared immutable series-store dependency.

        Args:
            store: Data series-store capability.
        """
        self._store = store

    async def prepare_profiles(
        self,
        request: PrepareProfilesRequest,
    ) -> PrepareProfilesSuccess | DataFailure:
        """Validate one source declaration against stored series precision.

        Args:
            request: Validated profile-source request.

        Returns:
            Source sufficiency evidence or stable not-found failure.
        """
        snapshot = await self._store.get_snapshot(request.data_version_id)
        if snapshot is None:
            return DataFailure(
                request_id=request.request_id,
                code="DATA_NOT_FOUND",
                problem=ProblemDetails(
                    status=404,
                    code="DATA_NOT_FOUND",
                    detail="Profile source data version is not available",
                    request_id=request.request_id,
                ),
            )
        if request.source_kind == "TICK":
            sufficient = snapshot.kind == "TICKS"
            expected = "TICKS"
        else:
            sufficient = snapshot.kind in {"BARS", "SCENARIO"}
            expected = "BARS_OR_SCENARIO"
        diagnostics: tuple[ValidationIssue, ...] = ()
        if not sufficient:
            diagnostics = (
                ValidationIssue(
                    path=("data_version_id",),
                    code="PROFILE_SOURCE_PRECISION_INSUFFICIENT",
                    message="Stored series precision does not satisfy the requested source kind.",
                    context={"stored_kind": snapshot.kind, "expected": expected},
                ),
            )
        source = VolumeProfileSource(
            source_id=generate_uuid7(),
            data_version_id=request.data_version_id,
            source_kind=request.source_kind,
            session_version_id=request.session_version_id,
            price_step=request.price_step,
            bin_count=request.bin_count,
            coverage_diagnostics=diagnostics,
            is_sufficient=sufficient,
        )
        return PrepareProfilesSuccess(request_id=request.request_id, source=source)


async def _demo() -> None:
    """Demonstrate the contract shape using an in-memory store double."""
    from typing import Any

    from app.contracts.data.internal import StoredSeriesSnapshot

    version_id = generate_uuid7()

    class _Store:
        async def get_snapshot(self, _: str) -> Any:
            return StoredSeriesSnapshot(
                version_id=version_id,
                kind="TICKS",
                content_hash="0" * 64,
                row_count=10,
            )

    service = PrepareProfilesService(_Store())  # type: ignore[arg-type]
    request = PrepareProfilesRequest(
        request_id=generate_uuid7(),
        capability_snapshot_id=generate_uuid7(),
        operation="VALIDATE_SOURCE",
        data_version_id=version_id,
        source_kind="TICK",
        session_version_id=generate_uuid7(),
        price_step="0.0001",
    )
    print((await service.prepare_profiles(request)).model_dump(mode="json"))


if __name__ == "__main__":
    asyncio.run(_demo())
