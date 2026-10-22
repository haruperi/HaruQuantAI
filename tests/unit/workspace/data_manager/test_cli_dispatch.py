"""Verify Data Manager headless CLI dispatch and normalization.

Tests command dispatch for -symbol, -instrument, -data, and -brokerprofile,
covering arg normalization, table formatting, CSV rendering, and error paths.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from app.cli import (
    HeadlessCliRunner,
    _normalize_cli_args,
)
from app.cli import (
    main as cli_main,
)
from app.host.bootstrap import AppHost
from app.host.persistence import HostPersistence
from app.workspace.data_manager.broker import Broker, BrokerCLI
from app.workspace.data_manager.data import Data, DataCLI
from app.workspace.data_manager.instruments import Instruments


@pytest.fixture(autouse=True)
def isolated_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Isolate host persistence database in temporary directory."""
    monkeypatch.setattr(HostPersistence, "DEFAULT_DB_PATH", tmp_path / "test.db")


# ============================================================================
# 1. Argument Normalization Tests
# ============================================================================


def test_normalize_cli_args_short_aliases() -> None:
    """Verify short aliases expand to canonical command and action pairs."""
    assert _normalize_cli_args(["-l"]) == ["symbol", "action=list"]
    assert _normalize_cli_args(["-a", "datasource=dukascopy"]) == [
        "symbol",
        "action=add",
        "datasource=dukascopy",
    ]
    assert _normalize_cli_args(["-e", "symbol=EURUSD"]) == [
        "symbol",
        "action=edit",
        "symbol=EURUSD",
    ]
    assert _normalize_cli_args(["-d", "symbols=EURUSD"]) == [
        "symbol",
        "action=delete",
        "symbols=EURUSD",
    ]
    assert _normalize_cli_args(["-c", "datasource=dukascopy"]) == [
        "symbol",
        "action=clear",
        "datasource=dukascopy",
    ]
    assert _normalize_cli_args(["-il"]) == ["instrument", "action=list"]
    assert _normalize_cli_args(["-ia", "instrument=EURUSD"]) == [
        "instrument",
        "action=add",
        "instrument=EURUSD",
    ]
    assert _normalize_cli_args(["-ie", "instrument=EURUSD"]) == [
        "instrument",
        "action=edit",
        "instrument=EURUSD",
    ]
    assert _normalize_cli_args(["-id", "instruments=EURUSD"]) == [
        "instrument",
        "action=delete",
        "instruments=EURUSD",
    ]
    assert _normalize_cli_args(["-ir"]) == ["instrument", "action=refresh"]
    assert _normalize_cli_args(["-u", "symbols=EURUSD"]) == [
        "data",
        "action=update",
        "symbols=EURUSD",
    ]
    assert _normalize_cli_args(["-di", "file=test.csv"]) == [
        "data",
        "action=import",
        "file=test.csv",
    ]
    assert _normalize_cli_args(["-tz"]) == ["data", "action=timezones"]


def test_normalize_cli_args_flags_and_quoted_args() -> None:
    """Verify flag commands and --args pass-through normalization."""
    assert _normalize_cli_args(["-symbol", "action=list"]) == ["symbol", "action=list"]
    assert _normalize_cli_args(["-instrument", "action=list"]) == [
        "instrument",
        "action=list",
    ]
    assert _normalize_cli_args(["-data", "action=list"]) == ["data", "action=list"]
    assert _normalize_cli_args(["-brokerprofile", "action=list"]) == [
        "brokerprofile",
        "action=list",
    ]
    assert _normalize_cli_args(["--args=-symbol action=list"]) == [
        "symbol",
        "action=list",
    ]
    assert _normalize_cli_args(["--args", "-u symbols=EURUSD"]) == [
        "data",
        "action=update",
        "symbols=EURUSD",
    ]


# ============================================================================
# 2. DataCLI.dispatch_symbol Tests
# ============================================================================


def test_data_cli_symbol_list() -> None:
    """Verify symbol listing with table rendering and CSV formatting."""
    data_svc = Data()
    data_svc.add("dukascopy", "EURUSD", "M1")

    # 1. Table format
    res_table = DataCLI.dispatch_symbol(["action=list"], data_svc)
    assert res_table["command"] == "symbol"
    assert res_table["action"] == "list"
    assert res_table["count"] == 1
    assert "EURUSD" in str(res_table["rendered"])

    # 2. CSV format
    res_csv = DataCLI.dispatch_symbol(["action=list", "csv=true"], data_svc)
    assert "EURUSD" in str(res_csv["rendered"])
    assert "symbol,source,timeframe" in str(res_csv["rendered"])


def test_data_cli_symbol_crud() -> None:
    """Verify symbol add, edit, delete, and clear actions."""
    data_svc = Data()

    # Add
    res_add = DataCLI.dispatch_symbol(
        [
            "action=add",
            "datasource=dukascopy",
            "symbols=EURUSD,GBPUSD",
            "category=Forex",
        ],
        data_svc,
    )
    assert res_add["command"] == "symbol"
    assert res_add["action"] == "add"
    assert res_add["count"] == 2

    # Edit
    res_edit = DataCLI.dispatch_symbol(
        [
            "action=edit",
            "symbol=EURUSD",
            "underlying=EUR",
        ],
        data_svc,
    )
    assert res_edit["command"] == "symbol"
    assert res_edit["action"] == "edit"
    assert res_edit["updated"]["underlying"] == "EUR"

    # Delete
    res_del = DataCLI.dispatch_symbol(
        [
            "action=delete",
            "symbols=EURUSD",
        ],
        data_svc,
    )
    assert res_del["command"] == "symbol"
    assert res_del["action"] == "delete"
    assert res_del["count"] == 1

    # Clear
    res_clear = DataCLI.dispatch_symbol(["action=clear", "symbols=GBPUSD"], data_svc)
    assert res_clear["command"] == "symbol"
    assert res_clear["action"] == "clear"
    assert res_clear["count"] == 1


def test_data_cli_symbol_darwinex_and_mt5() -> None:
    """Verify darwinexsymbols and mt5symbols actions."""
    data_svc = Data()
    res_dwx = DataCLI.dispatch_symbol(["action=darwinexsymbols"], data_svc)
    assert res_dwx["command"] == "symbol"
    assert res_dwx["action"] == "darwinexsymbols"
    assert "EURUSD" in res_dwx["symbols"]

    res_mt5 = DataCLI.dispatch_symbol(["action=mt5symbols"], data_svc)
    assert res_mt5["command"] == "symbol"
    assert res_mt5["action"] == "mt5symbols"


def test_data_cli_symbol_errors() -> None:
    """Verify validation errors for symbol operations."""
    data_svc = Data()

    with pytest.raises(ValueError, match="Unsupported symbol action: 'unknown'"):
        DataCLI.dispatch_symbol(["action=unknown"], data_svc)

    with pytest.raises(
        ValueError,
        match=r"Parameter 'symbols' or 'symbol' is required for action=add\.",
    ):
        DataCLI.dispatch_symbol(["action=add", "datasource=dukascopy"], data_svc)

    with pytest.raises(
        ValueError, match=r"Parameter 'symbol' is required for action=edit\."
    ):
        DataCLI.dispatch_symbol(["action=edit"], data_svc)

    with pytest.raises(
        ValueError, match=r"Parameter 'symbols' is required for action=delete\."
    ):
        DataCLI.dispatch_symbol(["action=delete"], data_svc)


# ============================================================================
# 3. DataCLI.dispatch_data Tests
# ============================================================================


def test_data_cli_data_dispatch_timezones() -> None:
    """Verify listing supported canonical timezones."""
    data_svc = Data()
    res = DataCLI.dispatch_data(["action=timezones"], data_svc)
    assert res["command"] == "data"
    assert res["action"] == "timezones"
    assert res["count"] == 9
    assert "UTC" in res["timezones"]
    assert "US/Eastern" in res["timezones"]


def test_data_cli_data_dispatch_update_and_list() -> None:
    """Verify price data update and list actions."""
    data_svc = Data()

    with patch.object(
        data_svc,
        "import_data",
        return_value={"dataset_id": "dukascopy:EURUSD:M1", "rows_imported": 50},
    ):
        res = DataCLI.dispatch_data(
            [
                "action=update",
                "symbols=EURUSD,GBPUSD",
                "datasource=dukascopy",
                "timeframe=1m",
            ],
            data_svc,
        )
        assert res["command"] == "data"
        assert res["action"] == "update"
        assert res["count"] == 2

    # Test data list
    res_list = DataCLI.dispatch_data(["action=list"], data_svc)
    assert res_list["command"] == "data"
    assert res_list["action"] == "list"
    assert "Symbols / Datasets" in str(res_list["rendered"])


def test_data_cli_data_dispatch_import(tmp_path: Path) -> None:
    """Verify price data file import action."""
    data_svc = Data()
    csv_file = tmp_path / "eurusd.csv"
    csv_file.write_text(
        "datetime,open,high,low,close,volume\n"
        "2026-01-01 00:00:00,1.1000,1.1010,1.0990,1.1005,100\n",
        encoding="utf-8",
    )

    with patch.object(
        data_svc,
        "import_file",
        return_value={"dataset_id": "file:EURUSD:M1", "rows_imported": 1},
    ):
        res = DataCLI.dispatch_data(
            [
                "action=import",
                "symbol=EURUSD",
                f"file={csv_file}",
                "timeframe=1m",
            ],
            data_svc,
        )
        assert res["command"] == "data"
        assert res["action"] == "import"
        assert res["import_result"]["rows_imported"] == 1


def test_data_cli_data_dispatch_errors() -> None:
    """Verify validation errors for price data operations."""
    data_svc = Data()

    with pytest.raises(ValueError, match="Unsupported data action: 'invalid'"):
        DataCLI.dispatch_data(["action=invalid"], data_svc)


# ============================================================================
# 4. BrokerCLI.dispatch Tests
# ============================================================================


def test_broker_cli_dispatch_crud() -> None:
    """Verify broker profile list, add, delete, update, updateall."""
    inst_svc = Instruments()
    inst_svc.add_instrument({"symbol": "EURUSD"})
    broker_svc = Broker()

    # 1. Add
    res_add = BrokerCLI.dispatch(
        ["action=add", "broker=DemoBroker"],
        broker_svc,
    )
    assert res_add["command"] == "brokerprofile"
    assert res_add["action"] == "add"
    assert res_add["profile"]["name"] == "DemoBroker"

    # 2. List
    res_list = BrokerCLI.dispatch(["action=list"], broker_svc)
    assert res_list["command"] == "brokerprofile"
    assert res_list["action"] == "list"
    assert res_list["count"] == 1
    assert "DemoBroker" in str(res_list["rendered"])

    res_csv = BrokerCLI.dispatch(["action=list", "csv=true"], broker_svc)
    assert "DemoBroker" in str(res_csv["rendered"])
    assert "name,server,account" in str(res_csv["rendered"])

    # 3. Update
    res_upd = BrokerCLI.dispatch(
        ["action=update", "broker=DemoBroker"],
        broker_svc,
    )
    assert res_upd["action"] == "update"

    # 4. Updateall
    res_all = BrokerCLI.dispatch(["action=updateall"], broker_svc)
    assert res_all["action"] == "updateall"
    assert res_all["count"] == 1

    # 5. Delete
    res_del = BrokerCLI.dispatch(
        ["action=delete", "broker=DemoBroker"],
        broker_svc,
    )
    assert res_del["action"] == "delete"
    assert res_del["name"] == "DemoBroker"


def test_broker_cli_dispatch_import_export_stocks(tmp_path: Path) -> None:
    """Verify broker stock import and export operations."""
    inst_svc = Instruments()
    inst_svc.add_instrument({"symbol": "AAPL"})
    broker_svc = Broker()
    broker_svc.add_broker({"name": "StockBroker", "postfix": "_s"})

    export_path = tmp_path / "stocks.txt"
    export_path.write_text("AAPL\nMSFT\n", encoding="utf-8")

    # Import stocks
    res_import = BrokerCLI.dispatch(
        ["action=importstocks", "broker=StockBroker", f"file={export_path}"],
        broker_svc,
    )
    assert res_import["command"] == "brokerprofile"
    assert res_import["action"] == "importstocks"
    assert res_import["count"] == 2

    # Export stocks
    out_export = tmp_path / "exported.txt"
    res_export = BrokerCLI.dispatch(
        ["action=exportstocks", "broker=StockBroker", f"file={out_export}"],
        broker_svc,
    )
    assert res_export["action"] == "exportstocks"
    assert res_export["count"] == 2
    assert out_export.exists()


def test_broker_cli_dispatch_errors() -> None:
    """Verify validation errors for broker profile operations."""
    broker_svc = Broker()

    with pytest.raises(ValueError, match="Unsupported brokerprofile action: 'invalid'"):
        BrokerCLI.dispatch(["action=invalid"], broker_svc)

    with pytest.raises(
        ValueError, match=r"Parameter 'broker' or 'name' is required for action=add\."
    ):
        BrokerCLI.dispatch(["action=add"], broker_svc)

    with pytest.raises(
        ValueError,
        match=r"Parameter 'broker' or 'name' is required for action=delete\.",
    ):
        BrokerCLI.dispatch(["action=delete"], broker_svc)


# ============================================================================
# 5. HeadlessCliRunner Full Dispatch Integration
# ============================================================================


def test_headless_cli_runner_dispatch_all(tmp_path: Path) -> None:
    """Verify HeadlessCliRunner integration across all new command types."""
    data_dir = tmp_path / "cli_data"
    host = AppHost(data_dir=data_dir, headless=True, use_process_pool=False)
    host.startup()
    host.initialize_db()
    host.register_modules()
    host.broadcast_event("system", "host.ready")

    try:
        runner = HeadlessCliRunner(host)

        # 1. Symbol command
        res_sym = runner.execute("symbol", action="list")
        assert res_sym["command"] == "symbol"
        assert res_sym["action"] == "list"

        # 2. Brokerprofile command
        res_bp = runner.execute("brokerprofile", action="list")
        assert res_bp["command"] == "brokerprofile"
        assert res_bp["action"] == "list"

        # 3. Data update command
        with patch.object(
            host.data_manager.data,  # type: ignore[union-attr]
            "import_data",
            return_value={"dataset_id": "dukascopy:EURUSD:M1", "rows_imported": 50},
        ):
            res_data_upd = runner.execute(
                "data",
                action="update",
                extra_args=["symbols=EURUSD", "datasource=dukascopy"],
            )
            assert res_data_upd["action"] == "update"

        # 4. Data timezones command
        res_tz = runner.execute("data", action="timezones")
        assert res_tz["action"] == "timezones"

        # 5. Instrument command
        res_inst = runner.execute("instrument", action="list")
        assert res_inst["command"] == "instrument"
        assert res_inst["action"] == "list"

        # 6. Home and diagnostics commands
        res_home = runner.execute("home")
        assert res_home["command"] == "home"

        res_diag = runner.execute("diagnostics")
        assert res_diag["command"] == "diagnostics"
    finally:
        host.shutdown()


# ============================================================================
# 6. CLI Entrypoint Integration
# ============================================================================


def test_cli_main_entrypoint_executions(tmp_path: Path) -> None:
    """Verify invoking main() with normalized flags and --args."""
    data_dir = tmp_path / "entrypoint_data"
    base_args = ["--data-dir", str(data_dir), "--json"]

    # 1. -symbol action=list
    code_sym = cli_main(["-symbol", "action=list", *base_args])
    assert code_sym == 0

    # 2. -l short alias
    code_l = cli_main(["-l", *base_args])
    assert code_l == 0

    # 3. -brokerprofile action=list
    code_bp = cli_main(["-brokerprofile", "action=list", *base_args])
    assert code_bp == 0

    # 4. -tz short alias
    code_tz = cli_main(["-tz", *base_args])
    assert code_tz == 0

    # 5. --args pass-through
    code_args = cli_main(["--args=-symbol action=list", *base_args])
    assert code_args == 0
