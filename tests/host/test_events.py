"""Bounded event delivery, immutable replay and explicit overflow behavior."""

import pytest
from app.host.events import ChannelError, EventBus, validate_channel


def test_validation_and_subscription_limits():
    assert validate_channel("settings.changed")
    for name in ("", "Bad-Name", "1bad"):
        with pytest.raises(ChannelError):
            validate_channel(name)
    with pytest.raises(ValueError):
        EventBus(queue_size=0)
    with pytest.raises(ChannelError):
        EventBus().subscribe([])


def test_delivery_replay_and_overflow():
    bus = EventBus(queue_size=1)
    subscriber = bus.subscribe(["boot.progress"])
    other = bus.subscribe(["settings.changed"])
    data = {"count": 1}
    assert bus.publish("boot.progress", data) == 1
    data["count"] = 2
    assert subscriber.queue.get_nowait()["data"]["count"] == 1
    bus.publish("boot.progress", {"count": 3})
    assert bus.publish("boot.progress", {"count": 4}) == 0
    assert subscriber.overflow
    assert other.queue.empty()
    assert bus.replay()[0]["data"]["count"] == 4
    assert bus.replay(after=bus.sequence) == []
    bus.unsubscribe(subscriber)
    bus.unsubscribe(subscriber)
    assert bus.subscriber_count() == 1
    with pytest.raises(ChannelError):
        bus.publish("ok", "x" * 300000)


def test_sse_requires_auth_and_public_topic(client, auth_headers):
    assert client.get("/api/v1/events?channels=settings.changed").status_code == 401
    for suffix in ("", "?channels=secret", "?channels=BAD"):
        assert (
            client.get("/api/v1/events" + suffix, headers=auth_headers).status_code
            == 400
        )


def test_sse_delivers_and_shutdown_releases_without_timeout(host_config):
    import asyncio

    from app.host.bootstrap import BootstrapCoordinator
    from app.host.transport import create_app, sse_endpoint
    from starlette.requests import Request
    from starlette.responses import StreamingResponse

    async def run() -> None:
        host = BootstrapCoordinator(
            host_config, installation_root=host_config.data_dir / "installation"
        )
        await host.initialize()
        token = host.session_manager().login("operator", None, peer="127.0.0.1")
        app = create_app(host)
        request = Request(
            {
                "type": "http",
                "method": "GET",
                "path": "/api/v1/events",
                "query_string": b"channels=settings.changed",
                "headers": [(b"authorization", ("Bearer " + token).encode())],
                "app": app,
            }
        )
        stream = await sse_endpoint(request)
        assert isinstance(stream, StreamingResponse)
        iterator = aiter(stream.body_iterator)
        next_event = asyncio.ensure_future(anext(iterator))
        await asyncio.sleep(0)
        host.events.publish("settings.changed", {"committed": True})
        event = await asyncio.wait_for(next_event, 1)
        assert isinstance(event, bytes)
        assert b'"committed": true' in event
        pending = asyncio.ensure_future(anext(iterator))
        await asyncio.sleep(0)
        host.shutdown_event.set()
        with pytest.raises(StopAsyncIteration):
            await asyncio.wait_for(pending, 1)
        assert host.events.subscriber_count() == 0
        await host.close()

    asyncio.run(run())
