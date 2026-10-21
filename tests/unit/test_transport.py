"""Verify gateway contracts, authenticated settings persistence and event delivery.

Description:
    Exercise real FastAPI requests against isolated HostPersistence stores,
    including typed settings patches, redaction, atomic account changes and errors.
Purpose:
    FEAT-HOST-TRANSPORT: Verify HTTP contracts and operation boundaries.
Key Capabilities:
    - FR-HOST-TRANSPORT-GATEWAY-APP: Test envelopes and settings transactions.
      Associated: test_settings_ui_contract_and_secret_boundaries().
      Logging: assert error boundaries and post-commit event metadata.
    - FR-HOST-TRANSPORT-SESSION-AUTH: Test account rotation and durable revocation.
      Associated: test_account_rotation_is_durable_and_revokes_other_gateway_cache().
      Logging: session and persistence operations emit structured FR logs.
Python API Usage:
    pytest.main(["tests/unit/test_transport.py", "--no-cov"])
CLI Usage:
    uv run pytest tests/unit/test_transport.py --no-cov
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest
from app.host import events as host_events
from app.host.persistence import HostPersistence
from app.host.response import (
    ApiResponse,
    ApiResponseCLI,
    ResponseMetadata,
    StandardError,
    StandardResponse,
)
from app.host.session import SessionManager, hash_password
from app.host.settings import SettingsManager
from app.host.transport import (
    CORE_EVENT_CHANNELS,
    ConnectionTest,
    EventBus,
    HostEvent,
    ServletConnection,
    ServletConstants,
    TransportCLI,
    TransportMiddleware,
    create_host_app,
    extract_bearer_token,
    get_global_event_bus,
    register_transport_exception_handlers,
)
from fastapi import APIRouter, FastAPI, HTTPException
from fastapi.testclient import TestClient
from pydantic import BaseModel


@pytest.fixture(autouse=True)
def _isolate_default_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Redirect HostPersistence.DEFAULT_DB_PATH to an isolated temporary SQLite file."""
    db_file = tmp_path / "transport_test.db"
    monkeypatch.setattr(HostPersistence, "DEFAULT_DB_PATH", db_file)
    return db_file


def _create_isolated_session_manager(tmp_path: Path | None = None) -> SessionManager:
    """Create a SessionManager backed by an isolated temporary SQLite DB."""
    return SessionManager(host_instance_id="test-host-01")


# ============================================================================
# 1. Response Envelope & StandardError Tests (app/host/response.py)
# ============================================================================


def test_standard_response_and_error_invariants(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Verify StandardResponse, ApiResponse, ApiResponseCLI, and invariants."""
    ok = StandardResponse.success(
        data={"symbol": "EURUSD"},
        message="Fetched",
        request_id="req-100",
        duration_ms=1.5,
        side_effects=False,
        extensions={"source": "cache"},
    )
    assert ok.is_success is True
    assert ok.is_error is False
    assert bool(ok) is True
    assert ok.unwrap() == {"symbol": "EURUSD"}
    assert ok.error_code is None
    assert ok.request_id == "req-100"
    ok_dict = ok.to_dict()
    assert ok_dict["status"] == "success"
    assert ok_dict["request_id"] == "req-100"

    api_ok = ApiResponse.ok(
        data={"symbol": "EURUSD"},
        meta={"message": "Fetched", "duration_ms": 1.5, "source": "cache"},
        request_id="req-100",
    )
    assert api_ok["status"] == "success"
    assert api_ok["data"] == {"symbol": "EURUSD"}
    assert api_ok["request_id"] == "req-100"
    assert api_ok["metadata"]["extensions"] == {"source": "cache"}

    err = StandardError(
        code="FEED_DOWN",
        message="Feed offline",
        details={"retry_in": 5},
        retryable=True,
    )
    fail: StandardResponse[dict[str, Any]] = StandardResponse.failure(
        message="Operation failed",
        error=err,
        request_id="req-101",
        duration_ms=2.0,
    )
    assert fail.is_error is True
    assert fail.is_success is False
    assert bool(fail) is False
    assert fail.error_code == "FEED_DOWN"
    with pytest.raises(RuntimeError, match="FEED_DOWN"):
        fail.unwrap()

    api_err = ApiResponse.error(
        code="FEED_DOWN",
        message="Feed offline",
        details={"retry_in": 5},
        status_code=503,
        request_id="req-101",
    )
    assert api_err["status"] == "error"
    assert api_err["status_code"] == 503
    assert api_err["error"]["code"] == "FEED_DOWN"
    assert api_err["error"]["retryable"] is True
    with pytest.raises(ValueError, match="status_code"):
        ApiResponse.error("BAD_STATUS", "Invalid status", status_code=99)

    assert ApiResponseCLI.run(["--verify", "--json"]) == 0
    cli_out = json.loads(capsys.readouterr().out)
    assert cli_out["status"] == "verified"

    # Invariant checks
    with pytest.raises(ValueError, match="Error code"):
        StandardError(code="  ", message="msg")
    with pytest.raises(ValueError, match="Error message"):
        StandardError(code="CODE", message="")
    with pytest.raises(ValueError, match="timestamp_utc"):
        ResponseMetadata(timestamp_utc="")
    with pytest.raises(ValueError, match="duration_ms cannot be negative"):
        ResponseMetadata(timestamp_utc="2026-01-01T00:00:00Z", duration_ms=-1.0)

    meta = ResponseMetadata(timestamp_utc="2026-01-01T00:00:00Z")
    with pytest.raises(ValueError, match="Invalid status"):
        StandardResponse(
            status="invalid",  # type: ignore[arg-type]
            message="m",
            data=None,
            error=None,
            metadata=meta,
        )
    with pytest.raises(ValueError, match="must not contain an error"):
        StandardResponse(
            status="success",
            message="m",
            data=None,
            error=err,
            metadata=meta,
        )
    with pytest.raises(ValueError, match="must contain a StandardError"):
        StandardResponse(
            status="error",
            message="m",
            data=None,
            error=None,
            metadata=meta,
        )
    with pytest.raises(TypeError, match="instance of StandardError"):
        StandardResponse(
            status="error",
            message="m",
            data=None,
            error="bad",  # type: ignore[arg-type]
            metadata=meta,
        )


# ============================================================================
# 2. EventBus Multi-Channel Pub/Sub, Replay, Gap & Slow Consumer Tests
# ============================================================================


def test_sensitive_routes_require_session_and_scope(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from unittest.mock import Mock

    config = SettingsManager()
    config.reload()
    monkeypatch.setattr("app.host.transport.settings", config)
    sessions = SessionManager()
    token, session = sessions.create_session("admin", "audit")
    headers = {"Authorization": f"Bearer {token}"}
    jobs = Mock()
    jobs.list_jobs.return_value = []
    jobs.get_job.return_value = None
    jobs.cancel_job.return_value = True
    client = TestClient(
        create_host_app(session_mgr=sessions, job_mgr=jobs, require_auth=True)
    )
    routes = [
        ("GET", "/settings", None),
        (
            "PUT",
            "/settings",
            {
                "changes": {"app.general": {"header_custom_text": "audit"}},
                "expected_revision": 0,
            },
        ),
        ("GET", "/diagnostics", None),
        ("GET", "/resources", None),
        ("GET", "/jobs", None),
        ("GET", "/jobs/job-audit", None),
        ("POST", "/jobs/job-audit/cancel", None),
    ]
    for prefix in ("", "/api/v1", "/api/v2"):
        for method, path, payload in routes:
            assert (
                client.request(method, prefix + path, json=payload).status_code == 401
            )
    jobs.cancel_job.assert_not_called()
    assert client.get("/api/v1/jobs", headers=headers).status_code == 200
    assert (
        client.post("/api/v1/jobs/job-audit/cancel", headers=headers).status_code == 200
    )
    jobs.cancel_job.assert_called_once_with("job-audit")
    jobs.cancel_job.reset_mock()
    monkeypatch.setattr(sessions, "authorize", lambda *_: False)
    for method, path, payload in routes:
        assert (
            client.request(
                method, "/api/v1" + path, headers=headers, json=payload
            ).status_code
            == 403
        )
    jobs.cancel_job.assert_not_called()
    sessions.revoke_session(session.session_id)
    assert client.get("/api/v1/jobs", headers=headers).status_code == 401


def test_transport_event_exports_share_implementation_identity() -> None:
    """Transport and event imports must share one class and channel definition."""
    assert EventBus is host_events.EventBus
    assert HostEvent is host_events.HostEvent
    assert CORE_EVENT_CHANNELS is host_events.CORE_EVENT_CHANNELS
    assert isinstance(get_global_event_bus(), host_events.EventBus)


def test_event_bus_publish_subscribe_replay_gap_and_slow_consumer(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Verify EventBus monotonic cursors, ring buffer gap, and queue bounds."""
    caplog.set_level(logging.DEBUG)
    bus = EventBus(ring_capacity=3, max_queue_size=2)
    assert set(CORE_EVENT_CHANNELS).issubset(set(bus.channels))

    # Subscribe to specific channel and wildcard
    sub_jobs, q_jobs, replay_0, gap_0 = bus.subscribe(channels=["jobs"])
    assert replay_0 == []
    assert gap_0 is False

    ev1 = bus.publish("jobs", "started", {"job_id": "j1"})
    ev2 = bus.publish("settings.changed", "update", {"revision": 2})
    ev3 = bus.publish("jobs", "progress", {"job_id": "j1", "pct": 50})

    assert ev1.cursor == 1
    assert ev2.cursor == 2
    assert ev3.cursor == 3
    assert bus.current_cursor == 3

    # q_jobs should have ev1 and ev3 (maxsize=2 is now full)
    assert q_jobs.qsize() == 2

    # Publishing a 3rd 'jobs' event triggers slow-consumer drop without raising
    ev4 = bus.publish("jobs", "completed", {"job_id": "j1"})
    assert ev4.cursor == 4
    assert q_jobs.qsize() == 2

    # Ring capacity is 3 (cursors 2, 3, 4 retained; cursor 1 evicted)
    # Requesting since_cursor=0 should report has_gap=True
    sub_late, _, replay_late, gap_late = bus.subscribe(
        channels=["jobs"], since_cursor=0
    )
    assert gap_late is True
    assert [e.cursor for e in replay_late] == [3, 4]

    # Update subscription dynamically
    assert bus.update_subscription(sub_late, ["system", "logs"]) is True
    assert bus.update_subscription("nonexistent-sub", ["system"]) is False

    # Snapshot queries
    snap = bus.get_snapshot(channel="jobs", since_cursor=0, limit=10)
    assert snap.has_gap is True
    assert snap.newest_cursor == 4
    assert [e.cursor for e in snap.events] == [3, 4]

    bus.unsubscribe(sub_jobs)
    bus.unsubscribe(sub_late)
    bus.clear()
    assert bus.get_snapshot("*").events == []

    # Global singleton check
    global_bus = get_global_event_bus()
    assert isinstance(global_bus, EventBus)
    for level in (logging.DEBUG, logging.INFO, logging.WARNING):
        assert any(
            record.levelno == level
            and getattr(record, "fr_id", None) == host_events.FR_BUS
            for record in caplog.records
        )


def test_helper_parsers_and_token_extraction() -> None:
    """Verify helper functions for bearer tokens and TransportCLI formatting."""
    assert extract_bearer_token("Bearer abc123") == "abc123"
    assert extract_bearer_token(None, "query_tok") == "query_tok"
    assert extract_bearer_token("Basic xyz", None) is None
    assert extract_bearer_token("Bearer   ", None) is None
    formatted = TransportCLI.format_output({"ok": True})
    assert json.loads(formatted) == {"ok": True}


# ============================================================================
# 3. Middleware & Exception Handler Envelopes
# ============================================================================


def test_middleware_and_exception_handlers() -> None:
    """Verify X-Request-Id, X-Response-Time-Ms, 500, HTTPException, and 422."""
    app = FastAPI()
    app.add_middleware(TransportMiddleware)
    register_transport_exception_handlers(app)

    class ItemBody(BaseModel):
        count: int

    @app.post("/validate-test")
    def validate_route(body: ItemBody) -> dict[str, int]:
        return {"count": body.count}

    @app.get("/http-err")
    def http_err_route() -> None:
        raise HTTPException(status_code=409, detail={"reason": "revision conflict"})

    @app.get("/unhandled-err")
    def unhandled_err_route() -> None:
        raise RuntimeError("unexpected database crash")

    client = TestClient(app, raise_server_exceptions=False)

    # 1. Validation error (422) with custom X-Request-Id
    r_val = client.post(
        "/validate-test",
        json={"count": "not-an-int"},
        headers={"X-Request-Id": "req-custom-422"},
    )
    assert r_val.status_code == 422
    assert r_val.headers["X-Request-Id"] == "req-custom-422"
    assert "X-Response-Time-Ms" in r_val.headers
    val_body = r_val.json()
    assert val_body["status"] == "error"
    assert val_body["error"]["code"] == "VALIDATION_ERROR"
    assert len(val_body["error"]["issues"]) >= 1

    # 2. HTTPException (409) with auto-generated X-Request-Id
    r_http = client.get("/http-err")
    assert r_http.status_code == 409
    assert r_http.headers["X-Request-Id"].startswith("req-")
    http_body = r_http.json()
    assert http_body["status"] == "error"
    assert http_body["error"]["code"] == "HTTP_409"

    # 3. Unhandled RuntimeError caught by TransportMiddleware (500)
    r_500 = client.get("/unhandled-err")
    assert r_500.status_code == 500
    body_500 = r_500.json()
    assert body_500["status"] == "error"
    assert body_500["error"]["code"] == "INTERNAL_SERVER_ERROR"
    assert "unexpected database crash" in body_500["error"]["message"]


# ============================================================================
# 4. Host Gateway Auth, Shell Status, SSE (/events) & WebSocket (/ws)
# ============================================================================


def test_gateway_auth_shell_and_event_routes(tmp_path: Path) -> None:
    """Verify /auth/login, /sessions/me, /status, /readiness, /app-loaded, /about."""
    sess_mgr = _create_isolated_session_manager(tmp_path)
    bus = EventBus()
    pw_hash = hash_password("correct-secret")

    extra_router = APIRouter()

    @extra_router.get("/custom-extra")
    def extra_endpoint() -> dict[str, bool]:
        return {"extra": True}

    app = create_host_app(
        event_bus=bus,
        session_mgr=sess_mgr,
        password_hash=pw_hash,
        require_auth=True,
        heartbeat_sec=0.05,
        extra_routers=[extra_router],
    )
    client = TestClient(app)

    # Extra router mounted
    assert client.get("/custom-extra").status_code == 200

    # Invalid password -> 401
    bad_login = client.post("/api/v1/auth/login", json={"password": "wrong-password"})
    assert bad_login.status_code == 401
    assert bad_login.json()["error"]["code"] == "INVALID_CREDENTIALS"

    # Unauthenticated /sessions/me & /app-loaded -> 401
    assert client.get("/api/v1/sessions/me").status_code == 401
    assert client.post("/api/v1/app-loaded", json={}).status_code == 401

    # Valid login -> 200 with opaque token and ISO expires_at
    ok_login = client.post(
        "/api/v1/auth/login",
        json={"username": "operator", "password": "correct-secret"},
    )
    assert ok_login.status_code == 200
    login_data = ok_login.json()["data"]
    token = login_data["token"]
    assert len(token) == 64
    assert "T" in login_data["expires_at"]

    auth_headers = {"Authorization": f"Bearer {token}"}

    # Verified /sessions/me
    me_res = client.get("/api/v1/sessions/me", headers=auth_headers)
    assert me_res.status_code == 200
    assert me_res.json()["data"]["username"] == "operator"

    # Shell endpoints: /status, /readiness, /app-loaded, /about
    status_res = client.get("/api/v1/status")
    assert status_res.status_code == 200
    assert status_res.json()["data"]["cpu_count"] >= 1
    assert status_res.json()["data"]["app_loaded"] is False

    loaded_res = client.post("/api/v1/app-loaded", json={}, headers=auth_headers)
    assert loaded_res.status_code == 200
    assert loaded_res.json()["data"]["acknowledged"] is True
    assert client.get("/api/v1/status").json()["data"]["app_loaded"] is True

    ready_res = client.get("/api/v1/readiness")
    assert ready_res.status_code == 200
    assert ready_res.json()["data"]["is_ready"] is True

    about_res = client.get("/api/v1/about")
    assert about_res.status_code == 200
    assert about_res.json()["data"]["application"] == "HaruQuantAI"

    # Publish & snapshot REST routes
    pub_res = client.post(
        "/api/v1/events/publish",
        json={
            "channel": "settings.changed",
            "event_type": "update",
            "payload": {"revision": 3},
        },
    )
    assert pub_res.status_code == 200

    snap_res = client.get("/api/v1/events/snapshot?channel=settings.changed")
    assert snap_res.status_code == 200
    assert len(snap_res.json()["data"]["events"]) == 1

    ch_res = client.get("/api/v1/events/channels")
    assert ch_res.status_code == 200
    assert "settings.changed" in ch_res.json()["data"]["active_channels"]


def test_sse_events_streaming_replay_gap_and_heartbeat(tmp_path: Path) -> None:
    """Verify GET /api/v1/events SSE streaming with replay, gap, and auth."""
    sess_mgr = _create_isolated_session_manager(tmp_path)
    bus = EventBus(ring_capacity=2)
    app = create_host_app(
        event_bus=bus,
        session_mgr=sess_mgr,
        require_auth=True,
        heartbeat_sec=0.02,
    )
    client = TestClient(app)

    # Unauthorized SSE attempt -> 401
    unauth_sse = client.get("/api/v1/events?channels=settings.changed")
    assert unauth_sse.status_code == 401

    token, _ = sess_mgr.create_session("operator", "127.0.0.1")
    headers = {"Authorization": f"Bearer {token}"}

    # Publish 3 events on ring_capacity=2 so cursor 1 is evicted (gap at since_cursor=0)
    bus.publish("settings.changed", "update", {"revision": 1})
    bus.publish("settings.changed", "update", {"revision": 2})
    bus.publish("settings.changed", "update", {"revision": 3})

    sse_res = client.get(
        "/api/v1/events?channels=settings.changed&since_cursor=0&limit=2",
        headers=headers,
    )
    assert sse_res.status_code == 200
    assert "text/event-stream" in sse_res.headers["content-type"]
    body_text = sse_res.text
    assert "event: system.gap" in body_text
    assert "event: settings.changed" in body_text
    assert '"revision":2' in body_text or '"revision": 2' in body_text
    assert '"revision":3' in body_text or '"revision": 3' in body_text


def test_websocket_streaming_and_commands(tmp_path: Path) -> None:
    """Verify WebSocket /api/v1/ws replay, ping/pong, subscribe, and publish."""
    sess_mgr = _create_isolated_session_manager(tmp_path)
    bus = EventBus(ring_capacity=2)
    bus.publish("jobs", "queued", {"job_id": "j-1"})
    bus.publish("jobs", "running", {"job_id": "j-1"})
    bus.publish("jobs", "done", {"job_id": "j-1"})

    app = create_host_app(
        event_bus=bus,
        session_mgr=sess_mgr,
        require_auth=False,
    )
    client = TestClient(app)

    with client.websocket_connect("/api/v1/ws?channels=jobs&since_cursor=0") as ws:
        # 1. Should receive initial gap frame + 2 replay frames (cursors 2 and 3)
        gap_msg = ws.receive_json()
        assert gap_msg["event_type"] == "gap"
        rep1 = ws.receive_json()
        rep2 = ws.receive_json()
        assert rep1["cursor"] == 2
        assert rep2["cursor"] == 3

        # 2. Ping -> Pong
        ws.send_json({"action": "ping"})
        pong = ws.receive_json()
        assert pong["event_type"] == "pong"

        # 3. Dynamic channel subscription update
        ws.send_json({"action": "subscribe", "channels": ["databanks", "jobs"]})
        sub_ack = ws.receive_json()
        assert sub_ack["event_type"] == "subscribed"

        # 4. Publish via WebSocket and receive broadcast
        ws.send_json(
            {
                "action": "publish",
                "channel": "databanks",
                "event_type": "strategy_added",
                "payload": {"strategy_id": "strat-42"},
            }
        )
        live_ev = ws.receive_json()
        assert live_ev["channel"] == "databanks"
        assert live_ev["payload"]["strategy_id"] == "strat-42"

        # 5. Clean close action
        ws.send_json({"action": "close"})


def test_transport_cli_main(capsys: pytest.CaptureFixture[str]) -> None:
    """Verify standalone CLI TransportCLI.run() execution including diagnostics."""
    assert TransportCLI.run(["--test-bus"]) == 0
    out_test = capsys.readouterr().out
    assert "settings.changed" in out_test

    assert TransportCLI.run([]) == 0
    out_default = json.loads(capsys.readouterr().out)
    assert "core_channels" in out_default
    conn_test = out_default["connection_test"]
    assert conn_test["ping_local"]["reachable"] is True
    assert "reachable" in conn_test["ping_remote"]
    assert conn_test["latency"]["samples"] == 3
    assert conn_test["latency"]["packet_loss_pct"] == 0.0
    assert conn_test["diagnostics"]["dns_resolved"] is True
    assert conn_test["diagnostics"]["reachable"] is True
    assert conn_test["diagnostics_failure"]["dns_resolved"] is False
    s_conn = out_default["servlet_connection"]
    assert s_conn["saved"]["connection_id"] == "demo-conn"
    assert len(s_conn["listed"]) == 1
    assert s_conn["tested"]["test_result"]["reachable"] is True
    assert s_conn["deleted"]["deleted"] is True
    s_const = out_default["servlet_constants"]
    assert s_const["constants"]["application"] == "HaruQuantAI"
    assert s_const["system_specs"]["cpu_cores"] >= 1


def test_gateway_settings_diagnostics_and_jobs_routes(tmp_path: Path) -> None:
    """Verify /api/v1/auth, /api/v1/settings, /api/v1/diagnostics, and /api/v1/jobs."""
    from app.host.jobs import JobManager
    from app.host.resources import ResourceMonitor
    from app.host.settings import settings as host_settings

    host_settings.reload()
    sess_mgr = SessionManager(host_instance_id="gov-host-01")
    res_mgr = ResourceMonitor(scratch_root=tmp_path / "scratch")
    job_mgr = JobManager(
        resource_mgr=res_mgr,
        use_process_pool=False,
    )

    try:
        bus = EventBus()
        app = create_host_app(
            event_bus=bus,
            session_mgr=sess_mgr,
            resource_mgr=res_mgr,
            job_mgr=job_mgr,
            require_auth=False,
        )
        client = TestClient(app)

        # 1. /api/v1/auth (POST login and GET session verification)
        login_res = client.post(
            "/api/v1/auth",
            json={"username": "admin", "password": "any"},
        )
        assert login_res.status_code == 200
        tok = login_res.json()["data"]["token"]
        auth_me = client.get(
            "/api/v1/auth",
            headers={"Authorization": f"Bearer {tok}"},
        )
        assert auth_me.status_code == 200
        assert auth_me.json()["data"]["username"] == "admin"

        # 2. /api/v1/diagnostics & /api/v1/resources
        diag_res = client.get("/api/v1/diagnostics")
        assert diag_res.status_code == 200
        diag_data = diag_res.json()["data"]
        assert "hardware" in diag_data
        assert "worker_capacity" in diag_data
        assert "memory_watchdog" in diag_data

        res_res = client.get("/api/v1/resources")
        assert res_res.status_code == 200
        assert res_res.json()["data"]["worker_capacity"]["allocated_workers"] >= 1

        # 3. /api/v1/settings GET & PUT with revision conflict checks
        get_set = client.get("/api/v1/settings")
        assert get_set.status_code == 200
        rev0 = get_set.json()["data"]["revision"]

        put_ok = client.put(
            "/api/v1/settings",
            json={
                "expected_revision": rev0,
                "changes": {"app.general": {"header_custom_text": "gateway_user"}},
            },
        )
        assert put_ok.status_code == 200
        rev1 = put_ok.json()["data"]["revision"]
        assert rev1 >= 1

        put_conflict = client.put(
            "/api/v1/settings",
            json={
                "expected_revision": rev0,
                "changes": {"app.general": {"header_custom_text": "stale_write"}},
            },
        )
        assert put_conflict.status_code == 409
        assert put_conflict.json()["error"]["code"] == "REVISION_CONFLICT"

        # 4. /api/v1/jobs, /api/v1/jobs/{job_id}, /api/v1/jobs/{job_id}/cancel
        list_res = client.get("/api/v1/jobs")
        assert list_res.status_code == 200
        assert "jobs" in list_res.json()["data"]

        missing_job = client.get("/api/v1/jobs/nonexistent-job-999")
        assert missing_job.status_code == 404
        assert missing_job.json()["error"]["code"] == "JOB_NOT_FOUND"

        cancel_missing = client.post("/api/v1/jobs/nonexistent-job-999/cancel")
        assert cancel_missing.status_code == 404
        assert cancel_missing.json()["error"]["code"] == "JOB_NOT_CANCELLABLE"
    finally:
        job_mgr.shutdown(wait=True)
        res_mgr.watchdog.stop()


def test_security_headers_injected_on_responses() -> None:
    """Verify FR-HOST-TRANSPORT-MIDDLEWARE injects security headers."""
    app = create_host_app()
    with TestClient(app) as client:
        resp = client.get("/status")
        assert resp.status_code == 200
        assert resp.headers.get("x-content-type-options") == "nosniff"
        assert resp.headers.get("x-frame-options") == "DENY"
        assert resp.headers.get("referrer-policy") == "no-referrer"
        assert "x-request-id" in resp.headers
        assert "x-response-time-ms" in resp.headers


def test_connection_test_utility(caplog: pytest.LogCaptureFixture) -> None:
    """Verify FR-HOST-TRANSPORT-PING, FR-HOST-TRANSPORT-LATENCY, and FR-HOST-TRANSPORT-DIAGNOSE."""
    caplog.set_level(logging.INFO)
    ping_res = ConnectionTest.ping_endpoint("127.0.0.1", timeout_seconds=1.0)
    assert "reachable" in ping_res
    assert "latency_ms" in ping_res
    assert ping_res["host"] == "127.0.0.1"
    assert ping_res["url"] == "127.0.0.1"

    latency_res = ConnectionTest.check_latency("127.0.0.1", port=443, samples=2)
    assert latency_res["samples"] == 2
    assert latency_res["port"] == 443
    assert "avg_latency_ms" in latency_res
    assert "packet_loss_pct" in latency_res

    diag_res = ConnectionTest.diagnose_network("127.0.0.1:80")
    assert diag_res["dns_resolved"] is True
    assert diag_res["port"] == 80
    assert "127.0.0.1" in diag_res["ip_addresses"]

    for fr_id in (
        "FR-HOST-TRANSPORT-PING",
        "FR-HOST-TRANSPORT-LATENCY",
        "FR-HOST-TRANSPORT-DIAGNOSE",
    ):
        assert any(getattr(r, "fr_id", None) == fr_id for r in caplog.records)


def test_servlet_connection_crud_and_routes(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """Verify FR-HOST-SERVLET-CONN-LIST/SAVE/DELETE/TEST and HostPersistence vault isolation."""
    caplog.set_level(logging.INFO)
    servlet = ServletConnection()
    assert servlet.list_connections() == []

    saved = servlet.save_connection(
        {
            "connection_id": "conn-direct-1",
            "provider": "binance",
            "name": "Direct Spot",
            "endpoint": "127.0.0.1",
            "api_secret": "raw_plaintext_secret_value",
        }
    )
    assert saved["connection_id"] == "conn-direct-1"
    assert saved["provider"] == "binance"
    assert saved["api_secret"] != "raw_plaintext_secret_value"
    assert (
        saved["vault_refs"]["api_secret"]
        == "vault://connections/conn-direct-1/api_secret"
    )

    # Verify SQLite host_entities never stores plaintext credentials
    entity_rows = HostPersistence.read_entity("connection", "conn-direct-1")
    assert len(entity_rows) == 1
    assert "raw_plaintext_secret_value" not in str(entity_rows[0]["payload"])

    assert len(servlet.list_connections(provider="binance")) == 1
    assert servlet.list_connections(provider="other") == []

    inline_test = servlet.test_connection({"endpoint": "127.0.0.1"})
    assert inline_test["endpoint"] == "127.0.0.1"
    assert "test_result" in inline_test

    del_direct = servlet.delete_connection("conn-direct-1")
    assert del_direct["deleted"] is True
    assert del_direct["revoked_vault_refs"] == 1

    sessions = _create_isolated_session_manager(tmp_path)
    app = create_host_app(session_mgr=sessions)
    with TestClient(app) as client:
        # 1. List initially empty
        res = client.get("/api/v1/connections")
        assert res.status_code == 200
        assert res.json()["data"]["connections"] == []

        # 2. Save connection
        payload = {
            "name": "Binance Spot Test",
            "provider": "binance",
            "endpoint": "127.0.0.1",
            "api_key": "test_key",
            "api_secret": "super_secret_token",
        }
        save_res = client.post("/api/v1/connections", json=payload)
        assert save_res.status_code == 200
        saved_data = save_res.json()["data"]
        cid = saved_data["connection_id"]
        assert saved_data["name"] == "Binance Spot Test"
        assert saved_data["api_secret"] != "super_secret_token"

        # 3. Test connection
        test_res = client.post(f"/api/v1/connections/{cid}/test")
        assert test_res.status_code == 200
        assert "test_result" in test_res.json()["data"]

        # 4. Delete connection
        del_res = client.delete(f"/api/v1/connections/{cid}")
        assert del_res.status_code == 200
        assert del_res.json()["data"]["deleted"] is True

        # 5. Delete non-existent returns 404
        del_404 = client.delete("/api/v1/connections/nonexistent-conn-999")
        assert del_404.status_code == 404

    for fr_id in (
        "FR-HOST-SERVLET-CONN-LIST",
        "FR-HOST-SERVLET-CONN-SAVE",
        "FR-HOST-SERVLET-CONN-DELETE",
        "FR-HOST-SERVLET-CONN-TEST",
    ):
        assert any(getattr(r, "fr_id", None) == fr_id for r in caplog.records)


def test_servlet_constants_and_specs(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """Verify FR-HOST-SERVLET-CONSTANTS and FR-HOST-SERVLET-SPECS."""
    caplog.set_level(logging.INFO)
    sessions = _create_isolated_session_manager(tmp_path)
    constants_servlet = ServletConstants(session_mgr=sessions)
    assert constants_servlet.get_constants()["application"] == "HaruQuantAI"
    assert constants_servlet.get_system_specs()["cpu_cores"] >= 1

    app = create_host_app(session_mgr=sessions)
    with TestClient(app) as client:
        const_res = client.get("/api/v1/constants")
        assert const_res.status_code == 200
        const_data = const_res.json()["data"]
        assert const_data["application"] == "HaruQuantAI"
        assert "supported_timeframes" in const_data
        assert "1m" in const_data["supported_timeframes"]

        spec_res = client.get("/api/v1/specs")
        assert spec_res.status_code == 200
        spec_data = spec_res.json()["data"]
        assert spec_data["cpu_cores"] >= 1
        assert "worker_capacity" in spec_data

    for fr_id in ("FR-HOST-SERVLET-CONSTANTS", "FR-HOST-SERVLET-SPECS"):
        assert any(getattr(r, "fr_id", None) == fr_id for r in caplog.records)


@pytest.mark.parametrize("prefix", ["", "/api/v1", "/api/v2"])
def test_settings_ui_contract_and_secret_boundaries(prefix: str) -> None:
    """Exercise real HTTP validation, merging, secret projection and events."""
    manager = SettingsManager()
    manager.save_settings(
        {
            "application": {
                "app_general": {"unregistered": "keep"},
                "notify_email": {"password": "synthetic-old"},
            }
        }
    )
    bus = EventBus()
    client = TestClient(create_host_app(host_settings=manager, event_bus=bus))
    snapshot = client.get(prefix + "/settings").json()["data"]
    assert "values" in snapshot and "settings" not in snapshot
    revision = snapshot["revision"]
    patch = {
        "expected_revision": revision,
        "changes": {
            "app.general": {"header_custom_text": "true"},
            "connect.remote": {"allow": True},
        },
    }
    response = client.put(prefix + "/settings", json=patch)
    assert response.status_code == 200
    assert (
        response.json()["data"]["values"]["app.general"]["header_custom_text"] == "true"
    )
    revision += 1
    independent = SettingsManager()
    assert independent.get_scope("app_general") == {
        "unregistered": "keep",
        "header_custom_text": "true",
        "remote_access": {"allow": True},
    }
    assert client.put(prefix + "/settings", json=patch).status_code == 409
    count = bus.current_cursor
    no_op = client.put(
        prefix + "/settings",
        json={
            "expected_revision": revision,
            "changes": {"app.general": {"header_custom_text": "true"}},
        },
    )
    assert no_op.json()["data"]["revision"] == revision
    assert bus.current_cursor == count
    for bad in (
        {},
        {"revision": revision, "settings": {}},
        {"expected_revision": True, "changes": {}},
        {"expected_revision": revision, "changes": {}, "settings": {}},
        {"expected_revision": revision, "changes": {"app.general": {"zoom": True}}},
        {"expected_revision": revision, "changes": {"app.general": {"unknown": 1}}},
        {
            "expected_revision": revision,
            "changes": {"user.access": {"username": "bypass"}},
        },
        {
            "expected_revision": revision,
            "changes": {"notify.email": {"password": "synthetic-leak"}},
        },
    ):
        failed = client.put(prefix + "/settings", json=bad)
        assert failed.status_code == 422
        assert "synthetic-leak" not in failed.text
    secret = client.put(
        prefix + "/settings/secrets",
        json={
            "expected_revision": revision,
            "changes": {"notify.email": {"password": "synthetic-new"}},
        },
    )
    assert secret.status_code == 200
    assert "synthetic-" not in secret.text
    catalogue = client.get(prefix + "/settings/catalogue")
    assert catalogue.status_code == 200
    assert "synthetic-" not in catalogue.text
    field = next(
        f
        for f in catalogue.json()["data"]["fields"]
        if f["scope"] == "notify.email" and f["key"] == "password"
    )
    assert field["configured"] is True and "value" not in field
    assert all(
        row["scope"] == "application"
        for row in HostPersistence.read_records("host_settings")
    )


def test_account_rotation_is_durable_and_revokes_other_gateway_cache() -> None:
    """Account commit invalidates old passwords/tokens across gateway instances."""
    manager = SettingsManager()
    manager.save_settings(
        {
            "application": {
                "user_access": {
                    "username": "old",
                    "session_timeout_mins": 1440,
                    "password_hash": hash_password("synthetic-old-password"),
                }
            }
        }
    )
    sessions = SessionManager()
    client = TestClient(
        create_host_app(
            host_settings=manager,
            session_mgr=sessions,
            require_auth=True,
            password_hash=hash_password("obsolete-override"),
        )
    )
    token = client.post(
        "/auth/login", json={"password": "synthetic-old-password"}
    ).json()["data"]["token"]
    auth = {"Authorization": "Bearer " + token}
    other = SessionManager()
    assert other.verify_session(token) is not None
    account = client.get("/auth/account", headers=auth).json()["data"]
    payload = {
        "username": "new",
        "expected_revision": account["revision"],
        "session_timeout_mins": 2880,
        "current_password": "wrong",
        "new_password": "synthetic-new-password",
    }
    assert client.put("/auth/account", headers=auth, json=payload).status_code == 401
    payload["current_password"] = "synthetic-old-password"
    assert client.put("/auth/account", headers=auth, json=payload).status_code == 200
    assert sessions.verify_session(token) is None
    assert other.verify_session(token) is None
    for password in ("synthetic-old-password", "obsolete-override"):
        assert (
            client.post("/auth/login", json={"password": password}).status_code == 401
        )
    new_login = client.post("/auth/login", json={"password": "synthetic-new-password"})
    assert new_login.status_code == 200
    assert new_login.json()["data"]["username"] == "new"
    rows = HostPersistence.read_records("host_session", {"status": "ACTIVE"})
    assert len(rows) == 1
    elapsed = datetime.fromisoformat(
        rows[0]["expires_at_utc"]
    ) - datetime.fromisoformat(rows[0]["created_at_utc"])
    assert elapsed.total_seconds() == 2880 * 60


def test_settings_database_failure_never_acknowledges_save(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Persistence failure returns a retryable boundary error without change events."""
    manager = SettingsManager()
    bus = EventBus()
    client = TestClient(create_host_app(host_settings=manager, event_bus=bus))
    client.get("/settings")

    def fail(*args: Any, **kwargs: Any) -> None:
        raise HostPersistence.Error("simulated store failure")

    monkeypatch.setattr(HostPersistence, "apply_batch", fail)
    response = client.put(
        "/settings",
        json={
            "expected_revision": 0,
            "changes": {"app.general": {"header_custom_text": "must not persist"}},
        },
    )
    assert response.status_code == 503
    assert bus.current_cursor == 0
    assert SettingsManager().get_snapshot()["revision"] == 0


def test_account_failure_rolls_back_settings_and_session_revocation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A failed account transaction leaves both credentials and sessions usable."""
    manager = SettingsManager()
    manager.save_settings(
        {
            "application": {
                "user_access": {
                    "username": "operator",
                    "session_timeout_mins": 1440,
                    "password_hash": hash_password("synthetic-current"),
                }
            }
        }
    )
    sessions = SessionManager()
    client = TestClient(
        create_host_app(host_settings=manager, session_mgr=sessions, require_auth=True)
    )
    token = client.post("/auth/login", json={"password": "synthetic-current"}).json()[
        "data"
    ]["token"]
    revision = manager.revision

    def fail(*args: Any, **kwargs: Any) -> None:
        raise HostPersistence.Error("simulated transaction failure")

    monkeypatch.setattr(HostPersistence, "apply_batch", fail)
    response = client.put(
        "/auth/account",
        headers={"Authorization": "Bearer " + token},
        json={
            "expected_revision": revision,
            "username": "changed",
            "session_timeout_mins": 1440,
            "current_password": "synthetic-current",
            "new_password": "synthetic-new",
        },
    )
    assert response.status_code == 503
    assert manager.get_account()["username"] == "operator"
    assert sessions.verify_session(token) is not None


def test_missing_account_reports_unconfigured_without_writing() -> None:
    """An empty store cannot claim an invented account identity or duration."""
    manager = SettingsManager()
    client = TestClient(create_host_app(host_settings=manager))
    response = client.get("/auth/account")
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "ACCOUNT_UNCONFIGURED"
    assert HostPersistence.read_records("host_settings") == []
