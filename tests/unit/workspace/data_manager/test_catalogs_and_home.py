"""Unit tests for Data Manager catalogs, home dashboard, logs, and help."""

from __future__ import annotations

import runpy
from datetime import UTC, datetime
from pathlib import Path

import pytest
from app.host.persistence.create import create_schema
from app.host.persistence.read import resolve_connection
from app.workspace.data_manager import (
    baskets,
    broker,
    sessions,
)
from app.workspace.data_manager import (
    help as help_mod,
)
from app.workspace.data_manager import (
    log as log_mod,
)
from app.workspace.data_manager.baskets import BasketsCatalogService
from app.workspace.data_manager.broker import BrokerProfilesService
from app.workspace.data_manager.data import DataInfo, DataManagerDataService
from app.workspace.data_manager.help import DataManagerHelpService
from app.workspace.data_manager.home import (
    Home,
    HomeCLI,
)
from app.workspace.data_manager.instruments import (
    Instruments,
    InstrumentsCLI,
)
from app.workspace.data_manager.log import DataManagerLogService
from app.workspace.data_manager.sessions import (
    SessionsCatalogService,
    SessionWindow,
    TradingHoliday,
)


@pytest.fixture
def test_db_path(tmp_path: Path) -> Path:
    """Fixture providing initialized SQLite database file path."""
    db_file = tmp_path / "test_datamgr.db"
    with resolve_connection(db_file) as conn:
        create_schema(conn)
    return db_file


# ============================================================================
# 1. Home Service Tests
# ============================================================================


@pytest.mark.filterwarnings("ignore::RuntimeWarning")
def test_home_service_overview_and_links(
    test_db_path: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Test Home dashboard metrics, document links, and storage audit."""
    monkeypatch.setattr("app.host.persistence.create.DEFAULT_DB_PATH", test_db_path)
    data_svc = DataManagerDataService(db_path=test_db_path, data_dir=tmp_path / "data")
    inst_svc = Instruments(db_path=test_db_path)
    inst_svc.ensure_default_instruments()
    sess_svc = SessionsCatalogService(db_path=test_db_path)
    sess_svc.ensure_default_sessions()

    # Import sample dataset with 100 explicit bars
    sample_csv = "timestamp,open,high,low,close,volume,spread\n" + "\n".join(
        f"2026-01-01 {i // 60:02d}:{i % 60:02d}:00,1.1000,1.1005,1.0995,1.1002,150,1"
        for i in range(100)
    )
    data_svc.import_dataset(
        {
            "symbol": "EURUSD",
            "timeframe": "M1",
            "source": "file",
            "csv_content": sample_csv,
        }
    )

    home_svc = Home(
        active_providers_getter=lambda: 2,
    )
    overview = home_svc.get_overview()
    assert isinstance(overview, dict)
    assert overview["datasets_count"] >= 1
    assert overview["instruments_count"] >= 7
    assert overview["sessions_count"] >= 4
    assert overview["active_providers_count"] == 2
    assert overview["total_bars"] >= 100
    assert overview["storage_bytes"] == 0
    assert overview["parquet_files_count"] == 0

    saved_datasets = home_svc.get_saved_datasets()
    assert len(saved_datasets) >= 1
    assert isinstance(saved_datasets[0], DataInfo)
    assert saved_datasets[0].symbol == "EURUSD"
    assert saved_datasets[0].total_records == 100
    assert saved_datasets[0].data_type == "Forex"
    assert saved_datasets[0].to_dict()["symbol"] == "EURUSD"

    rendered_dashboard = HomeCLI.format_home_dashboard(overview, saved_datasets)
    assert "Live Database Overview" in rendered_dashboard
    assert "EURUSD" in rendered_dashboard

    table_text = HomeCLI.format_dataset_table(saved_datasets)
    assert "Saved Datasets Catalog" in table_text
    assert "EURUSD" in table_text

    # Test execution under __main__ with isolated test database
    runpy.run_module("app.workspace.data_manager.home", run_name="__main__")
    captured = capsys.readouterr()
    assert "Live Database Overview" in captured.out


# ============================================================================
# 2. InstrumentsCatalogService Tests
# ============================================================================


@pytest.mark.filterwarnings("ignore::RuntimeWarning")
def test_instruments_service_lifecycle(test_db_path: Path) -> None:
    """Test instrument specifications, rounding, CRUD, aliases, and XML transfer."""
    log_svc = DataManagerLogService(db_path=test_db_path)
    service = Instruments(db_path=test_db_path, log_service=log_svc)

    seeded = service.ensure_default_instruments()
    assert seeded >= 7
    assert service.ensure_default_instruments() == 0

    eur = service.get_instrument("EURUSD")
    assert eur is not None
    assert eur.decimals == 5
    assert eur.round_to_tick_size(1.085427) == 1.08543
    info = eur
    assert info.name == "EURUSD"
    assert info.digits == 5

    # Filtered listing
    forex_list = service.list_instruments(data_type="Forex")
    assert len(forex_list) >= 3
    searched = service.list_instruments(search="Dollar")
    assert len(searched) >= 2

    # Update
    updated = service.update_instrument("EURUSD", {"default_spread": 2.0})
    assert updated.default_spread == 2.0

    # Clone
    cloned = service.clone_instrument("EURUSD", "EURUSD_VIP", broker_id=2)
    assert cloned.symbol == "EURUSD_VIP"
    assert cloned.broker_id == 2

    # Mass edit
    edited = service.mass_edit_instruments(["EURUSD_VIP"], {"min_volume": 0.1})
    assert edited == 1
    reloaded = service.get_instrument("EURUSD_VIP")
    assert reloaded is not None and reloaded.min_volume == 0.1

    # Mass delete
    del_res = service.mass_delete_instruments(["EURUSD_VIP"])
    assert del_res["deleted_count"] == 1
    assert service.get_instrument("EURUSD_VIP") is None

    # Symbol aliases
    alias = service.save_alias("EUR.USD", "EURUSD", "Broker symbol format")
    assert alias.alias == "EUR.USD"
    aliases = service.list_aliases()
    assert any(a.alias == "EUR.USD" for a in aliases)
    assert service.delete_alias("EUR.USD") is True
    assert service.delete_alias("EUR.USD") is False

    # XML export and import
    xml_data = service.export_xml(["EURUSD", "GBPUSD"])
    assert "<Instruments>" in xml_data
    import_res = service.import_xml(xml_data, conflict_policy="overwrite_all")
    assert import_res["overwritten"] >= 2

    skip_res = service.import_xml(xml_data, conflict_policy="skip")
    assert skip_res["skipped"] >= 2

    # Test InstrumentsCLI formatting
    table_text = InstrumentsCLI.format_instruments_table(forex_list)
    assert "Instruments Catalog" in table_text
    assert "EURUSD" in table_text

    # Test execution under __main__
    runpy.run_module("app.workspace.data_manager.instruments", run_name="__main__")


# ============================================================================
# 3. SessionsCatalogService Tests
# ============================================================================


def test_sessions_service_lifecycle(test_db_path: Path, tmp_path: Path) -> None:
    """Test session schedules, RTH/ETH windows, holidays, NT8 import, and XML."""
    service = SessionsCatalogService(db_path=test_db_path, data_dir=tmp_path / "data")

    seeded = service.ensure_default_sessions()
    assert seeded >= 4
    assert service.ensure_default_sessions() == 0

    all_sess = service.list_sessions()
    assert len(all_sess) >= 4

    forex = service.get_session("Forex 24/5")
    assert forex is not None
    # Wednesday 15:30 -> open
    assert forex.is_within_session(datetime(2026, 10, 14, 15, 30, tzinfo=UTC)) is True
    # Saturday 12:00 -> closed
    assert forex.is_within_session(datetime(2026, 10, 17, 12, 0, tzinfo=UTC)) is False

    # Custom session with holidays
    custom = service.save_session(
        {
            "name": "Custom RTH",
            "timezone": "UTC",
            "windows": [
                SessionWindow(
                    day_from="Mon",
                    day_to="Fri",
                    start_time="08:00",
                    end_time="17:00",
                )
            ],
            "holidays": [
                TradingHoliday(date_str="2026-10-15", description="Founders Day")
            ],
        }
    )
    assert custom.name == "Custom RTH"
    # Holiday -> closed
    assert custom.is_within_session(datetime(2026, 10, 15, 10, 0, tzinfo=UTC)) is False
    # Normal open day
    assert custom.is_within_session(datetime(2026, 10, 16, 10, 0, tzinfo=UTC)) is True

    # Clone and mass delete
    cloned = service.clone_session("Custom RTH", "Custom RTH Cloned")
    assert cloned.name == "Custom RTH Cloned"
    assert service.mass_delete_sessions(["Custom RTH Cloned"]) == 1

    # SQX XML
    xml_out = service.export_sqx_xml(["Forex 24/5"])
    assert "<Sessions>" in xml_out
    imported = service.import_sqx_xml(xml_out, policy="overwrite")
    assert len(imported["imported"]) == 1

    # NT8 Template Import
    nt_xml = """<?xml version="1.0" encoding="utf-8"?>
    <NinjaTrader>
        <TradingHours>
            <Name>CME US Index Futures</Name>
            <TimeZone>Central Standard Time</TimeZone>
            <Sessions>
                <Session>
                    <Day>Monday</Day>
                    <StartTime>17:00</StartTime>
                    <EndTime>16:00</EndTime>
                </Session>
            </Sessions>
        </TradingHours>
    </NinjaTrader>"""
    nt_res = service.import_nt_sessions(xml_content=nt_xml)
    assert nt_res["success"] is True
    assert "CME US Index Futures" in nt_res["imported"]

    # Test main()
    sessions.main()


# ============================================================================
# 4. BasketsCatalogService Tests
# ============================================================================


def test_baskets_service_lifecycle(test_db_path: Path, tmp_path: Path) -> None:
    """Test stock groups, survivorship-bias-free filtering, overview, and CSV/XML."""
    data_svc = DataManagerDataService(db_path=test_db_path, data_dir=tmp_path / "data")
    service = BasketsCatalogService(db_path=test_db_path, data_service=data_svc)

    seeded = service.ensure_default_baskets()
    assert seeded >= 3
    assert service.ensure_default_baskets() == 0

    baskets_list = service.list_baskets()
    assert len(baskets_list) >= 3

    sp100 = service.get_basket("S&P 100 limited")
    assert sp100 is not None
    assert len(sp100.items) >= 8

    # Survivorship-bias-free check
    active_now = sp100.active_members_on("20261015")
    assert len(active_now) >= 8
    active_past = sp100.active_members_on("20150101")
    assert len(active_past) == 0  # Default members date_from is 20200101

    # Overview calculation
    overview = service.get_baskets_overview()
    assert len(overview) >= 3
    item0 = overview[0]
    assert item0.total_count >= 1
    assert item0.is_ready is False  # Datasets not yet downloaded

    # CSV import and export
    csv_text = "NVDA;20200101;20261231;1.0\nAMD;20210101;;1.0\n"
    imported_b = service.import_csv("Tech Chips", csv_text)
    assert imported_b.name == "Tech Chips"
    assert len(imported_b.items) == 2

    exported_csv = service.export_csv("Tech Chips")
    assert "NVDA" in exported_csv and "AMD" in exported_csv

    # Update data provisioning
    up_res = service.update_baskets_data([imported_b.id or 1])
    assert len(up_res) == 1
    assert up_res[0]["provisioned_count"] == 2

    # XML transfer
    xml_out = service.export_xml(["Tech Chips"])
    assert "<Groups>" in xml_out
    imported_xml = service.import_xml(xml_out, overwrite=True)
    assert len(imported_xml) == 1

    # Delete
    assert service.delete_basket("Tech Chips") is True

    # Test main()
    baskets.main()


# ============================================================================
# 5. BrokerProfilesService Tests
# ============================================================================


def test_broker_profiles_lifecycle(test_db_path: Path, tmp_path: Path) -> None:
    """Test broker profiles, stock lists, CSV import/export, and XML migration."""
    inst_svc = Instruments(db_path=test_db_path)
    inst_svc.ensure_default_instruments()
    sess_svc = SessionsCatalogService(db_path=test_db_path)
    sess_svc.ensure_default_sessions()
    data_svc = DataManagerDataService(db_path=test_db_path, data_dir=tmp_path / "data")

    service = BrokerProfilesService(
        db_path=test_db_path,
        instruments_service=inst_svc,
        sessions_service=sess_svc,
        data_service=data_svc,
    )

    seeded = service.ensure_default_brokers()
    assert seeded >= 6
    assert service.ensure_default_brokers() == 0

    brokers = service.list_brokers()
    assert len(brokers) >= 6

    # Stocks management
    saved_stocks = service.save_broker_stocks(1, ["AAPL", "MSFT", "GOOGL"])
    assert saved_stocks == 3
    loaded = service.get_broker_stocks(1)
    assert loaded == ["AAPL", "MSFT", "GOOGL"]

    # CSV stocks transfer
    csv_text = "NVDA\nTSLA\nAMZN\n"
    imp_count = service.import_broker_stocks_csv(1, csv_text)
    assert imp_count == 3
    exp_csv = service.export_broker_stocks_csv(1)
    assert "NVDA" in exp_csv

    # Save custom broker
    custom = service.save_broker(
        {
            "name": "Custom ECN",
            "server_timezone": "UTC",
            "postfix": ".ecn",
            "mt_use": True,
            "stocks": ["EURUSD", "GBPUSD"],
        }
    )
    assert custom.name == "Custom ECN"
    assert custom.postfix == ".ecn"

    # XML transfer
    xml_out = service.export_brokers_xml([custom.id])
    assert "<Brokers>" in xml_out
    imported_b = service.import_brokers_xml(xml_out)
    assert len(imported_b) == 1

    # XML overview and selective import
    inst_xml = """<Instruments>
        <Instrument symbol="AUDUSD" tickSize="0.0001" pointValue="100000" description="Aussie"/>
    </Instruments>"""
    overview = service.inspect_xml_overview(inst_xml, kind="instrument")
    assert len(overview) == 1
    assert overview[0].name == "AUDUSD"

    rec_count = service.import_xml_records(
        inst_xml,
        kind="instrument",
        broker_id=custom.id,
        postfix="_ECN",
        selected_names=["AUDUSD"],
    )
    assert rec_count == 1
    assert inst_svc.get_instrument("AUDUSD_ECN") is not None

    # Trigger broker data update
    up_res = service.trigger_broker_data_update(custom.id)
    assert up_res["status"] == "completed"

    # Delete non-system broker
    deleted = service.delete_brokers([custom.id])
    assert deleted == 1

    # Test main()
    broker.main()


# ============================================================================
# 6. DataManagerLogService & HelpService Tests
# ============================================================================


def test_log_and_help_services(test_db_path: Path) -> None:
    """Test audit log persistence, SQX line formatting, operations, and help FAQ search."""
    log_svc = DataManagerLogService(db_path=test_db_path)

    entry = log_svc.append_log(
        action="IMPORT",
        message="Imported EURUSD M1 bars",
        symbol="EURUSD",
        details={"bars": 500},
    )
    assert entry.symbol == "EURUSD"
    assert "EURUSD" in entry.sqx_line
    assert "Imported EURUSD M1 bars" in entry.sqx_line

    logs = log_svc.list_logs(symbol="EURUSD")
    assert len(logs) == 1

    op = log_svc.record_operation(
        symbol="EURUSD",
        operation="IMPORT",
        status="SUCCESS",
        message="Parquet bars persisted",
        rows_affected=500,
        duration_ms=45.2,
    )
    assert op.operation == "IMPORT"
    assert op.rows_affected == 500

    ops = log_svc.list_operations(symbol="EURUSD")
    assert len(ops) == 1

    cleared = log_svc.clear_logs(symbol="EURUSD")
    assert cleared["cleared_count"] >= 1
    assert len(log_svc.list_logs(symbol="EURUSD")) == 0

    log_mod.main()

    # Help service
    help_svc = DataManagerHelpService()
    topics = help_svc.list_topics(section="data")
    assert len(topics) >= 1
    t = help_svc.get_topic("importing-csv-data")
    assert t is not None
    assert len(t.steps) >= 3

    faqs = help_svc.search_faqs(query="resampling")
    assert len(faqs) >= 1
    assert "resampling" in faqs[0].question.lower()

    help_mod.main()
