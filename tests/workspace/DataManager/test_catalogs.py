"""Catalog restart snapshots, stale writers and schema rejection."""

import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Any

import pytest
from app.host.capabilities import MarketAccess, SettingsAccess
from app.persistence.market import (
    MarketDataStore,
    create_isolated_schema,
    migrate_broker_clock_schema,
)
from app.workspace.DataManager.catalogs import broker_clock_operation, catalog_operation


def test_revision_and_restart(tmp_path: Path) -> None:
    database = tmp_path / "catalog.db"
    create_isolated_schema(database)
    market = MarketAccess("workspace.data_manager", MarketDataStore(tmp_path, database))
    backing: dict[str, Any] = {}
    settings = SettingsAccess("workspace.data_manager", backing)
    first = catalog_operation(settings, market, "catalogs.get", {"kind": "groups"})
    assert first["revision"] == 0
    state = {
        "groups": [
            {
                "id": "group-one",
                "name": "Actual group",
                "description": "",
                "system": False,
                "members": [{"ticker": "AAPL", "from": "2024-01-01"}],
            }
        ]
    }
    result = catalog_operation(
        settings,
        market,
        "catalogs.replace",
        {"kind": "groups", "revision": 0, "state": state},
    )
    assert result["revision"] == 1
    fresh = SettingsAccess("workspace.data_manager", backing)
    assert (
        catalog_operation(fresh, market, "catalogs.get", {"kind": "groups"})["state"]
        == state
    )
    with pytest.raises(ValueError, match="changed"):
        catalog_operation(
            settings,
            market,
            "catalogs.replace",
            {"kind": "groups", "revision": 0, "state": state},
        )


def test_invalid_session_never_persists(tmp_path: Path) -> None:
    database = tmp_path / "catalog.db"
    create_isolated_schema(database)
    market = MarketAccess("workspace.data_manager", MarketDataStore(tmp_path, database))
    backing: dict[str, Any] = {}
    settings = SettingsAccess("workspace.data_manager", backing)
    with pytest.raises(ValueError):
        catalog_operation(
            settings,
            market,
            "catalogs.replace",
            {
                "kind": "sessions",
                "state": {
                    "sessions": [
                        {
                            "name": "Bad",
                            "broker": "-1",
                            "brokerName": "Default",
                            "elements": [
                                {
                                    "dayFrom": "Mon",
                                    "dayTo": "Mon",
                                    "timeFrom": "25:00",
                                    "timeTo": "12:00",
                                    "eod": True,
                                }
                            ],
                        }
                    ]
                },
            },
        )
    assert backing == {}


def test_broker_propagation_and_referenced_catalog_removal(tmp_path: Path) -> None:
    from app.workspace.DataManager.catalogs import broker_operation

    database = tmp_path / "catalog.db"
    create_isolated_schema(database)
    store = MarketDataStore(tmp_path, database)
    producer = MarketAccess("plugin.data_manager.file_import", store)
    identity = producer.register_source(
        source="File import",
        symbol="EURUSD",
        underlying="EURUSD",
        instrument="EURUSD",
        timeframe="M1",
    )
    market = MarketAccess("workspace.data_manager", store)
    backing: dict[str, Any] = {}
    settings = SettingsAccess("workspace.data_manager", backing)
    instrument = {
        "symbol": "EURUSD",
        "name": "Euro USD",
        "type": "Forex",
        "broker": "actual",
        "brokerName": "Actual",
        "pointValue": 100000,
        "tickSize": 0.00001,
        "tickStep": 0.00001,
        "spread": 1,
        "slippage": 0,
        "minDistance": 0,
        "multiplier": 1,
        "sizeStep": 0.01,
        "timezone": "UTC",
        "commission": {
            "model": "None",
            "value": 0,
            "unit": "USD",
            "min": 0,
            "minUnit": "USD",
            "max": 0,
            "maxUnit": "USD",
        },
        "swap": {
            "use": False,
            "type": "money",
            "long": 0,
            "short": 0,
            "tripleSwapOn": "Wed",
            "rolloutHour": "00:00",
        },
    }
    catalog_operation(
        settings,
        market,
        "catalogs.replace",
        {"kind": "instruments", "state": {"instruments": [instrument]}},
    )
    broker = {
        "id": "actual",
        "name": "Actual",
        "desc": "",
        "postfix": "",
        "timezone": "UTC",
        "mtUse": True,
        "stockPickerUse": False,
        "system": False,
        "stocks": [],
        "instruments": ["EURUSD"],
    }
    catalog_operation(
        settings,
        market,
        "catalogs.replace",
        {"kind": "brokers", "state": {"brokers": [broker]}},
    )
    rows = broker_operation(
        settings,
        market,
        "actions.broker_data",
        {"query": "euro", "broker_id": "actual"},
    )
    assert rows["count"] == 1
    assert rows["instruments"][0]["decimals"] == 5
    assert (
        broker_operation(settings, market, "actions.broker_data", {"query": "missing"})[
            "count"
        ]
        == 0
    )
    result = broker_operation(
        settings,
        market,
        "actions.broker_data_update",
        {"profile_ids": ["actual"], "symbols": ["EURUSD"]},
    )
    assert result["updatedDatasets"] == 1
    assert market.retained_source(identity)["broker"] == "actual"
    for kind in ("brokers", "instruments"):
        with pytest.raises(ValueError, match="referenced"):
            catalog_operation(
                settings,
                market,
                "catalogs.replace",
                {"kind": kind, "revision": 1, "state": {kind: []}},
            )
    with pytest.raises(ValueError, match="Duplicate"):
        catalog_operation(
            settings,
            market,
            "catalogs.replace",
            {
                "kind": "instruments",
                "revision": 1,
                "state": {"instruments": [instrument, instrument]},
            },
        )
    with pytest.raises(ValueError, match="Override"):
        catalog_operation(
            settings,
            market,
            "catalogs.replace",
            {
                "kind": "instruments",
                "revision": 1,
                "state": {"overrides": {"wrong": instrument}},
            },
        )
    with pytest.raises(TypeError, match="selection"):
        broker_operation(
            settings, market, "actions.broker_data_update", {"symbols": "EURUSD"}
        )
    with pytest.raises(ValueError, match="Invalid catalog"):
        catalog_operation(settings, market, "unknown", {"kind": "groups"})


def test_broker_seeding_from_database(tmp_path: Path) -> None:
    """Unseeded broker catalog reads records directly from datamgr_broker database table."""
    import sqlite3
    from contextlib import closing

    database = tmp_path / "catalog.db"
    create_isolated_schema(database)
    with closing(sqlite3.connect(database)) as connection, connection:
        connection.execute(
            "CREATE TABLE IF NOT EXISTS datamgr_broker ("
            "id INTEGER PRIMARY KEY, name TEXT, is_system INTEGER, description TEXT, "
            "stockpicker_use INTEGER, mt_use INTEGER, server_timezone TEXT, postfix TEXT, enabled INTEGER)"
        )
        connection.execute(
            "INSERT INTO datamgr_broker VALUES (2, 'RoboForex', 1, 'RoboForex', 0, 1, 'EET', '_roboforex', 1)"
        )
    store = MarketDataStore(tmp_path, database)
    market = MarketAccess("workspace.data_manager", store)
    settings = SettingsAccess("workspace.data_manager", {})
    result = catalog_operation(settings, market, "catalogs.get", {"kind": "brokers"})
    brokers = result["state"]["brokers"]
    assert len(brokers) == 1
    assert brokers[0]["name"] == "RoboForex"
    assert brokers[0]["postfix"] == "_roboforex"


def test_broker_clock_association_is_explicit_immutable_and_unique(
    tmp_path: Path,
) -> None:
    database = tmp_path / "clock-catalog.db"
    create_isolated_schema(database)
    with closing(sqlite3.connect(database)) as connection, connection:
        connection.execute(
            "CREATE TABLE datamgr_broker (id INTEGER PRIMARY KEY, name TEXT, postfix TEXT, server_timezone TEXT, enabled INTEGER, mt_use INTEGER)"
        )
        connection.executemany(
            "INSERT INTO datamgr_broker VALUES (?,?,?,?,?,?)",
            [(2, "Same name", "", "UTC", 1, 1), (3, "Same name", "", "UTC", 1, 1)],
        )
    migrate_broker_clock_schema(database)
    market = MarketAccess("workspace.data_manager", MarketDataStore(tmp_path, database))
    profile = {
        "id": "custom",
        "name": "Same name",
        "desc": "",
        "postfix": "",
        "timezone": "UTC",
        "mtUse": True,
        "stockPickerUse": False,
        "system": False,
        "stocks": [],
        "instruments": [],
    }
    settings = SettingsAccess(
        "workspace.data_manager",
        {
            "workspace.data_manager:catalog.brokers": {
                "revision": 1,
                "state": {"brokers": [profile]},
            }
        },
    )
    with pytest.raises(ValueError, match="Associate"):
        broker_clock_operation(
            settings, market, "broker_clock.get", {"broker_id": "custom"}
        )
    mapped = {**profile, "databaseBrokerId": "2"}
    catalog_operation(
        settings,
        market,
        "catalogs.replace",
        {"kind": "brokers", "revision": 1, "state": {"brokers": [mapped]}},
    )
    policy = broker_clock_operation(
        settings, market, "broker_clock.get", {"broker_id": "custom"}
    )
    assert policy["revision"] == 0
    assert policy["database_broker_id"] == "2"
    assert "transitions" in policy["schema"]["properties"]
    for replacement in ({**mapped, "databaseBrokerId": "3"}, profile):
        with pytest.raises(ValueError, match="immutable"):
            catalog_operation(
                settings,
                market,
                "catalogs.replace",
                {"kind": "brokers", "revision": 2, "state": {"brokers": [replacement]}},
            )
    with pytest.raises(ValueError, match="Duplicate"):
        catalog_operation(
            settings,
            market,
            "catalogs.replace",
            {
                "kind": "brokers",
                "revision": 2,
                "state": {
                    "brokers": [mapped, {**mapped, "id": "other", "name": "Other"}]
                },
            },
        )
    with pytest.raises(ValueError):
        catalog_operation(
            settings,
            market,
            "catalogs.replace",
            {
                "kind": "brokers",
                "revision": 2,
                "state": {"brokers": [{**mapped, "clock_policy_json": "{}"}]},
            },
        )
