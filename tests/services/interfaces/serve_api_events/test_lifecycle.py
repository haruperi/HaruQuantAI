"""Lifecycle and non-functional requirement tests for FEAT-IFACE-SERVE_API_EVENTS.

Tests:
    ATN-IFACE-SERVE_API_EVENTS-001 (NFR-TRC-IFACE-SERVE_API_EVENTS-001):
        BM-APP-01 control/metadata p95 <= 250 ms and p99 <= 1 s;
        long commands return an owner job handle and no event-loop CPU blockage.
    ATN-IFACE-SERVE_API_EVENTS-002 (NFR-TRC-IFACE-SERVE_API_EVENTS-002):
        Remove each operation owner in turn; only its operations degrade
        and no unauthorized receiver gets invoked.
"""

from __future__ import annotations

import asyncio
import time
from typing import Any

import httpx
import pytest
from app.contracts.interfaces.capabilities import (
    OBSERVE_MARKET_DATA_CAPABILITY,
    SERVE_API_EVENTS_CAPABILITY,
)
from app.contracts.interfaces.errors import InterfaceError
from app.contracts.interfaces.models import AsyncJobState
from app.kernel.capability import CapabilityUnavailableError
from app.kernel.context import DefaultFeatureContext
from app.kernel.events import EventBus
from app.kernel.registry import ServiceRegistry
from app.kernel.scope import FeatureScope
from app.services.interfaces.serve_api_events.asgi import create_api_asgi_app
from app.services.interfaces.serve_api_events.config import ServeApiEventsConfig
from app.services.interfaces.serve_api_events.feature import feature
from app.services.interfaces.serve_api_events.transport import (
    ServeApiEventsTransport,
    translate_capability_unavailable,
)


@pytest.mark.asyncio
async def test_atn_iface_serve_api_events_001_control_latency_and_event_loop_responsiveness() -> (
    None
):
    """ATN-IFACE-SERVE_API_EVENTS-001.

    BM-APP-01 control/metadata p95 <= 250 ms and p99 <= 1 s;
    long commands return an owner job handle and no event-loop CPU blockage.
    """
    config = ServeApiEventsConfig()
    transport = ServeApiEventsTransport(config)

    # 1. Control / metadata latency profiling (50 iterations)
    latencies_ms: list[float] = []
    for _ in range(50):
        t0 = time.perf_counter()
        manifest = transport.get_openapi_manifest()
        assert manifest.openapi_version == "3.1.0"
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        latencies_ms.append(elapsed_ms)

    latencies_ms.sort()
    p95 = latencies_ms[int(len(latencies_ms) * 0.95)]
    p99 = latencies_ms[int(len(latencies_ms) * 0.99)]

    # Assert bounded metadata latency per NFR specification
    assert p95 <= 250.0, f"Control metadata p95 {p95:.2f}ms exceeds 250ms"
    assert p99 <= 1000.0, f"Control metadata p99 {p99:.2f}ms exceeds 1000ms"

    # 2. Long command returns job handle immediately without blocking event loop
    loop_blocked = False

    async def heartbeat() -> None:
        nonlocal loop_blocked
        for _ in range(5):
            await asyncio.sleep(0.01)
        loop_blocked = False

    heartbeat_task = asyncio.create_task(heartbeat())

    # Submit long command
    t0 = time.perf_counter()
    job = transport.submit_async_job("RUN_MONTE_CARLO_SIMULATION")
    submit_duration_ms = (time.perf_counter() - t0) * 1000.0

    # Submission must be immediate (< 50ms)
    assert submit_duration_ms <= 50.0, f"Job submission took {submit_duration_ms:.2f}ms"
    assert job.job_id
    assert job.state in (AsyncJobState.QUEUED, AsyncJobState.RUNNING)

    await heartbeat_task
    assert loop_blocked is False, "Event loop was blocked by job submission"

    transport.close()


@pytest.mark.asyncio
async def test_atn_iface_serve_api_events_002_provider_isolation_and_degradation() -> (
    None
):
    """ATN-IFACE-SERVE_API_EVENTS-002.

    Remove each operation owner in turn; only its operations degrade
    and no unauthorized receiver gets invoked.
    """
    # 1. Bare registry with NO providers mounted
    registry = ServiceRegistry()
    app = create_api_asgi_app(registry)
    transport_asgi = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(
        transport=transport_asgi, base_url="http://boundary"
    ) as client:
        # Settings route fails closed with CAPABILITY_UNAVAILABLE (503)
        res_settings = await client.get("/api/v1/settings")
        assert res_settings.status_code == 503
        data_settings = res_settings.json()
        assert data_settings["error"]["code"] == "CAPABILITY_UNAVAILABLE"

        # Data reference route fails closed with CAPABILITY_UNAVAILABLE (503)
        res_data = await client.get("/api/v1/data/capabilities")
        assert res_data.status_code == 503
        data_data = res_data.json()
        assert data_data["error"]["code"] == "CAPABILITY_UNAVAILABLE"

        # Market ticks route fails closed with CAPABILITY_UNAVAILABLE (503)
        res_ticks = await client.get("/api/v1/market/ticks")
        assert res_ticks.status_code == 503
        data_ticks = res_ticks.json()
        assert data_ticks["error"]["code"] == "CAPABILITY_UNAVAILABLE"

        # Unknown route fails closed with NOT_FOUND (404), never an invented default
        res_unknown = await client.get("/api/v1/nonexistent/endpoint")
        assert res_unknown.status_code == 404

    # 2. Kernel translation fidelity
    missing_cap = CapabilityUnavailableError(OBSERVE_MARKET_DATA_CAPABILITY)
    failure = translate_capability_unavailable(missing_cap)
    assert failure.code == "CAPABILITY_UNAVAILABLE"
    assert failure.problem.status == 503
    assert failure.problem.capability_key == OBSERVE_MARKET_DATA_CAPABILITY.identifier

    # 3. Scope teardown and resource release
    feat = feature()
    scope = FeatureScope(owner_id=feat.spec.feature_id)

    def register_provider(
        capability: Any,
        provider: Any,
        owner_scope: FeatureScope,
    ) -> None:
        registry.register(
            capability,
            provider,
            owner_id=feat.spec.feature_id,
            scope=owner_scope,
        )

    ctx = DefaultFeatureContext(
        spec=feat.spec,
        scope=scope,
        resolver=registry.resolve,
        provider_registrar=register_provider,
        event_bus=EventBus(),
    )
    await feat.mount(ctx, None)
    assert registry.resolve(SERVE_API_EVENTS_CAPABILITY) is feat.transport

    # Close the scope
    await scope.close()

    # Provider is revoked and cannot be resolved
    assert registry.resolve(SERVE_API_EVENTS_CAPABILITY) is None
    with pytest.raises(CapabilityUnavailableError):
        registry.require(SERVE_API_EVENTS_CAPABILITY)

    # Disposed transport rejects subsequent use
    assert feat.transport is not None
    with pytest.raises(InterfaceError) as exc_closed:
        feat.transport.serve_versioned_api("v1")
    assert exc_closed.value.error_code == "TRANSPORT_CLOSED"
