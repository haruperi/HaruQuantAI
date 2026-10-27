"""Persistent broker transfers validate actual domain records and conflict outcomes."""

import json
import sqlite3
from contextlib import closing

import pytest
from app.workspace.data_manager.brokers.imports import (
    import_broker_records,
    parse_broker_records,
)


def test_symbol_import_reports_only_confirmed_identities(temp_db):
    body = {
        "symbols": [
            {"symbol": "EURUSD", "tick_size": 0.0001, "commissions": "7"},
            {"symbol": "INVALID", "tick_size": "bad"},
        ],
        "options": {
            "selected_names": ["EURUSD", "INVALID"],
            "postfix": "_broker",
            "conflict_policy": "error",
        },
    }
    result = import_broker_records(temp_db, "symbols", "-1", body)
    assert result["created_count"] == 1 and result["imported_count"] == 1
    assert result["records"][0]["symbol"] == "EURUSD_broker"
    assert result["records"][0]["broker_id"] == -1
    assert result["failed"][0]["name"] == "INVALID_broker"
    repeated = import_broker_records(temp_db, "symbols", "-1", body)
    assert repeated["created_count"] == 0
    body["options"]["conflict_policy"] = "overwrite"
    body["symbols"][0]["commissions"] = "2"
    saved = import_broker_records(temp_db, "symbols", "-1", body)
    assert (
        saved["updated_count"] == 1 and float(saved["records"][0]["commissions"]) == 2.0
    )


def test_xml_normalization_and_entity_rejection():
    xml = '<Sessions version="1"><Session name="London" timezone="Europe/London"><SessionElement startDay="Mon" startTime="09:00" endDay="Mon" endTime="17:00" seoc="Yes"/><Holiday date="2025-12-25" description="Closed"/></Session></Sessions>'
    document = parse_broker_records(xml, "sessions")
    assert document["sessions"][0]["timezone"] == "Europe/London"
    assert document["sessions"][0]["holidays"][0]["date_str"] == "2025-12-25"
    assert parse_broker_records(json.dumps(document), "sessions") == document
    with pytest.raises(ValueError, match="DTD"):
        parse_broker_records("<!DOCTYPE Sessions><Sessions/>", "sessions")


def test_session_import_keeps_calendar_metadata(temp_db):
    with closing(sqlite3.connect(temp_db.database_path)) as database:
        database.execute(
            "CREATE TABLE datamgr_sessions (id INTEGER PRIMARY KEY, name TEXT UNIQUE, description TEXT, timezone TEXT, windows_json TEXT, holidays_json TEXT, is_default INTEGER, broker_id INTEGER)"
        )
    body = {
        "sessions": [
            {
                "name": "London",
                "timezone": "Europe/London",
                "windows": [
                    {
                        "day_from": "Mon",
                        "day_to": "Fri",
                        "start_time": "09:00",
                        "end_time": "17:00",
                    }
                ],
                "holidays": [{"date_str": "2025-12-25", "description": "Closed"}],
            }
        ],
        "options": {"selected_names": ["London"]},
    }
    result = import_broker_records(temp_db, "sessions", "-1", body)
    assert result["imported_count"] == 1
    assert result["records"][0]["holidays"][0]["date_str"] == "2025-12-25"
