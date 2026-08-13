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
    market_request: dict[str, object] = {}

    def _build_market_request(**values: object) -> object:
        market_request.update(values)
        return SimpleNamespace(**values)

    monkeypatch.setattr(
        orchestration,
        "build_market_data_request",
        _build_market_request,
    )
    metadata_calls = 0
    market_data_calls = 0

    def _metadata(_request: object) -> object:
        nonlocal metadata_calls
        metadata_calls += 1
        return SimpleNamespace(
            status="success", data=SimpleNamespace(digits=5, point=0.00001)
        )

    def _market_data(_request: object) -> object:
        nonlocal market_data_calls
        market_data_calls += 1
        return SimpleNamespace(status="success", data=dataset)

    monkeypatch.setattr(
        orchestration,
        "get_symbol_metadata",
        _metadata,
    )
    monkeypatch.setattr(
        orchestration,
        "get_market_data",
        _market_data,
    )
    calls: list[tuple[object, int, float, float | None]] = []

    def _project(
        evidence: object, *, digits: int, point: float, last_price: float | None
    ) -> dict[str, float | None]:
        calls.append((evidence, digits, point, last_price))
        return {"change": None if last_price is None else last_price - 1.0}

    monkeypatch.setattr(orchestration, "project_market_overlay", _project)

    first = orchestration.build_technical_evidence(
        "mt5", "EURUSD", last_price=1.1, request_id="req-1"
    )
    second = orchestration.build_technical_evidence(
        "mt5", "EURUSD", last_price=1.2, request_id="req-2"
    )

    assert first["change"] == pytest.approx(0.1)
    assert second["change"] == pytest.approx(0.2)
    assert calls == [(dataset, 5, 0.00001, 1.1), (dataset, 5, 0.00001, 1.2)]
    assert metadata_calls == 1
    assert market_data_calls == 1
    assert market_request["timeframe"] == "D1"
    assert market_request["limit"] == 40
    assert market_request["use_cache"] is False
    assert "start" not in market_request
    assert "end" not in market_request


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


def test_technical_evidence_retries_short_history_and_caches_only_warmup(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A transient one-bar MT5 response is retried and never cached."""
    orchestration._reset_cache_for_tests()
    short_dataset = SimpleNamespace(records=(object(),))
    sufficient_dataset = SimpleNamespace(records=(object(),) * 12)
    requests: list[object] = []
    market_data_calls = 0

    monkeypatch.setattr(
        orchestration,
        "build_symbol_metadata_request",
        SimpleNamespace,
    )

    def _build_market_request(**values: object) -> object:
        request = SimpleNamespace(**values)
        requests.append(request)
        return request

    def _market_data(_request: object) -> object:
        nonlocal market_data_calls
        market_data_calls += 1
        dataset = short_dataset if market_data_calls == 1 else sufficient_dataset
        return SimpleNamespace(status="success", data=dataset)

    monkeypatch.setattr(
        orchestration,
        "build_market_data_request",
        _build_market_request,
    )
    monkeypatch.setattr(
        orchestration,
        "get_symbol_metadata",
        lambda _request: SimpleNamespace(
            status="success", data=SimpleNamespace(digits=5, point=0.00001)
        ),
    )
    monkeypatch.setattr(orchestration, "get_market_data", _market_data)
    monkeypatch.setattr(
        orchestration,
        "project_market_overlay",
        lambda evidence, **_values: {
            "volatility": 0.1 if evidence is sufficient_dataset else None
        },
    )

    first = orchestration.build_technical_evidence(
        "mt5", "AUDCAD", last_price=1.0, request_id="req-1"
    )
    second = orchestration.build_technical_evidence(
        "mt5", "AUDCAD", last_price=1.1, request_id="req-2"
    )

    assert first == {"volatility": 0.1}
    assert second == {"volatility": 0.1}
    assert market_data_calls == 2
    assert [request.use_cache for request in requests] == [False, False]


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
