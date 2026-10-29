"""Qualify activity history, task lifecycle and event delivery."""

from argparse import ArgumentParser, Namespace
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import Mock

import httpx
import pytest
from app.host.events import EventBus
from app.workspace.data_manager.logs import Logs
from fastapi import FastAPI
from fastapi.testclient import TestClient


def test_history_pagination_filter_and_detached_results():
    logs = Logs(EventBus())
    for task, message in [("a", "first"), ("b", "second"), ("a", "third")]:
        assert logs.record_progress(task, progress=10, message=message)["success"]
    page = logs.list(limit=1, offset=1)["data"]
    assert page["total"] == 3
    assert page["entries"][0]["message"] == "second"
    entries = logs.list(task_id="a")["data"]["entries"]
    assert [item["message"] for item in entries] == ["third", "first"]
    entries[0]["message"] = "mutated"
    assert logs.list()["data"]["entries"][0]["message"] == "third"


def test_progress_clear_and_terminal_states():
    bus = EventBus()
    logs = Logs(bus)
    logs.record_progress("a", progress=0, message="Started")
    logs.record_progress("a", progress=50)
    assert len(logs.list()["data"]["entries"]) == 1
    assert logs.list_active()["data"][0]["progress"] == 50
    assert logs.clear()["data"]["cleared_count"] == 1
    assert logs.list()["data"]["total"] == 0
    assert len(logs.list_active()["data"]) == 1
    assert bus.get_snapshot("logs").events[-1].event_type == "datamanager.logs.cleared"
    logs.record_progress("a", progress=100, message="Done")
    logs.record_progress("b", progress=1)
    logs.record_progress("b", progress=-1, message="Failed", level="error")
    assert logs.list_active()["data"] == []
    event = bus.get_snapshot("logs").events[-1]
    assert event.payload["workspace"] == "data-manager"
    assert event.payload["entry"]["level"] == "error"


def test_bounded_history_and_plain_text():
    logs = Logs(EventBus(), max_characters=10)
    logs.record_progress("a", progress=1, message="123456")
    logs.record_progress("a", progress=2, message="abcdef")
    assert logs.list()["data"]["total"] == 1
    logs.record_progress("a", progress=3, message="<script>unchanged")
    assert logs.list()["data"]["entries"][0]["message"] == "<script>un"
    assert logs.list()["data"]["total"] == 1


@pytest.mark.parametrize("progress", [True, float("nan"), float("inf"), 101, "50"])
def test_invalid_progress_has_no_side_effects(progress):
    bus = EventBus()
    logs = Logs(bus)
    assert not logs.record_progress("a", progress=progress, message="bad")["success"]
    assert logs.list_active()["data"] == []
    assert bus.current_cursor == 0


@pytest.mark.parametrize(
    "kwargs", [{"limit": True}, {"limit": 0}, {"offset": -1}, {"task_id": ""}]
)
def test_invalid_queries(kwargs):
    assert not Logs(EventBus()).list(**kwargs)["success"]


def test_concurrent_producers():
    bus = EventBus(ring_capacity=500)
    logs = Logs(bus)

    def produce(index):
        task = f"task-{index}"
        logs.record_progress(task, progress=1, message="Started")
        logs.record_progress(task, progress=100, message="Done")

    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(produce, range(100)))
    assert logs.list(limit=1000)["data"]["total"] == 200
    assert logs.list_active()["data"] == []
    assert bus.current_cursor == 200


@pytest.mark.parametrize("capacity", [True, 0, -1, "10"])
def test_invalid_capacity(capacity):
    with pytest.raises(ValueError, match="positive integer"):
        Logs(EventBus(), max_characters=capacity)


@pytest.mark.parametrize(
    "kwargs", [{"task_id": ""}, {"task_id": " "}, {"message": None}, {"level": "fatal"}]
)
def test_invalid_update_fields(kwargs):
    logs = Logs(EventBus())
    values = {"task_id": "a", "progress": 1, "message": "hello"}
    values.update(kwargs)
    assert not logs.record_progress(**values)["success"]
    assert logs.list()["data"]["total"] == 0


def test_http_and_cli_share_backend_history(monkeypatch):
    from app.core.host.transport import register_transport_exception_handlers
    from app.workspace.data_manager import create_router, logs

    application = FastAPI()
    application.state.data_logs = Logs(EventBus())
    sessions = Mock()
    sessions.validate_session.return_value = object()
    sessions.authorize.return_value = True
    application.state.sessions = sessions
    application.include_router(create_router())
    register_transport_exception_handlers(application)
    application.state.data_logs.record_progress(
        "job", progress=30, message="Downloading"
    )
    monkeypatch.setenv("HARUQUANTAI_SESSION_TOKEN", "test-token")
    settings = Mock()
    settings.get.side_effect = lambda scope, key, default: default
    monkeypatch.setattr(logs, "SettingsManager", lambda: settings)
    real_client = httpx.Client
    with TestClient(application) as backend:

        def request(request):
            response = backend.request(
                request.method, str(request.url), headers=dict(request.headers)
            )
            return httpx.Response(response.status_code, json=response.json())

        monkeypatch.setattr(
            logs.httpx,
            "Client",
            lambda **kwargs: real_client(transport=httpx.MockTransport(request)),
        )
        args = Namespace(log_command="list", task_id=None, limit=100, offset=0)
        assert logs.run_log_command(args, ArgumentParser())["data"]["total"] == 1
        args.log_command = "list-active"
        assert (
            logs.run_log_command(args, ArgumentParser())["data"][0]["task_id"] == "job"
        )
        args.log_command = "clear"
        assert (
            logs.run_log_command(args, ArgumentParser())["data"]["cleared_count"] == 1
        )
        assert len(application.state.data_logs.list_active()["data"]) == 1
        sessions.authorize.return_value = False
        assert (
            backend.post(
                "/api/v1/data/logs/clear", headers={"X-Peer-Id": "cli"}
            ).status_code
            == 403
        )
        sessions.validate_session.return_value = None
        assert (
            backend.get("/api/v1/data/logs", headers={"X-Peer-Id": "cli"}).status_code
            == 401
        )


def test_logged_worker_failure_cleans_active_tasks():
    from app.workspace.data_manager.logs import run_logged_task

    logs = Logs(EventBus())
    context = Mock(job_id="job")

    def action(tracked):
        tracked.wait_if_paused()
        tracked.report_progress(50, "AAPL")
        raise RuntimeError("provider failure")

    with pytest.raises(RuntimeError):
        run_logged_task(logs, context, action)
    assert logs.list_active()["data"] == []
    assert logs.list()["data"]["entries"][0]["level"] == "error"


def test_cli_reports_missing_session_and_backend(monkeypatch):
    from app.workspace.data_manager import logs

    args = Namespace(log_command="list-active")
    monkeypatch.delenv("HARUQUANTAI_SESSION_TOKEN", raising=False)
    assert (
        logs.run_log_command(args, ArgumentParser())["error"]["code"] == "unauthorized"
    )
    monkeypatch.setenv("HARUQUANTAI_SESSION_TOKEN", "test-token")
    monkeypatch.setattr(logs, "SettingsManager", Mock(side_effect=OSError))
    assert (
        logs.run_log_command(args, ArgumentParser())["error"]["code"] == "unavailable"
    )
