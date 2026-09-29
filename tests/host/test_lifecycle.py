"""Host readiness, independent clients, bounded hooks and resource cleanup."""

import asyncio
from typing import Literal, cast

import pytest
from app.host.contracts import LifecycleHook
from app.host.events import EventBus
from app.host.startup import STAGES, Startup


def test_empty_hooks_are_normal_and_do_not_invent_events():
    host = Startup(EventBus())
    assert len(STAGES) == len(dict(STAGES)) == 5
    asyncio.run(host.step("services", lambda: host.providers("services")))
    assert host.results["services"].outcome == "succeeded"
    assert [e["data"]["outcome"] for e in host.events.replay()] == [
        "running",
        "succeeded",
    ]
    assert host.snapshot().schema_version == 2


def test_optional_failure_required_failure_and_timeout():
    async def fail() -> None:
        raise RuntimeError("private failure")

    async def wait() -> None:
        await asyncio.sleep(10)

    async def run() -> None:
        optional = Startup(EventBus(), (LifecycleHook("optional", "services", fail),))
        optional.state = "INITIALIZING"
        await optional.step("services", lambda: optional.providers("services"))
        assert optional.results["services"].outcome == "failed"
        assert optional.state == "INITIALIZING"
        optional.listening()
        assert optional.snapshot().state == "DEGRADED"
        required = Startup(
            EventBus(), (LifecycleHook("required", "services", fail, required=True),)
        )
        with pytest.raises(RuntimeError, match="Required provider"):
            await required.step("services", lambda: required.providers("services"))
        assert required.state == "FAILED"
        timed = Startup(
            EventBus(), (LifecycleHook("slow", "services", wait, timeout=0.001),)
        )
        await timed.step("services", lambda: timed.providers("services"))
        assert timed.results["services"].outcome == "failed"
        for host in (optional, required, timed):
            await host.close()

    asyncio.run(run())


def test_ack_is_per_client_and_has_no_process_effect(monkeypatch, caplog):
    clock = [100.0]
    monkeypatch.setattr("app.host.startup.time.monotonic", lambda: clock[0])
    host = Startup(EventBus(), runtime_started_at=0)
    host.listening()
    before = host.snapshot()
    with pytest.raises(ValueError, match="connect"):
        host.acknowledge("never-attached")
    host.connected("one")
    clock[0] = 101.0
    host.connected("two")
    clock[0] = 102.0
    with caplog.at_level("INFO", logger="app.host.startup"):
        host.acknowledge("one")
        host.acknowledge("one")
        assert not host.clients["two"][1]
        host.acknowledge("two")
    assert host.snapshot() == before
    assert "Client initialized after 2.000 seconds" in caplog.text
    assert "Client initialized after 1.000 seconds" in caplog.text
    assert caplog.text.count("Client initialized") == 2


def test_cleanup_reverse_order_and_cancellation():
    closed = []

    async def run_hook() -> None:
        pass

    async def close_one() -> None:
        closed.append("one")

    async def close_two() -> None:
        closed.append("two")

    async def run() -> None:
        host = Startup(
            EventBus(),
            (
                LifecycleHook("one", "services", run_hook, interval=1, close=close_one),
                LifecycleHook("two", "services", run_hook, close=close_two),
            ),
        )
        await host.step("services", lambda: host.providers("services"))
        await host.close()
        assert closed == ["two", "one"]
        assert host.snapshot().state == "STOPPED"
        await host.close()
        assert closed == ["two", "one"]

    asyncio.run(run())


def test_deadline_reconnect_capacity_and_invalid_hooks(monkeypatch):
    clock = [100.0]
    monkeypatch.setattr("app.host.startup.time.monotonic", lambda: clock[0])
    monkeypatch.setattr("app.host.startup.MAX_CLIENTS", 1)
    host = Startup(EventBus())
    host.connected("test")
    with pytest.raises(ValueError, match="capacity"):
        host.connected("other")
    clock[0] = 131.0
    with pytest.raises(ValueError, match="deadline"):
        host.acknowledge("test")
    host.connected("test")
    assert host.clients["test"][0] == 131.0
    clock[0] = 162.0
    host.connected("other")
    assert "test" not in host.clients

    async def noop() -> None:
        pass

    with pytest.raises(ValueError):
        Startup(
            EventBus(),
            (LifecycleHook("bad", cast("Literal['services']", "I08"), noop),),
        )


def test_summary_is_concise_readonly_and_uses_process_clock(monkeypatch, caplog):
    host = Startup(EventBus(), runtime_started_at=10)
    monkeypatch.setattr("app.host.startup.time.monotonic", lambda: 11.5)
    host.listening()
    before = host.snapshot()
    with caplog.at_level("INFO", logger="app.host.startup"):
        host.log_summary("ready")
    assert host.snapshot() == before
    assert "elapsed_ms=1500.000" in caplog.text
    assert "Boot summary" not in caplog.text
    assert "no_registered_provider" not in caplog.text


def test_cancelled_phase_and_partial_hook_cleanup():
    closed = []

    async def cancel() -> None:
        raise asyncio.CancelledError

    async def cleanup() -> None:
        closed.append(True)

    async def run() -> None:
        host = Startup(
            EventBus(), (LifecycleHook("partial", "services", cancel, close=cleanup),)
        )
        with pytest.raises(asyncio.CancelledError):
            await host.step("services", lambda: host.providers("services"))
        assert host.results["services"].outcome == "cancelled"
        await host.close()
        assert closed == [True]

    asyncio.run(run())


@pytest.mark.parametrize("listening", [False, True])
def test_periodic_failure_does_not_advertise_readiness_early(listening, caplog):
    async def fail() -> None:
        raise ValueError("private provider message")

    async def run() -> None:
        host = Startup(EventBus())
        host.state = "INITIALIZING"
        if listening:
            host.listening()
        # An already elapsed interval makes this supervisor test deterministic.
        hook = LifecycleHook("periodic", "services", fail, interval=-1)
        await host._periodic(hook)
        assert host.state == ("DEGRADED" if listening else "INITIALIZING")
        assert host.results["services"].reason == "periodic_provider_failed"
        if not listening:
            host.listening()
            assert host.snapshot().state == "DEGRADED"
        await host.close()

    with caplog.at_level("WARNING"):
        asyncio.run(run())
    assert "private provider message" not in caplog.text
