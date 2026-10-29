"""Custom indicator persistence, file transfers, imports and job contracts."""

import csv
import io
import json
import sqlite3
import zipfile
from contextlib import closing
from unittest.mock import Mock, patch

import pytest
from app.core.host.persistence import HostPersistence
from app.host.events import EventBus
from app.workspace.data_manager.custom import CustomData
from app.workspace.data_manager.logs import Logs


@pytest.fixture
def service(tmp_path):
    database = tmp_path / "custom.db"
    with closing(sqlite3.connect(database)) as connection:
        connection.execute("CREATE TABLE unrelated(id INTEGER PRIMARY KEY)")
        connection.commit()
    return CustomData(HostPersistence(database))


def _csv(tmp_path, content="2020-01-01,1\n2020-01-02,2\n"):
    path = tmp_path / "values.csv"
    path.write_text(content, encoding="utf-8")
    return path


def _add(service, name="Test"):
    response = service.add(name, values=[{"name": "Score"}])
    assert response["success"], response
    return response["data"]


def _import(service, path, **kwargs):
    result = service.import_data("Test", path, columns=["date", "Score"], **kwargs)
    assert result["success"], result
    return result["data"]


def test_schema_catalog_and_definition_crud(service):
    assert service.list()["data"] == []
    first = _add(service)
    assert service.gateway.read_records("unrelated")["success"]
    assert not service.add("test", values=[{"name": "Score"}])["success"]
    edited = service.edit("test", {"name": "Renamed", "timeframe": "W1"})
    assert edited["data"]["id"] == first["id"]
    assert edited["data"]["timeframe"] == "W1"
    assert service.delete("Renamed")["success"]
    assert service.list()["data"] == []


@pytest.mark.parametrize(
    "values",
    [
        [],
        [{"name": "a b"}],
        [{"name": "A"}, {"name": "a"}],
        [{"name": "A", "extra": 1}],
        [{"name": "A", "mt4": 5}],
        [None],
    ],
)
def test_invalid_definitions_do_not_write(service, values):
    assert not service.add("Test", values=values)["success"]
    assert service.list()["data"] == []


def test_import_merge_replace_and_review_historical_dates(service, tmp_path):
    _add(service)
    path = _csv(tmp_path, "1950-01-02,2\n1950-01-01,1\n")
    assert _import(service, path)["imported_count"] == 2
    page = service.review_data("Test", limit=1)["data"]
    assert page["records"][0]["timestamp"].startswith("1950-01-01")
    assert page["pagination"]["has_more"]
    path = _csv(tmp_path, "1950-01-01,10\n1950-01-03,3\n")
    _import(service, path)
    rows = service.review_data("Test")["data"]["records"]
    assert len(rows) == 3 and rows[0]["values"]["Score"] == 10
    summary = service.list()["data"][0]
    assert summary["total_records"] == 3 and summary["total_days"] == 2
    _import(service, path, replace=True)
    assert service.list()["data"][0]["total_records"] == 2
    assert not service.edit("Test", {"values": [{"name": "Changed"}]})["success"]
    assert service.edit("Test", {"name": "New"})["success"]


@pytest.mark.parametrize(
    "content",
    [
        "bad,1\n",
        "2020-01-01,nan\n",
        "2020-01-01,inf\n",
        "2020-01-01,1,2\n",
        "2020-01-01,1\n2020-01-01,2\n",
        "2020-02-30,1\n",
        "",
    ],
)
def test_failed_replace_preserves_observations(service, tmp_path, content):
    _add(service)
    path = _csv(tmp_path)
    _import(service, path)
    before = service.review_data("Test")["data"]
    path = _csv(tmp_path, content)
    assert not service.import_data(
        "Test", path, columns=["date", "Score"], replace=True
    )["success"]
    assert service.review_data("Test")["data"] == before


def test_csv_preview_presets_skip_and_roundtrip(service, tmp_path):
    _add(service)
    config = {
        "separator": ";",
        "date_format": "%d.%m.%Y",
        "skip_rows": 1,
        "skip_columns": 1,
        "columns": ["date", "Score", "ignore"],
        "error_handling": "skip",
    }
    assert service.add_import_format("Semicolon", config)["success"]
    assert not service.add_import_format("semicolon", config)["success"]
    assert service.edit_import_format("SEMICOLON", config)["success"]
    path = _csv(tmp_path, "header\nx;01.01.1950;1;ignored\nx;bad;2;ignored\n")
    preview = service.import_preview("Test", path, format_name="Semicolon")["data"]
    assert preview["total_records"] == 1 and preview["skipped_rows"] == 1
    assert service.list()["data"][0]["total_records"] == 0
    result = service.import_data("Test", path, format_name="Semicolon")
    assert result["data"]["imported_count"] == 1
    exported = tmp_path / "export.csv"
    assert service.export_values("Test", exported)["data"]["count"] == 1
    assert service.clear("Test")["data"]["cleared_records"] == 1
    assert service.import_data(
        "Test", exported, columns=["date", "Score"], skip_rows=1
    )["success"]
    assert service.review_data("Test")["data"]["records"][0]["timestamp"].startswith(
        "1950"
    )
    assert len(service.import_get_info()["data"]["formats"]) == 1
    assert service.delete_import_format("semicolon")["success"]
    assert not service.delete_import_format("missing")["success"]


def test_bulk_clear_and_delete_are_atomic(service, tmp_path):
    _add(service)
    _import(service, _csv(tmp_path))
    assert not service.clear(["Test", "missing"])["success"]
    assert service.list()["data"][0]["total_records"] == 2
    assert not service.delete(["Test", "missing"])["success"]
    assert service.list()["data"][0]["total_records"] == 2
    assert service.clear("Test")["success"]
    assert len(service.list()["data"]) == 1
    assert service.delete("Test")["success"]


def test_json_definition_transfers_and_conflicts(service, tmp_path):
    _add(service)
    _import(service, _csv(tmp_path))
    path = tmp_path / "definitions.json"
    assert service.save(path)["data"]["count"] == 1
    payload = json.loads(path.read_text())
    assert "records" not in payload["indicators"][0]
    assert not service.load(path)["success"]
    assert service.load(path, on_conflict="skip")["data"]["skipped"] == ["Test"]
    assert service.list()["data"][0]["total_records"] == 2
    assert service.load(path, on_conflict="overwrite")["success"]
    assert service.list()["data"][0]["total_records"] == 0
    assert service.delete("Test")["success"]
    assert service.load(path)["data"]["loaded_count"] == 1
    payload["indicators"].append({"name": "Broken", "values": []})
    path.write_text(json.dumps(payload))
    assert not service.load(path, on_conflict="overwrite")["success"]
    assert len(service.list()["data"]) == 1


def test_recognition_creates_definition_without_executing_source(service, tmp_path):
    path = tmp_path / "Signal.mq5"
    path.write_text('#property indicator_label1 "Score"\nvoid OnStart() {}\n')
    result = service.recognize_from_file(path)
    assert result["data"]["name"] == "Signal"
    assert result["data"]["values"][0]["mt5"] == "0"
    assert not service.recognize_from_file(path)["success"]
    path = tmp_path / "Definition.json"
    path.write_text(json.dumps({"name": "Json", "values": [{"name": "Value"}]}))
    assert service.recognize_from_file(path)["success"]


def test_import_job_controls_and_rollback_on_cancellation(service, tmp_path):
    _add(service)
    _import(service, _csv(tmp_path))
    service.logs = Logs(EventBus())
    service.jobs = Mock()
    service.jobs.submit_job.return_value = {"job_id": "job"}
    path = _csv(tmp_path, "2021-01-01,10\n")
    assert service.import_data("Test", path, columns=["date", "Score"], replace=True)[
        "success"
    ]
    args = service.jobs.submit_job.call_args.args
    context = Mock(job_id="job")
    context.raise_if_cancelled.side_effect = InterruptedError("Cancelled")
    with pytest.raises(InterruptedError):
        args[0](context, *args[1:])
    assert service.list()["data"][0]["total_records"] == 2
    assert service.logs.list_active()["data"] == []
    record = Mock(kind="custom.import", owner="data-manager")
    record.to_dict.return_value = {"job_id": "job"}
    service.jobs.get_job.return_value = record
    for action in ("pause", "resume", "stop"):
        assert service.import_action("job", action)["success"]
    record.kind = "unrelated"
    assert not service.import_action("job", "stop")["success"]


def _cot_report():
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "CFTC_Contract_Market_Code",
            "As_of_Date_In_Form_YYYY-MM-DD",
            "Comm_Positions_Long_All",
            "Comm_Positions_Short_All",
            "NonComm_Positions_Long_All",
            "NonComm_Positions_Short_All",
            "Open_Interest_All",
        ]
    )
    writer.writerow(["001602", "2020-01-07", 1, 2, 3, 4, 10])
    return output.getvalue()


def test_cot_merges_by_contract_date_and_protects_system_definitions(service):
    result = service.update_cot(years=[2020], fetcher=lambda year: _cot_report())
    assert result["success"], result
    assert result["data"]["updated_count"] == 1
    assert service.update_cot(years=[2020], fetcher=lambda year: _cot_report())[
        "success"
    ]
    row = service.list()["data"][0]
    assert row["system"] and row["total_records"] == 1
    assert len(row["values"]) == 5
    assert not service.delete(row["name"])["success"]
    assert not service.edit(row["name"], {"name": "Changed"})["success"]
    assert service.clear(row["name"])["success"]


def test_cot_failure_across_years_preserves_database(service):
    result = service.update_cot(
        years=[2020, 2021],
        fetcher=lambda year: _cot_report() if year == 2020 else "invalid",
    )
    assert not result["success"]
    assert service.list()["data"] == []


def test_missing_database_is_not_created(tmp_path):
    path = tmp_path / "missing.db"
    assert not CustomData(HostPersistence(path)).list()["success"]
    assert not path.exists()


def test_large_import_clear_and_delete_respect_gateway_bounds(service, tmp_path):
    from datetime import UTC, datetime, timedelta

    _add(service)
    start = datetime(1950, 1, 1, tzinfo=UTC)
    path = _csv(
        tmp_path,
        "".join(
            f"{(start + timedelta(days=i)).isoformat()},{i}\n" for i in range(1001)
        ),
    )
    assert _import(service, path)["imported_count"] == 1001
    assert service.clear(["TEST", "test"])["data"]["cleared_records"] == 1001
    _import(service, path)
    assert service.delete(["Test", "TEST"])["success"]
    assert service.list()["data"] == []


def test_platform_mapping_edits_preserve_observations(service, tmp_path):
    _add(service)
    _import(service, _csv(tmp_path))
    result = service.edit("Test", {"values": [{"name": "Score", "mt5": "0"}]})
    assert result["success"], result
    assert service.list()["data"][0]["total_records"] == 2


def test_json_load_rolls_back_earlier_new_definitions_on_conflict(service, tmp_path):
    _add(service)
    path = tmp_path / "definitions.json"
    path.write_text(
        json.dumps(
            {
                "version": 1,
                "indicators": [
                    {"name": "New", "values": [{"name": "Score"}]},
                    {"name": "Test", "values": [{"name": "Score"}]},
                ],
            }
        )
    )
    assert not service.load(path)["success"]
    assert [row["name"] for row in service.list()["data"]] == ["Test"]


def test_real_background_import_records_values_and_logs(service, tmp_path):
    from app.core.host.resources import MemoryObservation, ResourceMonitor
    from app.host.jobs import JobManager

    with closing(sqlite3.connect(service.gateway.database_path)) as connection:
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
        persistence=service.gateway,
        resource_mgr=monitor,
        max_workers=1,
        use_process_pool=False,
    )
    service.jobs, service.logs = jobs, Logs(EventBus())
    try:
        _add(service)
        response = service.import_data(
            "Test", _csv(tmp_path), columns=["date", "Score"]
        )
        assert response["success"], response
        record = jobs.wait_for_job(response["data"]["job_id"], timeout=10)
        assert record.status == "COMPLETED", record.error_message
        assert service.list()["data"][0]["total_records"] == 2
        assert service.logs.list_active()["data"] == []
        assert service.logs.list()["data"]["entries"][0]["progress"] == 100
    finally:
        jobs.shutdown(cancel_futures=True)


def test_system_flag_and_name_validation(service):
    assert not service.add("Test", values=[{"name": "V"}], system="yes")["success"]
    assert not service.add("", values=[{"name": "V"}])["success"]
    assert not service.add("   ", values=[{"name": "V"}])["success"]
    assert not service.add("A" * 101, values=[{"name": "V"}])["success"]
    assert not service.add("Test\nName", values=[{"name": "V"}])["success"]


def test_edit_validation_errors(service):
    assert not service.edit("Test", {})["success"]
    assert not service.edit("Test", {"unsupported": 123})["success"]
    assert not service.edit("Missing", {"name": "New"})["success"]
    _add(service, "First")
    _add(service, "Second")
    assert not service.edit("Second", {"name": "First"})["success"]


def test_review_data_validation(service):
    _add(service)
    assert not service.review_data("Test", limit=0)["success"]
    assert not service.review_data("Test", limit=1001)["success"]
    assert not service.review_data("Test", limit="invalid")["success"]
    assert not service.review_data("Test", offset=-1)["success"]
    assert not service.review_data("Test", offset="invalid")["success"]
    assert not service.review_data("Missing")["success"]


def test_recognize_from_file_errors(service, tmp_path):
    text_file = tmp_path / "plain.txt"
    text_file.write_text("hello", encoding="utf-8")
    assert not service.recognize_from_file(text_file)["success"]

    bad_json = tmp_path / "bad.json"
    bad_json.write_text(json.dumps({"extra": 1}), encoding="utf-8")
    assert not service.recognize_from_file(bad_json)["success"]

    bad_mq = tmp_path / "empty.mq4"
    bad_mq.write_text("int start() { return(0); }", encoding="utf-8")
    assert not service.recognize_from_file(bad_mq)["success"]


def test_import_validation_and_errors(service, tmp_path):
    _add(service)
    path = _csv(tmp_path)
    assert not service.import_data("Test", path, format_name="NonExistent")["success"]
    assert not service.import_data("Test", path, columns=["date"])["success"]
    assert not service.import_data("Test", path, columns=["date", "Score", "Extra"])[
        "success"
    ]
    assert not service.import_data(
        "Test", path, columns=["date", "Score"], replace="not_bool"
    )["success"]
    assert not service.import_preview("Test", path, columns=["date", "Score"], limit=0)[
        "success"
    ]
    assert not service.import_preview(
        "Test", path, columns=["date", "Score"], limit=1001
    )["success"]


def test_import_action_validation(service):
    service.jobs = None
    assert not service.import_action("job-1", "pause")["success"]

    service.jobs = Mock()
    service.jobs.get_job.return_value = None
    assert not service.import_action("missing", "pause")["success"]

    job = Mock(kind="custom.import", owner="data-manager")
    service.jobs.get_job.return_value = job
    assert not service.import_action("job", "unknown_action")["success"]

    service.jobs.pause_job.return_value = False
    assert not service.import_action("job", "pause")["success"]


def test_definition_file_and_load_errors(service, tmp_path):
    path = tmp_path / "bad_load.json"
    path.write_text(json.dumps({"version": 2, "indicators": []}), encoding="utf-8")
    assert not service.load(path)["success"]
    assert not service.load(path, on_conflict="invalid_policy")["success"]

    path.write_text(
        json.dumps(
            {
                "version": 1,
                "indicators": [
                    {"name": "Dup", "values": [{"name": "Score"}]},
                    {"name": "dup", "values": [{"name": "Score"}]},
                ],
            }
        ),
        encoding="utf-8",
    )
    assert not service.load(path)["success"]

    path.write_text(
        json.dumps({"version": 1, "indicators": [{"name": "A", "unexpected": 1}]}),
        encoding="utf-8",
    )
    assert not service.load(path)["success"]


def test_cot_validation_and_fetch_archive(service):
    assert not service.update_cot(years=[1980])["success"]
    assert not service.update_cot(years=[2099])["success"]
    assert not service.update_cot(years=["2020"])["success"]
    assert not service.update_cot(years=[])["success"]

    _add(service, "COT001602")
    assert not service.update_cot(years=[2020], fetcher=lambda y: _cot_report())[
        "success"
    ]

    from app.workspace.data_manager.custom import fetch_cot

    zip_bytes = io.BytesIO()
    with zipfile.ZipFile(zip_bytes, "w") as zf:
        zf.writestr("annual.txt", "report_content")
    zip_bytes.seek(0)

    mock_resp = Mock()
    mock_resp.raise_for_status = Mock()
    mock_resp.iter_bytes.return_value = [zip_bytes.getvalue()]
    mock_cm = Mock()
    mock_cm.__enter__ = Mock(return_value=mock_resp)
    mock_cm.__exit__ = Mock(return_value=None)

    with patch("httpx.stream", return_value=mock_cm):
        content = fetch_cot(2020)
        assert content == "report_content"


def test_export_empty_and_missing_indicator(service, tmp_path):
    assert not service.export_values("Missing", tmp_path / "missing.csv")["success"]
    _add(service, "Empty")
    export_path = tmp_path / "empty.csv"
    res = service.export_values("Empty", export_path)
    assert res["success"]
    assert res["data"]["count"] == 0
    assert export_path.read_text(encoding="utf-8").strip() == "date,Score"


def test_import_format_validation_branches(service):
    assert not service.add_import_format("F1", {"unknown_key": 1})["success"]
    assert not service.add_import_format("F1", {"separator": " "})["success"]
    assert not service.add_import_format("F1", {"skip_rows": -1})["success"]
    assert not service.add_import_format("F1", {"skip_columns": "bad"})["success"]
    assert not service.add_import_format("F1", {"date_format": 123})["success"]
    assert not service.add_import_format("F1", {"columns": "not_list"})["success"]
    assert not service.add_import_format("F1", {"columns": ["date", 123]})["success"]
    assert not service.add_import_format("F1", {"columns": ["Score"]})["success"]
    assert not service.add_import_format("F1", {"columns": ["date", "Score", "Score"]})[
        "success"
    ]
    assert not service.add_import_format(
        "F1", {"columns": ["date", "Score"], "error_handling": "ignore"}
    )["success"]


def test_empty_targets_and_timestamp_validation(service, tmp_path):
    assert not service.delete([])["success"]
    assert not service.clear([])["success"]
    _add(service)
    path = _csv(tmp_path, "   ,1\n")
    assert not service.import_data("Test", path, columns=["date", "Score"])["success"]


def test_cot_report_non_finite_values(service):
    def bad_report():
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(
            [
                "CFTC_Contract_Market_Code",
                "As_of_Date_In_Form_YYYY-MM-DD",
                "Comm_Positions_Long_All",
                "Comm_Positions_Short_All",
                "NonComm_Positions_Long_All",
                "NonComm_Positions_Short_All",
                "Open_Interest_All",
            ]
        )
        writer.writerow(["001602", "2020-01-07", "nan", 2, 3, 4, 10])
        return output.getvalue()

    assert not service.update_cot(years=[2020], fetcher=lambda y: bad_report())[
        "success"
    ]


def test_import_values_conflict_on_changed_definition(service, tmp_path):
    _add(service)
    row = service._lookup(service.gateway, "Test")
    modified_row = dict(row)
    modified_row["data_type"] = "modified"
    path = _csv(tmp_path)
    config = service._import_config(None, {"columns": ["date", "Score"]})
    with pytest.raises(Exception):
        service._import_values(
            modified_row, path.read_text(encoding="utf-8"), config, replace=False
        )


def test_import_skip_max_errors_cap(service, tmp_path):
    _add(service)
    bad_lines = "\n".join(f"bad_{i},1" for i in range(105)) + "\n2020-01-01,1\n"
    path = _csv(tmp_path, bad_lines)
    result = service.import_data(
        "Test", path, columns=["date", "Score"], error_handling="skip"
    )
    assert result["success"]
    assert len(result["data"]["errors"]) == 100
    assert result["data"]["skipped_rows"] == 105
    assert result["data"]["imported_count"] == 1
