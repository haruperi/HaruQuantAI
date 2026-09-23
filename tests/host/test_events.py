"""Tests for the channel event hub and the SSE endpoint."""

import pytest
from app.host.events import ChannelError, EventBus, validate_channel
from app.host.webserver import HostServices
from starlette.testclient import TestClient


def test_channel_names_are_validated() -> None:
    assert validate_channel("settings.changed")
    with pytest.raises(ChannelError):
        validate_channel("Bad-Name")
    with pytest.raises(ChannelError):
        validate_channel("")
    with pytest.raises(ChannelError):
        validate_channel("1starts-with-digit")


def test_publish_delivers_only_to_matching_subscribers() -> None:
    bus = EventBus()
    matching = bus.subscribe(["builder.progress"])
    other = bus.subscribe(["retester.progress"])

    delivered = bus.publish("builder.progress", {"generation": 42})

    assert delivered == 1
    assert matching.queue.get_nowait() == {
        "channel": "builder.progress",
        "data": {"generation": 42},
    }
    assert other.queue.empty()


def test_full_queue_drops_event_without_raising() -> None:
    bus = EventBus(queue_size=1)
    subscriber = bus.subscribe(["alerts"])

    bus.publish("alerts", {"first": True})
    dropped = bus.publish("alerts", {"second": True})

    assert dropped == 0
    assert subscriber.queue.get_nowait()["data"] == {"first": True}


def test_publish_rejects_invalid_channel() -> None:
    with pytest.raises(ChannelError):
        EventBus().publish("NOPE", {})


def test_sse_endpoint_requires_channels(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = client.get("/api/v1/events", headers=auth_headers)

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "BAD_REQUEST"


def test_sse_endpoint_rejects_invalid_channel(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = client.get("/api/v1/events?channels=BAD", headers=auth_headers)

    assert response.status_code == 400
    assert response.json()["error"]["issues"][0]["path"] == "channels"


def test_sse_stream_delivers_published_event(
    client: TestClient, auth_headers: dict[str, str], services: HostServices
) -> None:
    # Driven as a raw ASGI call: the SSE response is an endless stream, which
    # the buffered test transport cannot read incrementally.
    import asyncio
    from typing import Any

    token = auth_headers["Authorization"][len("Bearer ") :]

    async def drive() -> list[dict[str, Any]]:
        from starlette.types import ASGIApp, Message

        messages: list[dict[str, Any]] = []
        got_body = asyncio.Event()
        request_sent = {"done": False}
        never = asyncio.Event()

        async def receive() -> Message:
            # First call completes the request body; later calls block like a
            # connected client that never disconnects (and always yield, so
            # Starlette's disconnect listener cannot starve the event loop).
            if not request_sent["done"]:
                request_sent["done"] = True
                return {"type": "http.request", "body": b"", "more_body": False}
            await never.wait()
            raise AssertionError("unreachable")

        async def send(message: Message) -> None:
            messages.append(dict(message))
            if message["type"] == "http.response.body" and message.get("body"):
                got_body.set()

        def make_scope() -> dict[str, Any]:
            return {
                "type": "http",
                "asgi": {"version": "3.0"},
                "http_version": "1.1",
                "method": "GET",
                "scheme": "http",
                "path": "/api/v1/events",
                "query_string": b"channels=demo.channel",
                "headers": [
                    (b"authorization", f"Bearer {token}".encode()),
                    (b"content-type", b"application/json"),
                ],
                "client": ("127.0.0.1", 12345),
                "server": ("127.0.0.1", 8000),
                "root_path": "",
            }

        app_asgi: ASGIApp = client.app

        async def run_app() -> None:
            await app_asgi(make_scope(), receive, send)

        task: asyncio.Task[None] = asyncio.create_task(run_app())
        try:
            await asyncio.sleep(0.05)
            services.events.publish("demo.channel", {"hello": "world"})
            await asyncio.wait_for(got_body.wait(), timeout=5)
        finally:
            task.cancel()
        return messages

    messages = asyncio.run(drive())

    start = next(m for m in messages if m["type"] == "http.response.start")
    body = b"".join(
        m.get("body", b"") for m in messages if m["type"] == "http.response.body"
    )
    content_type = {
        key.decode(): value.decode()
        for key, value in start["headers"]
        if key == b"content-type"
    }
    assert start["status"] == 200
    assert content_type["content-type"].startswith("text/event-stream")
    assert b"demo.channel" in body
    assert b"world" in body
    assert body.startswith(b"data: ")


def test_publish_endpoint_reports_delivery(
    client: TestClient, auth_headers: dict[str, str], services: HostServices
) -> None:
    event_bus = services.events
    event_bus.subscribe(["builder.progress"])

    response = client.post(
        "/api/v1/events/publish",
        json={"channel": "builder.progress", "data": {"step": 1}},
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["data"] == {"delivered": 1}
