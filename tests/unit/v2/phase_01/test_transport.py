"""Unit tests for the unified HTTP and event transport subsystem.

Covers:
    - FR-HOST-TRANSPORT-MIDDLEWARE: Request ID correlation and response timing.
    - FR-HOST-TRANSPORT-SESSION-AUTH: Token-based session authentication.
    - FR-HOST-TRANSPORT-EVENT-BUS: In-memory multi-channel event broker.
    - FR-HOST-TRANSPORT-SSE-STREAMING: Server-Sent Events streaming with gap detection.
    - FR-HOST-TRANSPORT-REST-PROJECTION: Transport router endpoints and CLI.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from app.host.logging import TelemetryEngine
from app.host.transport import (
    AuthenticationError,
    EventBus,
    EventSnapshot,
    LoginRequest,
    LoginResponse,
    SessionExpiredError,
    SessionTokenManager,
    TransportMiddleware,
    create_transport_router,
    get_global_event_bus,
    get_global_token_manager,
    main,
    register_transport_exception_handlers,
)
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

# -----------------------------------------------------------------------------
# Session Token Manager Tests
# -----------------------------------------------------------------------------


def test_session_token_manager_lifecycle() -> None:
    """Verify session token issuance, validation, revocation, and clearance."""
    mgr = SessionTokenManager(default_ttl_sec=3600)

    # Issue token
    login_resp: LoginResponse = mgr.create_token(username="operator")
    assert login_resp.username == "operator"
    assert login_resp.token != ""
    assert mgr.is_valid(login_resp.token) is True
    assert mgr.verify_token(login_resp.token) == "operator"

    # Revoke token
    assert mgr.revoke_token(login_resp.token) is True
    assert mgr.is_valid(login_resp.token) is False
    assert mgr.revoke_token(login_resp.token) is False

    # Issue another and clear
    t2 = mgr.create_token(username="admin")
    assert mgr.is_valid(t2.token) is True
    mgr.clear()
    assert mgr.is_valid(t2.token) is False


def test_session_token_manager_expiration() -> None:
    """Verify expired token raises SessionExpiredError."""
    mgr = SessionTokenManager()
    token_str = "expired-token-123"
    # Inject directly an expired token
    past = datetime.now(UTC) - timedelta(seconds=10)
    mgr._tokens[token_str] = ("operator", past)

    with pytest.raises(SessionExpiredError, match="Session token has expired"):
        mgr.verify_token(token_str)
    assert mgr.is_valid(token_str) is False


def test_session_token_manager_invalid_token() -> None:
    """Verify non-existent token raises AuthenticationError."""
    mgr = SessionTokenManager()
    with pytest.raises(AuthenticationError, match="Invalid or missing session token"):
        mgr.verify_token("unknown-token")


# -----------------------------------------------------------------------------
# EventBus Tests
# -----------------------------------------------------------------------------


def test_event_bus_publish_and_subscribe() -> None:
    """Verify publishing to channel and selective subscription."""
    bus = EventBus()
    assert bus.current_cursor == 0

    sub_id, queue, replay, has_gap = bus.subscribe(channels=["settings.changed"])
    assert sub_id.startswith("sub-")
    assert replay == []
    assert has_gap is False

    # Publish matching event
    ev1 = bus.publish("settings.changed", "update", {"rev": 1})
    assert ev1.cursor == 1
    assert ev1.channel == "settings.changed"
    assert bus.current_cursor == 1
    assert queue.qsize() == 1

    # Publish non-matching event
    bus.publish("other.channel", "ping", {})
    assert bus.current_cursor == 2
    assert queue.qsize() == 1  # Not delivered to settings.changed subscriber

    bus.unsubscribe(sub_id)


def test_event_bus_wildcard_subscription() -> None:
    """Verify wildcard '*' subscription receives all channel events."""
    bus = EventBus()
    sub_id, queue, _, _ = bus.subscribe(channels=["*"])

    bus.publish("c1", "t1", {})
    bus.publish("c2", "t2", {})
    assert queue.qsize() == 2

    bus.unsubscribe(sub_id)


def test_event_bus_replay_and_gap_detection() -> None:
    """Verify ring buffer replay and gap detection when cursor is expired."""
    bus = EventBus(ring_capacity=3)

    # Publish 5 events: ring will retain cursors 3, 4, 5
    for i in range(1, 6):
        bus.publish("channel.a", "tick", {"i": i})

    assert bus.current_cursor == 5

    # Replay from cursor 3 (within ring): returns cursors 4, 5, has_gap=False
    _, _, replay_ok, gap_ok = bus.subscribe(channels=["channel.a"], since_cursor=3)
    assert gap_ok is False
    assert [e.cursor for e in replay_ok] == [4, 5]

    # Replay from cursor 1 (dropped from ring): returns cursors 3, 4, 5, has_gap=True
    _, _, replay_gap, gap_detected = bus.subscribe(
        channels=["channel.a"], since_cursor=1
    )
    assert gap_detected is True
    assert [e.cursor for e in replay_gap] == [3, 4, 5]


def test_event_bus_slow_consumer_drop() -> None:
    """Verify slow consumer bounded queue drops excess events without blocking."""
    bus = EventBus(max_queue_size=2)
    sub_id, queue, _, _ = bus.subscribe(channels=["c1"])

    # Publish 4 events: first 2 fill queue, remaining 2 are dropped
    for i in range(4):
        bus.publish("c1", "event", {"i": i})

    assert queue.qsize() == 2
    ev1 = queue.get_nowait()
    ev2 = queue.get_nowait()
    assert ev1.cursor == 1
    assert ev2.cursor == 2
    assert queue.empty() is True

    bus.unsubscribe(sub_id)


def test_event_bus_snapshot() -> None:
    """Verify get_snapshot returns channel history and gap indicator."""
    bus = EventBus(ring_capacity=10)
    for i in range(5):
        bus.publish("settings.changed", "update", {"rev": i})
    bus.publish("other", "ping", {})

    snap = bus.get_snapshot("settings.changed", limit=3)
    assert isinstance(snap, EventSnapshot)
    assert snap.channel == "settings.changed"
    assert snap.newest_cursor == 6
    assert len(snap.events) == 3
    assert snap.has_gap is False

    # Snapshot with wildcard
    all_snap = bus.get_snapshot("*", limit=10)
    assert len(all_snap.events) == 6

    bus.clear()
    assert len(bus.get_snapshot("*").events) == 0


# -----------------------------------------------------------------------------
# TransportMiddleware & Exception Handlers Tests
# -----------------------------------------------------------------------------


def test_transport_middleware_request_id_and_timing() -> None:
    """Verify middleware injects X-Request-Id and X-Response-Time-Ms."""
    app = FastAPI()
    app.add_middleware(TransportMiddleware)

    @app.get("/ping")
    async def ping() -> dict[str, str]:
        return {"ping": "pong"}

    client = TestClient(app)

    # Without client request ID
    res1 = client.get("/ping")
    assert res1.status_code == 200
    assert "X-Request-Id" in res1.headers
    assert res1.headers["X-Request-Id"].startswith("req-")
    assert "X-Response-Time-Ms" in res1.headers

    # With client custom request ID
    res2 = client.get("/ping", headers={"X-Request-Id": "client-corr-99"})
    assert res2.headers["X-Request-Id"] == "client-corr-99"


def test_transport_middleware_unhandled_exception() -> None:
    """Verify unhandled exception is caught and wrapped into StandardResponse."""
    app = FastAPI()
    app.add_middleware(TransportMiddleware)

    @app.get("/crash")
    async def crash() -> None:
        raise RuntimeError("Fatal unhandled crash")

    client = TestClient(app, raise_server_exceptions=False)
    res = client.get("/crash")
    assert res.status_code == 500
    data = res.json()
    assert data["status"] == "error"
    assert data["error"]["code"] == "INTERNAL_SERVER_ERROR"
    assert "Fatal unhandled crash" in data["error"]["message"]
    assert "X-Request-Id" in res.headers


def test_register_transport_exception_handlers() -> None:
    """Verify HTTPException and RequestValidationError are wrapped into StandardResponse."""
    app = FastAPI()
    register_transport_exception_handlers(app)

    @app.get("/not-found")
    async def not_found() -> None:
        raise HTTPException(status_code=404, detail="Entity not found.")

    class BodyModel(LoginRequest):
        pass

    @app.post("/validate")
    async def validate(body: BodyModel) -> dict[str, str]:
        return {"status": "ok"}

    client = TestClient(app)

    # Test 404
    r404 = client.get("/not-found")
    assert r404.status_code == 404
    d404 = r404.json()
    assert d404["status"] == "error"
    assert d404["error"]["code"] == "HTTP_404"
    assert d404["error"]["message"] == "Entity not found."

    # Test 422 validation
    r422 = client.post("/validate", json={"extra_field": "forbidden"})
    assert r422.status_code == 422
    d422 = r422.json()
    assert d422["status"] == "error"
    assert d422["error"]["code"] == "VALIDATION_ERROR"
    assert "issues" in d422["error"]["details"]


# -----------------------------------------------------------------------------
# REST Router & Endpoints Tests
# -----------------------------------------------------------------------------


def test_auth_login_endpoints() -> None:
    """Verify /auth/login and /login with valid and invalid credentials."""
    app = FastAPI()
    bus = EventBus()
    tokens = SessionTokenManager()
    router = create_transport_router(event_bus=bus, token_manager=tokens)
    app.include_router(router)
    client = TestClient(app)

    # Valid login
    res = client.post("/auth/login", json={"username": "operator", "password": ""})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert "token" in data["data"]
    assert data["data"]["username"] == "operator"

    # Also test /login alias
    res_alias = client.post("/login", json={"username": "operator", "password": ""})
    assert res_alias.status_code == 200
    assert "token" in res_alias.json()["data"]

    # Invalid login (empty username)
    res_err = client.post("/auth/login", json={"username": "  ", "password": ""})
    assert res_err.status_code == 400
    assert res_err.json()["error"]["code"] == "INVALID_CREDENTIALS"


def test_auth_status_endpoint() -> None:
    """Verify /auth/status checks token authenticity."""
    app = FastAPI()
    bus = EventBus()
    tokens = SessionTokenManager()
    router = create_transport_router(event_bus=bus, token_manager=tokens)
    app.include_router(router)
    client = TestClient(app)

    # Missing token
    r_unauth = client.get("/auth/status")
    assert r_unauth.status_code == 401

    # Valid token in Bearer header
    login_tok = tokens.create_token("operator").token
    r_auth = client.get(
        "/auth/status", headers={"Authorization": f"Bearer {login_tok}"}
    )
    assert r_auth.status_code == 200
    assert r_auth.json()["data"]["authenticated"] is True
    assert r_auth.json()["data"]["username"] == "operator"

    # Valid token via query param
    r_query = client.get(f"/auth/status?token={login_tok}")
    assert r_query.status_code == 200


def test_events_publish_and_snapshot_endpoints() -> None:
    """Verify POST /events/publish and GET /events/snapshot."""
    app = FastAPI()
    bus = EventBus()
    tokens = SessionTokenManager()
    router = create_transport_router(event_bus=bus, token_manager=tokens)
    app.include_router(router)
    client = TestClient(app)

    # Publish
    pub_res = client.post(
        "/events/publish",
        json={
            "channel": "settings.changed",
            "event_type": "update",
            "payload": {"revision": 3},
        },
    )
    assert pub_res.status_code == 200
    assert pub_res.json()["data"]["cursor"] == 1

    # Snapshot
    snap_res = client.get("/events/snapshot?channel=settings.changed")
    assert snap_res.status_code == 200
    snap_data = snap_res.json()["data"]
    assert snap_data["channel"] == "settings.changed"
    assert len(snap_data["events"]) == 1
    assert snap_data["events"][0]["payload"] == {"revision": 3}


def test_events_sse_unauthorized() -> None:
    """Verify /events requires authorization."""
    app = FastAPI()
    bus = EventBus()
    tokens = SessionTokenManager()
    router = create_transport_router(event_bus=bus, token_manager=tokens)
    app.include_router(router)
    client = TestClient(app)

    # Without token
    res = client.get("/events")
    assert res.status_code == 401
    assert res.json()["error"]["code"] == "UNAUTHORIZED"


def test_events_sse_streaming() -> None:
    """Verify /events streams SSE frames with channel demux and replay."""
    app = FastAPI()
    bus = EventBus()
    tokens = SessionTokenManager()
    router = create_transport_router(event_bus=bus, token_manager=tokens)
    app.include_router(router)

    # Pre-populate 1 event
    bus.publish("settings.changed", "initial", {"rev": 1})

    tok = tokens.create_token("operator").token
    client = TestClient(app)

    # Connect to stream with since_cursor=0 and limit=1
    with client.stream(
        "GET",
        "/events?channels=settings.changed&since_cursor=0&limit=1",
        headers={"Authorization": f"Bearer {tok}"},
    ) as response:
        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]

        # Read first line / event frame
        lines: list[str] = []
        for line in response.iter_lines():
            lines.append(line)
            if len(lines) >= 3:
                break

        full_frame = "\n".join(lines)
        assert "id: 1" in full_frame
        assert "event: settings.changed" in full_frame
        assert '"channel":"settings.changed"' in full_frame


def test_events_sse_last_event_id() -> None:
    """Verify Last-Event-ID header is used when since_cursor query param is omitted."""
    app = FastAPI()
    bus = EventBus()
    tokens = SessionTokenManager()
    router = create_transport_router(event_bus=bus, token_manager=tokens)
    app.include_router(router)

    bus.publish("ch1", "t1", {})
    bus.publish("ch1", "t2", {})
    tok = tokens.create_token("operator").token
    client = TestClient(app)

    with client.stream(
        "GET",
        "/events?channels=ch1&limit=1",
        headers={"Authorization": f"Bearer {tok}", "Last-Event-ID": "1"},
    ) as response:
        assert response.status_code == 200
        lines: list[str] = []
        for line in response.iter_lines():
            lines.append(line)
            if len(lines) >= 3:
                break
        assert "id: 2" in "\n".join(lines)


def test_events_sse_gap_notification() -> None:
    """Verify gap event is sent when historical cursor is expired."""
    app = FastAPI()
    bus = EventBus(ring_capacity=2)
    tokens = SessionTokenManager()
    router = create_transport_router(event_bus=bus, token_manager=tokens)
    app.include_router(router)

    # Publish 4 events: ring has 3, 4
    for i in range(4):
        bus.publish("ch1", "tick", {"i": i})

    tok = tokens.create_token("operator").token
    client = TestClient(app)

    with client.stream(
        "GET",
        "/events?channels=ch1&since_cursor=0&limit=1",
        headers={"Authorization": f"Bearer {tok}"},
    ) as response:
        assert response.status_code == 200
        lines = [line for line in response.iter_lines() if line]
        full_text = "\n".join(lines)
        assert "event: system.gap" in full_text


def test_global_singletons() -> None:
    """Verify get_global_event_bus and get_global_token_manager provide stable instances."""
    b1 = get_global_event_bus()
    b2 = get_global_event_bus()
    assert b1 is b2

    t1 = get_global_token_manager()
    t2 = get_global_token_manager()
    assert t1 is t2


def test_cli_main(capsys: pytest.CaptureFixture[str]) -> None:
    """Verify CLI --test-bus and --help execution."""
    rc = main(["--test-bus"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "Published test event" in out

    rc_default = main([])
    assert rc_default == 0

    with pytest.raises(SystemExit):
        main(["--help"])


def test_telemetry_logging_emissions() -> None:
    """Verify requirement IDs are recorded in TelemetryEngine ring buffer."""
    engine = TelemetryEngine.get_or_create()
    bus = EventBus()
    tokens = SessionTokenManager()
    app = FastAPI()
    app.add_middleware(TransportMiddleware)
    router = create_transport_router(event_bus=bus, token_manager=tokens)
    app.include_router(router)

    client = TestClient(app)
    tok = tokens.create_token("operator").token
    sub_id, *_ = bus.subscribe(["chan.test"])
    bus.publish("chan.test", "ping", {})
    client.get("/auth/status", headers={"Authorization": f"Bearer {tok}"})
    engine.flush()

    requirements = [e.context.get("requirement") for e in engine.ring_buffer._entries]
    assert "FR-HOST-TRANSPORT-SESSION-AUTH" in requirements
    assert "FR-HOST-TRANSPORT-EVENT-BUS" in requirements
    assert "FR-HOST-TRANSPORT-MIDDLEWARE" in requirements
    assert "FR-HOST-TRANSPORT-REST-PROJECTION" in requirements
