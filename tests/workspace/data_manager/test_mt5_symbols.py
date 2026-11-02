"""MT5 catalog updates fetch first and persist the complete batch atomically."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from app import cli
from app.core.data.contracts import SymbolInfo, SymbolPrice, SymbolTrade
from app.workspace.data_manager import symbols as symbols_module
from app.workspace.data_manager.symbols import Symbols


@pytest.fixture
def mt5(monkeypatch):
    current = []

    async def name(value):
        current.append(value)
        return True

    async def snapshot():
        return SymbolInfo(
            name=current[-1],
            path=f"Forex\\{current[-1]}",
            description="MT5 specification",
            price=SymbolPrice(
                digits=3, tick_size=0.001, tick_step=0.001, contract_size=500
            ),
            trade=SymbolTrade(
                commission_settings='{"version":2,"source":"mt5","status":"not_retrieved","rules":null}'
            ),
        )

    client = SimpleNamespace(
        bridge=SimpleNamespace(command_timeout=1),
        start=AsyncMock(),
        wait_connected=AsyncMock(),
        close=AsyncMock(),
        symbol=SimpleNamespace(
            SymbolsGet=AsyncMock(return_value=["EURUSD", "GBPUSD"]),
            Name=AsyncMock(side_effect=name),
            SymbolInfo=AsyncMock(side_effect=snapshot),
        ),
    )
    factory = Mock(return_value=client)
    monkeypatch.setattr(symbols_module, "create_mt5_client", factory)
    return client, factory


@pytest.mark.parametrize(
    "names", ["EURUSD_demo", ["EURUSD_demo", "GBPUSD_demo", "EURUSD_demo"]]
)
def test_updates_one_or_more_symbols_and_preserves_identity(temp_db, mt5, names):
    service = Symbols(temp_db)
    for name in ("EURUSD", "GBPUSD"):
        assert service.add(
            name=name,
            datasource="demo",
            broker_id=42,
            commission=7,
            spread={"slippage": 2},
            margin={"rate": 0.05},
        )["success"]
    result = service.mt5update(names)
    assert result["success"]
    assert result["metadata"]["operation"] == "symbols.mt5update"
    expected = [names] if isinstance(names, str) else list(dict.fromkeys(names))
    assert [row["name"] for row in result["data"]] == expected
    for name in expected:
        info = service.get(name)["data"]
        assert info["price"]["digits"] == 3
        assert info["price"]["contract_size"] == 500
        assert info["spread"]["slippage"] == 2
        assert info["margin"]["rate"] == 0.05
        assert info["commission"] == 7
        row = temp_db.read_records("datamgr_symbols", filters={"name": name})["data"][
            "records"
        ][0]
        assert row["broker_id"] == 42
    mt5[0].close.assert_awaited_once()


@pytest.mark.parametrize("names", [[], "", "MISSING"])
def test_invalid_or_missing_catalog_symbols_do_not_connect(temp_db, mt5, names):
    result = Symbols(temp_db).mt5update(names)
    assert not result["success"]
    mt5[1].assert_not_called()


def test_missing_terminal_symbol_does_not_partially_write(temp_db, mt5):
    service = Symbols(temp_db)
    for name in ("EURUSD", "MISSING"):
        service.add(name=name, datasource="demo", description="Original")
    result = service.mt5update(["EURUSD_demo", "MISSING_demo"])
    assert result["error"]["code"] == "not_found"
    assert service.get("EURUSD_demo")["data"]["description"] == "Original"
    mt5[0].close.assert_awaited_once()


def test_bridge_timeout_cleans_up_and_keeps_catalog(temp_db, mt5):
    service = Symbols(temp_db)
    service.add(name="EURUSD", datasource="demo", description="Original")
    mt5[0].wait_connected.side_effect = TimeoutError("private-connection-detail")
    result = service.mt5update("EURUSD_demo")
    assert result["error"]["code"] == "unavailable"
    assert "private-connection-detail" not in str(result)
    assert service.get("EURUSD_demo")["data"]["description"] == "Original"
    mt5[0].close.assert_awaited_once()


def test_exact_terminal_name_wins_and_suffix_can_contain_underscores(temp_db, mt5):
    service = Symbols(temp_db)
    service.add(name="EURUSD", datasource="demo_profile")
    assert service.mt5update("EURUSD_demo_profile")["success"]
    mt5[0].symbol.Name.assert_awaited_with("EURUSD")
    mt5[0].symbol.SymbolsGet.return_value = ["EURUSD", "EURUSD_demo_profile"]
    assert service.mt5update("EURUSD_demo_profile")["success"]
    mt5[0].symbol.Name.assert_awaited_with("EURUSD_demo_profile")


def test_update_busy_returns_without_connecting(temp_db, mt5):
    with symbols_module._MT5_UPDATE_LOCK:
        result = Symbols(temp_db).mt5update("EURUSD")
    assert result["error"]["code"] == "unavailable"
    mt5[1].assert_not_called()


def test_cli_update_renders_table(temp_db, mt5, monkeypatch, capsys):
    monkeypatch.setattr(cli, "shutdown_logging", lambda: None)
    Symbols(temp_db).add(name="EURUSD", datasource="demo")
    assert cli.main(["data-manager", "symbol", "update", "EURUSD_demo"]) == 0
    output = capsys.readouterr().out
    assert "Updated 1 symbol(s) from MT5" in output
    assert "EURUSD_demo" in output
    assert "500" in output


def test_http_update_returns_confirmed_rows(symbol_http, temp_db, mt5):
    service = Symbols(temp_db)
    service.add(name="EURUSD", datasource="demo")
    service.add(name="GBPUSD", datasource="demo")
    ids = [
        row["id"] for row in symbol_http.get("/api/v1/data/instruments").json()["data"]
    ]
    response = symbol_http.post(
        "/api/v1/data/instruments/update", json={"instrument_ids": ids}
    )
    assert response.status_code == 200
    assert response.json()["data"]["updated_count"] == 2
    assert all(row["point_value"] == 500 for row in response.json()["data"]["symbols"])


def test_storage_failure_rolls_back_the_batch(temp_db, mt5, monkeypatch):
    from app.core.host.persistence import HostPersistence

    service = Symbols(temp_db)
    for name in ("EURUSD", "GBPUSD"):
        service.add(name=name, datasource="demo", description="Original")
    original = HostPersistence.update_record

    def fail_second(gateway, table, fields, **kwargs):
        if kwargs.get("filters") == {"name": "GBPUSD_demo"}:
            return {"success": False}
        return original(gateway, table, fields, **kwargs)

    monkeypatch.setattr(HostPersistence, "update_record", fail_second)
    result = service.mt5update(["EURUSD_demo", "GBPUSD_demo"])
    assert not result["success"]
    for name in ("EURUSD_demo", "GBPUSD_demo"):
        assert service.get(name)["data"]["description"] == "Original"


def test_empty_catalog_imports_all_terminal_symbols(temp_db, mt5):
    service = Symbols(temp_db)
    result = service.mt5update()
    assert result["success"]
    assert result["message"] == "Imported 2 symbol(s) from MT5"
    assert {item["name"] for item in result["data"]} == {"EURUSD", "GBPUSD"}
    assert service.get("EURUSD")["data"]["price"]["contract_size"] == 500
    mt5[0].close.assert_awaited_once()


def test_full_import_is_rejected_when_catalog_has_records(temp_db, mt5):
    service = Symbols(temp_db)
    service.add(name="LOCAL", datasource="demo")
    result = service.mt5update()
    assert result["error"]["code"] == "conflict"
    mt5[1].assert_not_called()


def test_full_import_rechecks_empty_catalog_after_fetch(temp_db, mt5):
    service = Symbols(temp_db)

    async def concurrent_add():
        service.add(name="LOCAL", datasource="demo")

    mt5[0].close.side_effect = concurrent_add
    result = service.mt5update()
    assert result["error"]["code"] == "conflict"
    assert not service.get("EURUSD")["success"]
    assert service.get("LOCAL_demo")["success"]


@pytest.mark.parametrize("fail_second_batch", [False, True])
def test_full_import_batches_over_1000_and_rolls_back(
    temp_db, mt5, monkeypatch, fail_second_batch
):
    from app.core.host.persistence import HostPersistence

    service = Symbols(temp_db)
    mt5[0].symbol.SymbolsGet.return_value = [f"SYMBOL{i:04d}" for i in range(1001)]
    original = HostPersistence.create_records
    batch_sizes = []

    def create(gateway, table, values):
        batch_sizes.append(len(values))
        if fail_second_batch and len(batch_sizes) == 2:
            return {"success": False}
        return original(gateway, table, values)

    monkeypatch.setattr(HostPersistence, "create_records", create)
    result = service.mt5update()
    assert batch_sizes == [1000, 1]
    assert result["success"] is not fail_second_batch
    assert len(service.list()["data"]) == (0 if fail_second_batch else 1001)


def test_http_and_cli_can_bootstrap_empty_catalog(
    symbol_http, temp_db, mt5, monkeypatch, capsys
):
    result = symbol_http.post(
        "/api/v1/data/instruments/update", json={"instrument_ids": []}
    )
    assert result.status_code == 200
    assert result.json()["data"]["updated_count"] == 2
    assert {row["symbol"] for row in result.json()["data"]["symbols"]} == {
        "EURUSD",
        "GBPUSD",
    }
    assert (
        symbol_http.post(
            "/api/v1/data/instruments/update", json={"instrument_ids": []}
        ).status_code
        == 409
    )
    assert Symbols(temp_db).delete(["EURUSD", "GBPUSD"])["success"]
    monkeypatch.setattr(cli, "shutdown_logging", lambda: None)
    assert cli.main(["data-manager", "symbol", "update"]) == 0
    assert "Imported 2 symbol(s)" in capsys.readouterr().out


@pytest.mark.parametrize(
    "path,expected",
    [
        (r"Forex\EURJPY", "Forex"),
        (r"Markets\Forex\Crosses\EURJPY", r"Markets\Forex\Crosses"),
        (r"Indices\Cash\US500", r"Indices\Cash"),
        ("EURJPY", ""),
    ],
)
def test_data_type_comes_from_parent_path(path, expected):
    calculation = "Calculation of profit and margin for Forex"
    snapshot = SymbolInfo(
        name="EURJPY",
        path=path,
        data_type=calculation,
        trade=SymbolTrade(calculation=calculation),
    )
    assert snapshot.data_type == expected
    assert snapshot.trade.calculation == calculation


def test_path_category_survives_update_clone_and_csv(temp_db, mt5, tmp_path):
    service = Symbols(temp_db)
    service.add(name="EURUSD", datasource="demo")
    calculation = "Calculation of profit and margin for Forex"
    mt5[0].symbol.SymbolInfo.side_effect = None
    mt5[0].symbol.SymbolInfo.return_value = SymbolInfo(
        name="EURUSD",
        path=r"Markets\Forex\Majors\EURUSD",
        trade=SymbolTrade(calculation=calculation),
    )
    assert service.mt5update("EURUSD_demo")["success"]
    assert service.clone("EURUSD_demo", "COPY")["success"]
    names = ["EURUSD_demo", "COPY_demo"]
    path = tmp_path / "symbols.csv"
    assert service.save(names, path)["success"]
    assert service.delete(names)["success"]
    assert service.load(path)["success"]
    for name in names:
        saved = service.get(name)["data"]
        assert saved["data_type"] == r"Markets\Forex\Majors"
        assert saved["trade"]["calculation"] == calculation


def test_old_expert_cannot_overwrite_categories(temp_db, mt5):
    service = Symbols(temp_db)
    service.add(name="EURUSD", datasource="demo", data_type="Forex")
    mt5[0].symbol.SymbolInfo.side_effect = None
    mt5[0].symbol.SymbolInfo.return_value = SymbolInfo(
        name="EURUSD", data_type="Calculation of profit and margin for Forex"
    )
    result = service.mt5update("EURUSD_demo")
    assert not result["success"]
    assert "Reload the updated PythonBridge" in result["message"]
    assert service.get("EURUSD_demo")["data"]["data_type"] == "Forex"
