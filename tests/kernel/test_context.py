"""Tests for DefaultFeatureContext capability operations and boundary enforcement."""

import asyncio
from collections.abc import Sequence
from contextlib import asynccontextmanager, contextmanager
from typing import Any, override

import pytest

from app.contracts.broker.market_data import (
    BROKER_MARKET_DATA,
    BrokerBarsRequest,
    BrokerMarketData,
    BrokerRawBar,
)
from app.contracts.data.bar_cache import BAR_CACHE, BarCache
from app.contracts.data.historical_bars import (
    HISTORICAL_BARS,
    Bar,
    HistoricalBarsRequest,
)
from app.contracts.data.realtime_ticks import REALTIME_TICKS
from app.kernel.capability import CapabilityKey, CapabilityUnavailableError
from app.kernel.context import DefaultFeatureContext
from app.kernel.feature import FeatureSpec
from app.kernel.scope import FeatureScope


class StubBrokerMarketData(BrokerMarketData):
    """Protocol-compatible broker test double."""

    @override
    async def retrieve_bars(
        self,
        _request: BrokerBarsRequest,
    ) -> Sequence[BrokerRawBar]:
        return ()


class StubBarCache(BarCache):
    """Protocol-compatible bar-cache test double."""

    @override
    async def get_bars(
        self,
        _request: HistoricalBarsRequest,
    ) -> Sequence[Bar] | None:
        return None

    @override
    async def put_bars(
        self,
        _request: HistoricalBarsRequest,
        _bars: Sequence[Bar],
    ) -> None:
        return None


def test_context_require_and_optional_declared() -> None:
    """Test resolving declared required and optional capabilities."""
    spec = FeatureSpec(
        feature_id="FEAT-DATA-RETRIEVE_BARS",
        domain="data",
        provides=frozenset({HISTORICAL_BARS}),
        requires=frozenset({BROKER_MARKET_DATA}),
        optional=frozenset({BAR_CACHE}),
    )
    scope = FeatureScope("FEAT-DATA-RETRIEVE_BARS")
    broker_service = StubBrokerMarketData()
    bar_cache = StubBarCache()
    registry: dict[str, object] = {
        BROKER_MARKET_DATA.identifier: broker_service,
        BAR_CACHE.identifier: bar_cache,
    }

    def resolver(key: CapabilityKey[Any]) -> Any | None:
        return registry.get(key.identifier)

    ctx = DefaultFeatureContext(spec=spec, scope=scope, resolver=resolver)

    assert ctx.require(BROKER_MARKET_DATA) is broker_service
    assert ctx.optional(BAR_CACHE) is bar_cache


def test_context_require_undeclared_raises() -> None:
    """Test requiring undeclared capability raises ValueError."""
    spec = FeatureSpec(
        feature_id="FEAT-DATA-RETRIEVE_BARS",
        domain="data",
        provides=frozenset({HISTORICAL_BARS}),
        requires=frozenset({BROKER_MARKET_DATA}),
    )
    scope = FeatureScope("FEAT-DATA-RETRIEVE_BARS")
    ctx = DefaultFeatureContext(spec=spec, scope=scope)

    with pytest.raises(ValueError, match="attempted to require undeclared capability"):
        ctx.require(REALTIME_TICKS)


def test_context_require_missing_raises_unavailable() -> None:
    """Test requiring declared capability with no provider raises CapabilityUnavailableError."""
    spec = FeatureSpec(
        feature_id="FEAT-DATA-RETRIEVE_BARS",
        domain="data",
        provides=frozenset({HISTORICAL_BARS}),
        requires=frozenset({BROKER_MARKET_DATA}),
    )
    scope = FeatureScope("FEAT-DATA-RETRIEVE_BARS")
    ctx = DefaultFeatureContext(spec=spec, scope=scope, resolver=lambda _key: None)

    with pytest.raises(
        CapabilityUnavailableError,
        match=r"Capability 'broker\.market-data@1' is unavailable",
    ):
        ctx.require(BROKER_MARKET_DATA)


def test_context_optional_undeclared_raises() -> None:
    """Test accessing undeclared optional capability raises ValueError."""
    spec = FeatureSpec(
        feature_id="FEAT-DATA-RETRIEVE_BARS",
        domain="data",
        provides=frozenset({HISTORICAL_BARS}),
    )
    scope = FeatureScope("FEAT-DATA-RETRIEVE_BARS")
    ctx = DefaultFeatureContext(spec=spec, scope=scope)

    with pytest.raises(
        ValueError, match="attempted to access undeclared optional capability"
    ):
        ctx.optional(REALTIME_TICKS)


def test_context_provide_declared_success() -> None:
    """Test providing a declared capability invokes the provider registrar."""
    spec = FeatureSpec(
        feature_id="FEAT-DATA-RETRIEVE_BARS",
        domain="data",
        provides=frozenset({HISTORICAL_BARS}),
    )
    scope = FeatureScope("FEAT-DATA-RETRIEVE_BARS")
    provided: dict[str, object] = {}

    def registrar(key: CapabilityKey[Any], impl: object, sc: FeatureScope) -> None:
        provided[key.identifier] = impl
        sc.callback(lambda: provided.pop(key.identifier, None))

    ctx = DefaultFeatureContext(spec=spec, scope=scope, provider_registrar=registrar)
    ctx.provide(HISTORICAL_BARS, "dummy_historical_bars_impl")

    assert provided[HISTORICAL_BARS.identifier] == "dummy_historical_bars_impl"


def test_context_provide_undeclared_raises() -> None:
    """Test providing an undeclared capability raises ValueError."""
    spec = FeatureSpec(
        feature_id="FEAT-DATA-RETRIEVE_BARS",
        domain="data",
        provides=frozenset({HISTORICAL_BARS}),
    )
    scope = FeatureScope("FEAT-DATA-RETRIEVE_BARS")
    ctx = DefaultFeatureContext(spec=spec, scope=scope)

    with pytest.raises(ValueError, match="attempted to provide undeclared capability"):
        ctx.provide(REALTIME_TICKS, "invalid_impl")


@pytest.mark.asyncio
async def test_context_spawn_and_cleanup_delegation() -> None:
    """Test spawning tasks and registering callbacks through FeatureContext."""
    spec = FeatureSpec(
        feature_id="FEAT-TASK-RUN_BACKGROUND",
        domain="data",
        provides=frozenset(),
    )
    scope = FeatureScope("FEAT-TASK-RUN_BACKGROUND")
    ctx = DefaultFeatureContext(spec=spec, scope=scope)
    cleaned_sync = False
    cleaned_async = False

    def sync_cb() -> None:
        nonlocal cleaned_sync
        cleaned_sync = True

    async def async_cb() -> None:
        nonlocal cleaned_async
        cleaned_async = True

    ctx.register_callback(sync_cb)
    ctx.register_callback(async_cb)

    task = ctx.spawn(asyncio.sleep(10), name="sleeper")
    assert not task.done()

    await ctx.scope.close()
    assert task.done()
    assert task.cancelled()
    assert cleaned_sync
    assert cleaned_async


@pytest.mark.asyncio
async def test_context_enter_context_managers() -> None:
    """Test entering sync and async context managers through FeatureContext."""
    spec = FeatureSpec(
        feature_id="FEAT-TEST-CM_CONTEXT",
        domain="data",
        provides=frozenset(),
    )
    scope = FeatureScope("FEAT-TEST-CM_CONTEXT")
    ctx = DefaultFeatureContext(spec=spec, scope=scope)
    exited: set[str] = set()

    @contextmanager
    def sync_res() -> Any:
        try:
            yield "sync_result"
        finally:
            exited.add("sync")

    @asynccontextmanager
    async def async_res() -> Any:
        try:
            yield "async_result"
        finally:
            exited.add("async")

    v1 = ctx.enter_context(sync_res(), name="sync_cm")
    v2 = await ctx.enter_async_context(async_res(), name="async_cm")

    assert v1 == "sync_result"
    assert v2 == "async_result"
    assert not exited

    await ctx.scope.close()
    assert exited == {"sync", "async"}
