"""Unit, contract, and scenario tests for External Indicator Series."""

import hashlib

import pytest
from app.contracts.catalogue.models import InstrumentRef
from app.contracts.common.models import Timeframe
from app.contracts.data.errors import DataFailure
from app.contracts.data.models import (
    AlignmentPolicy,
    ImportIndicatorsRequest,
    ImportIndicatorsSuccess,
)
from app.services.data.external_indicator_series.config import (
    ExternalIndicatorSeriesConfig,
)
from app.services.data.external_indicator_series.external_indicator_series import (
    ImportIndicatorsService,
    _derive_deterministic_uuid7,
    _generate_uuid7,
    _is_valid_sha256,
    _is_valid_timezone,
    _is_valid_uuid,
    _is_valid_uuid7,
    _run_usage_scenarios,
    data_import_indicator_values,
)


def _sample_request(
    *,
    source_hash: str | None = None,
    timezone: str = "UTC",
    look_ahead_prohibited: bool = True,
    definition_version: int = 1,
) -> ImportIndicatorsRequest:
    """Build a valid sample ImportIndicatorsRequest."""
    req_id = _generate_uuid7()
    snap_id = _generate_uuid7()
    series_id = _generate_uuid7()
    def_id = _generate_uuid7()
    artifact_id = _generate_uuid7()
    inst_id = _generate_uuid7()
    h = source_hash or hashlib.sha256(b"sample-indicator-payload").hexdigest()

    policy = AlignmentPolicy(
        direction="LAST_KNOWN",
        max_age_seconds=600,
        missing_policy="CARRY_FORWARD",
        timezone="UTC",
        look_ahead_prohibited=look_ahead_prohibited,  # type: ignore[arg-type]
    )
    instrument = InstrumentRef(instrument_id=inst_id)
    timeframe = Timeframe(unit="MINUTE", multiple=5)

    return ImportIndicatorsRequest(
        request_id=req_id,
        capability_snapshot_id=snap_id,
        operation="IMPORT",
        series_id=series_id,
        definition_id=def_id,
        definition_version=definition_version,
        instrument=instrument,
        timeframe=timeframe,
        timezone=timezone,
        source_artifact_id=artifact_id,
        source_hash=h,
        alignment_policy=policy,
    )


def test_data_import_indicator_values() -> None:
    """Verify FR-DATA-IMPORT_INDICATOR_VALUES: standard valid import."""
    req = _sample_request()
    res = data_import_indicator_values(req)

    assert isinstance(res, ImportIndicatorsSuccess)
    assert res.request_id == req.request_id
    assert res.outcome == "SUCCESS"
    assert res.result_version == 1
    assert res.version_id is not None
    assert _is_valid_uuid7(res.version_id)
    assert len(res.findings) == 0


def test_data_import_indicator_values_deterministic_reimport() -> None:
    """Verify FR-DATA-IMPORT_INDICATOR_VALUES: deterministic re-import produces same version ID."""
    req = _sample_request()
    res1 = data_import_indicator_values(req)
    res2 = data_import_indicator_values(req)

    assert isinstance(res1, ImportIndicatorsSuccess)
    assert isinstance(res2, ImportIndicatorsSuccess)
    assert res1.version_id == res2.version_id


def test_data_import_indicator_values_nondeterministic_mode() -> None:
    """Verify non-deterministic config generates distinct version IDs."""
    cfg = ExternalIndicatorSeriesConfig(require_deterministic_reimport=False)
    req = _sample_request()
    res1 = data_import_indicator_values(req, config=cfg)
    res2 = data_import_indicator_values(req, config=cfg)

    assert isinstance(res1, ImportIndicatorsSuccess)
    assert isinstance(res2, ImportIndicatorsSuccess)
    assert res1.version_id != res2.version_id


def test_data_import_invalid_identifiers() -> None:
    """Verify data failure on invalid UUID fields."""
    req = _sample_request()
    object.__setattr__(req, "series_id", "not-a-uuid")

    res = data_import_indicator_values(req)
    assert isinstance(res, DataFailure)
    assert res.code == "DATA_VALIDATION_FAILED"
    assert any(err.code == "IDENTIFIER_INVALID" for err in res.problem.errors)


def test_data_import_invalid_source_hash() -> None:
    """Verify data failure on invalid source hash."""
    req = _sample_request()
    object.__setattr__(req, "source_hash", "invalid_short_hash")

    res = data_import_indicator_values(req)
    assert isinstance(res, DataFailure)
    assert res.code == "DATA_VALIDATION_FAILED"
    assert any(err.code == "SOURCE_HASH_INVALID" for err in res.problem.errors)


def test_data_import_invalid_timezone() -> None:
    """Verify data failure on invalid timezone."""
    req = _sample_request()
    object.__setattr__(req, "timezone", "Invalid/Fake_Zone_999")

    res = data_import_indicator_values(req)
    assert isinstance(res, DataFailure)
    assert res.code == "DATA_VALIDATION_FAILED"
    assert any(err.code == "TIMEZONE_INVALID" for err in res.problem.errors)


@pytest.mark.asyncio
async def test_import_indicators_service_execution() -> None:
    """Verify ImportIndicatorsService async invocation."""
    service = ImportIndicatorsService()
    req = _sample_request()
    res = await service.import_indicators(req)

    assert isinstance(res, ImportIndicatorsSuccess)
    assert res.outcome == "SUCCESS"
    assert res.version_id is not None


def test_uuid7_helper_utilities() -> None:
    """Verify internal UUIDv7 and hash validation helpers."""
    u7 = _generate_uuid7()
    assert _is_valid_uuid(u7)
    assert _is_valid_uuid7(u7)
    assert not _is_valid_uuid7("12345678-1234-4234-8234-1234567890ab")
    assert not _is_valid_uuid("bad-uuid")

    derived = _derive_deterministic_uuid7("test-seed-key")
    assert _is_valid_uuid7(derived)
    assert derived == _derive_deterministic_uuid7("test-seed-key")

    assert _is_valid_sha256("a" * 64)
    assert not _is_valid_sha256("A" * 64)
    assert not _is_valid_sha256("short")
    assert _is_valid_timezone("UTC")
    assert _is_valid_timezone("America/New_York")
    assert not _is_valid_timezone("Invalid/BadZone")
    assert not _is_valid_timezone("")
    assert not _is_valid_timezone(None)  # type: ignore[arg-type]


def test_validation_issues_branches() -> None:
    """Verify data failure on invalid instrument, lookahead prohibited violated, and invalid definition version."""
    # Invalid instrument ID
    req1 = _sample_request()
    object.__setattr__(
        req1, "instrument", InstrumentRef.model_construct(instrument_id="bad-uuid")
    )
    res1 = data_import_indicator_values(req1)
    assert isinstance(res1, DataFailure)
    assert any(err.code == "IDENTIFIER_INVALID" for err in res1.problem.errors)

    # Lookahead prohibition violated
    req2 = _sample_request()
    bad_policy = AlignmentPolicy.model_construct(
        direction="LAST_KNOWN",
        max_age_seconds=300,
        missing_policy="CARRY_FORWARD",
        timezone="UTC",
        look_ahead_prohibited=False,
    )
    object.__setattr__(req2, "alignment_policy", bad_policy)
    res2 = data_import_indicator_values(req2)
    assert isinstance(res2, DataFailure)
    assert any(
        err.code == "LOOKAHEAD_PROHIBITION_VIOLATED" for err in res2.problem.errors
    )

    # Definition version < 1 (non-fatal finding)
    req3 = _sample_request()
    object.__setattr__(req3, "definition_version", 0)
    res3 = data_import_indicator_values(req3)
    assert isinstance(res3, ImportIndicatorsSuccess)
    assert any(err.code == "DEFINITION_VERSION_INVALID" for err in res3.findings)


@pytest.mark.asyncio
async def test_run_usage_scenarios_harness() -> None:
    """Verify execution of the standalone usage scenario harness."""
    await _run_usage_scenarios()


def test_external_indicator_persistence() -> None:
    """Verify ExternalIndicatorPersistence operations."""
    from app.services.data.external_indicator_series._persistence import (
        ExternalIndicatorPersistence,
    )

    store = ExternalIndicatorPersistence()
    version_id = _generate_uuid7()
    res = ImportIndicatorsSuccess(
        request_id=_generate_uuid7(),
        version_id=version_id,
        findings=(),
        outcome="SUCCESS",
    )
    store.save_series(version_id, res)
    assert store.get_series(version_id) == res
    assert len(store.get_all_series()) == 1
    assert store.get_series("unknown") is None

    store.clear()
    assert len(store.get_all_series()) == 0
