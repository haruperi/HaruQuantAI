"""Phase 2.0 characterization tests for the brownfield Data service."""

import math
from datetime import UTC, datetime
from pathlib import Path

import pytest
from app.services.data import OFFICIAL_DATA_TOOL_NAMES, get_data, list_symbols
from app.services.data import __all__ as data_exports
from app.services.data.sources import get_source_adapter, update_circuit_breaker
from app.services.data.storage import load_local_dataset, save_market_data
from app.services.data.transforms import (
    align_multitimeframe_data,
    generate_synthetic_bars,
)
from app.services.data.errors import DataExternalServiceError as ExternalServiceError
from app.services.data.errors import DataValidationError as ValidationError


def test_phase20_public_exports_import_without_broker_credentials() -> None:
    """Verify public Data imports expose official tools without broker credentials."""
    assert (
        frozenset(
            (
                "get_data",
                "list_symbols",
                "get_market_hours",
                "get_feed_status",
            )
        )
        == OFFICIAL_DATA_TOOL_NAMES
    )
    assert set(OFFICIAL_DATA_TOOL_NAMES).issubset(set(data_exports))
    assert list_symbols(source="synthetic", request_id="phase20-import-safe")


def test_phase20_get_data_applies_limit_and_propagates_request_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify synthetic get_data limit handling and observable request ID plumbing."""
    captured_request_ids: list[str | None] = []

    def fake_execute_gateway_request(
        source: str,
        symbol: str,
        timeframe: str | None,
        start_time: datetime,
        end_time: datetime,
        data_kind: str,
        stale_data_behavior: str = "refresh_and_return",
        workflow_context: str = "research",
        request_id: str | None = None,
    ) -> list[dict[str, object]]:
        """Return deterministic records while capturing the request identifier."""
        del source, symbol, timeframe, start_time, end_time
        del data_kind, stale_data_behavior, workflow_context
        captured_request_ids.append(request_id)
        return [
            {"timestamp": f"2026-01-01T00:0{idx}:00Z", "close": float(idx)}
            for idx in range(5)
        ]

    monkeypatch.setattr(
        "app.services.data.gateway.execute_gateway_request",
        fake_execute_gateway_request,
    )

    records = get_data(
        symbol="EURUSD",
        start_time="2026-01-01T00:00:00Z",
        end_time="2026-01-01T01:00:00Z",
        data_kind="ohlcv",
        timeframe="M1",
        source="synthetic",
        limit=3,
        request_id="phase20-request",
    )

    assert len(records) == 3
    assert captured_request_ids == ["phase20-request"]


def test_phase20_get_data_rejects_unsupported_timeframe() -> None:
    """Verify get_data preserves validation for unsupported synthetic timeframes."""
    with pytest.raises(ValidationError):
        get_data(
            symbol="EURUSD",
            start_time="2026-01-01T00:00:00Z",
            end_time="2026-01-01T01:00:00Z",
            data_kind="ohlcv",
            timeframe="M999",
            source="synthetic",
            request_id="phase20-bad-timeframe",
        )


def test_phase20_local_parquet_round_trip_when_engine_available() -> None:
    """Verify local Parquet save/load behavior when a pandas engine is installed."""
    pytest.importorskip("pyarrow")
    target_path = Path("artifacts/data/phase20_roundtrip.parquet")
    records = [
        {
            "timestamp": "2026-01-01T00:00:00Z",
            "symbol": "EURUSD",
            "timeframe": "M1",
            "open": 1.1,
            "high": 1.2,
            "low": 1.0,
            "close": 1.15,
            "volume": 10.0,
            "source": "phase20",
        }
    ]

    try:
        result = save_market_data(
            records,
            str(target_path),
            "parquet",
            overwrite=True,
            request_id="phase20-parquet",
        )
        loaded = load_local_dataset(
            str(target_path),
            request_id="phase20-parquet",
        )
    finally:
        target_path.unlink(missing_ok=True)

    assert result["record_count"] == 1
    assert loaded == records


def test_phase20_broker_factories_remain_lazy_until_data_read(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify broker adapters do not instantiate clients during discovery calls."""
    adapter = get_source_adapter("mt5")
    update_circuit_breaker("mt5", "closed", 0)
    factory_calls = 0

    def failing_factory() -> object:
        """Raise if the broker client factory is invoked."""
        nonlocal factory_calls
        factory_calls += 1
        raise RuntimeError("broker credentials unavailable")

    monkeypatch.setattr(adapter, "_client_factory", failing_factory)

    assert adapter.list_symbols(request_id="phase20-lazy")
    assert adapter.get_symbol_metadata("EURUSD", request_id="phase20-lazy")["symbol"]
    assert factory_calls == 0

    with pytest.raises(ExternalServiceError):
        adapter.get_market_data(
            "EURUSD",
            "M1",
            datetime(2026, 1, 1, tzinfo=UTC),
            datetime(2026, 1, 1, 1, tzinfo=UTC),
            request_id="phase20-lazy",
        )
    assert factory_calls == 1


def test_phase20_synthetic_generation_and_alignment_are_deterministic() -> None:
    """Verify synthetic generation is seeded and alignment avoids lookahead."""
    first = generate_synthetic_bars(
        "EURUSD",
        "M5",
        "2026-01-01T00:00:00Z",
        2,
        1.1,
        0.0,
        0.01,
        seed=42,
        request_id="phase20-transform",
    )
    second = generate_synthetic_bars(
        "EURUSD",
        "M5",
        "2026-01-01T00:00:00Z",
        2,
        1.1,
        0.0,
        0.01,
        seed=42,
        request_id="phase20-transform",
    )

    aligned = align_multitimeframe_data(
        {"M5": first[:1]},
        ["2026-01-01T00:02:00Z", "2026-01-01T00:06:00Z"],
        request_id="phase20-transform",
    )

    assert first == second
    assert math.isnan(aligned["M5"][0]["close"])
    assert aligned["M5"][1]["close"] == first[0]["close"]
