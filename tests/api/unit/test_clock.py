"""Unit tests for API readiness clock diagnostics."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from types import SimpleNamespace

import pytest
from app.services.api import check_clock_drift, get_readiness
from app.services.api.health import clock as health_clock
from app.services.api.health import probes
from pydantic import ValidationError


def _context() -> object:
    """Build a minimal authenticated context for readiness calls."""
    return SimpleNamespace(
        principal_type="USER",
        permissions=("ops:read",),
        request_id="req-11111111-1111-4111-8111-111111111111",
        correlation_id="cor-33333333-3333-4333-8333-333333333333",
    )


def test_drift_is_signed_and_utc_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Drift direction must remain signed and input reference must be UTC-aware."""
    now = datetime(2026, 7, 24, 9, 0, 0, tzinfo=UTC)
    reference = now + timedelta(seconds=5)

    monkeypatch.setattr(health_clock, "utc_now", lambda: now)
    drift = check_clock_drift(reference=reference, tolerance_seconds="10")
    assert drift == Decimal(-5)

    monkeypatch.setattr(health_clock, "utc_now", lambda: now)
    drift = check_clock_drift(
        reference=now - timedelta(seconds=7), tolerance_seconds="10"
    )
    assert drift == Decimal(7)

    with pytest.raises(ValidationError):
        check_clock_drift(
            reference=reference.replace(tzinfo=None), tolerance_seconds="1"
        )
    with pytest.raises(ValidationError):
        check_clock_drift(
            reference=datetime(
                2026,
                7,
                24,
                9,
                0,
                0,
                tzinfo=timezone(timedelta(hours=1)),
            ),
            tolerance_seconds="1",
        )


def test_drift_beyond_tolerance_degrades_readiness(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Clock drift beyond tolerance must be surfaced as optional readiness degradation."""
    now = datetime(2026, 7, 24, 9, 0, 0, tzinfo=UTC)
    reference = now - timedelta(seconds=12)

    monkeypatch.setattr(health_clock, "utc_now", lambda: now)
    monkeypatch.setattr(probes, "_readiness_dependency_reference", lambda: reference)
    response = get_readiness(_context())

    assert response.data is not None
    assert response.data.status == "degraded"
    assert response.data.clock_drift_seconds > Decimal(2)
    assert any(
        not dep.required and not dep.healthy for dep in response.data.dependencies
    )
