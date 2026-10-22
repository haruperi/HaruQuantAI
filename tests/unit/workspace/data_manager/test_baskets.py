"""Verify public stock baskets using isolated host persistence."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
from app.host.persistence import HostPersistence
from app.workspace.data_manager.baskets import Basket
from app.workspace.data_manager.routes import AppDataManager, create_data_manager_router
from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def isolated(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(HostPersistence, "DEFAULT_DB_PATH", tmp_path / "baskets.db")


def test_metadata_and_historical_membership_roundtrip(
    caplog: pytest.LogCaptureFixture,
) -> None:
    service = Basket()
    with caplog.at_level(logging.INFO):
        row = service.add_basket({"name": " Tech ", "description": " Leaders "})
        saved = service.edit_stocks(
            row["id"],
            [
                "AAPL",
                "aapl",
                "OLD;1950-01-01;2000-01-01",
                "OLD;2001-01-01;",
                "UNTIL;;2020-01-01",
            ],
        )
        assert len(saved["items"]) == 4
        assert saved["items"][1] == {
            "symbol": "OLD",
            "date_from": "1950-01-01",
            "date_to": "2000-01-01",
        }
        before = HostPersistence.read_records("datamgr_stock", limit=0)
        edited = service.add_basket({"id": row["id"], "name": "Renamed"})
        assert edited["id"] == row["id"]
        assert edited["description"] == "Leaders"
        assert edited["items"] == saved["items"]
        assert HostPersistence.read_records("datamgr_stock", limit=0) == before
        assert service.baskets() == [edited]
        assert service.edit_stocks(row["id"], [])["items"] == []
    assert {"FR-DATAMGR-BASKET-" + kind for kind in ("LIST", "ADD", "EDIT")} <= {
        getattr(r, "fr_id", "") for r in caplog.records
    }
    assert service.baskets()[0]["name"] == "[Renamed]"


@pytest.mark.parametrize(
    "payload",
    [
        None,
        [],
        {},
        {"name": ""},
        {"name": "[]"},
        {"name": "X" * 51},
        {"name": "bad\nname"},
        {"name": "Good", "description": "X" * 251},
        {"name": "Good", "system": True},
        {"id": "0"},
        {"id": "01"},
        {"id": 1},
    ],
)
def test_invalid_metadata(payload: Any) -> None:
    with pytest.raises(ValueError):
        Basket().add_basket(payload)
    assert Basket().baskets() == []


@pytest.mark.parametrize(
    "symbols",
    [
        None,
        "AAPL",
        [None],
        [""],
        ["X" * 51],
        ["X\nY"],
        ["X;bad"],
        ["X;2020-02-30"],
        ["X;2021-01-01;2020-01-01"],
        ["X;2020-01-01;2021-01-01;extra"],
        ["X"] * 50001,
    ],
    ids=[
        "none",
        "string",
        "null-member",
        "blank",
        "long",
        "control",
        "bad-date",
        "impossible-date",
        "reversed",
        "extra-column",
        "oversize",
    ],
)
def test_invalid_members_preserve_previous_rows(symbols: Any) -> None:
    service = Basket()
    row = service.add_basket({"name": "Tech"})
    service.edit_stocks(row["id"], ["KEEP"])
    before = HostPersistence.read_records("datamgr_stock")
    with pytest.raises(ValueError):
        service.edit_stocks(row["id"], symbols)
    assert HostPersistence.read_records("datamgr_stock") == before


def test_duplicate_missing_and_system_guards() -> None:
    service = Basket()
    row = service.add_basket({"name": "Tech"})
    with pytest.raises(FileExistsError):
        service.add_basket({"name": "tech"})
    with pytest.raises(LookupError):
        service.add_basket({"id": "999", "name": "Missing"})
    with pytest.raises(LookupError):
        service.edit_stocks("999", [])
    HostPersistence.update_record(
        "datamgr_stock_group", {"ID": int(row["id"])}, {"SYSTEM": 1, "NAME": "[[Tech]]"}
    )
    before = service.baskets()
    with pytest.raises(ValueError):
        service.add_basket({"id": row["id"], "description": "No"})
    with pytest.raises(ValueError):
        service.edit_stocks(row["id"], [])
    assert service.baskets() == before


def test_member_replacement_rolls_back_and_keeps_other_groups() -> None:
    service = Basket()
    first = service.add_basket({"name": "First"})
    second = service.add_basket({"name": "Second"})
    service.edit_stocks(first["id"], ["KEEP"])
    service.edit_stocks(second["id"], ["OTHER"])
    before = service.baskets()
    real = HostPersistence.apply_batch

    def fail(operations: Any) -> Any:
        return real(
            [*operations, {"op": "create", "table": "not_approved", "values": {}}]
        )

    with patch.object(HostPersistence, "apply_batch", side_effect=fail):
        with pytest.raises(RuntimeError):
            service.edit_stocks(first["id"], ["NEW"])
    assert service.baskets() == before
    service.edit_stocks(first["id"], [])
    assert service.baskets()[1]["items"] == before[1]["items"]


def test_listing_reads_each_table_once_and_individual_edits_filter_members() -> None:
    service = Basket()
    row = service.add_basket({"name": "Tech"})
    with patch.object(
        HostPersistence, "read_records", wraps=HostPersistence.read_records
    ) as reads:
        service.baskets()
    assert [c.args[0] for c in reads.call_args_list] == [
        "datamgr_stock_group",
        "datamgr_stock",
    ]
    with patch.object(
        HostPersistence, "read_records", wraps=HostPersistence.read_records
    ) as reads:
        service.edit_stocks(row["id"], ["AAPL"])
    for call in reads.call_args_list:
        assert call.args[1] == (
            {"ID": int(row["id"])}
            if call.args[0] == "datamgr_stock_group"
            else {"BASKET_ID": int(row["id"])}
        )


@pytest.mark.parametrize("start,end", [(-1, -1), (-630892800000, None), (0, 86400000)])
def test_legacy_dates_preserved_on_reads(start: int, end: int | None) -> None:
    row = Basket().add_basket({"name": "Legacy"})
    HostPersistence.create_record(
        "datamgr_stock",
        {
            "TICKER": "OLD",
            "BASKET_ID": int(row["id"]),
            "DATE_FROM": start,
            "DATE_TO": end,
        },
    )
    before = HostPersistence.read_records("datamgr_stock")
    item = Basket().baskets()[0]["items"][0]
    assert (
        item["date_from"]
        == ({-1: None, -630892800000: "1950-01-04", 0: "1970-01-01"}[start])
    )
    assert HostPersistence.read_records("datamgr_stock") == before


@pytest.mark.parametrize("changes", [{"SYSTEM": 2}, {"SYSTEM": "bad"}])
def test_invalid_stored_flags_fail_closed(changes: dict[str, Any]) -> None:
    row = Basket().add_basket({"name": "Tech"})
    HostPersistence.update_record(
        "datamgr_stock_group", {"ID": int(row["id"])}, changes
    )
    with pytest.raises(RuntimeError):
        Basket().baskets()


@pytest.mark.parametrize("start,end", [(1, -1), (86400000, 0), (10**18, -1)])
def test_invalid_stored_dates_fail_closed(start: int, end: int) -> None:
    row = Basket().add_basket({"name": "Tech"})
    HostPersistence.create_record(
        "datamgr_stock",
        {
            "TICKER": "X",
            "BASKET_ID": int(row["id"]),
            "DATE_FROM": start,
            "DATE_TO": end,
        },
    )
    with pytest.raises(RuntimeError):
        Basket().baskets()


def test_routes_auth_and_sanitized_storage_failures() -> None:
    app = FastAPI()
    app.include_router(create_data_manager_router(AppDataManager()))
    with TestClient(app) as client:
        assert client.get("/data/baskets").json()["data"] == []
        row = client.post("/data/baskets", json={"name": "Tech"}).json()["data"]
        assert client.post("/data/baskets", json={"name": "tech"}).status_code == 409
        path = f"/data/baskets/{row['id']}/stocks"
        assert (
            client.put(path, json={"symbols": ["X;1950-01-01;"]}).json()["data"][
                "items"
            ][0]["date_from"]
            == "1950-01-01"
        )
        assert client.put(path, json={"wrong": []}).status_code == 422
        assert (
            client.put("/data/baskets/999/stocks", json={"symbols": []}).status_code
            == 404
        )
        assert (
            client.put("/data/baskets/bad/stocks", json={"symbols": []}).status_code
            == 422
        )
        with patch.object(
            HostPersistence, "read_records", side_effect=RuntimeError("private detail")
        ):
            reply = client.get("/data/baskets")
        assert reply.status_code == 503
        assert "private detail" not in reply.text
    protected = FastAPI()
    protected.include_router(
        create_data_manager_router(AppDataManager(), require_auth=True)
    )
    with TestClient(protected) as client:
        assert client.get("/data/baskets").status_code == 401
        assert client.post("/data/baskets", json={"name": "Tech"}).status_code == 401
        assert (
            client.put("/data/baskets/1/stocks", json={"symbols": []}).status_code
            == 401
        )


def test_delete_baskets_removes_selected_history_only(
    caplog: pytest.LogCaptureFixture,
) -> None:
    service = Basket()
    first = service.add_basket({"name": "First"})
    second = service.add_basket({"name": "Second"})
    retained = service.add_basket({"name": "Retained"})
    service.edit_stocks(first["id"], ["OLD;1950-01-01;2000-01-01", "OLD;2001-01-01;"])
    service.edit_stocks(retained["id"], ["KEEP"])
    before = next(row for row in service.baskets() if row["id"] == retained["id"])
    fields = "id source symbol underlying instrument timeframe broker broker_name timezone category date_from date_to created_at updated_at".split()
    HostPersistence.create_record("datamgr_datasets", dict.fromkeys(fields, "fixture"))
    datasets = HostPersistence.read_records("datamgr_datasets", limit=0)
    with caplog.at_level(logging.INFO):
        result = service.delete_basket([first["id"], second["id"], first["id"]])
    assert result == {"deleted_ids": [first["id"], second["id"]], "deleted_count": 2}
    assert service.baskets() == [before]
    assert [
        r["TICKER"] for r in HostPersistence.read_records("datamgr_stock", limit=0)
    ] == ["KEEP"]
    assert HostPersistence.read_records("datamgr_datasets", limit=0) == datasets
    assert any(
        getattr(r, "fr_id", "") == "FR-DATAMGR-BASKET-DELETE" for r in caplog.records
    )


@pytest.mark.parametrize(
    "ids",
    [[], "1", None, [1], ["0"], ["-1"], ["01"], ["bad"], ["1"] * 1001],
    ids=[
        "empty",
        "string",
        "none",
        "number",
        "zero",
        "default",
        "leading-zero",
        "bad",
        "oversize",
    ],
)
def test_delete_rejects_invalid_ids(ids: Any) -> None:
    with pytest.raises(ValueError):
        Basket().delete_basket(ids)


@pytest.mark.parametrize("protected", [False, True])
def test_delete_preflight_preserves_mixed_selection(protected: bool) -> None:
    service = Basket()
    first = service.add_basket({"name": "First"})
    service.edit_stocks(first["id"], ["KEEP;1950-01-01;"])
    identifier = "999"
    if protected:
        system = service.add_basket({"name": "System"})
        identifier = system["id"]
        HostPersistence.update_record(
            "datamgr_stock_group", {"ID": int(identifier)}, {"SYSTEM": 1}
        )
    before = {
        table: HostPersistence.read_records(table, limit=0)
        for table in ("datamgr_stock_group", "datamgr_stock")
    }
    with pytest.raises((ValueError, LookupError)):
        service.delete_basket([first["id"], identifier])
    assert before == {
        table: HostPersistence.read_records(table, limit=0) for table in before
    }


def test_delete_basket_rolls_back_every_selected_group() -> None:
    service = Basket()
    rows = [service.add_basket({"name": name}) for name in ("First", "Second")]
    for row in rows:
        service.edit_stocks(row["id"], ["OLD;1950-01-01;2000-01-01", "OLD;2001-01-01;"])
    before = {
        table: HostPersistence.read_records(table, limit=0)
        for table in ("datamgr_stock_group", "datamgr_stock")
    }
    real = HostPersistence.apply_batch

    def fail(operations: Any) -> Any:
        return real(
            [*operations, {"op": "create", "table": "not_approved", "values": {}}]
        )

    with patch.object(HostPersistence, "apply_batch", side_effect=fail):
        with pytest.raises(RuntimeError):
            service.delete_basket([row["id"] for row in rows])
    assert before == {
        table: HostPersistence.read_records(table, limit=0) for table in before
    }


def test_delete_routes_validation_authority_and_errors() -> None:
    app = FastAPI()
    app.include_router(create_data_manager_router(AppDataManager()))
    with TestClient(app) as client:
        row = client.post("/data/baskets", json={"name": "Tech"}).json()["data"]
        payloads: tuple[dict[str, Any], ...] = (
            {},
            {"ids": []},
            {"ids": [row["id"]], "extra": True},
        )
        for payload in payloads:
            assert client.post("/data/baskets/delete", json=payload).status_code == 422
        assert (
            client.post("/data/baskets/delete", json={"ids": ["999"]}).status_code
            == 404
        )
        with patch.object(
            HostPersistence, "apply_batch", side_effect=RuntimeError("private detail")
        ):
            failed = client.post("/data/baskets/delete", json={"ids": [row["id"]]})
        assert failed.status_code == 503
        assert "private detail" not in failed.text
        assert client.post("/data/baskets/delete", json={"ids": [row["id"]]}).json()[
            "data"
        ] == {"deleted_ids": [row["id"]], "deleted_count": 1}
    protected = FastAPI()
    protected.include_router(
        create_data_manager_router(AppDataManager(), require_auth=True)
    )
    assert (
        TestClient(protected)
        .post("/data/baskets/delete", json={"ids": ["1"]})
        .status_code
        == 401
    )
