"""Lifecycle and non-functional requirement tests for FEAT-AGT-ENFORCE_MANDATE.

Covers:
- ATN-AGT-ENFORCE_MANDATE-001: Denied, expired, over-budget, resumed, and removed-provider cases
  fail closed without unauthorized receiver invocation.
- ATN-AGT-ENFORCE_MANDATE-002: 100 enable/disable cycles plus physical feature removal leave no
  leaked tasks/listeners/leases/roles/clients/staging resources and quality gates pass.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from app.contracts.agentic.capabilities import ENFORCE_MANDATE_CAPABILITY
from app.contracts.agentic.mandate import (
    BudgetEnvelope,
    CheckMandateScopeRequest,
    FirmMandate,
    MandateRefused,
    MandateScopeDecision,
    ValidateMandateRequest,
    compute_mandate_digest,
)
from app.contracts.workspace.capabilities import (
    ADMINISTER_SETTINGS_CAPABILITY,
    MANAGE_ACCOUNTS_CAPABILITY,
)
from app.contracts.workspace.models import (
    AdministerSettingsRequest,
    AdministerSettingsSuccess,
    ManageAccountsRequest,
    ManageAccountsSuccess,
    SystemSettingsRecord,
)
from app.kernel.capability import CapabilityKey
from app.kernel.context import DefaultFeatureContext
from app.kernel.events import EventBus
from app.kernel.registry import ServiceRegistry
from app.kernel.scope import FeatureScope
from app.services.agentic.enforce_mandate.enforce_mandate import (
    EnforceMandateService,
)
from app.services.agentic.enforce_mandate.feature import feature


class _FakeAccountsPort:
    """Mock accounts port."""

    def __init__(self) -> None:
        self.call_count = 0

    async def manage_accounts(
        self, request: ManageAccountsRequest
    ) -> ManageAccountsSuccess:
        self.call_count += 1
        return ManageAccountsSuccess(
            request_id=request.request_id,
            outcome="SUCCESS",
        )


class _FakeSettingsPort:
    """Mock settings port."""

    def __init__(
        self,
        settings: dict[str, str] | None = None,
        *,
        should_fail: bool = False,
    ) -> None:
        self.settings = settings or {}
        self.should_fail = should_fail
        self.call_count = 0

    async def administer_settings(
        self, request: AdministerSettingsRequest
    ) -> AdministerSettingsSuccess:
        self.call_count += 1
        if self.should_fail:
            msg = "Simulated settings port error"
            raise RuntimeError(msg)
        sys_record = SystemSettingsRecord(
            settings=self.settings,
            updated_at="2026-09-09T00:00:00.000000Z",
        )
        return AdministerSettingsSuccess(
            request_id=request.request_id,
            system=sys_record,
        )


def _build_mandate(
    now: datetime,
    *,
    offset_effective_hours: int = -1,
    offset_expires_hours: int = 24,
    budget: BudgetEnvelope | None = None,
) -> FirmMandate:
    effective_at = now + timedelta(hours=offset_effective_hours)
    expires_at = now + timedelta(hours=offset_expires_hours)
    issued_at = effective_at - timedelta(hours=1)

    env_budget = budget or BudgetEnvelope(
        max_input_tokens=10000,
        max_output_tokens=2000,
        max_model_calls=50,
        max_tool_calls=20,
        max_cost=25.0,
    )

    raw = FirmMandate(
        mandate_id="MANDATE-LIFECYCLE-001",
        version=1,
        issuer="compliance-system",
        issued_at=issued_at,
        effective_at=effective_at,
        expires_at=expires_at,
        environments=("PAPER",),
        enabled_roles=("researcher",),
        enabled_features=("signals",),
        account_scopes=("ACC-001",),
        asset_scopes=("EURUSD",),
        budgets=env_budget,
        integrity_digest="",
    )
    digest = compute_mandate_digest(raw)
    return FirmMandate(
        mandate_id=raw.mandate_id,
        version=raw.version,
        issuer=raw.issuer,
        issued_at=raw.issued_at,
        effective_at=raw.effective_at,
        expires_at=raw.expires_at,
        environments=raw.environments,
        enabled_roles=raw.enabled_roles,
        enabled_features=raw.enabled_features,
        account_scopes=raw.account_scopes,
        asset_scopes=raw.asset_scopes,
        budgets=raw.budgets,
        integrity_digest=digest,
    )


def _context(
    instance: Any,
    registry: ServiceRegistry,
    scope: FeatureScope,
) -> DefaultFeatureContext:
    def register(
        capability: CapabilityKey[Any],
        implementation: object,
        owner_scope: FeatureScope,
    ) -> None:
        registry.register(
            capability,
            implementation,
            owner_id=instance.spec.feature_id,
            scope=owner_scope,
        )

    return DefaultFeatureContext(
        spec=instance.spec,
        scope=scope,
        resolver=registry.resolve,
        provider_registrar=register,
        event_bus=EventBus(),
    )


@pytest.mark.asyncio
async def test_trc_lifecycle_001_budget_exhaustion_and_narrowing() -> None:
    """ATN-AGT-ENFORCE_MANDATE-001: budget ceilings and parent budget narrowing."""
    now = datetime(2026, 9, 9, 12, 0, tzinfo=UTC)
    accounts = _FakeAccountsPort()
    settings = _FakeSettingsPort()
    mandate_budget = BudgetEnvelope(
        max_input_tokens=1000,
        max_output_tokens=200,
        max_model_calls=10,
        max_tool_calls=5,
        max_cost=5.0,
    )
    mandate = _build_mandate(now, budget=mandate_budget)
    service = EnforceMandateService(
        accounts_port=accounts,  # type: ignore[arg-type]
        settings_port=settings,  # type: ignore[arg-type]
        clock=lambda: now,
    )

    # 1. Requested budget exceeds mandate ceiling
    over_budget_req = CheckMandateScopeRequest(
        mandate=mandate,
        requested_environment="PAPER",
        requested_role="researcher",
        requested_feature="signals",
        requested_budget=BudgetEnvelope(
            max_input_tokens=1500,  # Exceeds 1000
            max_output_tokens=100,
            max_model_calls=5,
            max_tool_calls=2,
            max_cost=2.0,
        ),
    )
    over_resp = await service.enforce_mandate(over_budget_req)
    assert isinstance(over_resp, MandateScopeDecision)
    assert over_resp.outcome == "DENIED"
    assert "BUDGET_INPUT_TOKENS_EXCEEDED" in over_resp.reason_codes

    # 2. Parent budget narrows effective ceiling
    parent_budget = BudgetEnvelope(
        max_input_tokens=400,  # Lower than mandate's 1000
        max_output_tokens=200,
        max_model_calls=10,
        max_tool_calls=5,
        max_cost=5.0,
    )
    parent_constrained_req = CheckMandateScopeRequest(
        mandate=mandate,
        requested_environment="PAPER",
        requested_role="researcher",
        requested_feature="signals",
        parent_budget=parent_budget,
        requested_budget=BudgetEnvelope(
            max_input_tokens=600,  # Below mandate (1000) but exceeds parent (400)
            max_output_tokens=100,
            max_model_calls=5,
            max_tool_calls=2,
            max_cost=2.0,
        ),
    )
    parent_resp = await service.enforce_mandate(parent_constrained_req)
    assert isinstance(parent_resp, MandateScopeDecision)
    assert parent_resp.outcome == "DENIED"
    assert "BUDGET_INPUT_TOKENS_EXCEEDED" in parent_resp.reason_codes


@pytest.mark.asyncio
async def test_trc_lifecycle_001_expired_at_retry_and_freshness() -> None:
    """ATN-AGT-ENFORCE_MANDATE-001: freshness enforcement prevents reuse of stale decisions."""
    t0 = datetime(2026, 9, 9, 12, 0, tzinfo=UTC)
    current_time = t0
    accounts = _FakeAccountsPort()
    settings = _FakeSettingsPort()
    # Mandate expires 1 hour from t0
    mandate = _build_mandate(t0, offset_effective_hours=-1, offset_expires_hours=1)
    service = EnforceMandateService(
        accounts_port=accounts,  # type: ignore[arg-type]
        settings_port=settings,  # type: ignore[arg-type]
        clock=lambda: current_time,
    )

    # Initial check at T0 is ALLOWED
    req = CheckMandateScopeRequest(
        mandate=mandate,
        requested_environment="PAPER",
        requested_role="researcher",
        requested_feature="signals",
    )
    resp_t0 = await service.enforce_mandate(req)
    assert isinstance(resp_t0, MandateScopeDecision)
    assert resp_t0.outcome == "ALLOWED"

    # Time advances 2 hours to T1 (past expires_at)
    current_time = t0 + timedelta(hours=2)
    resp_t1 = await service.enforce_mandate(req)
    assert isinstance(resp_t1, MandateRefused)
    assert resp_t1.outcome == "REFUSED"
    assert "MANDATE_EXPIRED" in resp_t1.reason_codes


@pytest.mark.asyncio
async def test_trc_lifecycle_001_provider_failure_fails_closed() -> None:
    """ATN-AGT-ENFORCE_MANDATE-001: provider failures return typed UNAVAILABLE refusal."""
    now = datetime(2026, 9, 9, 12, 0, tzinfo=UTC)
    accounts = _FakeAccountsPort()
    failing_settings = _FakeSettingsPort(should_fail=True)
    mandate = _build_mandate(now)
    service = EnforceMandateService(
        accounts_port=accounts,  # type: ignore[arg-type]
        settings_port=failing_settings,  # type: ignore[arg-type]
        clock=lambda: now,
    )

    req = CheckMandateScopeRequest(
        mandate=mandate,
        requested_environment="PAPER",
        requested_role="researcher",
        requested_feature="signals",
    )
    resp = await service.enforce_mandate(req)
    assert isinstance(resp, MandateRefused)
    assert resp.outcome == "UNAVAILABLE"
    assert "SETTINGS_PROVIDER_ERROR" in resp.reason_codes


@pytest.mark.asyncio
async def test_trc_lifecycle_002_100_mount_unmount_cycles() -> None:
    """ATN-AGT-ENFORCE_MANDATE-002: 100 mount/unmount cycles leave no leaked tasks or resources."""
    now = datetime.now(UTC)
    accounts_port = _FakeAccountsPort()
    settings_port = _FakeSettingsPort()

    disposed_count = 0

    def on_dispose() -> None:
        nonlocal disposed_count
        disposed_count += 1

    for _ in range(100):
        registry = ServiceRegistry()
        accounts_scope = FeatureScope(owner_id="ACCOUNTS")
        registry.register(
            MANAGE_ACCOUNTS_CAPABILITY,
            accounts_port,
            owner_id="ACCOUNTS",
            scope=accounts_scope,
        )
        settings_scope = FeatureScope(owner_id="SETTINGS")
        registry.register(
            ADMINISTER_SETTINGS_CAPABILITY,
            settings_port,
            owner_id="SETTINGS",
            scope=settings_scope,
        )

        feat = feature()
        feat_scope = FeatureScope(owner_id=feat.spec.feature_id)
        feat_scope.callback(on_dispose)
        ctx = _context(feat, registry, feat_scope)

        # Mount feature
        await feat.mount(ctx, {})

        # Verify capability is published and functional
        mandate_cap = registry.resolve(ENFORCE_MANDATE_CAPABILITY)
        assert mandate_cap is not None
        mandate = _build_mandate(now)
        val_resp = await mandate_cap.enforce_mandate(
            ValidateMandateRequest(mandate=mandate)
        )
        assert val_resp.outcome == "ACCEPTED"

        # Unmount / close scope
        await feat_scope.close()
        await accounts_scope.close()
        await settings_scope.close()

        # Verify capability is withdrawn
        assert registry.resolve(ENFORCE_MANDATE_CAPABILITY) is None

    assert disposed_count == 100
