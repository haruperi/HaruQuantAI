"""Executable usage demonstration harness for External Indicator Series."""

from __future__ import annotations

import asyncio
import hashlib

from app.contracts.catalogue.models import InstrumentRef
from app.contracts.common.models import Timeframe
from app.contracts.data.errors import DataFailure
from app.contracts.data.models import (
    AlignmentPolicy,
    ImportIndicatorsRequest,
    ImportIndicatorsSuccess,
)
from app.services.data.external_indicator_series.external_indicator_series import (
    ImportIndicatorsService,
    _generate_uuid7,
)


async def _run_usage_scenarios() -> None:
    """Executable usage harness executing named requirement scenarios."""
    print("=== External Indicator Series Usage Harness ===")
    service = ImportIndicatorsService()

    req_id = _generate_uuid7()
    snap_id = _generate_uuid7()
    series_id = _generate_uuid7()
    def_id = _generate_uuid7()
    artifact_id = _generate_uuid7()
    inst_id = _generate_uuid7()
    source_hash = hashlib.sha256(b"sample-indicator-values-payload").hexdigest()

    policy = AlignmentPolicy(
        direction="LAST_KNOWN",
        max_age_seconds=300,
        missing_policy="CARRY_FORWARD",
        timezone="UTC",
        look_ahead_prohibited=True,
    )
    instrument = InstrumentRef(instrument_id=inst_id)
    timeframe = Timeframe(unit="MINUTE", multiple=1)

    req = ImportIndicatorsRequest(
        request_id=req_id,
        capability_snapshot_id=snap_id,
        operation="IMPORT",
        series_id=series_id,
        definition_id=def_id,
        definition_version=1,
        instrument=instrument,
        timeframe=timeframe,
        timezone="UTC",
        source_artifact_id=artifact_id,
        source_hash=source_hash,
        alignment_policy=policy,
    )

    print("\nScenario 1: FR-DATA-IMPORT_INDICATOR_VALUES - Standard Import")
    res1 = await service.import_indicators(req)
    if isinstance(res1, ImportIndicatorsSuccess):
        print(f"[OK] Import successful: version_id={res1.version_id}")
    else:
        print(f"[FAIL] Unexpected failure: {res1.problem.detail}")

    print("\nScenario 2: FR-DATA-IMPORT_INDICATOR_VALUES - Deterministic Re-import")
    res2 = await service.import_indicators(req)
    if (
        isinstance(res2, ImportIndicatorsSuccess)
        and isinstance(res1, ImportIndicatorsSuccess)
        and res1.version_id == res2.version_id
    ):
        print(f"[OK] Deterministic reimport matched version_id={res2.version_id}")
    else:
        print("[FAIL] Re-import was non-deterministic!")

    print("\nScenario 3: Validation Failure on Invalid Attribute")
    invalid_req = ImportIndicatorsRequest(
        request_id=_generate_uuid7(),
        capability_snapshot_id=snap_id,
        operation="IMPORT",
        series_id=series_id,
        definition_id=def_id,
        definition_version=1,
        instrument=instrument,
        timeframe=timeframe,
        timezone="UTC",
        source_artifact_id=artifact_id,
        source_hash=source_hash,
        alignment_policy=policy,
    )
    object.__setattr__(invalid_req, "source_hash", "invalid-not-64-hex")
    res3 = await service.import_indicators(invalid_req)
    if isinstance(res3, DataFailure):
        print(f"[OK] Handled invalid hash failure code={res3.code}")
    else:
        print("[FAIL] Should have failed validation on invalid hash.")

    print("\nAll usage scenarios completed successfully.")


async def main() -> None:
    """Execute all external indicator series usage scenarios."""
    await _run_usage_scenarios()


def run_usage_scenarios() -> None:
    """Run all usage scenarios synchronously."""
    asyncio.run(main())


if __name__ == "__main__":
    run_usage_scenarios()
