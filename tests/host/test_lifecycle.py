"""Lifecycle ordering, deadlines, failure isolation and resource cleanup."""

import asyncio

import pytest
from app.host.contracts import LifecycleHook
from app.host.events import EventBus
from app.host.startup import STAGES, Startup


def test_stage_identity_and_missing_hooks():
    assert len(STAGES) == len(dict(STAGES)) == 37
    host = Startup(EventBus())
    asyncio.run(host.providers("I08"))
    assert host.results["I08"].outcome == "unavailable"
    assert [e["data"]["outcome"] for e in host.events.replay()] == [
        "running",
        "unavailable",
    ]


def test_optional_failure_required_failure_and_timeout():
    async def fail() -> None:
        raise RuntimeError("provider failure")

    async def wait() -> None:
        await asyncio.sleep(10)

    async def run() -> None:
        optional = Startup(EventBus(), (LifecycleHook("optional", "I08", fail),))
        await optional.providers("I08")
        assert optional.results["I08"].outcome == "failed"
        required = Startup(
            EventBus(), (LifecycleHook("required", "I08", fail, required=True),)
        )
        with pytest.raises(RuntimeError):
            await required.providers("I08")
        assert required.state == "FAILED"
        timed = Startup(
            EventBus(), (LifecycleHook("slow", "I08", wait, timeout=0.001),)
        )
        await timed.providers("I08")
        assert timed.results["I08"].outcome == "failed"

    asyncio.run(run())


def test_ack_is_per_client_and_restoration_runs_once():
    calls = []

    async def restore() -> None:
        calls.append("restore")

    async def run() -> None:
        host = Startup(EventBus(), (LifecycleHook("restore", "A11", restore),))
        with pytest.raises(ValueError):
            host.acknowledge("never-attached")
        host.connected("one")
        host.acknowledge("one")
        host.acknowledge("one")
        host.connected("two")
        host.acknowledge("two")
        await asyncio.sleep(0)
        assert calls == ["restore"]
        assert host.state == "STANDBY"
        await host.close()
        assert host.snapshot().state == "STOPPED"

    asyncio.run(run())


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
                LifecycleHook("one", "I08", run_hook, interval=1, close=close_one),
                LifecycleHook("two", "I08", run_hook, close=close_two),
            ),
        )
        await host.providers("I08")
        await host.close()
        assert closed == ["two", "one"]

    asyncio.run(run())


def test_deadline_and_invalid_hooks(monkeypatch):
    host = Startup(EventBus())
    host.connected("test")
    host.clients["test"] = (0, False)
    with pytest.raises(ValueError):
        host.acknowledge("test")
    host.connected("test")
    assert host.clients["test"][0] > 0

    async def noop() -> None:
        pass

    with pytest.raises(ValueError):
        Startup(EventBus(), (LifecycleHook("bad", "B01", noop),))


def test_fatal_restore_is_observable_without_unhandled_task_error():
    async def fail() -> None:
        raise ValueError("failed")

    host = Startup(EventBus(), (LifecycleHook("fatal", "A11", fail, required=True),))
    asyncio.run(host.restore())
    assert host.state == "FAILED"


@pytest.mark.parametrize("open_browser", [False, True])
def test_summary_is_complete_and_does_not_execute_or_mutate(caplog, open_browser):
    calls = []

    async def provider():
        calls.append("called")

    host = Startup(EventBus(), (LifecycleHook("engine", "I08", provider),))
    host.state = "SERVER_READY"
    before = host.snapshot()
    began = dict(host._began)
    with caplog.at_level("INFO", logger="app.host.startup"):
        host.log_summary("server_ready", open_browser=open_browser)
    assert host.snapshot() == before
    assert host._began == began
    assert calls == []
    for stage, _ in STAGES:
        assert f"Boot summary [server_ready] {stage} " in caplog.text
    assert "registered providers=1" in caplog.text
    assert "strategy scan unavailable: no restoration provider" in caplog.text
    assert "awaiting client readiness before strategy restoration" in caplog.text
    assert "0 strategies loaded" not in caplog.text


@pytest.mark.parametrize("fail", [False, True])
def test_restoration_summary_includes_success_and_failure(caplog, fail):
    async def restore():
        if fail:
            raise RuntimeError("private detail")

    host = Startup(
        EventBus(), (LifecycleHook("restore", "A11", restore, required=True),)
    )
    with caplog.at_level("INFO", logger="app.host.startup"):
        asyncio.run(host.restore())
    for stage, _ in STAGES:
        assert f"Boot summary [client_initialization] {stage} " in caplog.text
    assert host.state == ("FAILED" if fail else "STANDBY")
    assert "private detail" not in caplog.text
    if fail:
        assert "not reached because boot failed" in caplog.text
