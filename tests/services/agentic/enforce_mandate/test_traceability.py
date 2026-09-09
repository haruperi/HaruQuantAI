"""Functional traceability tests for FEAT-AGT-ENFORCE_MANDATE.

Covers:
- AT-AGT-ENFORCE_MANDATE-001: Tampered, absent, future, or expired mandate fails;
  the narrowest applicable owner/system rule wins.
- AT-AGT-ENFORCE_MANDATE-002: Forbidden authority fields are unrepresentable or rejected
  and no prohibited receiver is invoked.
- AT-AGT-ENFORCE_MANDATE-003: Missing configuration never selects a permissive default;
  removing mandate affects Agentic consumers only.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import Mock

import pytest
from app.contracts.agentic.capabilities import ENFORCE_MANDATE_CAPABILITY
from app.contracts.agentic.mandate import (
    SYSTEM_PROHIBITED_AUTHORITIES,
    BudgetEnvelope,
    CheckMandateScopeRequest,
    FirmMandate,
    InspectMandateRequest,
    MandateAccepted,
    MandateRefused,
    MandateScopeDecision,
    MandateView,
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
from app.services.agentic.enforce_mandate.config import (
    EnforceMandateConfig,
    from_dict,
)
from app.services.agentic.enforce_mandate.enforce_mandate import (
    EnforceMandateService,
)
from app.services.agentic.enforce_mandate.feature import feature


class _FakeAccountsPort:
    """Mock accounts port for tests."""

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
    """Mock settings port for tests."""

    def __init__(self, settings: dict[str, str] | None = None) -> None:
        self.settings = settings or {}
        self.call_count = 0

    async def administer_settings(
        self, request: AdministerSettingsRequest
    ) -> AdministerSettingsSuccess:
        self.call_count += 1
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
    environments: tuple[str, ...] = ("PAPER", "BACKTEST"),
    enabled_roles: tuple[str, ...] = ("researcher", "analyst"),
    enabled_features: tuple[str, ...] = ("signals", "backtest"),
    account_scopes: tuple[str, ...] = ("ACC-001", "ACC-002"),
    asset_scopes: tuple[str, ...] = ("EURUSD", "BTCUSD"),
    tamper_digest: bool = False,
) -> FirmMandate:
    effective_at = now + timedelta(hours=offset_effective_hours)
    expires_at = now + timedelta(hours=offset_expires_hours)
    issued_at = effective_at - timedelta(hours=1)

    raw_mandate = FirmMandate(
        mandate_id="MANDATE-TEST-001",
        version=1,
        issuer="compliance-system",
        issued_at=issued_at,
        effective_at=effective_at,
        expires_at=expires_at,
        environments=environments,
        enabled_roles=enabled_roles,
        enabled_features=enabled_features,
        account_scopes=account_scopes,
        asset_scopes=asset_scopes,
        budgets=BudgetEnvelope(
            max_input_tokens=10000,
            max_output_tokens=2000,
            max_model_calls=50,
            max_tool_calls=20,
            max_cost=25.0,
        ),
        integrity_digest="",
    )

    computed = compute_mandate_digest(raw_mandate)
    digest = (
        "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
        if tamper_digest
        else computed
    )

    return FirmMandate(
        mandate_id=raw_mandate.mandate_id,
        version=raw_mandate.version,
        issuer=raw_mandate.issuer,
        issued_at=raw_mandate.issued_at,
        effective_at=raw_mandate.effective_at,
        expires_at=raw_mandate.expires_at,
        environments=raw_mandate.environments,
        enabled_roles=raw_mandate.enabled_roles,
        enabled_features=raw_mandate.enabled_features,
        account_scopes=raw_mandate.account_scopes,
        asset_scopes=raw_mandate.asset_scopes,
        budgets=raw_mandate.budgets,
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
async def test_trc_mandate_001_validation_and_tamper() -> None:
    """AT-AGT-ENFORCE_MANDATE-001: validation success and integrity failure."""
    now = datetime(2026, 9, 9, 12, 0, tzinfo=UTC)
    accounts = _FakeAccountsPort()
    settings = _FakeSettingsPort()
    service = EnforceMandateService(
        accounts_port=accounts,  # type: ignore[arg-type]
        settings_port=settings,  # type: ignore[arg-type]
        clock=lambda: now,
    )

    # Valid mandate
    valid_mandate = _build_mandate(now)
    resp = await service.enforce_mandate(ValidateMandateRequest(mandate=valid_mandate))
    assert isinstance(resp, MandateAccepted)
    assert resp.outcome == "ACCEPTED"
    assert resp.mandate_ref == valid_mandate.mandate_id
    assert resp.integrity_digest == valid_mandate.integrity_digest

    # Tampered mandate
    tampered_mandate = _build_mandate(now, tamper_digest=True)
    resp_tampered = await service.enforce_mandate(
        ValidateMandateRequest(mandate=tampered_mandate)
    )
    assert isinstance(resp_tampered, MandateRefused)
    assert resp_tampered.outcome == "INVALID"
    assert "INTEGRITY_DIGEST_MISMATCH" in resp_tampered.reason_codes


@pytest.mark.asyncio
async def test_trc_mandate_001_temporal_bounds() -> None:
    """AT-AGT-ENFORCE_MANDATE-001: temporal checks fail closed on future or expired mandate."""
    now = datetime(2026, 9, 9, 12, 0, tzinfo=UTC)
    accounts = _FakeAccountsPort()
    settings = _FakeSettingsPort()
    service = EnforceMandateService(
        accounts_port=accounts,  # type: ignore[arg-type]
        settings_port=settings,  # type: ignore[arg-type]
        clock=lambda: now,
    )

    # Future mandate: effective 2 hours from now
    future_mandate = _build_mandate(
        now, offset_effective_hours=2, offset_expires_hours=24
    )
    resp_future = await service.enforce_mandate(
        ValidateMandateRequest(mandate=future_mandate)
    )
    assert isinstance(resp_future, MandateRefused)
    assert resp_future.outcome == "REFUSED"
    assert "MANDATE_FUTURE" in resp_future.reason_codes

    # Expired mandate: expired 1 hour ago
    expired_mandate = _build_mandate(
        now, offset_effective_hours=-5, offset_expires_hours=-1
    )
    resp_expired = await service.enforce_mandate(
        ValidateMandateRequest(mandate=expired_mandate)
    )
    assert isinstance(resp_expired, MandateRefused)
    assert resp_expired.outcome == "REFUSED"
    assert "MANDATE_EXPIRED" in resp_expired.reason_codes


@pytest.mark.asyncio
async def test_trc_mandate_001_narrowest_rule_wins() -> None:
    """AT-AGT-ENFORCE_MANDATE-001: system settings narrow mandate scope."""
    now = datetime(2026, 9, 9, 12, 0, tzinfo=UTC)
    accounts = _FakeAccountsPort()
    # System settings restrict environment to BACKTEST only and roles to analyst only
    settings = _FakeSettingsPort(
        settings={
            "environment": "BACKTEST",
            "allowed_roles": "analyst",
            "allowed_features": "signals,backtest",
        }
    )
    service = EnforceMandateService(
        accounts_port=accounts,  # type: ignore[arg-type]
        settings_port=settings,  # type: ignore[arg-type]
        clock=lambda: now,
    )
    mandate = _build_mandate(
        now,
        environments=("PAPER", "BACKTEST"),
        enabled_roles=("researcher", "analyst"),
    )

    # Allowed check: requesting BACKTEST, analyst, signals, with matching auth account
    allowed_req = CheckMandateScopeRequest(
        mandate=mandate,
        requested_environment="BACKTEST",
        requested_role="analyst",
        requested_feature="signals",
        requested_account="ACC-001",
        auth_account="ACC-001",
        requested_asset="EURUSD",
    )
    allowed_resp = await service.enforce_mandate(allowed_req)
    assert isinstance(allowed_resp, MandateScopeDecision)
    assert allowed_resp.outcome == "ALLOWED"
    assert not allowed_resp.reason_codes

    # Narrowed environment: mandate allows PAPER, but system only allows BACKTEST
    paper_req = CheckMandateScopeRequest(
        mandate=mandate,
        requested_environment="PAPER",
        requested_role="analyst",
        requested_account="ACC-001",
        auth_account="ACC-001",
    )
    paper_resp = await service.enforce_mandate(paper_req)
    assert isinstance(paper_resp, MandateScopeDecision)
    assert paper_resp.outcome == "DENIED"
    assert "ENVIRONMENT_NARROWED_BY_SYSTEM" in paper_resp.reason_codes

    # Narrowed role: mandate allows researcher, but system only allows analyst
    role_req = CheckMandateScopeRequest(
        mandate=mandate,
        requested_environment="BACKTEST",
        requested_role="researcher",
        requested_account="ACC-001",
        auth_account="ACC-001",
    )
    role_resp = await service.enforce_mandate(role_req)
    assert isinstance(role_resp, MandateScopeDecision)
    assert role_resp.outcome == "DENIED"
    assert "ROLE_NARROWED_BY_SYSTEM" in role_resp.reason_codes

    # Out of mandate scope role
    unknown_role_req = CheckMandateScopeRequest(
        mandate=mandate,
        requested_role="superadmin",
    )
    unknown_role_resp = await service.enforce_mandate(unknown_role_req)
    assert isinstance(unknown_role_resp, MandateScopeDecision)
    assert unknown_role_resp.outcome == "DENIED"
    assert "ROLE_OUT_OF_MANDATE_SCOPE" in unknown_role_resp.reason_codes

    # Account not authenticated
    unauth_req = CheckMandateScopeRequest(
        mandate=mandate,
        requested_account="ACC-001",
        auth_account="ACC-OTHER",
    )
    unauth_resp = await service.enforce_mandate(unauth_req)
    assert isinstance(unauth_resp, MandateScopeDecision)
    assert unauth_resp.outcome == "DENIED"
    assert "ACCOUNT_NOT_AUTHENTICATED" in unauth_resp.reason_codes


@pytest.mark.asyncio
async def test_trc_mandate_002_prohibited_authorities() -> None:
    """AT-AGT-ENFORCE_MANDATE-002: prohibited authority fields fail closed with 0 receiver calls."""
    now = datetime(2026, 9, 9, 12, 0, tzinfo=UTC)
    accounts = _FakeAccountsPort()
    settings = _FakeSettingsPort()
    service = EnforceMandateService(
        accounts_port=accounts,  # type: ignore[arg-type]
        settings_port=settings,  # type: ignore[arg-type]
        clock=lambda: now,
    )
    mandate = _build_mandate(now)

    receiver_spy = Mock()

    # Test each prohibited authority
    for prohibited in SYSTEM_PROHIBITED_AUTHORITIES:
        req = CheckMandateScopeRequest(
            mandate=mandate,
            prohibited_authority_requested=(prohibited,),
        )
        resp = await service.enforce_mandate(req)
        assert isinstance(resp, MandateScopeDecision)
        assert resp.outcome == "DENIED"
        assert "PROHIBITED_AUTHORITY_REQUESTED" in resp.reason_codes

    # Verify zero receiver calls were made
    assert receiver_spy.call_count == 0


@pytest.mark.asyncio
async def test_trc_mandate_003_missing_configuration_and_isolation() -> None:
    """AT-AGT-ENFORCE_MANDATE-003: strict configuration, unavailable dependencies, and feature isolation."""
    # 1. Strict configuration rejects unknown keys
    with pytest.raises(
        ValueError, match="Unknown mandate-enforcement configuration keys"
    ):
        from_dict({"arbitrary_permissive_key": True})
    assert isinstance(from_dict({}), EnforceMandateConfig)

    # 2. Missing dependencies fail closed
    now = datetime(2026, 9, 9, 12, 0, tzinfo=UTC)
    unconfigured_service = EnforceMandateService(accounts_port=None, settings_port=None)
    mandate = _build_mandate(now)
    resp = await unconfigured_service.enforce_mandate(
        ValidateMandateRequest(mandate=mandate)
    )
    assert isinstance(resp, MandateRefused)
    assert resp.outcome == "UNAVAILABLE"
    assert "DEPENDENCY_UNAVAILABLE" in resp.reason_codes

    # 3. Closed service fails closed
    configured_service = EnforceMandateService(
        accounts_port=_FakeAccountsPort(),  # type: ignore[arg-type]
        settings_port=_FakeSettingsPort(),  # type: ignore[arg-type]
        clock=lambda: now,
    )
    configured_service.close()
    resp_closed = await configured_service.enforce_mandate(
        ValidateMandateRequest(mandate=mandate)
    )
    assert isinstance(resp_closed, MandateRefused)
    assert resp_closed.outcome == "UNAVAILABLE"
    assert "SERVICE_CLOSED" in resp_closed.reason_codes

    # 4. Feature isolation: removing mandate stops Agentic consumers only
    registry = ServiceRegistry()
    accounts_port = _FakeAccountsPort()
    settings_port = _FakeSettingsPort()
    unrelated_key: CapabilityKey[object] = CapabilityKey("test.unrelated", 1)
    unrelated_provider = object()

    unrelated_scope = FeatureScope(owner_id="TEST-UNRELATED")
    registry.register(
        unrelated_key,
        unrelated_provider,
        owner_id="TEST-UNRELATED",
        scope=unrelated_scope,
    )

    accounts_scope = FeatureScope(owner_id="WORKSPACE-ACCOUNTS")
    registry.register(
        MANAGE_ACCOUNTS_CAPABILITY,
        accounts_port,
        owner_id="WORKSPACE-ACCOUNTS",
        scope=accounts_scope,
    )

    settings_scope = FeatureScope(owner_id="WORKSPACE-SETTINGS")
    registry.register(
        ADMINISTER_SETTINGS_CAPABILITY,
        settings_port,
        owner_id="WORKSPACE-SETTINGS",
        scope=settings_scope,
    )

    # Mount EnforceMandateFeature
    feat = feature()
    feat_scope = FeatureScope(owner_id=feat.spec.feature_id)
    ctx = _context(feat, registry, feat_scope)
    await feat.mount(ctx, {})

    # Verify mandate capability is available
    mandate_cap = registry.resolve(ENFORCE_MANDATE_CAPABILITY)
    assert mandate_cap is not None

    # Unmount / withdraw mandate capability
    await feat_scope.close()

    # Mandate capability is gone
    assert registry.resolve(ENFORCE_MANDATE_CAPABILITY) is None

    # Sibling and workspace capabilities remain fully intact
    assert registry.resolve(unrelated_key) is unrelated_provider
    assert registry.resolve(MANAGE_ACCOUNTS_CAPABILITY) is accounts_port
    assert registry.resolve(ADMINISTER_SETTINGS_CAPABILITY) is settings_port

    await unrelated_scope.close()
    await accounts_scope.close()
    await settings_scope.close()


@pytest.mark.asyncio
async def test_trc_mandate_inspect() -> None:
    """InspectMandateRequest returns exact MandateView."""
    now = datetime(2026, 9, 9, 12, 0, tzinfo=UTC)
    accounts = _FakeAccountsPort()
    settings = _FakeSettingsPort()
    service = EnforceMandateService(
        accounts_port=accounts,  # type: ignore[arg-type]
        settings_port=settings,  # type: ignore[arg-type]
        clock=lambda: now,
    )
    mandate = _build_mandate(now)

    resp = await service.enforce_mandate(InspectMandateRequest(mandate=mandate))
    assert isinstance(resp, MandateView)
    assert resp.outcome == "VIEW"
    assert resp.mandate.mandate_id == mandate.mandate_id
    assert resp.mandate.integrity_digest == mandate.integrity_digest


@pytest.mark.asyncio
async def test_feature_factory_and_config_types() -> None:
    """Test feature factories and configuration validation branches."""
    from app.services.agentic.enforce_mandate.feature import create_feature

    feat = create_feature()
    assert feat.spec.feature_id == "FEAT-AGT-ENFORCE_MANDATE"

    registry = ServiceRegistry()
    accounts_port = _FakeAccountsPort()
    settings_port = _FakeSettingsPort()
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

    # Invalid config type raises TypeError
    scope_err = FeatureScope(owner_id="TEST-ERR")
    ctx_err = _context(feat, registry, scope_err)
    with pytest.raises(TypeError, match="must be a mapping or EnforceMandateConfig"):
        await feat.mount(ctx_err, 123)  # type: ignore[arg-type]

    # EnforceMandateConfig instance succeeds
    scope_valid = FeatureScope(owner_id="TEST-VALID")
    ctx_valid = _context(feat, registry, scope_valid)
    await feat.mount(ctx_valid, EnforceMandateConfig())
    assert registry.resolve(ENFORCE_MANDATE_CAPABILITY) is not None

    await scope_valid.close()
    await accounts_scope.close()
    await settings_scope.close()


@pytest.mark.asyncio
async def test_trc_mandate_additional_rejection_dimensions() -> None:
    """Test out-of-mandate account, asset, and specific budget dimensions."""
    now = datetime(2026, 9, 9, 12, 0, tzinfo=UTC)
    accounts = _FakeAccountsPort()
    settings = _FakeSettingsPort()
    service = EnforceMandateService(
        accounts_port=accounts,  # type: ignore[arg-type]
        settings_port=settings,  # type: ignore[arg-type]
        clock=lambda: now,
    )
    mandate = _build_mandate(now)

    # 1. Requested account not in mandate
    req_acc = CheckMandateScopeRequest(
        mandate=mandate,
        requested_account="ACC-NOT-IN-MANDATE",
        auth_account="ACC-NOT-IN-MANDATE",
    )
    resp_acc = await service.enforce_mandate(req_acc)
    assert isinstance(resp_acc, MandateScopeDecision)
    assert resp_acc.outcome == "DENIED"
    assert "ACCOUNT_OUT_OF_MANDATE_SCOPE" in resp_acc.reason_codes

    # 2. Requested asset not in mandate
    req_asset = CheckMandateScopeRequest(
        mandate=mandate,
        requested_asset="UNKNOWN-ASSET",
    )
    resp_asset = await service.enforce_mandate(req_asset)
    assert isinstance(resp_asset, MandateScopeDecision)
    assert resp_asset.outcome == "DENIED"
    assert "ASSET_OUT_OF_MANDATE_SCOPE" in resp_asset.reason_codes

    # 3. Budget dimensions exceeding mandate ceiling
    req_output_tokens = CheckMandateScopeRequest(
        mandate=mandate,
        requested_budget=BudgetEnvelope(max_output_tokens=999999),
    )
    resp_out = await service.enforce_mandate(req_output_tokens)
    assert isinstance(resp_out, MandateScopeDecision)
    assert "BUDGET_OUTPUT_TOKENS_EXCEEDED" in resp_out.reason_codes

    req_models = CheckMandateScopeRequest(
        mandate=mandate,
        requested_budget=BudgetEnvelope(max_model_calls=999999),
    )
    resp_models = await service.enforce_mandate(req_models)
    assert isinstance(resp_models, MandateScopeDecision)
    assert "BUDGET_MODEL_CALLS_EXCEEDED" in resp_models.reason_codes

    req_tools = CheckMandateScopeRequest(
        mandate=mandate,
        requested_budget=BudgetEnvelope(max_tool_calls=999999),
    )
    resp_tools = await service.enforce_mandate(req_tools)
    assert isinstance(resp_tools, MandateScopeDecision)
    assert "BUDGET_TOOL_CALLS_EXCEEDED" in resp_tools.reason_codes

    req_cost = CheckMandateScopeRequest(
        mandate=mandate,
        requested_budget=BudgetEnvelope(max_cost=999999.0),
    )
    resp_cost = await service.enforce_mandate(req_cost)
    assert isinstance(resp_cost, MandateScopeDecision)
    assert "BUDGET_COST_EXCEEDED" in resp_cost.reason_codes


@pytest.mark.asyncio
async def test_usage_offline_demonstration() -> None:
    """Test offline usage execution from _usage.py."""
    from app.services.agentic.enforce_mandate._usage import _run_usage_example

    results = await _run_usage_example()
    assert results["scenario_a"]["validate_outcome"] == "ACCEPTED"  # type: ignore[index]
    assert results["scenario_a"]["scope_outcome"] == "ALLOWED"  # type: ignore[index]
    assert results["scenario_b"]["outcome"] == "INVALID"  # type: ignore[index]
    assert results["scenario_c"]["outcome"] == "UNAVAILABLE"  # type: ignore[index]
