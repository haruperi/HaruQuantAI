"""Unit isolation tests for Indicators genuine-MT5 usage support."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from tests.indicators.usage import _support as usage_support


def test_usage_market_request_is_mt5_h1_for_exactly_100_days(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The unit fake verifies request shape without initializing MT5."""
    fixed_end = datetime(2026, 8, 10, 12, tzinfo=UTC)
    captured: dict[str, object] = {}
    dataset = object()

    class _FixedDateTime(datetime):
        @classmethod
        def now(cls, tz: object = None) -> datetime:
            del cls, tz
            return fixed_end

    def _get_market_data(**kwargs: object) -> object:
        captured.update(kwargs)
        return object()

    monkeypatch.setenv("ENVIRONMENT", "dev")
    monkeypatch.setattr(usage_support, "datetime", _FixedDateTime)
    monkeypatch.setattr(usage_support, "get_market_data", _get_market_data)
    monkeypatch.setattr(
        usage_support,
        "unwrap_market_data_response",
        lambda _response: dataset,
    )
    monkeypatch.setattr(
        usage_support,
        "_resolve_mt5_usage_config",
        lambda _request_id: object(),
    )
    monkeypatch.setattr(usage_support, "_MARKET_DATASET_CACHE", {})

    assert usage_support.get_mt5_usage_dataset() is dataset
    assert captured == {
        "source_id": "mt5",
        "symbol": "EURUSD",
        "timeframe": "H1",
        "start": fixed_end - timedelta(days=100),
        "end": fixed_end,
    }


def test_missing_persisted_mt5_configuration_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Missing database-backed configuration never creates a fallback."""
    monkeypatch.setenv("ENVIRONMENT", "dev")

    def _missing(request_id: str) -> object:
        del request_id
        raise ValueError("credential unavailable")

    monkeypatch.setattr(usage_support, "_build_persisted_mt5_config", _missing)

    with pytest.raises(SystemExit) as raised:
        usage_support._resolve_mt5_usage_config("req-unit")

    assert raised.value.code == 3


def test_usage_support_contains_no_configuration_or_credential_writes() -> None:
    """The usage helper cannot enable providers or store credentials."""
    source = Path(usage_support.__file__).read_text(encoding="utf-8")
    forbidden = {
        "store_system_credential",
        "update_system_settings",
        "run_api_migrations",
        "run_data_migrations",
        "MetaQuotes-Demo",
        '"login": "123456"',
    }
    assert not {token for token in forbidden if token in source}


def test_non_dev_genuine_usage_fails_before_configuration_resolution(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Genuine usage rejects a non-development process before credential reads."""
    called = False

    def _unexpected(request_id: str) -> object:
        nonlocal called
        del request_id
        called = True
        return object()

    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setattr(usage_support, "_build_persisted_mt5_config", _unexpected)

    with pytest.raises(SystemExit) as raised:
        usage_support._resolve_mt5_usage_config("req-unit")

    assert raised.value.code == 3
    assert called is False
