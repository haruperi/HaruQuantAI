from app.host.response import ResponseMetadata, StandardResponse
from app.include.contracts import DataInfo
from app.workspace.data_manager.cli import (
    BasketsCLI,
    BrokersCLI,
    DataCLI,
    SessionsCLI,
    SymbolsCLI,
    format_basket_table,
    format_broker_table,
    format_data_dashboard,
    format_dataset_table,
    format_session_table,
    format_symbol_table,
)


def test_format_dataset_table_and_dashboard() -> None:
    mock_datasets = [
        DataInfo(
            id="ds_test",
            symbol="EURUSD",
            instrument="EURUSD",
            broker="dukascopy",
            broker_name="dukascopy",
            underlying="EURUSD",
            timeframe="M1",
            timezone="UTC",
            date_from="2025-01-01",
            date_to="2025-01-02",
            total_days=1,
            total_records=2,
            bars=2,
            rows=2,
            source="dukascopy",
            connection="dukascopy",
            data_type="Forex",
            category="Forex",
            path="data/test",
            bar_type="start",
        )
    ]
    overview = {"datasets_count": 1, "total_bars": 2}

    table = format_dataset_table(mock_datasets)
    assert "EURUSD" in table
    assert "=== Saved Datasets Catalog (1 items) ===" in table

    dashboard = format_data_dashboard(overview, mock_datasets)
    assert "=== Data Manager: Live Database Overview ===" in dashboard
    assert "EURUSD" in dashboard

    cli_dashboard = DataCLI.format_data_dashboard(overview, mock_datasets)
    assert cli_dashboard == dashboard


def test_format_dataset_table_with_standard_response() -> None:
    resp_overview = StandardResponse.success(
        message="ok",
        metadata=ResponseMetadata(operation="overview", duration_ms=1.0),
        data={"datasets_count": 1, "total_bars": 2},
    )
    resp_list = StandardResponse.success(
        message="ok",
        metadata=ResponseMetadata(operation="list", duration_ms=1.0),
        data=[
            {
                "symbol": "EURUSD",
                "instrument": "EURUSD",
                "broker": "dukascopy",
                "underlying": "EURUSD",
                "timeframe": "M1",
                "timezone": "UTC",
                "date_from": "2025-01-01",
                "date_to": "2025-01-02",
                "total_days": 1,
                "total_records": 2,
                "source": "dukascopy",
                "data_type": "Forex",
            }
        ],
    )

    dashboard = format_data_dashboard(resp_overview, resp_list)
    assert "=== Data Manager: Live Database Overview ===" in dashboard
    assert "EURUSD" in dashboard
    assert "Total Datasets:       1" in dashboard


def test_format_symbol_table() -> None:
    sample_symbols = [
        {
            "symbol": "EURUSD",
            "description": "Euro vs US Dollar",
            "broker_name": "Default",
            "contract": {"point_value": 100000.0},
            "price": {"tick_size": 1e-05, "tick_step": 1e-05},
            "spread": {"default": 0.0, "slippage": 0.0},
            "swap": {"long": -7.21, "short": 1.53},
            "commissions": {"rules": [{"tiers": [{"value": 3.5, "currency": "USD"}]}]},
            "data_type": "Forex\\Majors",
            "order_size": {"multiplier": 1.0, "step": 0.0},
        }
    ]

    table = format_symbol_table(sample_symbols)
    assert "=== Symbols Catalog (1 items) ===" in table
    assert "EURUSD" in table
    assert "Euro vs US Dollar" in table
    assert "100,000" in table
    assert "3.5 USD" in table
    assert "-7.21 / 1.53" in table
    assert "Forex\\Majors" in table
    assert "1 / 0" in table

    cli_table = SymbolsCLI.format_symbol_table(sample_symbols)
    assert cli_table == table

    data_cli_table = DataCLI.format_symbol_table(sample_symbols)
    assert data_cli_table == table


def test_format_session_table() -> None:
    sample_sessions = [
        {
            "name": "24/5 Forex",
            "broker_name": "Default",
            "description": "Standard 24/5 Foreign Exchange trading hours",
            "timezone": "UTC",
            "windows": [
                {
                    "day_of_week": 0,
                    "open_time": "00:00:00",
                    "close_time": "23:59:59",
                },
                {
                    "day_of_week": 1,
                    "open_time": "00:00:00",
                    "close_time": "23:59:59",
                },
                {
                    "day_of_week": 2,
                    "open_time": "00:00:00",
                    "close_time": "23:59:59",
                },
                {
                    "day_of_week": 3,
                    "open_time": "00:00:00",
                    "close_time": "23:59:59",
                },
                {
                    "day_of_week": 4,
                    "open_time": "00:00:00",
                    "close_time": "23:59:59",
                },
            ],
            "holidays": [],
        },
        {
            "name": "CME Futures",
            "broker_name": "[[RoboForex]]",
            "description": "Chicago Mercantile Exchange",
            "timezone": "America/Chicago",
            "windows": [],
            "holidays": [{"date_str": "2026-12-25", "description": "Christmas Day"}],
        },
    ]

    table = format_session_table(sample_sessions)
    assert "=== Trading Sessions Catalog (2 items) ===" in table
    assert "24/5 Forex" in table
    assert "SQ default" in table
    assert "UTC" in table
    assert "Mon-Fri 00:00-23:59 (5d)" in table
    assert "CME Futures" in table
    assert "[[RoboForex]]" in table
    assert "Christmas Day" in table

    cli_table = SessionsCLI.format_session_table(sample_sessions)
    assert cli_table == table

    data_cli_table = DataCLI.format_session_table(sample_sessions)
    assert data_cli_table == table


def test_format_basket_table() -> None:
    sample_baskets = [
        {
            "name": "[[Dow Jones Industrial Average]]",
            "active_count": 29,
            "stocks_count": 69,
            "description": "",
            "symbols_count": 69,
            "downloaded_count": 69,
            "ready": True,
            "date_from": "01.02.1970",
            "date_to": "08.05.2025",
        },
        {
            "name": "[[Nasdaq Biotechnology]]",
            "active_count": 205,
            "stocks_count": 785,
            "description": "",
            "symbols_count": 38,
            "downloaded_count": 38,
            "ready": "No, Update data in group",
            "date_from": "21.05.2001",
            "date_to": "08.05.2025",
        },
        {
            "name": "[GLD D]",
            "active_count": 0,
            "stocks_count": 1,
            "description": "GLD D;01.01.2020;01.05.2025",
            "symbols_count": 1,
            "downloaded_count": 1,
            "ready": True,
            "date_from": "01.01.2020",
            "date_to": "01.05.2025",
        },
    ]

    table = format_basket_table(sample_baskets)
    assert "=== Stock Groups / Baskets Catalog (3 items) ===" in table
    assert "[[Dow Jones Industrial Average]]" in table
    assert "29 / 69" in table
    assert "69 / 69" in table
    assert "Yes" in table
    assert "01.02.1970" in table
    assert "08.05.2025" in table
    assert "[[Nasdaq Biotechnology]]" in table
    assert "205 / 785" in table
    assert "38 / 785" in table
    assert "No, Update.." in table
    assert "[GLD D]" in table
    assert "0 / 1" in table

    cli_table = BasketsCLI.format_basket_table(sample_baskets)
    assert cli_table == table

    data_cli_table = DataCLI.format_basket_table(sample_baskets)
    assert data_cli_table == table


def test_format_broker_table() -> None:
    sample_brokers = [
        {
            "name": "[[Darwinex Zero]]",
            "description": "Darwinex Zero",
            "postfix": "",
            "server_timezone": "UTC",
            "customized_stocks": 812,
            "customized_instruments": 0,
            "customized_sessions": 0,
        },
        {
            "name": "[[Darwinex]]",
            "description": "Darwinex CFDs",
            "postfix": "_darwinex",
            "server_timezone": "EETUS",
            "customized_stocks": 0,
            "customized_instruments": 158,
            "customized_sessions": 158,
        },
        {
            "name": "[[XTB]]",
            "description": "XTB broker",
            "postfix": "_xtb",
            "server_timezone": "UTC",
            "customized_stocks": 1334,
            "customized_instruments": 0,
            "customized_sessions": 0,
        },
    ]

    table = format_broker_table(sample_brokers)
    assert "=== Broker Profiles Catalog (3 items) ===" in table
    assert "[[Darwinex Zero]]" in table
    assert "Darwinex Zero" in table
    assert "812" in table
    assert "[[Darwinex]]" in table
    assert "_darwinex" in table
    assert "EETUS" in table
    assert "158" in table
    assert "[[XTB]]" in table
    assert "_xtb" in table
    assert "1334" in table

    cli_table = BrokersCLI.format_broker_table(sample_brokers)
    assert cli_table == table

    data_cli_table = DataCLI.format_broker_table(sample_brokers)
    assert data_cli_table == table
