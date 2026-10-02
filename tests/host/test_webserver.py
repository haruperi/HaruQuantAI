"""Real HTTP/ASGI authentication, static delivery and WebSocket lifecycle."""

import pytest
from app.host.contracts import OperationRejectedError
from app.host.logging import DiagnosticCaptureHandler, get_logger
from pydantic import BaseModel
from starlette.websockets import WebSocketDisconnect


def test_status_catalog_and_unknown_routes(client, auth_headers):
    status = client.get("/api/v1/status")
    assert status.status_code == 200
    assert status.headers["X-Request-Id"].startswith("req-")
    assert len(status.json()["data"]["boot"]["stages"]) == 5
    catalog = client.get("/api/v1/catalog", headers=auth_headers).json()["data"]
    assert catalog == {"domains": [], "issues": []}
    assert client.get("/api/v1/unknown", headers=auth_headers).status_code == 404
    assert client.get("/").status_code == 503
    assert client.get("/", headers={"host": "evil.example"}).status_code == 400


def test_handshake_snapshot_ack_does_not_change_process_state(
    client, auth_headers, services
):
    token = auth_headers["Authorization"].removeprefix("Bearer ")
    assert (
        client.post("/api/v1/app-loaded", json={}, headers=auth_headers).status_code
        == 409
    )
    with client.websocket_connect("ws://127.0.0.1/ws/updates") as socket:
        socket.send_json({"token": token, "topics": ["boot.progress"]})
        snapshot = socket.receive_json()
        assert snapshot["type"] == "snapshot"
        assert len(snapshot["boot"]["stages"]) == 5
        initial = client.get("/api/v1/init-data", headers=auth_headers).json()["data"]
        assert initial["first_run"]
        assert initial["settings"] == {"revision": 0, "values": {}}
        for _ in range(2):
            assert client.post(
                "/api/v1/app-loaded", json={}, headers=auth_headers
            ).json()["data"] == {"acknowledged": True}
        assert services.startup.snapshot().state == "INITIALIZING"
        assert services.startup.results["serving"].outcome == "running"
        socket.send_json({"type": "ping"})
        for _ in range(100):
            if socket.receive_json().get("type") == "pong":
                break
        else:
            pytest.fail("no heartbeat response")
    assert services.events.subscriber_count() == 0


@pytest.mark.parametrize("message", [{}, {"token": "bad"}, {"token": ["bad"]}])
def test_unauthorized_websocket_closes(client, message):
    with client.websocket_connect("ws://127.0.0.1/ws/updates") as socket:
        socket.send_json(message)
        with pytest.raises(WebSocketDisconnect):
            socket.receive_json()


def test_websocket_origin_and_control_authority(client, auth_headers):
    with (
        pytest.raises(WebSocketDisconnect),
        client.websocket_connect(
            "ws://127.0.0.1/ws/updates", headers={"origin": "https://evil.example"}
        ),
    ):
        pass
    token = auth_headers["Authorization"].removeprefix("Bearer ")
    with client.websocket_connect("ws://127.0.0.1/ws/control") as socket:
        socket.send_json({"token": token, "topics": ["boot.progress"]})
        assert socket.receive_json()["type"] == "snapshot"
        socket.send_json({"type": "execute_arbitrary_code"})
        with pytest.raises(WebSocketDisconnect):
            while True:
                socket.receive_json()


def test_payload_failures_unknown_command_and_shutdown(client, auth_headers, services):
    for content in ("[]", "broken"):
        assert client.post("/api/v1/auth/login", content=content).status_code == 400
    result = client.post("/api/v1/commands/builder", json={}, headers=auth_headers)
    assert result.status_code == 503
    assert result.json()["error"]["code"] == "MISSING_DEPENDENCY"
    assert client.post("/api/v1/shutdown", json={}).status_code == 401
    assert (
        client.post("/api/v1/shutdown", json={}, headers=auth_headers).status_code
        == 200
    )
    assert services.shutdown_event.is_set()


def test_static_bundle_is_confined(client, services):
    root = services.config.ui_dist
    root.mkdir()
    (root / "index.html").write_text("<html>shell</html>")
    (root / "asset.js").write_text("export {}")
    assert "shell" in client.get("/builder").text
    assert client.get("/asset.js").text == "export {}"
    assert client.get("/api/v1/missing").status_code == 401


def test_request_rejections_are_correlated_and_secret_free(client, auth_headers):
    sink = DiagnosticCaptureHandler(100)
    log = get_logger()
    log.addHandler(sink)

    async def prerequisite() -> None:
        get_logger(__name__).warning("Inside clock admission")
        raise OperationRejectedError(
            "CLOCK_SCHEMA_REQUIRED", "Clock setup required", status=409
        )

    async def unexpected() -> None:
        raise RuntimeError("password=never-log-this-private-value")

    async def invalid_fields() -> None:
        class Input(BaseModel):
            count: int

        Input.model_validate({"count": "never-log-this-private-value"})

    for name, endpoint in [
        ("prerequisite", prerequisite),
        ("unexpected", unexpected),
        ("invalid_fields", invalid_fields),
    ]:
        client.app.add_api_route(
            "/api/v1/diagnostic/" + name, endpoint, methods=["POST"]
        )
    try:
        prerequisite_response = client.post(
            "/api/v1/diagnostic/prerequisite", json={}, headers=auth_headers
        )
        assert prerequisite_response.status_code == 409
        envelope = prerequisite_response.json()
        assert envelope["error"]["code"] == "CLOCK_SCHEMA_REQUIRED"
        request_id = envelope["request_id"]
        assert prerequisite_response.headers["X-Request-Id"] == request_id
        first_records = sink.snapshot()
        assert any(
            "Inside clock admission" in record and request_id in record
            for record in first_records
        )
        assert any(
            "CLOCK_SCHEMA_REQUIRED" in record and request_id in record
            for record in first_records
        )
        failure = client.post(
            "/api/v1/diagnostic/unexpected", json={}, headers=auth_headers
        )
        assert failure.status_code == 500
        assert failure.json()["request_id"] != request_id
        invalid = client.post(
            "/api/v1/diagnostic/invalid_fields", json={}, headers=auth_headers
        )
        assert invalid.status_code == 422
        assert invalid.json()["error"]["code"] == "VALIDATION_FAILED"
        malformed = client.post("/api/v1/auth/login", content="broken")
        assert malformed.status_code == 400
        missing = client.post("/api/v1/commands/builder", json={}, headers=auth_headers)
        assert missing.status_code == 503
        get_logger(__name__).warning("After request context")
        records = "\n".join(sink.snapshot())
        assert "RuntimeError" in records and "unexpected" in records
        assert "int_parsing" in records
        assert "MALFORMED_REQUEST" in records
        assert "MISSING_DEPENDENCY" in records
        assert "never-log-this-private-value" not in records
        assert "C:\\" not in records
        assert "correlation_id=" not in sink.snapshot()[-1]
    finally:
        log.removeHandler(sink)
        sink.close()
