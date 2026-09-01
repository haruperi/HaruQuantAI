"""Immutable run-data binding for ``FEAT-DATA-BIND_RUN_DATA``.

A binding pins exact stored version identifiers before Simulation, Research, or
Optimization starts. Later imports cannot change the binding. Tick-only precision
modes fail before a run is admitted when any bound version lacks tick evidence.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from app.contracts.common.models import ProblemDetails
from app.contracts.data.errors import DataFailure
from app.contracts.data.models import (
    BindRunDataRequest,
    BindRunDataSuccess,
    RunDataBinding,
)
from app.kernel.identity import generate_uuid7
from app.kernel.time import format_utc_timestamp, utc_now
from app.services.data.bind_run_data.binding_store import BindingStore

if TYPE_CHECKING:
    from app.contracts.data.internal import DataSeriesStoreCapability

_TICK_PRECISIONS = {
    "REAL_TICK_CUSTOM_SPREAD",
    "REAL_TICK_RECORDED_SPREAD",
}


def _failure(request_id: str, *, code: str, detail: str) -> DataFailure:
    """Build one stable binding failure."""
    return DataFailure(
        request_id=request_id,
        code=code,  # type: ignore[arg-type]
        problem=ProblemDetails(
            status=422 if code == "DATA_PRECISION_UNAVAILABLE" else 404,
            code=code,
            detail=detail,
            request_id=request_id,
        ),
    )


class BindRunDataService:
    """Capability implementation for exact run-data binding."""

    def __init__(
        self,
        series_store: DataSeriesStoreCapability,
        binding_store: BindingStore,
    ) -> None:
        """Initialize the binding service.

        Args:
            series_store: Declared immutable Data series-store capability.
            binding_store: Feature-owned binding persistence adapter.
        """
        self._series_store = series_store
        self._binding_store = binding_store

    async def _validate_versions(
        self,
        request: BindRunDataRequest,
    ) -> DataFailure | None:
        assert request.series_version_ids is not None
        assert request.precision is not None
        for version_id in request.series_version_ids:
            snapshot = await self._series_store.get_snapshot(version_id)
            if snapshot is None:
                return _failure(
                    request.request_id,
                    code="DATA_NOT_FOUND",
                    detail=f"Bound Data version is unavailable: {version_id}",
                )
            if request.precision in _TICK_PRECISIONS and snapshot.kind != "TICKS":
                return _failure(
                    request.request_id,
                    code="DATA_PRECISION_UNAVAILABLE",
                    detail=(
                        "Requested real-tick precision requires every bound version "
                        "to contain genuine tick-shaped evidence"
                    ),
                )
        return None

    async def bind_run_data(
        self,
        request: BindRunDataRequest,
    ) -> BindRunDataSuccess | DataFailure:
        """Validate precision and optionally persist/pin an immutable binding.

        Args:
            request: Operation-discriminated run binding request.

        Returns:
            Contract-native binding success or deterministic failure.
        """
        failure = await self._validate_versions(request)
        if failure is not None:
            return failure
        if request.operation == "VALIDATE_PRECISION":
            return BindRunDataSuccess(request_id=request.request_id)

        assert request.run_manifest_id is not None
        assert request.series_version_ids is not None
        assert request.precision is not None
        binding = RunDataBinding(
            binding_id=generate_uuid7(),
            run_manifest_id=request.run_manifest_id,
            series_version_ids=request.series_version_ids,
            precision=request.precision,
            validated_at=format_utc_timestamp(utc_now()),
        )
        await self._binding_store.put(binding)
        await self._series_store.pin_versions(
            binding.binding_id,
            binding.series_version_ids,
        )
        return BindRunDataSuccess(request_id=request.request_id, binding=binding)


async def _demo() -> None:
    """Demonstrate precision validation with a minimal capability double."""
    from typing import Any

    from app.contracts.data.internal import StoredSeriesSnapshot

    version_id = generate_uuid7()

    class _Store:
        async def get_snapshot(self, _: str) -> Any:
            return StoredSeriesSnapshot(
                version_id=version_id,
                kind="TICKS",
                content_hash="0" * 64,
                row_count=1,
            )

    request = BindRunDataRequest(
        request_id=generate_uuid7(),
        capability_snapshot_id=generate_uuid7(),
        operation="VALIDATE_PRECISION",
        series_version_ids=(version_id,),
        precision="REAL_TICK_RECORDED_SPREAD",
    )
    service = BindRunDataService(_Store(), None)  # type: ignore[arg-type]
    print((await service.bind_run_data(request)).model_dump(mode="json"))


if __name__ == "__main__":
    asyncio.run(_demo())
