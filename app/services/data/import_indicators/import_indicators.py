"""Immutable external indicator-series import for FEAT-DATA-IMPORT_INDICATORS.

This feature records provenance and synchronization metadata for indicator values
calculated outside HaruQuantAI. It deliberately does not calculate indicators and
therefore cannot make externally supplied values appear to be Indicators-domain
results. Imported evidence is immutable and classified as ``INDICATOR`` in the
Data series store.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
from typing import TYPE_CHECKING

from app.contracts.data.models import ImportIndicatorsRequest, ImportIndicatorsSuccess
from app.kernel.identity import generate_uuid7

if TYPE_CHECKING:
    from app.contracts.data.internal import DataSeriesStoreCapability


def _content_hash(request: ImportIndicatorsRequest) -> str:
    payload = request.model_dump(
        mode="json",
        exclude={"request_id", "capability_snapshot_id"},
    )
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    return hashlib.sha256(encoded, usedforsecurity=False).hexdigest()


class ImportIndicatorsService:
    """Capability implementation for immutable external indicator imports."""

    def __init__(self, store: DataSeriesStoreCapability) -> None:
        """Initialize with the declared immutable Data series store.

        Args:
            store: Internal capability that owns immutable Data series versions.
        """
        self._store = store

    async def import_indicators(
        self,
        request: ImportIndicatorsRequest,
    ) -> ImportIndicatorsSuccess:
        """Record an external indicator-series version and its provenance.

        Args:
            request: Strict import request naming the external definition,
                source artifact/hash, market identity, and alignment policy.

        Returns:
            Successful import result carrying the immutable version identity.
        """
        version_id = generate_uuid7()
        payload = {
            "record_type": "external_indicator_series",
            "series_id": request.series_id,
            "definition_id": request.definition_id,
            "definition_version": request.definition_version,
            "instrument": request.instrument.model_dump(mode="json"),
            "timeframe": (
                request.timeframe.model_dump(mode="json")
                if request.timeframe is not None
                else None
            ),
            "timezone": request.timezone,
            "source_artifact_id": request.source_artifact_id,
            "source_hash": request.source_hash,
            "alignment_policy": request.alignment_policy.model_dump(mode="json"),
            "provenance": "EXTERNAL_INDICATOR",
        }
        await self._store.put_opaque(
            version_id,
            payload,
            content_hash=_content_hash(request),
            kind="INDICATOR",
        )
        return ImportIndicatorsSuccess(
            request_id=request.request_id,
            version_id=version_id,
            findings=(),
        )


async def _demo() -> None:
    """Demonstrate construction of an explicit external-indicator request."""
    from app.contracts.catalogue.models import InstrumentRef
    from app.contracts.data.models import AlignmentPolicy, ImportIndicatorsRequest

    request = ImportIndicatorsRequest(
        request_id=generate_uuid7(),
        capability_snapshot_id=generate_uuid7(),
        operation="IMPORT",
        series_id=generate_uuid7(),
        definition_id=generate_uuid7(),
        definition_version=1,
        instrument=InstrumentRef(instrument_id=generate_uuid7()),
        timezone="UTC",
        source_artifact_id=generate_uuid7(),
        source_hash="0" * 64,
        alignment_policy=AlignmentPolicy(
            direction="EXACT",
            max_age_seconds=60,
            missing_policy="FAIL",
            timezone="UTC",
        ),
    )
    print(request.model_dump(mode="json"))


if __name__ == "__main__":
    asyncio.run(_demo())
