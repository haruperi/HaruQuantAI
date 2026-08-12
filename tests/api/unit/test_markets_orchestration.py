"""Unit tests for markets technical-evidence orchestration."""

from types import SimpleNamespace

import pytest
from app.services.api.workstation.markets import orchestration


def test_technical_evidence_fetches_then_delegates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The API fetches evidence and delegates all calculations to Indicators."""
    orchestration._reset_cache_for_tests()
    dataset = SimpleNamespace(records=(object(),) * 12)
    monkeypatch.setattr(
        orchestration,
        "build_symbol_metadata_request",
        SimpleNamespace,
    )
    monkeypatch.setattr(
        orchestration,
        "build_market_data_request",
        SimpleNamespace,
    )
    monkeypatch.setattr(
        orchestration,
        "get_symbol_metadata",
        lambda _request: SimpleNamespace(
            status="success", data=SimpleNamespace(digits=5, point=0.00001)
        ),
    )
    monkeypatch.setattr(
        orchestration,
        "get_market_data",
        lambda _request: SimpleNamespace(status="success", data=dataset),
    )
    calls: list[tuple[object, int, float, float | None]] = []

    def _project(
        evidence: object, *, digits: int, point: float, last_price: float | None
    ) -> dict[str, float | None]:
        calls.append((evidence, digits, point, last_price))
        return {"volatility": 12.5}

    monkeypatch.setattr(orchestration, "project_market_overlay", _project)

    first = orchestration.build_technical_evidence(
        "mt5", "EURUSD", last_price=1.1, request_id="req-1"
    )
    second = orchestration.build_technical_evidence(
        "mt5", "EURUSD", last_price=1.1, request_id="req-2"
    )

    assert first == {"volatility": 12.5}
    assert second == first
    assert calls == [(dataset, 5, 0.00001, 1.1)]


def test_technical_evidence_does_not_invent_missing_metadata(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Missing precision evidence produces no projection."""
    orchestration._reset_cache_for_tests()
    monkeypatch.setattr(
        orchestration,
        "build_symbol_metadata_request",
        SimpleNamespace,
    )
    monkeypatch.setattr(
        orchestration,
        "build_market_data_request",
        SimpleNamespace,
    )
    monkeypatch.setattr(
        orchestration,
        "get_symbol_metadata",
        lambda _request: SimpleNamespace(status="success", data=SimpleNamespace()),
    )
    monkeypatch.setattr(
        orchestration,
        "get_market_data",
        lambda _request: SimpleNamespace(status="success", data=object()),
    )

    assert (
        orchestration.build_technical_evidence(
            "mt5", "EURUSD", last_price=None, request_id="req-1"
        )
        == {}
    )


def test_runtime_source_resolution_fails_closed_without_configuration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Missing broker configuration never defaults to MT5."""
    monkeypatch.setattr(
        orchestration,
        "get_system_settings",
        lambda **_values: SimpleNamespace(settings={}),
    )

    with pytest.raises(RuntimeError, match="RUNTIME_BROKER_UNAVAILABLE"):
        orchestration.resolve_runtime_source_id(request_id="req-1")
