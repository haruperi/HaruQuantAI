"""Unit test for app/services/data/time_sessions/utc.py to reach 100% coverage."""

from datetime import UTC, datetime, timedelta, timezone

from app.services.data.contracts.responses import unwrap_data_response
from app.services.data.time_sessions.utc import require_utc


def _unwrap(response: object) -> object:
    """Unwrap a successful Data standard response to its raw payload."""
    return unwrap_data_response(
        response,  # type: ignore[arg-type]
        operation="data.time_sessions.require_utc",
        request_id="req-00000000-0000-4000-8000-000000000000",
    )


def test_require_utc_valid() -> None:
    """Test require_utc returns valid aware UTC datetime in the response data."""
    now = datetime.now(UTC)
    assert _unwrap(require_utc(now)) is now


def test_require_utc_naive() -> None:
    """Test require_utc rejects a naive datetime with a validation error."""
    # Deliberately naive to exercise the rejection path.
    naive = datetime(2026, 1, 1, 12, 0, 0)  # noqa: DTZ001
    response = require_utc(naive)
    assert response.status == "error"
    assert response.error is not None
    assert response.error.code == "VALIDATION_FAILED"


def test_require_utc_non_utc_timezone() -> None:
    """Test require_utc rejects a non-UTC timezone with a validation error."""
    non_utc = datetime.now(timezone(timedelta(hours=5)))
    response = require_utc(non_utc)
    assert response.status == "error"
    assert response.error is not None
    assert response.error.code == "VALIDATION_FAILED"
