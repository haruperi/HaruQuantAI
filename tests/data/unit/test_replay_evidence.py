"""Unit tests for point-in-time replay evidence export (feature)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest
from app.services.data import export_replay_evidence
from app.services.data.replay import packages as service
from app.services.data.replay.evidence import ReplayEvidenceRequest
from app.utils import generate_id

_T0 = datetime(2026, 8, 7, 12, tzinfo=UTC)


def _record(available_at: datetime) -> SimpleNamespace:
    """Return one structural canonical-record fixture."""
    return SimpleNamespace(available_at=available_at, timestamp=available_at)


@pytest.fixture
def isolated_evidence(monkeypatch: pytest.MonkeyPatch):
    """Replace source access and dataset retrieval with deterministic fakes."""
    from app.services.data.sources import composition

    monkeypatch.setattr(composition, "ensure_storage", lambda *_args: None)
    monkeypatch.setattr(composition, "ensure_identity", lambda *_args: None)


def test_export_replay_evidence_excludes_events_not_yet_visible(
    isolated_evidence: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Only evidence visible at `as_of` is ever included in the export."""
    del isolated_evidence
    visible = _record(_T0)
    future = _record(_T0 + timedelta(hours=1))
    monkeypatch.setattr(
        service,
        "_fetch_market_dataset_raw",
        lambda _request: SimpleNamespace(records=(visible, future)),
    )
    request = ReplayEvidenceRequest(
        source_id="mt5",
        symbols=("EURUSD",),
        data_kind="ticks",
        start=_T0,
        end=_T0 + timedelta(days=1),
        as_of=_T0,
        request_id=generate_id("req"),
    )

    response = export_replay_evidence(request)

    assert response.status == "success"
    assert response.data is not None
    assert response.data.event_count == 1
    assert response.data.events[0].available_at == _T0
    assert response.data.as_of == _T0
    assert response.data.symbols == ("EURUSD",)


def test_export_replay_evidence_is_empty_before_any_coverage(
    isolated_evidence: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A boundary before any coverage yields a genuinely empty export."""
    del isolated_evidence
    monkeypatch.setattr(
        service,
        "_fetch_market_dataset_raw",
        lambda _request: SimpleNamespace(records=(_record(_T0),)),
    )
    request = ReplayEvidenceRequest(
        source_id="mt5",
        symbols=("EURUSD",),
        data_kind="ticks",
        start=_T0,
        end=_T0 + timedelta(days=1),
        as_of=_T0 - timedelta(days=365),
        request_id=generate_id("req"),
    )

    response = export_replay_evidence(request)

    assert response.status == "success"
    assert response.data is not None
    assert response.data.event_count == 0
    assert response.data.events == ()
