"""Unit tests for tools.data.mt5."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

import pandas as pd
import pytest

from tools.data import mt5 as mt5_module


@dataclass
class FakeSymbol:
    name: str
    description: str = ""
    path: str = "Forex\\Majors"


class FakeMT5Module:
    TIMEFRAME_M1 = 1
    TIMEFRAME_H1 = 60
    TIMEFRAME_D1 = 1440

    def __init__(self, *, initialize_ok: bool = True, login_ok: bool = True) -> None:
        self.initialize_ok = initialize_ok
        self.login_ok = login_ok
        self.shutdown_called = False
        self.login_kwargs: dict[str, Any] = {}

    def initialize(self, **kwargs: Any) -> bool:
        return self.initialize_ok

    def login(self, **kwargs: Any) -> bool:
        self.login_kwargs = kwargs
        return self.login_ok

    def shutdown(self) -> bool:
        self.shutdown_called = True
        return True

    def last_error(self) -> tuple[int, str]:
        return (1, "fake error")

    def symbols_get(self) -> list[FakeSymbol]:
        return [FakeSymbol("EURUSD", "Euro vs US Dollar"), FakeSymbol("GBPUSD")]

    def copy_rates_from_pos(
        self, symbol: str, timeframe: int, start_pos: int, count: int
    ):
        return [
            {
                "time": 1_700_000_000,
                "open": 1.1,
                "high": 1.2,
                "low": 1.0,
                "close": 1.15,
                "tick_volume": 100,
                "spread": 10,
            }
        ]

    def copy_rates_from(
        self, symbol: str, timeframe: int, date_from: datetime, count: int
    ):
        return self.copy_rates_from_pos(symbol, timeframe, 0, count)

    def copy_rates_range(
        self, symbol: str, timeframe: int, date_from: datetime, date_to: datetime
    ):
        return self.copy_rates_from_pos(symbol, timeframe, 0, 1)


@pytest.fixture(autouse=True)
def clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(mt5_module, "_load_dotenv", lambda *args, **kwargs: False)
    for key in (
        mt5_module.ENV_MT5_ENABLED,
        mt5_module.ENV_MT5_LOGIN,
        mt5_module.ENV_MT5_PASSWORD,
        mt5_module.ENV_MT5_SERVER,
        mt5_module.ENV_MT5_TERMINAL_PATH,
        mt5_module.ENV_MT5_ENVIRONMENT,
    ):
        monkeypatch.delenv(key, raising=False)


@pytest.fixture
def valid_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(mt5_module.ENV_MT5_ENABLED, "true")
    monkeypatch.setenv(mt5_module.ENV_MT5_LOGIN, "61528639")
    monkeypatch.setenv(mt5_module.ENV_MT5_PASSWORD, "secret")
    monkeypatch.setenv(mt5_module.ENV_MT5_SERVER, "Pepperstone-Demo")
    monkeypatch.setenv(mt5_module.ENV_MT5_TERMINAL_PATH, "")
    monkeypatch.setenv(mt5_module.ENV_MT5_ENVIRONMENT, "demo")


@pytest.fixture
def fake_api(monkeypatch: pytest.MonkeyPatch) -> FakeMT5Module:
    fake = FakeMT5Module()
    monkeypatch.setattr(mt5_module, "_MT5_API", mt5_module.MT5Api(fake))
    return fake


def assert_standard_schema(result: dict[str, Any]) -> None:
    assert set(result) == {"status", "message", "data", "error", "metadata"}
    assert result["status"] in {"success", "error"}
    metadata = result["metadata"]
    assert metadata["tool_category"] == "data"
    assert metadata["tool_risk_level"] == "low"
    assert metadata["read_only"] is True
    assert metadata["writes_file"] is False
    assert metadata["modifies_database"] is False
    assert metadata["places_trade"] is False
    assert metadata["requires_network"] is True
    assert "execution_ms" in metadata


def test_load_mt5_credentials_from_env_success(valid_env: None) -> None:
    credentials = mt5_module._load_mt5_credentials_from_env()
    assert credentials.login == 61528639
    assert credentials.password == "secret"
    assert credentials.server == "Pepperstone-Demo"
    assert credentials.environment == "demo"
    assert credentials.masked_login == "***8639"


@pytest.mark.parametrize(
    ("env_name", "expected"),
    [
        (mt5_module.ENV_MT5_ENABLED, "MT5_ENABLED"),
        (mt5_module.ENV_MT5_LOGIN, "MT5_LOGIN"),
        (mt5_module.ENV_MT5_PASSWORD, "MT5_PASSWORD"),
        (mt5_module.ENV_MT5_SERVER, "MT5_SERVER"),
    ],
)
def test_load_mt5_credentials_from_env_missing_required(
    valid_env: None,
    monkeypatch: pytest.MonkeyPatch,
    env_name: str,
    expected: str,
) -> None:
    monkeypatch.delenv(env_name, raising=False)
    with pytest.raises(ValueError, match=expected):
        mt5_module._load_mt5_credentials_from_env()


def test_load_mt5_credentials_rejects_bad_login_and_environment(
    valid_env: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(mt5_module.ENV_MT5_LOGIN, "not-an-int")
    with pytest.raises(ValueError, match="integer"):
        mt5_module._load_mt5_credentials_from_env()

    monkeypatch.setenv(mt5_module.ENV_MT5_LOGIN, "-1")
    with pytest.raises(ValueError, match="positive"):
        mt5_module._load_mt5_credentials_from_env()

    monkeypatch.setenv(mt5_module.ENV_MT5_LOGIN, "61528639")
    monkeypatch.setenv(mt5_module.ENV_MT5_ENVIRONMENT, "sandbox")
    with pytest.raises(ValueError, match="MT5_ENVIRONMENT"):
        mt5_module._load_mt5_credentials_from_env()


def test_mt5_api_unavailable_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(mt5_module, "_mt5_module", None)
    api = mt5_module.MT5Api(None)

    assert api.is_available() is False
    assert api.initialize() is False
    assert api.login() is False
    assert api.last_error() is None
    with pytest.raises(AttributeError):
        api.symbols_get()


def test_mt5_client_connect_rejects_disabled_credentials() -> None:
    client = mt5_module.MT5Client(api=mt5_module.MT5Api(FakeMT5Module()))
    credentials = mt5_module.MT5Credentials(
        enabled=False,
        login=1,
        password="secret",
        server="Demo",
    )

    assert client.connect(credentials) is False
    assert client.connection_state == mt5_module.ConnectionState.FAILED


def test_mt5_client_connect_handles_login_failure() -> None:
    fake = FakeMT5Module(login_ok=False)
    client = mt5_module.MT5Client(api=mt5_module.MT5Api(fake))
    credentials = mt5_module.MT5Credentials(
        enabled=True,
        login=61528639,
        password="secret",
        server="Demo",
        terminal_path="terminal64.exe",
    )

    assert client.connect(credentials) is False
    assert fake.login_kwargs["login"] == 61528639
    assert client.connection_state == mt5_module.ConnectionState.FAILED


def test_mt5_client_lists_empty_when_broker_returns_none() -> None:
    class EmptySymbolsMT5(FakeMT5Module):
        def symbols_get(self) -> None:
            return None

    client = mt5_module.MT5Client(api=mt5_module.MT5Api(EmptySymbolsMT5()))

    assert client.list_symbols() == []
    assert client.list_symbol_details() == []


def test_mt5_client_symbol_details_skips_empty_names() -> None:
    class MixedSymbolsMT5(FakeMT5Module):
        def symbols_get(self) -> list[FakeSymbol]:
            return [FakeSymbol("", ""), FakeSymbol("XAUUSD", "", "Metals")]

    client = mt5_module.MT5Client(api=mt5_module.MT5Api(MixedSymbolsMT5()))

    assert client.list_symbol_details() == [
        {
            "symbol": "XAUUSD",
            "name": "XAUUSD",
            "category": "Metals",
            "path": "Metals",
        }
    ]


def test_mt5_client_get_bars_error_paths() -> None:
    client = mt5_module.MT5Client(api=mt5_module.MT5Api(FakeMT5Module()))

    with pytest.raises(RuntimeError, match="not connected"):
        client.get_bars(symbol="EURUSD", timeframe="H1")

    client.connection_state = mt5_module.ConnectionState.CONNECTED
    with pytest.raises(ValueError, match="TIMEFRAME_BAD"):
        client.get_bars(symbol="EURUSD", timeframe="BAD")


def test_mt5_client_get_bars_date_modes(valid_env: None) -> None:
    client = mt5_module.MT5Client(api=mt5_module.MT5Api(FakeMT5Module()))
    assert client.connect(mt5_module._load_mt5_credentials_from_env()) is True

    frame_from = client.get_bars(
        symbol="EURUSD",
        timeframe="H1",
        count=1,
        date_from=datetime(2026, 1, 1),
    )
    frame_range = client.get_bars(
        symbol="EURUSD",
        timeframe="H1",
        count=1,
        date_from=datetime(2026, 1, 1),
        date_to=datetime(2026, 1, 2),
    )

    assert len(frame_from) == 1
    assert len(frame_range) == 1


def test_mt5_client_get_bars_none_rates_raises() -> None:
    class NoneRatesMT5(FakeMT5Module):
        def copy_rates_from_pos(
            self, symbol: str, timeframe: int, start_pos: int, count: int
        ) -> None:
            return None

    client = mt5_module.MT5Client(api=mt5_module.MT5Api(NoneRatesMT5()))
    client.connection_state = mt5_module.ConnectionState.CONNECTED

    with pytest.raises(RuntimeError, match="no rates"):
        client.get_bars(symbol="EURUSD", timeframe="H1", count=1)


def test_normalize_rates_frame_rejects_missing_columns() -> None:
    with pytest.raises(ValueError, match="time"):
        mt5_module._normalize_rates_frame(pd.DataFrame({"open": [1.0]}))

    with pytest.raises(ValueError, match="missing required"):
        mt5_module._normalize_rates_frame(
            pd.DataFrame({"time": [1_700_000_000], "open": [1.0]})
        )


def test_context_manager_shutdown(valid_env: None) -> None:
    fake = FakeMT5Module()
    client = mt5_module.MT5Client(api=mt5_module.MT5Api(fake))

    with client as managed:
        assert managed is client

    assert fake.shutdown_called is True


def test_connection_check_success(valid_env: None, fake_api: FakeMT5Module) -> None:
    result = mt5_module.mt5_connection_check(request_id="test-001")
    assert_standard_schema(result)
    assert result["status"] == "success"
    assert result["data"]["connected"] is True
    assert result["data"]["login"] == "***8639"
    assert "secret" not in str(result)


def test_connection_check_broker_unavailable(
    valid_env: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = FakeMT5Module(initialize_ok=False)
    monkeypatch.setattr(mt5_module, "_MT5_API", mt5_module.MT5Api(fake))
    result = mt5_module.mt5_connection_check(request_id="test-002")
    assert_standard_schema(result)
    assert result["status"] == "error"
    assert result["error"]["code"] == "BROKER_UNAVAILABLE"


def test_list_symbols_success(valid_env: None, fake_api: FakeMT5Module) -> None:
    result = mt5_module.mt5_data_list_symbols(pattern="EUR*", request_id="test-003")
    assert_standard_schema(result)
    assert result["status"] == "success"
    assert result["data"]["symbols"] == ["EURUSD"]


def test_list_symbols_invalid_pattern() -> None:
    result = mt5_module.mt5_data_list_symbols(pattern=123, request_id="test-004")
    assert_standard_schema(result)
    assert result["status"] == "error"
    assert result["error"]["code"] == "INVALID_INPUT"


def test_get_bars_success(valid_env: None, fake_api: FakeMT5Module) -> None:
    result = mt5_module.mt5_data_get_bars(symbol="EURUSD", timeframe="H1", count=1)
    assert_standard_schema(result)
    assert result["status"] == "success"
    assert result["data"]["source"] == "mt5"
    assert result["data"]["rows"] == 1
    assert {"open", "high", "low", "close"}.issubset(set(result["data"]["columns"]))
    assert "secret" not in str(result)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"symbol": "", "timeframe": "H1", "count": 1},
        {"symbol": "EURUSD", "timeframe": "BAD", "count": 1},
        {"symbol": "EURUSD", "timeframe": "H1", "count": 0},
        {"symbol": "EURUSD", "timeframe": "H1", "count": 1, "start_pos": -1},
    ],
)
def test_get_bars_invalid_input(kwargs: dict[str, Any]) -> None:
    result = mt5_module.mt5_data_get_bars(**kwargs)
    assert_standard_schema(result)
    assert result["status"] == "error"
    assert result["error"]["code"] == "INVALID_INPUT"


def test_get_bars_empty_result_returns_data_not_found(
    valid_env: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class EmptyRatesMT5(FakeMT5Module):
        def copy_rates_from_pos(
            self, symbol: str, timeframe: int, start_pos: int, count: int
        ):
            return []

    monkeypatch.setattr(mt5_module, "_MT5_API", mt5_module.MT5Api(EmptyRatesMT5()))
    result = mt5_module.mt5_data_get_bars(symbol="EURUSD", timeframe="H1", count=1)
    assert_standard_schema(result)
    assert result["status"] == "error"
    assert result["error"]["code"] == "DATA_NOT_FOUND"


def test_list_symbol_details_success(valid_env: None, fake_api: FakeMT5Module) -> None:
    result = mt5_module.mt5_data_list_symbol_details(request_id="test-005")
    assert_standard_schema(result)
    assert result["status"] == "success"
    assert result["data"]["count"] == 2
    assert result["data"]["symbols"][0]["symbol"] == "EURUSD"


def test_official_tools_never_return_none(
    valid_env: None, fake_api: FakeMT5Module
) -> None:
    assert mt5_module.mt5_connection_check() is not None
    assert mt5_module.mt5_data_list_symbols() is not None
    assert mt5_module.mt5_data_get_bars(symbol="EURUSD", timeframe="H1") is not None
    assert mt5_module.mt5_data_list_symbol_details() is not None
