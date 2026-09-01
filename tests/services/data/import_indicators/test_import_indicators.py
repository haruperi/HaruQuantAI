"""Behavior tests for FEAT-DATA-IMPORT_INDICATORS."""

from typing import Any

import pytest

from app.contracts.catalogue.models import InstrumentRef
from app.contracts.data.models import AlignmentPolicy, ImportIndicatorsRequest
from app.kernel.identity import generate_uuid7
from app.services.data.import_indicators.import_indicators import ImportIndicatorsService


class _Store:
    def __init__(self) -> None:
        self.kind: str | None = None
        self.payload: dict[str, object] | None = None

    async def put_opaque(
        self,
        version_id: str,
        payload: dict[str, object],
        **kwargs: Any,
    ) -> object:
        del version_id
        self.payload = payload
        self.kind = str(kwargs["kind"])
        return object()


@pytest.mark.asyncio
async def test_import_preserves_external_indicator_provenance() -> None:
    store = _Store()
    service = ImportIndicatorsService(store)  # type: ignore[arg-type]
    request = ImportIndicatorsRequest(
        request_id=generate_uuid7(),
        capability_snapshot_id=generate_uuid7(),
        operation="IMPORT",
        series_id=generate_uuid7(),
        definition_id=generate_uuid7(),
        definition_version=2,
        instrument=InstrumentRef(instrument_id=generate_uuid7()),
        timezone="UTC",
        source_artifact_id=generate_uuid7(),
        source_hash="a" * 64,
        alignment_policy=AlignmentPolicy(
            direction="EXACT",
            max_age_seconds=60,
            missing_policy="FAIL",
            timezone="UTC",
        ),
    )

    result = await service.import_indicators(request)

    assert result.outcome == "SUCCESS"
    assert result.version_id is not None
    assert store.kind == "INDICATOR"
    assert store.payload is not None
    assert store.payload["provenance"] == "EXTERNAL_INDICATOR"
    assert store.payload["definition_version"] == 2
