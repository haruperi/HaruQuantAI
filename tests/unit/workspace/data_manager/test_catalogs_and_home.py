"""Unit tests for Data Manager catalogs, home dashboard, logs, and help."""

from __future__ import annotations

import runpy
from datetime import UTC, datetime
from pathlib import Path

import pytest
from app.host.persistence.create import create_schema
from app.host.persistence.read import resolve_connection
from app.services.include.contracts import (
    SessionWindow,
    TradingHoliday,
    TradingSession,
)
from app.workspace.data_manager import (
    baskets,
    broker,
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
    Sessions,
    SessionsCLI,
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
    for sym in ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "USDCHF", "NZDUSD"]:
        inst_svc.add(
            {
                "symbol": sym,
                "description": f"{sym} Currency Pair",
                "data_type": "Forex",
                "tick_size": 0.00001,
                "point_value": 100000.0,
                "decimals": 5,
                "default_spread": 1.0,
            }
        )
    sess_svc = Sessions(db_path=test_db_path)
    for s_name in ["Forex 24/5", "24/7", "US Equities RTH", "Futures ETH"]:
        sess_svc.add({"name": s_name, "timezone": "UTC", "description": s_name})

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
def test_instruments_service_lifecycle(test_db_path: Path, tmp_path: Path) -> None:
    """Test instrument domain operations (view, add, edit, clone, delete, import, export)."""
    log_svc = DataManagerLogService(db_path=test_db_path)
    service = Instruments(db_path=test_db_path, log_service=log_svc)

    # 1. Add instruments
    eur = service.add(
        {
            "symbol": "EURUSD",
            "description": "Euro vs US Dollar",
            "data_type": "Forex",
            "tick_size": 0.00001,
            "point_value": 100000.0,
            "decimals": 5,
            "default_spread": 1.2,
        }
    )
    assert eur["symbol"] == "EURUSD"
    assert eur["decimals"] == 5

    service.add(
        {
            "symbol": "GBPUSD",
            "description": "British Pound vs US Dollar",
            "data_type": "Forex",
            "tick_size": 0.00001,
            "point_value": 100000.0,
            "decimals": 5,
            "default_spread": 1.5,
        }
    )
    service.add(
        {
            "symbol": "USDJPY",
            "description": "US Dollar vs Japanese Yen",
            "data_type": "Forex",
            "tick_size": 0.001,
            "point_value": 100000.0,
            "decimals": 3,
            "default_spread": 1.0,
        }
    )

    # 2. View instruments
    all_inst = service.view()
    assert len(all_inst) >= 3

    forex_list = service.view(data_type="Forex")
    assert len(forex_list) >= 3

    searched = service.view(search="Dollar")
    assert len(searched) >= 3

    # 3. Edit instrument (single and multiple)
    updated = service.edit("EURUSD", {"default_spread": 2.0})
    assert isinstance(updated, dict)
    assert updated["default_spread"] == 2.0

    multi_count = service.edit(["EURUSD"], {"min_volume": 0.1})
    assert multi_count == 1

    # 4. Clone instrument
    cloned = service.clone("EURUSD", "EURUSD_VIP", broker_id=2)
    assert cloned["symbol"] == "EURUSD_VIP"
    assert cloned["broker_id"] == 2

    # 5. Delete instrument (single and multiple)
    assert service.delete("EURUSD_VIP") is True
    assert service.delete("NON_EXISTENT") is False
    assert service.delete(["NON_EXISTENT_1", "NON_EXISTENT_2"]) == 0

    # 6. Export and Import JSON
    exp_file = tmp_path / "instruments_export.json"
    exported_path = service.export(file_path=exp_file, symbols=["EURUSD", "GBPUSD"])
    assert Path(exported_path).is_file()

    # Export string
    exported_str = service.export(symbols=["EURUSD"])
    assert isinstance(exported_str, str)
    assert "EURUSD" in exported_str

    # Import from file
    import_report = service.import_(exp_file, conflict_policy="overwrite_all")
    assert import_report["overwritten"] >= 2

    # Dynamic attribute import alias
    getattr(service, "import")(exp_file, conflict_policy="skip")

    # 7. InstrumentsCLI dispatching
    cli_list = InstrumentsCLI.dispatch(["list"], service=service)
    assert cli_list["count"] >= 2
    assert "symbol" in cli_list["rendered"].lower()

    cli_csv = InstrumentsCLI.dispatch(["-il", "csv=true"], service=service)
    assert "Symbol,Description" in cli_csv["rendered"]

    cli_add = InstrumentsCLI.dispatch(
        [
            "add",
            "symbol=CLI_TEST",
            "type=Forex",
            "tick_size=0.0001",
            "point_value=100000.0",
        ],
        service=service,
    )
    assert cli_add["instrument"]["symbol"] == "CLI_TEST"

    cli_edit = InstrumentsCLI.dispatch(
        ["edit", "symbol=CLI_TEST", "description=CLI Updated"],
        service=service,
    )
    assert cli_edit["instrument"]["description"] == "CLI Updated"

    cli_clone = InstrumentsCLI.dispatch(
        ["clone", "symbol=CLI_TEST", "clone_symbol=CLI_CLONED"],
        service=service,
    )
    assert cli_clone["instrument"]["symbol"] == "CLI_CLONED"

    cli_export = InstrumentsCLI.dispatch(
        ["export", f"filepath={tmp_path / 'cli_export.json'}", "symbols=CLI_TEST"],
        service=service,
    )
    assert "Exported" in cli_export["rendered"]

    cli_import = InstrumentsCLI.dispatch(
        ["import", f"filepath={tmp_path / 'cli_export.json'}"],
        service=service,
    )
    assert "Imported" in cli_import["rendered"]

    cli_delete = InstrumentsCLI.dispatch(
        ["delete", "symbols=CLI_TEST,CLI_CLONED"],
        service=service,
    )
    assert cli_delete["deleted_count"] == 2

    # 8. Test execution under __main__
    runpy.run_module("app.workspace.data_manager.instruments", run_name="__main__")


# ============================================================================
# 3. SessionsCatalogService Tests
# ============================================================================


@pytest.mark.filterwarnings("ignore::RuntimeWarning")
def test_sessions_service_lifecycle(test_db_path: Path, tmp_path: Path) -> None:
    """Test session schedules, calendar contract evaluation, CRUD, and CLI."""
    service = Sessions(db_path=test_db_path)

    # 1. Add sessions
    forex = service.add(
        {
            "name": "Forex 24/5",
            "timezone": "UTC",
            "description": "Standard 24/5 Forex schedule",
            "windows": [
                SessionWindow(
                    day_from="Mon",
                    day_to="Fri",
                    start_time="00:00",
                    end_time="23:59",
                    session_type="Regular",
                ),
            ],
            "holidays": [],
            "is_default": 0,
        }
    )
    assert forex["name"] == "Forex 24/5"

    crypto = service.add(
        {
            "name": "24/7 Crypto",
            "timezone": "UTC",
            "description": "Continuous crypto trading",
            "windows": [
                SessionWindow(
                    day_from="Mon",
                    day_to="Sun",
                    start_time="00:00",
                    end_time="23:59",
                )
            ],
            "is_default": 1,
        }
    )
    assert crypto["name"] == "24/7 Crypto"

    # 2. View sessions
    all_sess = service.view()
    assert len(all_sess) >= 2
    filtered = service.view(search="Forex")
    assert len(filtered) == 1
    assert filtered[0]["name"] == "Forex 24/5"

    # 3. Calendar contract evaluation
    trading_sess = TradingSession.from_dict(forex)
    assert (
        trading_sess.is_within_session(datetime(2026, 10, 14, 15, 30, tzinfo=UTC))
        is True
    )
    assert (
        trading_sess.is_within_session(datetime(2026, 10, 17, 12, 0, tzinfo=UTC))
        is False
    )

    # 4. Custom session with holidays
    custom = service.add(
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
    custom_model = TradingSession.from_dict(custom)
    # Holiday -> closed
    assert (
        custom_model.is_within_session(datetime(2026, 10, 15, 10, 0, tzinfo=UTC))
        is False
    )
    # Normal open day
    assert (
        custom_model.is_within_session(datetime(2026, 10, 16, 10, 0, tzinfo=UTC))
        is True
    )

    # 5. Edit session
    edited = service.edit("Custom RTH", {"description": "Updated RTH Description"})
    assert isinstance(edited, dict)
    assert edited["description"] == "Updated RTH Description"

    # Multi-edit
    count_edited = service.edit(["Custom RTH"], {"description": "Multi Updated"})
    assert count_edited == 1

    # 6. Clone session
    cloned = service.clone("Custom RTH", "Custom RTH Cloned")
    assert cloned["name"] == "Custom RTH Cloned"

    # 7. Delete sessions (single and multi)
    assert service.delete("Custom RTH Cloned") is True
    assert service.delete(["NonExistentSession"]) == 0

    # 8. Export and Import JSON
    export_path = tmp_path / "sessions_export.json"
    exported_file = service.export(file_path=export_path, names=["Custom RTH"])
    assert Path(exported_file).is_file()

    # Raw string export
    exported_str = service.export(names=["Custom RTH"])
    assert isinstance(exported_str, str)
    assert "Custom RTH" in exported_str

    # Import
    import_report = service.import_(export_path, conflict_policy="overwrite_all")
    assert import_report["overwritten"] >= 1

    # Dynamic alias import
    getattr(service, "import")(export_path, conflict_policy="skip")

    # 9. CLI Dispatching & Formatting
    cli_list = SessionsCLI.dispatch(["list"], service=service)
    assert cli_list["count"] >= 2
    assert "Name" in cli_list["rendered"]

    cli_csv = SessionsCLI.dispatch(["action=list", "csv=true"], service=service)
    assert "name,timezone" in cli_csv["rendered"]

    cli_add = SessionsCLI.dispatch(
        ["action=add", "session=CLI_SESS", "timezone=UTC", "description=CLI created"],
        service=service,
    )
    assert cli_add["session"]["name"] == "CLI_SESS"

    cli_edit = SessionsCLI.dispatch(
        ["action=edit", "session=CLI_SESS", "description=CLI updated"],
        service=service,
    )
    assert cli_edit["session"]["description"] == "CLI updated"

    cli_clone = SessionsCLI.dispatch(
        ["action=clone", "session=CLI_SESS", "clone_name=CLI_SESS_CLONED"],
        service=service,
    )
    assert cli_clone["session"]["name"] == "CLI_SESS_CLONED"

    cli_export = SessionsCLI.dispatch(
        ["action=export", f"filepath={tmp_path / 'cli_export.json'}"],
        service=service,
    )
    assert "Exported" in cli_export["rendered"]

    cli_import = SessionsCLI.dispatch(
        ["action=import", f"filepath={tmp_path / 'cli_export.json'}"],
        service=service,
    )
    assert "Imported" in cli_import["rendered"]

    cli_del = SessionsCLI.dispatch(
        ["action=delete", "sessions=CLI_SESS,CLI_SESS_CLONED"],
        service=service,
    )
    assert cli_del["deleted_count"] == 2

    # Run standalone demo
    runpy.run_module("app.workspace.data_manager.sessions", run_name="__main__")


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
    inst_svc.add(
        {
            "symbol": "EURUSD",
            "description": "Euro vs US Dollar",
            "data_type": "Forex",
            "tick_size": 0.00001,
            "point_value": 100000.0,
            "decimals": 5,
            "default_spread": 1.2,
        }
    )
    sess_svc = Sessions(db_path=test_db_path)
    sess_svc.add({"name": "24/7", "timezone": "UTC", "description": "Continuous 24/7"})
    sess_svc.add(
        {"name": "Forex 24/5", "timezone": "UTC", "description": "Standard Forex"}
    )
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
    assert any(i["symbol"] == "AUDUSD_ECN" for i in inst_svc.view())

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
