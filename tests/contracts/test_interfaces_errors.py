"""Unit tests for interfaces error hierarchy and wire failure models."""

from __future__ import annotations

from app.contracts.common.models import ProblemDetails
from app.contracts.interfaces.errors import (
    WIRE_FAILURES,
    ApiIncompatibleError,
    ArtifactAccessDeniedError,
    CommandExecutionError,
    CommandNotFoundError,
    CommandValidationError,
    DurableJobNotFoundError,
    EventCursorExpiredError,
    IdempotencyConflictError,
    InterfaceError,
    InterfaceFailure,
    JobNotFoundError,
    VersionConflictError,
)


def test_interfaces_errors_hierarchy() -> None:
    """Verify interfaces error classes format messages and attributes properly."""
    e1 = InterfaceError("general interface error", error_code="CUSTOM_ERR")
    assert e1.error_code == "CUSTOM_ERR"
    assert "[CUSTOM_ERR] general interface error" in str(e1)

    e2 = VersionConflictError(expected_version=1, current_version=2)
    assert e2.error_code == "VERSION_CONFLICT"
    assert e2.expected_version == 1
    assert e2.current_version == 2
    assert "expected=1, current=2" in str(e2)

    e2_no_vers = VersionConflictError()
    assert "Object version conflict detected" in str(e2_no_vers)

    e3 = IdempotencyConflictError("idem-key-123")
    assert e3.error_code == "IDEMPOTENCY_CONFLICT"
    assert e3.idempotency_key == "idem-key-123"

    e4 = EventCursorExpiredError("cur-456")
    assert e4.error_code == "EVENT_CURSOR_EXPIRED"
    assert e4.cursor == "cur-456"

    e5 = JobNotFoundError("job-789")
    assert e5.error_code == "JOB_NOT_FOUND"
    assert e5.job_id == "job-789"

    e6 = ArtifactAccessDeniedError("/path/to/art", "escapes root")
    assert e6.error_code == "ARTIFACT_ACCESS_DENIED"
    assert e6.path == "/path/to/art"
    assert e6.reason == "escapes root"

    e7 = ApiIncompatibleError("v0.9", ("v1.0", "v2.0"))
    assert e7.error_code == "UPGRADE_REQUIRED"
    assert e7.client_version == "v0.9"
    assert e7.supported_versions == ("v1.0", "v2.0")

    e8 = CommandNotFoundError("cmd.unknown")
    assert e8.error_code == "COMMAND_NOT_FOUND"
    assert e8.command_name == "cmd.unknown"

    e9 = CommandValidationError("cmd.run", ("err1", "err2"))
    assert e9.error_code == "COMMAND_VALIDATION_FAILED"
    assert e9.command_name == "cmd.run"
    assert e9.validation_errors == ("err1", "err2")

    e10 = CommandExecutionError("cmd.run", "timeout exceeded")
    assert e10.error_code == "COMMAND_EXECUTION_FAILED"
    assert e10.command_name == "cmd.run"
    assert e10.reason == "timeout exceeded"

    e11 = DurableJobNotFoundError("djob-1")
    assert e11.error_code == "DURABLE_JOB_NOT_FOUND"
    assert e11.durable_job_id == "djob-1"


def test_interface_failure_wire_model() -> None:
    """Verify InterfaceFailure WireModel structure and WIRE_FAILURES map."""
    assert WIRE_FAILURES["InterfaceFailure"] == InterfaceFailure

    problem = ProblemDetails(
        type="urn:error:interface:job_not_found",
        title="Job Not Found",
        status=404,
        detail="The specified job was not found",
    )
    failure = InterfaceFailure(
        request_id="01918a99-0000-7000-8000-000000000001",
        code="JOB_NOT_FOUND",
        problem=problem,
    )
    assert failure.outcome == "FAILURE"
    assert failure.code == "JOB_NOT_FOUND"
    assert failure.schema_version == 1
    assert failure.problem.status == 404
