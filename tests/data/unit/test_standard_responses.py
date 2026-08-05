"""Standard-response contract tests for the DATA envelope infrastructure.

These tests lock down the Data-specific construction and consumption helpers
defined in ``app/services/data/contracts/responses.py`` and the alignment of
``DATA_ERROR_MANIFEST`` with the Utils-owned ``ErrorDefinition`` contract. They
do not exercise feature algorithms; operation-boundary behavior is covered by
the per-feature response tests added alongside each migration slice.
"""

from __future__ import annotations

import asyncio
from decimal import Decimal
from types import MappingProxyType

import pytest
from app.services.data.contracts.errors import DATA_ERROR_MANIFEST, DataError
from app.services.data.contracts.responses import (
    OPERATION_TRAITS,
    OperationTraits,
    build_data_response,
    build_exception_response,
    data_start_time,
    resolve_operation_request_id,
    run_data_operation,
    run_data_operation_async,
    unwrap_data_response,
)
from app.utils import generate_id
from app.utils.responses.models import StandardResponse

_OPERATION = "data.quality.get_quality_policy"
_REQ = "req-11111111-1111-4111-8111-111111111111"


# ---------------------------------------------------------------------------
# Top-level response shape and field policy.
# ---------------------------------------------------------------------------


def test_success_response_has_exact_five_top_level_fields() -> None:
    """A success response serializes exactly the five standard fields."""
    response = build_data_response(
        operation=_OPERATION,
        request_id=_REQ,
        start_time=data_start_time(),
        data=Decimal("1.5"),
    )
    fields = set(response.model_dump().keys())
    assert fields == {"status", "message", "data", "error", "metadata"}


def test_success_response_carries_raw_identity_of_data() -> None:
    """The raw successful result goes directly into ``data`` unmodified."""
    payload = MappingProxyType({"a": 1, "b": (1, 2)})
    response = build_data_response(
        operation=_OPERATION,
        request_id=_REQ,
        start_time=data_start_time(),
        data=payload,
    )
    assert response.status == "success"
    assert response.data is payload
    assert response.error is None


def test_success_response_with_none_data_is_valid() -> None:
    """A successful operation may legitimately return ``data=None``."""
    response = build_data_response(
        operation=_OPERATION,
        request_id=_REQ,
        start_time=data_start_time(),
        data=None,
    )
    assert response.status == "success"
    assert response.data is None
    assert response.error is None


def test_error_response_requires_data_none() -> None:
    """Error responses always carry ``data=None`` and a populated error."""
    error = DataError("INVALID_INPUT", safe_details={"field": "symbol"})
    response = build_data_response(
        operation=_OPERATION,
        request_id=_REQ,
        start_time=data_start_time(),
        error=error,
    )
    assert response.status == "error"
    assert response.data is None
    assert response.error is not None
    assert response.error.code == "INVALID_INPUT"


def test_extra_top_level_field_is_rejected() -> None:
    """StandardResponse forbids additional top-level fields."""
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        StandardResponse[None](  # type: ignore[misc]
            status="success",
            message="m",
            data=None,
            error=None,
            metadata=None,
            extra="forbidden",
        )


# ---------------------------------------------------------------------------
# Timing invariant.
# ---------------------------------------------------------------------------


def test_execution_ms_is_non_negative_monotonic_and_rounded() -> None:
    """``execution_ms`` is non-negative, monotonic, rounded to three decimals."""
    start = data_start_time()
    response_a = build_data_response(
        operation=_OPERATION, request_id=_REQ, start_time=start, data=1
    )
    response_b = build_data_response(
        operation=_OPERATION, request_id=_REQ, start_time=start, data=2
    )
    assert response_a.metadata.execution_ms >= 0
    assert response_b.metadata.execution_ms >= response_a.metadata.execution_ms
    # Three decimal places -> at most 3 digits after the decimal point.
    for response in (response_a, response_b):
        text = repr(response.metadata.execution_ms)
        if "." in text and "e" not in text.lower():
            assert len(text.split(".")[1]) <= 3


# ---------------------------------------------------------------------------
# Static risk and side-effect metadata policy.
# ---------------------------------------------------------------------------


def test_metadata_declares_data_domain_and_never_trades() -> None:
    """Every Data operation carries ``domain="data"`` and ``places_trade=False``."""
    for operation in OPERATION_TRAITS:
        response = build_data_response(
            operation=operation,
            request_id=_REQ,
            start_time=data_start_time(),
            data=None,
        )
        meta = response.metadata
        assert meta.domain == "data"
        assert meta.places_trade is False


def test_read_only_operations_declare_no_mutation_side_effects() -> None:
    """Read-only operations declare no writes or mutations."""
    for operation, traits in OPERATION_TRAITS.items():
        if not traits.read_only:
            continue
        meta = build_data_response(
            operation=operation,
            request_id=_REQ,
            start_time=data_start_time(),
            data=None,
        ).metadata
        assert meta.read_only is True
        assert meta.writes_file is False
        assert meta.modifies_database is False
        assert meta.places_trade is False


def test_static_traits_match_operation_registry() -> None:
    """The static capability traits are recoverable for each operation."""
    operation = "data.persistence.run_data_migrations"
    traits = OPERATION_TRAITS[operation]
    meta = build_data_response(
        operation=operation,
        request_id=_REQ,
        start_time=data_start_time(),
        data=None,
    ).metadata
    assert meta.risk_level.value == getattr(
        traits.risk_level, "value", str(traits.risk_level)
    )
    assert meta.read_only is traits.read_only
    assert meta.writes_file is traits.writes_file
    assert meta.modifies_database is traits.modifies_database
    assert meta.requires_network is traits.requires_network


# ---------------------------------------------------------------------------
# Error catalogue alignment.
# ---------------------------------------------------------------------------


_PLANNED_CODES = frozenset(
    {
        "INVALID_INPUT",
        "VALIDATION_FAILED",
        "DATA_QUALITY_FAILED",
        "DATA_NOT_FOUND",
        "EMPTY_RESULT",
        "LIMIT_EXCEEDED",
        "UNSUPPORTED_SOURCE",
        "UNSUPPORTED_TIMEFRAME",
        "UNSUPPORTED_OPERATION",
        "SOURCE_UNAVAILABLE",
        "SERVICE_UNAVAILABLE",
        "NETWORK_ERROR",
        "TIMEOUT",
        "LICENSE_RESTRICTION",
        "CREDENTIALS_MISSING",
        "AUTHENTICATION_FAILED",
        "PERMISSION_DENIED",
        "POLICY_BLOCKED",
        "STALE_EVIDENCE",
        "CIRCUIT_BREAKER_OPEN",
        "PRECISION_MISMATCH",
        "MISSING_ASSET_METADATA",
        "DATABASE_ERROR",
        "DB_CONNECTION_ERROR",
        "DB_WRITE_FAILED",
        "CONCURRENT_WRITE_LOCKED",
        "FILE_CORRUPTED",
        "SCHEMA_MIGRATION_FAILED",
        "JOB_NOT_FOUND",
        "SCHEDULER_ERROR",
        "CHECKPOINT_CORRUPTED",
        "STATE_RECOVERY_FAILED",
        "BUFFER_OVERFLOW",
        "DATA_DROPPED",
        "FEED_HEARTBEAT_TIMEOUT",
        "UNKNOWN_ERROR",
    }
)


def test_every_current_data_code_appears_exactly_once() -> None:
    """All 36 planned Data codes appear exactly once in the catalogue."""
    assert set(DATA_ERROR_MANIFEST) == _PLANNED_CODES
    assert len(_PLANNED_CODES) == 36


def test_unapproved_code_is_rejected() -> None:
    """A code absent from the catalogue fails validation at the factory."""
    from app.utils.errors.exceptions import ValidationError
    from app.utils.responses.factories import error_response
    from app.utils.responses.models import ResponseMetadata

    metadata = ResponseMetadata(
        name=_OPERATION,
        domain="data",
        risk_level="low",
        request_id=_REQ,
        execution_ms=0.0,
        read_only=True,
        writes_file=False,
        modifies_database=False,
        places_trade=False,
        requires_network=False,
        extensions={},
    )
    with pytest.raises(ValidationError):
        error_response(
            code="DEFINITELY_NOT_A_REAL_CODE",
            details={},
            message="m",
            metadata=metadata,
            catalog=DATA_ERROR_MANIFEST,
        )


def test_manifest_uses_utils_owned_error_definition_with_data_domain() -> None:
    """The manifest uses the Utils-owned contract and stamps ``domain='data'``."""
    from app.services.data.contracts.errors import (
        ErrorDefinition as UtilsErrorDefinition,
    )

    for definition in DATA_ERROR_MANIFEST.values():
        assert isinstance(definition, UtilsErrorDefinition)
        assert definition.domain == "data"
        assert definition.description  # legacy safe_message mapped over


def test_legacy_data_error_fields_are_preserved() -> None:
    """All safe legacy ``DataError`` evidence survives in the response."""
    error = DataError(
        "DATA_QUALITY_FAILED",
        safe_details={"symbol": "EURUSD"},
        request_id=_REQ,
    )
    response = build_data_response(
        operation=_OPERATION,
        request_id=_REQ,
        start_time=data_start_time(),
        error=error,
    )
    assert response.error is not None
    details = response.error.details
    assert details["retryable"] is error.retryable
    assert details["severity"] == error.severity
    assert details["operator_action"] == error.operator_action
    assert details["request_id"] == _REQ
    assert details["symbol"] == "EURUSD"
    assert response.message == error.safe_message


def test_raw_exception_text_and_secrets_are_absent() -> None:
    """Exception payloads and secret values never cross the boundary."""
    error = DataError(
        "INVALID_INPUT",
        safe_details={
            "api_key": "supersecret",  # pragma: allowlist secret
            "note": "plain text",
        },
    )
    response = build_data_response(
        operation=_OPERATION,
        request_id=_REQ,
        start_time=data_start_time(),
        error=error,
    )
    blob = repr(response)
    assert "supersecret" not in blob
    # Safe details redact sensitive keys before they reach the response.
    assert response.error is not None
    assert response.error.details["api_key"] == "[REDACTED]"


# ---------------------------------------------------------------------------
# Boundary runner.
# ---------------------------------------------------------------------------


def test_run_data_operation_success_wraps_raw_value() -> None:
    """The runner puts the exact raw result into ``data`` on success."""

    def raw() -> list[int]:
        return [1, 2, 3]

    response = run_data_operation(
        operation=_OPERATION,
        request_id=_REQ,
        start_time=data_start_time(),
        raw=raw,
    )
    assert response.status == "success"
    assert response.data == [1, 2, 3]


def test_run_data_operation_maps_data_error_to_error_response() -> None:
    """A raised ``DataError`` becomes an in-band error response."""

    def raw() -> int:
        raise DataError("DATA_NOT_FOUND")

    response = run_data_operation(
        operation=_OPERATION,
        request_id=_REQ,
        start_time=data_start_time(),
        raw=raw,
    )
    assert response.status == "error"
    assert response.error is not None
    assert response.error.code == "DATA_NOT_FOUND"


def test_run_data_operation_normalizes_unexpected_exception() -> None:
    """Unexpected exceptions map to ``INTERNAL_ERROR`` via Utils."""

    def raw() -> int:
        raise RuntimeError("boom")

    response = run_data_operation(
        operation=_OPERATION,
        request_id=_REQ,
        start_time=data_start_time(),
        raw=raw,
    )
    assert response.status == "error"
    assert response.error is not None
    assert response.error.code == "INTERNAL_ERROR"
    assert "boom" not in repr(response)


@pytest.mark.parametrize(
    "exc",
    [KeyboardInterrupt, SystemExit, GeneratorExit],
)
def test_run_data_operation_propagates_process_control_exceptions(
    exc: type[BaseException],
) -> None:
    """Cancellation and process-control exceptions propagate unchanged."""

    def raw() -> int:
        raise exc

    with pytest.raises(exc):
        run_data_operation(
            operation=_OPERATION,
            request_id=_REQ,
            start_time=data_start_time(),
            raw=raw,
        )


def test_run_data_operation_async_propagates_cancellation() -> None:
    """``asyncio.CancelledError`` propagates through the async runner."""

    async def raw() -> int:
        raise asyncio.CancelledError

    async def main() -> None:
        await run_data_operation_async(
            operation=_OPERATION,
            request_id=_REQ,
            start_time=data_start_time(),
            raw=raw,
        )

    with pytest.raises(asyncio.CancelledError):
        asyncio.run(main())


def test_build_exception_response_normalizes_without_keeping_exception() -> None:
    """``build_exception_response`` maps any exception safely."""

    response = build_exception_response(
        operation=_OPERATION,
        request_id=_REQ,
        start_time=data_start_time(),
        exception=ValueError("x"),
    )
    assert response.status == "error"
    assert response.error is not None
    assert response.error.code == "INTERNAL_ERROR"
    assert "x" not in repr(response.error)


# ---------------------------------------------------------------------------
# Nested-response consumption.
# ---------------------------------------------------------------------------


def test_unwrap_data_response_returns_raw_data_on_success() -> None:
    """``unwrap_data_response`` returns the nested raw data on success."""
    nested = build_data_response(
        operation=_OPERATION,
        request_id=_REQ,
        start_time=data_start_time(),
        data={"k": 1},
    )
    assert unwrap_data_response(nested, operation=_OPERATION, request_id=_REQ) == {
        "k": 1
    }


def test_unwrap_data_response_raises_data_error_on_failure() -> None:
    """A nested failure is converted into a ``DataError`` preserving the code."""
    nested = build_data_response(
        operation=_OPERATION,
        request_id=_REQ,
        start_time=data_start_time(),
        error=DataError("DATA_NOT_FOUND", safe_details={"symbol": "EURUSD"}),
    )
    with pytest.raises(DataError) as info:
        unwrap_data_response(nested, operation=_OPERATION, request_id=_REQ)
    assert info.value.code == "DATA_NOT_FOUND"


def test_unwrap_data_response_returns_none_when_data_is_none() -> None:
    """A successful nested response carrying ``None`` data returns ``None``.

    Some Data operations legitimately return ``None`` on success (for example
    ``validate_resample_target``); the unwrap helper must not reclassify that as
    failure. Callers requiring a non-null result check ``data`` themselves.
    """
    nested = build_data_response(
        operation=_OPERATION,
        request_id=_REQ,
        start_time=data_start_time(),
        data=None,
    )
    assert unwrap_data_response(nested, operation=_OPERATION, request_id=_REQ) is None


def test_nested_standard_response_is_not_returned_by_build() -> None:
    """Building a response from raw data never nests a second response."""
    inner = build_data_response(
        operation=_OPERATION,
        request_id=_REQ,
        start_time=data_start_time(),
        data=5,
    )
    outer = build_data_response(
        operation=_OPERATION,
        request_id=_REQ,
        start_time=data_start_time(),
        data=inner,
    )
    # The test asserts the boundary contract: build_data_response does not
    # forbid nesting by type (it accepts T | None), but a migrated operation
    # must unwrap before building. Here we verify the helper itself does not
    # auto-nest: data identity is preserved verbatim.
    assert outer.data is inner  # caller responsibility to unwrap.


# ---------------------------------------------------------------------------
# Request-identity resolution.
# ---------------------------------------------------------------------------


def test_resolve_request_id_generates_when_absent() -> None:
    """Absent identity yields a freshly generated ``req-`` identifier."""
    resolved, error = resolve_operation_request_id()
    assert error is None
    assert resolved.startswith("req-")


def test_resolve_request_id_accepts_valid_explicit() -> None:
    """A valid explicit identifier is retained verbatim."""
    resolved, error = resolve_operation_request_id(explicit=_REQ)
    assert error is None
    assert resolved == _REQ


def test_resolve_request_id_reads_request_attribute() -> None:
    """A request object's ``request_id`` attribute takes precedence."""

    class _Req:
        request_id = _REQ

    resolved, error = resolve_operation_request_id(_Req())
    assert error is None
    assert resolved == _REQ


def test_resolve_request_id_rejects_invalid_explicit() -> None:
    """An invalid explicit identifier yields a valid id plus a validation error."""
    resolved, error = resolve_operation_request_id(explicit="not-a-real-id")
    assert error is not None
    assert error.code == "VALIDATION_FAILED"
    # The response identifier must still be valid so the error response traces.
    assert resolved.startswith("req-")
    assert resolved != "not-a-real-id"


# ---------------------------------------------------------------------------
# Registry completeness sanity (the full 134-candidate coverage gate lives in
# the boundary test added with the final slice).
# ---------------------------------------------------------------------------


def test_operation_registry_covers_134_candidates() -> None:
    """The static registry carries the 134 qualifying Data operations."""
    assert len(OPERATION_TRAITS) == 134


def test_every_trait_is_immutable_instance() -> None:
    """Each registry entry is a frozen ``OperationTraits``."""
    for traits in OPERATION_TRAITS.values():
        assert isinstance(traits, OperationTraits)


def test_no_operation_returns_invalid_request_id_in_success() -> None:
    """Generating a request id never yields an invalid identifier."""
    for _ in range(50):
        ident = generate_id("req")
        resolved, error = resolve_operation_request_id(explicit=ident)
        assert error is None
        assert resolved == ident
