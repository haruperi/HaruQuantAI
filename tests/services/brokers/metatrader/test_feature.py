"""Feature specification and mount tests for MetaTrader 5 Connection."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import app.services.brokers.metatrader.client as client_mod
import pytest
from app.contracts.broker.capabilities import (
    BROKER_OPERATIONS_CAPABILITY,
    PROVIDER_METATRADER_CAPABILITY,
)
from app.kernel.context import DefaultFeatureContext
from app.kernel.events import EventBus
from app.kernel.registry import ServiceRegistry
from app.kernel.scope import FeatureScope
from app.kernel.state import RetentionPolicy
from app.services.brokers.metatrader.config import MetaTraderConfig
from app.services.brokers.metatrader.feature import (
    MetaTraderFeature,
    feature,
)
from app.services.brokers.metatrader.manifest import SPEC


def _context(
    feature_instance: MetaTraderFeature,
) -> tuple[DefaultFeatureContext, ServiceRegistry, FeatureScope]:
    """Build a scoped context for testing feature mounting."""
    registry = ServiceRegistry()
    scope = FeatureScope(owner_id=feature_instance.spec.feature_id)

    def register(
        capability: Any,
        provider: Any,
        owner_scope: FeatureScope,
    ) -> None:
        registry.register(
            capability,
            provider,
            owner_id=feature_instance.spec.feature_id,
            scope=owner_scope,
        )

    return (
        DefaultFeatureContext(
            spec=feature_instance.spec,
            scope=scope,
            resolver=registry.resolve,
            provider_registrar=register,
            event_bus=EventBus(),
        ),
        registry,
        scope,
    )


def test_spec_declares_exact_provider_and_retained_state() -> None:
    """Verify specification metadata, capabilities, and state retention."""
    assert SPEC.provides == frozenset(
        {PROVIDER_METATRADER_CAPABILITY, BROKER_OPERATIONS_CAPABILITY}
    )
    assert SPEC.requires == frozenset()
    assert SPEC.optional == frozenset()
    assert SPEC.config_keys == frozenset(
        {"database_path", "terminal_path", "login", "password", "server", "timeout"}
    )
    assert SPEC.state is not None
    assert SPEC.state.namespace == "broker.metatrader"
    assert SPEC.state.schema_version == 1
    assert SPEC.state.retention_policy == RetentionPolicy.RETAIN


@pytest.mark.asyncio
async def test_mount_stages_provider_and_scope_withdraws_it(
    tmp_path: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify mounting stages capabilities and scope close withdraws them."""
    mock_mt5 = MagicMock()
    mock_mt5.initialize.return_value = True
    mock_mt5.terminal_info.return_value = MagicMock(connected=True)
    monkeypatch.setattr(client_mod, "mt5", mock_mt5)

    feature_instance = feature()
    assert isinstance(feature_instance, MetaTraderFeature)
    context, registry, scope = _context(feature_instance)

    db_path = str(tmp_path / "mt5_test.db")
    await feature_instance.mount(
        context,
        {"database_path": db_path, "login": 61563411, "server": "Pepperstone-Demo"},
    )
    assert feature_instance.service is not None
    resolved_ops = registry.resolve(BROKER_OPERATIONS_CAPABILITY)
    assert resolved_ops is feature_instance.service

    resolved_mt5 = registry.resolve(PROVIDER_METATRADER_CAPABILITY)
    assert resolved_mt5 is feature_instance.service

    conn_res = resolved_ops.connect()
    assert conn_res["status"] == "connected"

    await scope.close()
    assert registry.resolve(BROKER_OPERATIONS_CAPABILITY) is None
    assert registry.resolve(PROVIDER_METATRADER_CAPABILITY) is None


@pytest.mark.asyncio
async def test_mount_with_typed_config(tmp_path: Any) -> None:
    """Verify mounting with a MetaTraderConfig object."""
    feature_instance = feature()
    context, registry, scope = _context(feature_instance)

    cfg = MetaTraderConfig(database_path=tmp_path / "typed.db", login=61563411)
    await feature_instance.mount(context, cfg)

    assert registry.resolve(BROKER_OPERATIONS_CAPABILITY) is feature_instance.service
    assert registry.resolve(PROVIDER_METATRADER_CAPABILITY) is feature_instance.service
    await scope.close()
