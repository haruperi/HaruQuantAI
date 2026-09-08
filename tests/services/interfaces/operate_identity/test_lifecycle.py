"""Lifecycle, performance, and failure acceptance tests for FEAT-IFACE-OPERATE_IDENTITY."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any
from uuid import uuid7

import pytest
from app.contracts.interfaces.errors import InterfaceFailure
from app.contracts.interfaces.models import (
    OperateIdentityRequest,
    OperateIdentitySuccess,
)
from app.contracts.workspace.capabilities import MANAGE_ACCOUNTS_CAPABILITY
from app.kernel.capability import CapabilityUnavailableError
from app.kernel.context import DefaultFeatureContext
from app.kernel.events import EventBus
from app.kernel.registry import ServiceRegistry
from app.kernel.scope import FeatureScope
from app.services.interfaces.operate_identity.config import OperateIdentityConfig
from app.services.interfaces.operate_identity.feature import OperateIdentityFeature
from app.services.interfaces.operate_identity.gateway import IdentityGateway
from app.services.workspace.execute_persistence.execute_persistence import (
    ExecutePersistenceService,
)
from app.services.workspace.manage_accounts.accounts import AccountService
from app.services.workspace.manage_accounts.config import ManageAccountsConfig

if TYPE_CHECKING:
    from pathlib import Path


def _make_request(operation: str, **kwargs: object) -> OperateIdentityRequest:
    """Construct one typed operate-identity request."""
    return OperateIdentityRequest(
        request_id=str(uuid7()),
        capability_snapshot_id=str(uuid7()),
        operation=operation,  # type: ignore[arg-type]
        **kwargs,  # type: ignore[arg-type]
    )


def _context(
    feature: OperateIdentityFeature,
    registry: ServiceRegistry,
    scope: FeatureScope,
) -> DefaultFeatureContext:
    def register(capability: Any, provider: Any, owner_scope: FeatureScope) -> None:
        registry.register(
            capability,
            provider,
            owner_id=feature.spec.feature_id,
            scope=owner_scope,
        )

    return DefaultFeatureContext(
        spec=feature.spec,
        scope=scope,
        resolver=registry.resolve,
        provider_registrar=register,
        event_bus=EventBus(),
    )


@pytest.mark.asyncio
async def test_trc_operate_identity_nfr_001(tmp_path: Path) -> None:
    """ATN-IFACE-OPERATE_IDENTITY-001: BM-APP-01 latency control p95 <= 250ms and p99 <= 1s.

    Covers:
        NFR-TRC-IFACE-OPERATE_IDENTITY-001
        ATN-IFACE-OPERATE_IDENTITY-001
    """
    store = AccountService(
        ExecutePersistenceService(),
        ManageAccountsConfig(database_path=tmp_path / "nfr_001_db"),
    )
    gateway = IdentityGateway(store, OperateIdentityConfig())

    # Warm up with initial registration and initial identity lookup
    reg_req = _make_request(
        "REGISTER",
        username="perf_user",
        password="Password123",  # pragma: allowlist secret
    )
    reg_res = await gateway.operate_identity(reg_req)
    assert isinstance(reg_res, OperateIdentitySuccess)
    token = reg_res.session_token
    warmup_res = await gateway.operate_identity(
        _make_request("ME", session_token=token)
    )
    assert isinstance(warmup_res, OperateIdentitySuccess)

    latencies: list[float] = []
    # Execute 30 identity check operations (metadata lookup)
    for _ in range(30):
        t0 = time.perf_counter()
        res = await gateway.operate_identity(_make_request("ME", session_token=token))
        elapsed = time.perf_counter() - t0
        latencies.append(elapsed)
        assert isinstance(res, OperateIdentitySuccess)

    latencies.sort()
    p95 = latencies[int(len(latencies) * 0.95)]
    p99 = latencies[int(len(latencies) * 0.99)]

    # Assert performance threshold: p95 <= 250ms (0.250s), p99 <= 1.0s
    assert p95 <= 0.250, f"p95 latency exceeded 250ms: {p95 * 1000:.2f}ms"
    assert p99 <= 1.000, f"p99 latency exceeded 1s: {p99 * 1000:.2f}ms"


@pytest.mark.asyncio
async def test_trc_operate_identity_nfr_002(tmp_path: Path) -> None:
    """ATN-IFACE-OPERATE_IDENTITY-002: Provider loss or disposal returns CAPABILITY_UNAVAILABLE fail-closed.

    Covers:
        NFR-TRC-IFACE-OPERATE_IDENTITY-002
        ATN-IFACE-OPERATE_IDENTITY-002
    """
    store = AccountService(
        ExecutePersistenceService(),
        ManageAccountsConfig(database_path=tmp_path / "nfr_002_db"),
    )
    gateway = IdentityGateway(store, OperateIdentityConfig())

    # Initial operation works
    reg_res = await gateway.operate_identity(
        _make_request(
            "REGISTER",
            username="dave",
            password="Password123",  # pragma: allowlist secret
        )
    )
    assert isinstance(reg_res, OperateIdentitySuccess)

    # Dispose the gateway (simulating provider loss or teardown)
    gateway.close()

    # Subsequent requests must fail closed with CAPABILITY_UNAVAILABLE and status 503
    closed_res = await gateway.operate_identity(
        _make_request("ME", session_token=reg_res.session_token)
    )
    assert isinstance(closed_res, InterfaceFailure)
    assert closed_res.code == "CAPABILITY_UNAVAILABLE"
    assert closed_res.problem.status == 503

    # FeatureContext mount without provider must raise CapabilityUnavailableError
    feature = OperateIdentityFeature()
    registry = ServiceRegistry()
    scope = FeatureScope(feature.spec.feature_id)
    ctx = _context(feature, registry, scope)

    with pytest.raises(CapabilityUnavailableError) as exc_info:
        await feature.mount(ctx, None)
    assert MANAGE_ACCOUNTS_CAPABILITY.identifier in str(exc_info.value)
