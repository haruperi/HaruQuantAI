"""Basket CRUD, historical memberships, file transfer, and data acquisition."""

import json
import sqlite3
from contextlib import closing
from unittest.mock import Mock

import pandas as pd
import pytest
from app.host.persistence import HostPersistence
from app.workspace.data_manager.baskets import Baskets


@pytest.fixture
def baskets(tmp_path):
    database = tmp_path / "baskets.db"
    with closing(sqlite3.connect(database)) as connection:
        connection.executescript("""
            CREATE TABLE datamgr_stock_group (
                ID INTEGER PRIMARY KEY AUTOINCREMENT, NAME VARCHAR(50) NOT NULL,
                SYSTEM BOOLEAN NOT NULL, DESC VARCHAR(250), description TEXT DEFAULT '');
            CREATE TABLE datamgr_stock (
                ID INTEGER PRIMARY KEY AUTOINCREMENT, TICKER VARCHAR(50) NOT NULL,
                BASKET_ID INTEGER NOT NULL, DATE_FROM LONG NOT NULL, DATE_TO LONG,
                FOREIGN KEY(BASKET_ID) REFERENCES datamgr_stock_group(ID));
            CREATE TABLE datamgr_datasets (
                id TEXT PRIMARY KEY, source TEXT NOT NULL, symbol TEXT NOT NULL,
                underlying TEXT NOT NULL, timeframe TEXT NOT NULL,
                broker TEXT NOT NULL, timezone TEXT NOT NULL,
                category TEXT NOT NULL, date_from TEXT NOT NULL, date_to TEXT NOT NULL,
                bars INTEGER NOT NULL DEFAULT 0, created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL, path TEXT NOT NULL DEFAULT '');
        """)
        connection.commit()
    return Baskets(HostPersistence(database))


def test_group_crud(baskets):
    created = baskets.add("A", description="First")
    assert created["success"], created
    assert baskets.add("B")["success"]
    assert baskets.edit(["A", "B", "A"], description="Both")["success"]
    renamed = baskets.edit("A", name="Renamed")
    assert renamed["success"]
    assert renamed["data"][0]["description"] == "Both"
    assert baskets.edit_stocks("Renamed", "AAPL")["success"]
    removed = baskets.delete(["Renamed", "B"])
    assert removed["success"], removed
    assert removed["data"][0]["stocks"][0]["ticker"] == "AAPL"
    assert baskets.list()["data"] == []
    assert baskets.gateway.read_records("datamgr_stock")["data"]["records"] == []


@pytest.mark.parametrize("operation", ["edit", "delete"])
def test_bulk_rollback(baskets, operation):
    assert baskets.add("A")["success"]
    assert baskets.edit_stocks("A", "AAPL")["success"]
    result = (
        baskets.edit(["A", "missing"], description="Wrong")
        if operation == "edit"
        else baskets.delete(["A", "missing"])
    )
    assert not result["success"]
    assert result["error"]["code"] == "not_found"
    row = baskets.list()["data"][0]
    assert row["description"] == ""
    assert row["stocks_count"] == 1


def test_names_and_protection(baskets):
    assert baskets.add("A")["success"]
    assert baskets.add("a")["error"]["code"] == "conflict"
    assert baskets.add("B")["success"]
    assert baskets.edit("A", name="B")["error"]["code"] == "conflict"
    assert not baskets.edit(["A", "B"], name="C")["success"]
    assert baskets.add("System", system=True)["success"]
    for response in (
        baskets.edit("System", description="changed"),
        baskets.delete("System"),
        baskets.edit_stocks("System", "AAPL"),
    ):
        assert not response["success"]
        assert response["error"]["code"] == "validation"


@pytest.mark.parametrize(
    "fields",
    [
        {"name": ""},
        {"name": "x" * 51},
        {"name": "A", "description": "x" * 251},
        {"name": "A", "system": "false"},
    ],
)
def test_group_validation(baskets, fields):
    assert not baskets.add(**fields)["success"]
    assert baskets.list()["data"] == []


def test_memberships_and_csv_roundtrip(baskets, tmp_path):
    identifier = baskets.add("History")["data"]["id"]
    result = baskets.edit_stocks(
        identifier,
        "AAPL\nTSLA;01.12.2020\nAMZN;15.04.2007;30.05.2015\nAAPL;01.01.2000;31.12.2010",
    )
    assert result["success"], result
    assert len(result["data"]) == 4
    assert result["data"][0]["date_from"] == 0
    assert result["data"][0]["date_to"] == -1
    assert result["data"][2]["date_to"] > result["data"][2]["date_from"]
    target = tmp_path / "stocks.csv"
    assert baskets.export_stocks("History", target)["success"]
    assert "AMZN;15.04.2007;30.05.2015" in target.read_text(encoding="utf-8")
    expected = [
        {k: v for k, v in row.items() if k not in {"id", "basket_id"}}
        for row in baskets.list_stocks("History")["data"]
    ]
    assert baskets.edit_stocks("History", [])["success"]
    assert baskets.import_stocks("History", target)["success"]
    actual = [
        {k: v for k, v in row.items() if k not in {"id", "basket_id"}}
        for row in baskets.list_stocks("History")["data"]
    ]
    assert actual == expected


@pytest.mark.parametrize(
    "stocks",
    [
        "AAPL;31.02.2020",
        "AAPL;2025-01-01;2024-01-01",
        "AAPL;1;2;3",
        "AAPL\nAAPL",
        [{"ticker": "A", "date_from": True}],
        [{"ticker": "A", "date_to": -62135596800001}],
        [{"ticker": "A", "extra": 1}],
        [None],
    ],
)
def test_invalid_memberships_preserve_existing(baskets, stocks):
    assert baskets.add("A")["success"]
    assert baskets.edit_stocks("A", "OLD")["success"]
    result = baskets.edit_stocks("A", stocks)
    assert not result["success"], result
    assert baskets.list_stocks("A")["data"][0]["ticker"] == "OLD"


def test_large_batch_and_json_roundtrip(baskets, tmp_path):
    assert baskets.add("Large")["success"]
    rows = [
        {"ticker": f"T{i}", "date_from": 1001, "date_to": 2001} for i in range(1001)
    ]
    assert baskets.edit_stocks("Large", rows)["success"]
    assert len(baskets.list_stocks("Large")["data"]) == 1001
    assert baskets.add("Excluded")["success"]
    target = tmp_path / "groups.json"
    assert baskets.save(target, "Large")["data"]["count"] == 1
    exported = json.loads(target.read_text(encoding="utf-8"))
    assert "id" not in exported[0]
    assert "basket_id" not in exported[0]["stocks"][0]
    assert baskets.delete("Large")["success"]
    assert baskets.load(target)["success"]
    assert baskets.list_stocks("Large")["data"][0]["date_from"] == 1001
    assert baskets.edit_stocks("Large", [])["success"]
    assert baskets.list_stocks("Large")["data"] == []
    assert baskets.delete(["Large", "Excluded"])["success"]


@pytest.mark.parametrize(
    "payload",
    [
        [{"name": "B"}, {"name": "A"}],
        [{"name": "B", "stocks": [{"ticker": "X", "date_to": -62135596800001}]}],
        [{"name": "B"}, {"name": "b"}],
        {},
        [None],
    ],
)
def test_json_import_atomicity(baskets, tmp_path, payload):
    assert baskets.add("A")["success"]
    target = tmp_path / "groups.json"
    target.write_text(json.dumps(payload), encoding="utf-8")
    assert not baskets.load(target)["success"]
    assert [row["name"] for row in baskets.list()["data"]] == ["A"]


def test_empty_exports_and_missing_files(baskets, tmp_path):
    target = tmp_path / "groups.json"
    assert baskets.save(target)["success"]
    assert json.loads(target.read_text(encoding="utf-8")) == []
    assert baskets.load(target)["data"] == []
    assert not baskets.load(tmp_path / "missing.json")["success"]
    target.write_text("{bad", encoding="utf-8")
    assert not baskets.load(target)["success"]


def test_update_data_registers_real_parquet_and_reports_failures(baskets, tmp_path):
    for name in ("A", "B"):
        assert baskets.add(name)["success"]
        assert baskets.edit_stocks(name, "AAPL")["success"]
    frame = pd.DataFrame(
        {
            "Open": [1.0, 2.0],
            "High": [2.0, 3.0],
            "Low": [0.5, 1.0],
            "Close": [1.5, 2.5],
        },
        index=pd.to_datetime(["2026-01-01", "2026-01-02"]),
    )
    client = Mock()
    client.get_bars.return_value = frame
    result = baskets.update_data(["A", "B"], client=client, data_dir=tmp_path / "bars")
    assert result["success"], result
    assert result["data"]["updated_count"] == 1
    client.get_bars.assert_called_once_with("AAPL", "D1", count=100000)
    path = result["data"]["completed"][0]["path"]
    assert len(pd.read_parquet(path)) == 2
    assert baskets.list()["data"][0]["ready"]
    assert baskets.update_data("A", client=client, data_dir=tmp_path / "bars")[
        "success"
    ]
    assert len(baskets.gateway.read_records("datamgr_datasets")["data"]["records"]) == 1
    assert baskets.edit_stocks("B", "FAIL")["success"]
    client.get_bars.side_effect = lambda ticker, *args, **kwargs: (
        frame
        if ticker == "AAPL"
        else (_ for _ in ()).throw(RuntimeError("Provider failed"))
    )
    result = baskets.update_data(["A", "B"], client=client, data_dir=tmp_path / "bars")
    assert not result["success"]
    assert result["error"]["details"]["updated_count"] == 1
    assert result["error"]["details"]["failed"][0]["ticker"] == "FAIL"
    assert not baskets.update_data("missing", client=client)["success"]


def test_update_data_uses_injected_job_manager(baskets, tmp_path):
    assert baskets.add("A")["success"]
    assert baskets.edit_stocks("A", "AAPL")["success"]
    jobs = Mock()
    jobs.submit_job.return_value = {"job_id": "test-job", "status": "QUEUED"}
    service = Baskets(baskets.gateway, jobs=jobs)
    response = service.update_data("A", client=Mock(), data_dir=tmp_path)
    assert response["success"], response
    assert response["data"]["job_id"] == "test-job"
    assert jobs.submit_job.call_args.kwargs["executor_kind"] == "thread"


def test_membership_storage_failure_rolls_back_replacement(baskets):
    assert baskets.add("A")["success"]
    assert baskets.edit_stocks("A", "OLD")["success"]
    with closing(sqlite3.connect(baskets.gateway.database_path)) as connection:
        connection.execute("""CREATE TRIGGER reject_bad_ticker BEFORE INSERT ON datamgr_stock
            WHEN NEW.TICKER='FAIL' BEGIN SELECT RAISE(ABORT, 'Rejected ticker'); END""")
        connection.commit()
    assert not baskets.edit_stocks("A", "GOOD\nFAIL")["success"]
    assert [row["ticker"] for row in baskets.list_stocks("A")["data"]] == ["OLD"]


def test_csv_milliseconds_and_missing_end_roundtrip(baskets, tmp_path):
    assert baskets.add("A")["success"]
    assert baskets.edit_stocks(
        "A", [{"ticker": "AAPL", "date_from": 1001, "date_to": 2001}]
    )["success"]
    target = tmp_path / "stocks.csv"
    assert baskets.export_stocks("A", target)["success"]
    assert baskets.import_stocks("A", target)["success"]
    row = baskets.list_stocks("A")["data"][0]
    assert row["date_from"] == 1001 and row["date_to"] == 2001
    assert baskets.edit_stocks("A", "AAPL; ; ")["success"]
    assert baskets.list_stocks("A")["data"][0]["date_to"] == -1


def test_background_update_cooperates_with_job_context(baskets, tmp_path):
    assert baskets.add("A")["success"]
    assert baskets.edit_stocks("A", "AAPL")["success"]
    frame = pd.DataFrame(
        {"Open": [1.0], "High": [2.0], "Low": [0.5], "Close": [1.5]},
        index=pd.to_datetime(["2026-01-01"]),
    )
    jobs = Mock()
    jobs.submit_job.return_value = {"job_id": "job", "status": "QUEUED"}
    client = Mock(get_bars=Mock(return_value=frame))
    assert Baskets(baskets.gateway, jobs=jobs).update_data(
        "A", client=client, data_dir=tmp_path
    )["success"]
    args = jobs.submit_job.call_args.args
    context = Mock()
    result = args[0](context, *args[1:])
    assert result["updated_count"] == 1
    context.wait_if_paused.assert_called_once()
    context.report_progress.assert_called_once_with(100.0, "AAPL")


def test_failed_registration_removes_unregistered_file(baskets, tmp_path, monkeypatch):
    assert baskets.add("A")["success"]
    assert baskets.edit_stocks("A", "AAPL")["success"]
    frame = pd.DataFrame(
        {"Open": [1.0], "High": [2.0], "Low": [0.5], "Close": [1.5]},
        index=pd.to_datetime(["2026-01-01"]),
    )
    original = HostPersistence.create_records

    def reject_dataset(gateway, table, values):
        if table == "datamgr_datasets":
            return {
                "success": False,
                "message": "Storage unavailable",
                "error": {"code": "unavailable"},
            }
        return original(gateway, table, values)

    monkeypatch.setattr(HostPersistence, "create_records", reject_dataset)
    result = baskets.update_data(
        "A", client=Mock(get_bars=Mock(return_value=frame)), data_dir=tmp_path
    )
    assert not result["success"]
    assert list(tmp_path.glob("*.parquet")) == []


def test_invalid_provider_data_reports_failure(baskets, tmp_path):
    assert baskets.add("A")["success"]
    assert baskets.edit_stocks("A", "AAPL")["success"]
    frame = pd.DataFrame({"Open": [1.0], "High": [2.0], "Low": [0.5], "Close": [1.5]})
    result = baskets.update_data(
        "A", client=Mock(get_bars=Mock(return_value=frame)), data_dir=tmp_path
    )
    assert not result["success"]
    assert result["error"]["details"]["failed"][0]["ticker"] == "AAPL"
    assert list(tmp_path.glob("*.parquet")) == []


def test_default_provider_is_owned_and_closed(baskets, tmp_path, monkeypatch):
    assert baskets.add("A")["success"]
    assert baskets.edit_stocks("A", "AAPL")["success"]
    frame = pd.DataFrame(
        {"Open": [1.0], "High": [2.0], "Low": [0.5], "Close": [1.5]},
        index=pd.to_datetime(["2026-01-01"]),
    )
    client = Mock(get_bars=Mock(return_value=frame))
    factory = Mock(return_value=client)
    monkeypatch.setattr("app.workspace.brokers.sq_equity.SQEquityClient", factory)
    result = baskets.update_data("A", data_dir=tmp_path)
    assert result["success"], result
    factory.assert_called_once_with(data_dir=tmp_path)
    client.session.close.assert_called_once()


@pytest.fixture
def basket_http(baskets):
    from app.host.transport import register_transport_exception_handlers
    from app.workspace.data_manager import http
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    application = FastAPI()
    application.state.persistence = baskets.gateway
    from app.workspace.data_manager.logs import Logs

    application.state.data_logs = Logs()
    application.include_router(http.create_router())
    application.dependency_overrides[http._access] = lambda: None
    register_transport_exception_handlers(application)
    with TestClient(application) as client:
        yield client


def test_basket_http_crud_memberships_and_files(basket_http):
    base = "/api/v1/data/baskets"
    created = basket_http.post(base, json={"name": "Plain name", "description": "Test"})
    assert created.status_code == 200, created.text
    identifier = created.json()["data"]["id"]
    assert basket_http.get(base).json()["data"][0]["name"] == "Plain name"
    edited = basket_http.post(base, json={"id": identifier, "description": "Changed"})
    assert edited.status_code == 200, edited.text
    rows = basket_http.put(
        f"{base}/{identifier}/stocks",
        json={"symbols": ["AAPL;01.01.2020", "OLD;1001;2001"]},
    )
    assert rows.status_code == 200, rows.text
    assert rows.json()["data"]["items"][1]["date_from_ms"] == 1001
    listed = basket_http.get(f"{base}/{identifier}/stocks").json()["data"]
    assert len(listed["items"]) == 2
    content = basket_http.post(f"{base}/{identifier}/export-stocks", json={}).json()[
        "data"
    ]["content"]
    assert "AAPL;01.01.2020" in content
    assert (
        basket_http.post(
            f"{base}/{identifier}/import-stocks", json={"content": "AAPL;31.02.2020"}
        ).status_code
        == 422
    )
    assert (
        basket_http.post(
            f"{base}/{identifier}/import-stocks", json={"content": "MSFT"}
        ).json()["data"]["items"][0]["symbol"]
        == "MSFT"
    )
    exported = basket_http.post(base + "/save", json={"ids": [identifier]}).json()[
        "data"
    ]["content"]
    assert json.loads(exported)[0]["stocks"][0]["ticker"] == "MSFT"
    assert (
        basket_http.post(base + "/load", json={"content": exported}).status_code == 409
    )
    assert (
        basket_http.post(base + "/delete", json={"ids": [identifier]}).status_code
        == 200
    )
    assert (
        basket_http.post(base + "/load", json={"content": exported}).status_code == 200
    )
    assert basket_http.post(base + "/load", json={"content": "{}"}).status_code == 422


def test_basket_http_atomic_bulk_edit_and_protection(basket_http, baskets):
    base = "/api/v1/data/baskets"
    a = basket_http.post(base, json={"name": "A"}).json()["data"]["id"]
    b = basket_http.post(base, json={"name": "B"}).json()["data"]["id"]
    assert (
        basket_http.post(
            base + "/edit", json={"ids": [a, b], "updates": {"description": "Both"}}
        ).status_code
        == 200
    )
    assert (
        basket_http.post(
            base + "/edit",
            json={"ids": [a, "999"], "updates": {"description": "Wrong"}},
        ).status_code
        == 404
    )
    assert basket_http.get(base).json()["data"][0]["description"] == "Both"
    system = baskets.add("System", system=True)["data"]["id"]
    assert (
        basket_http.post(base + "/delete", json={"ids": [a, str(system)]}).status_code
        == 422
    )
    assert len(basket_http.get(base).json()["data"]) == 3


def test_basket_http_jobs_and_get_cannot_cancel(basket_http, baskets):
    from app.host.jobs import JobRecord

    identifier = baskets.add("A")["data"]["id"]
    assert baskets.edit_stocks("A", "AAPL")["success"]
    record = JobRecord(
        job_id="basket-job",
        owner="data-manager",
        kind="baskets.update_data",
        status="RUNNING",
        progress=25.0,
        message="AAPL",
        attempt_id=1,
        submitted_at_utc="now",
    )
    jobs = Mock()
    jobs.submit_job.return_value = record
    jobs.get_job.return_value = record
    jobs.pause_job.return_value = True
    basket_http.app.state.basket_jobs = jobs
    started = basket_http.post(
        "/api/v1/data/baskets/update-data", json={"ids": [str(identifier)]}
    )
    assert started.status_code == 200, started.text
    assert started.json()["data"]["job_id"] == "basket-job"
    assert jobs.submit_job.call_args.kwargs["executor_kind"] == "thread"
    assert (
        basket_http.get("/api/v1/data/basket-jobs/basket-job?action=stop").status_code
        == 200
    )
    jobs.cancel_job.assert_not_called()
    assert (
        basket_http.post(
            "/api/v1/data/basket-jobs/basket-job/pause", json={}
        ).status_code
        == 200
    )
    jobs.pause_job.assert_called_once_with("basket-job")
    jobs.get_job.return_value = None
    assert basket_http.get("/api/v1/data/basket-jobs/unknown").status_code == 404


def test_all_eleven_basket_cli_operations(baskets, monkeypatch, tmp_path, capsys):
    import argparse

    from app.workspace.data_manager import cli

    monkeypatch.setattr("app.workspace.data_manager.baskets.Baskets", lambda: baskets)
    parser = argparse.ArgumentParser()
    cli.register_commands(parser.add_subparsers(dest="command", required=True))
    csv_path = tmp_path / "stocks.csv"
    json_path = tmp_path / "groups.json"
    monkeypatch.setattr(
        baskets,
        "update_data",
        Mock(return_value={"success": True, "data": {"updated_count": 1}}),
    )
    commands = [
        ["add", "--name", "A"],
        ["list"],
        ["edit", "A", "--description", "Changed"],
        ["edit-stocks", "A", "--stocks", "AAPL;01.01.2020"],
        ["list-stocks", "A"],
        ["export-stocks", "A", str(csv_path)],
        ["import-stocks", "A", str(csv_path)],
        ["update-data", "A"],
        ["save", str(json_path), "--baskets", "A"],
        ["delete", "A"],
        ["load", str(json_path)],
    ]
    for command in commands:
        args = parser.parse_args(["data-manager", "basket", *command])
        assert args.handler(args) == 0, command
    assert baskets.list()["data"][0]["stocks"][0]["ticker"] == "AAPL"
    assert "Page 1 of 1" in capsys.readouterr().out
    args = parser.parse_args(
        ["data-manager", "basket", "edit-stocks", "A", "--stocks", "[bad"]
    )
    with pytest.raises(SystemExit) as failure:
        args.handler(args)
    assert failure.value.code == 2


def test_http_update_runs_real_background_worker(
    basket_http, baskets, tmp_path, monkeypatch
):
    from app.host.jobs import JobManager
    from app.host.resources import MemoryObservation, ResourceMonitor

    with closing(sqlite3.connect(baskets.gateway.database_path)) as connection:
        connection.executescript("""
            CREATE TABLE host_jobs (
                job_id TEXT PRIMARY KEY, owner TEXT NOT NULL DEFAULT 'default',
                kind TEXT NOT NULL DEFAULT 'compute', status TEXT NOT NULL,
                progress REAL NOT NULL DEFAULT 0, accepted INTEGER DEFAULT 0,
                rejected INTEGER DEFAULT 0, message TEXT NOT NULL DEFAULT '',
                attempt_id INTEGER DEFAULT 1, submitted_at_utc TEXT NOT NULL DEFAULT '',
                started_at_utc TEXT, finished_at_utc TEXT, error_message TEXT);
            CREATE TABLE host_job_events (
                event_id TEXT PRIMARY KEY, job_id TEXT NOT NULL, attempt_id TEXT,
                from_state TEXT, to_state TEXT NOT NULL, details_json TEXT NOT NULL,
                created_at_utc TEXT NOT NULL);
        """)
        connection.commit()
    monitor = ResourceMonitor(
        scratch_root=tmp_path / "scratch",
        probe_memory_fn=lambda: MemoryObservation(100, 50, 50, 50, 1, 0.5, True),
    )
    jobs = JobManager(
        persistence=baskets.gateway,
        resource_mgr=monitor,
        max_workers=1,
        use_process_pool=False,
    )
    basket_http.app.state.basket_jobs = jobs
    frame = pd.DataFrame(
        {"Open": [1.0], "High": [2.0], "Low": [0.5], "Close": [1.5]},
        index=pd.to_datetime(["2026-01-01"]),
    )
    monkeypatch.setattr(
        "app.workspace.brokers.sq_equity.SQEquityClient",
        Mock(return_value=Mock(get_bars=Mock(return_value=frame))),
    )
    download = Baskets._download_data

    def isolated_download(self, tickers, client, folder, **kwargs):
        return download(self, tickers, client, tmp_path / "bars", **kwargs)

    monkeypatch.setattr(Baskets, "_download_data", isolated_download)
    identifier = baskets.add("Background")["data"]["id"]
    assert baskets.edit_stocks("Background", "AAPL")["success"]
    try:
        response = basket_http.post(
            "/api/v1/data/baskets/update-data", json={"ids": [str(identifier)]}
        )
        assert response.status_code == 200, response.text
        job_id = response.json()["data"]["job_id"]
        completed = jobs.wait_for_job(job_id, timeout=10)
        assert completed.status == "COMPLETED", completed.error_message
        status = basket_http.get(f"/api/v1/data/basket-jobs/{job_id}")
        assert status.json()["data"]["progress"] == 100
        activity = basket_http.get("/api/v1/data/logs").json()["data"]["entries"]
        assert activity[0]["progress"] == 100
        assert activity[0]["task_id"] == job_id
        assert any("AAPL" in entry["message"] for entry in activity)
        assert basket_http.get("/api/v1/data/logs/active").json()["data"] == []
        assert baskets.list()["data"][0]["ready"]
        assert len(list((tmp_path / "bars").glob("*.parquet"))) == 1
    finally:
        jobs.shutdown(cancel_futures=True)


def test_historical_membership_dates(basket_http, tmp_path):
    base = "/api/v1/data/baskets"
    identifier = basket_http.post(base, json={"name": "Historical"}).json()["data"][
        "id"
    ]
    response = basket_http.put(
        f"{base}/{identifier}/stocks", json={"symbols": ["OLD;1950-01-01;1960-01-01"]}
    )
    assert response.status_code == 200
    item = basket_http.get(base).json()["data"][0]["items"][0]
    assert item["date_from"] == "1950-01-01"
    assert item["date_to"] == "1960-01-01"
    exported = basket_http.post(f"{base}/{identifier}/export-stocks", json={}).json()[
        "data"
    ]
    assert "01.01.1950;01.01.1960" in exported["content"]


def test_saved_dataset_http_catalog(basket_http, monkeypatch):
    from app.workspace.data_manager import http

    monkeypatch.setattr(
        http.Data,
        "list",
        lambda self: {
            "success": True,
            "data": [{"id": "saved", "symbol": "AAPL", "timeframe": "D1"}],
        },
    )
    response = basket_http.get("/api/v1/data/home/datasets")
    assert response.status_code == 200
    assert response.json()["data"][0]["id"] == "saved"
