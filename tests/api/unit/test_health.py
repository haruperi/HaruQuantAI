"""Unit tests for API health probes."""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from app.services.api import (
    build_health_dependency_check,
    get_liveness,
    get_readiness,
)
from app.services.api.health import probes
from fastapi import HTTPException

_REQUEST_ID = "req-11111111-1111-4111-8111-111111111111"
_CORRELATION_ID = "cor-33333333-3333-4333-8333-333333333333"


def _context() -> object:
    """Build a minimal authenticated context for protected readiness."""
    return SimpleNamespace(
        principal_type="USER",
        permissions=("ops:read",),
        request_id=_REQUEST_ID,
        correlation_id=_CORRELATION_ID,
    )


def test_liveness_contains_no_private_data() -> None:
    """Liveness must not expose dependency internals or clock drift."""
    response = get_liveness()
    assert response.status == "success"
    assert response.data is not None
    assert response.data.status == "healthy"
    payload = response.data.model_dump()
    assert payload.keys() == {"status", "checked_at"}


def test_required_failure_is_not_healthy(monkeypatch: pytest.MonkeyPatch) -> None:
    """Required dependency failures must return a dependency-unavailable envelope."""

    def _collect_dependencies(
        *,
        now: object,
    ) -> tuple[tuple[object, object], object]:
        """Return a one broken required dependency."""
        return (
            (
                build_health_dependency_check(
                    component="api.process",
                    required=True,
                    healthy=False,
                    checked_at=probes.utc_now(),
                    reason="process dependency unavailable",
                ),
                build_health_dependency_check(
                    component="api.clock",
                    required=False,
                    healthy=True,
                    checked_at=probes.utc_now(),
                ),
            ),
            0,
        )

    monkeypatch.setattr(
        probes, "_collect_readiness_dependencies", _collect_dependencies
    )
    with pytest.raises(HTTPException) as exc_info:
        get_readiness(_context())
    assert exc_info.value.status_code == 503
    assert exc_info.value.detail == "DEPENDENCY_UNAVAILABLE"
