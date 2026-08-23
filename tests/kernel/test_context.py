"""Tests for DefaultFeatureContext capability operations and boundary enforcement."""

import asyncio
from contextlib import asynccontextmanager, contextmanager
from typing import Any

import pytest

from app.kernel.capability import CapabilityKey, CapabilityUnavailableError
from app.kernel.context import DefaultFeatureContext
from app.kernel.feature import FeatureSpec
from app.kernel.scope import FeatureScope
from tests._support.composability import (
    CONSUMER_CAPABILITY,
    OPTIONAL_CAPABILITY,
    PROVIDER_CAPABILITY,
    UNDECLARED_CAPABILITY,
)


def test_context_require_and_optional_declared() -> None:
    """Test resolving declared required and optional capabilities."""
    spec = FeatureSpec(
        feature_id="FEAT-TEST-CONSUME_SERVICE",
        domain="test",
        provides=frozenset({CONSUMER_CAPABILITY}),
        requires=frozenset({PROVIDER_CAPABILITY}),
        optional=frozenset({OPTIONAL_CAPABILITY}),
    )
    scope = FeatureScope("FEAT-TEST-CONSUME_SERVICE")
    provider_service = object()
    optional_service = object()
    registry: dict[str, object] = {
        PROVIDER_CAPABILITY.identifier: provider_service,
        OPTIONAL_CAPABILITY.identifier: optional_service,
    }

    def resolver(key: CapabilityKey[Any]) -> Any | None:
        return registry.get(key.identifier)

    ctx = DefaultFeatureContext(spec=spec, scope=scope, resolver=resolver)

    assert ctx.require(PROVIDER_CAPABILITY) is provider_service
    assert ctx.optional(OPTIONAL_CAPABILITY) is optional_service


def test_context_require_undeclared_raises() -> None:
    """Test requiring undeclared capability raises ValueError."""
    spec = FeatureSpec(
        feature_id="FEAT-TEST-CONSUME_SERVICE",
        domain="test",
        provides=frozenset({CONSUMER_CAPABILITY}),
        requires=frozenset({PROVIDER_CAPABILITY}),
    )
    scope = FeatureScope("FEAT-TEST-CONSUME_SERVICE")
    ctx = DefaultFeatureContext(spec=spec, scope=scope)

    with pytest.raises(ValueError, match="attempted to require undeclared capability"):
        ctx.require(UNDECLARED_CAPABILITY)


def test_context_require_missing_raises_unavailable() -> None:
    """Test requiring declared capability with no provider raises CapabilityUnavailableError."""
    spec = FeatureSpec(
        feature_id="FEAT-TEST-CONSUME_SERVICE",
        domain="test",
        provides=frozenset({CONSUMER_CAPABILITY}),
        requires=frozenset({PROVIDER_CAPABILITY}),
    )
    scope = FeatureScope("FEAT-TEST-CONSUME_SERVICE")
    ctx = DefaultFeatureContext(spec=spec, scope=scope, resolver=lambda _key: None)

    with pytest.raises(
        CapabilityUnavailableError,
        match=r"Capability 'test\.provider@1' is unavailable",
    ):
        ctx.require(PROVIDER_CAPABILITY)


def test_context_optional_undeclared_raises() -> None:
    """Test accessing undeclared optional capability raises ValueError."""
    spec = FeatureSpec(
        feature_id="FEAT-TEST-CONSUME_SERVICE",
        domain="test",
        provides=frozenset({CONSUMER_CAPABILITY}),
    )
    scope = FeatureScope("FEAT-TEST-CONSUME_SERVICE")
    ctx = DefaultFeatureContext(spec=spec, scope=scope)

    with pytest.raises(
        ValueError, match="attempted to access undeclared optional capability"
    ):
        ctx.optional(UNDECLARED_CAPABILITY)


def test_context_provide_declared_success() -> None:
    """Test providing a declared capability invokes the provider registrar."""
    spec = FeatureSpec(
        feature_id="FEAT-TEST-CONSUME_SERVICE",
        domain="test",
        provides=frozenset({CONSUMER_CAPABILITY}),
    )
    scope = FeatureScope("FEAT-TEST-CONSUME_SERVICE")
    provided: dict[str, object] = {}

    def registrar(key: CapabilityKey[Any], impl: object, sc: FeatureScope) -> None:
        provided[key.identifier] = impl
        sc.callback(lambda: provided.pop(key.identifier, None))

    ctx = DefaultFeatureContext(spec=spec, scope=scope, provider_registrar=registrar)
    ctx.provide(CONSUMER_CAPABILITY, "consumer_service")

    assert provided[CONSUMER_CAPABILITY.identifier] == "consumer_service"


def test_context_provide_undeclared_raises() -> None:
    """Test providing an undeclared capability raises ValueError."""
    spec = FeatureSpec(
        feature_id="FEAT-TEST-CONSUME_SERVICE",
        domain="test",
        provides=frozenset({CONSUMER_CAPABILITY}),
    )
    scope = FeatureScope("FEAT-TEST-CONSUME_SERVICE")
    ctx = DefaultFeatureContext(spec=spec, scope=scope)

    with pytest.raises(ValueError, match="attempted to provide undeclared capability"):
        ctx.provide(UNDECLARED_CAPABILITY, "invalid_impl")


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
