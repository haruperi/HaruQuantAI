"""Offline usage demonstration for Mandate Enforcement."""

from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime, timedelta

from app.composition.logging import get_logger
from app.contracts.agentic.mandate import (
    BudgetEnvelope,
    CheckMandateScopeRequest,
    FirmMandate,
    ValidateMandateRequest,
    compute_mandate_digest,
)
from app.contracts.workspace.models import (
    AdministerSettingsRequest,
    AdministerSettingsSuccess,
    ManageAccountsRequest,
    ManageAccountsSuccess,
    SystemSettingsRecord,
)
from app.services.agentic.enforce_mandate.enforce_mandate import (
    EnforceMandateService,
)

logger = get_logger("agentic.enforce_mandate._usage")


class _DemoAccountsPort:
    """Offline accounts port for demonstration."""

    async def manage_accounts(
        self, request: ManageAccountsRequest
    ) -> ManageAccountsSuccess:
        """Handle mock accounts operation.

        Args:
            request: Account request.

        Returns:
            ManageAccountsSuccess.
        """
        return ManageAccountsSuccess(
            request_id=request.request_id,
            outcome="SUCCESS",
        )


class _DemoSettingsPort:
    """Offline settings port providing deterministic system environment."""

    async def administer_settings(
        self, request: AdministerSettingsRequest
    ) -> AdministerSettingsSuccess:
        """Handle mock settings operation.

        Args:
            request: Settings request.

        Returns:
            AdministerSettingsSuccess.
        """
        sys_record = SystemSettingsRecord(
            settings={
                "environment": "demo,research",
                "allowed_roles": "analyst,specialist",
            },
            updated_at="2026-09-09T00:00:00.000000Z",
        )
        return AdministerSettingsSuccess(
            request_id=request.request_id,
            system=sys_record,
        )


async def _run_usage_example() -> dict[str, object]:
    """Execute offline scenarios demonstrating mandate enforcement.

    Returns:
        Dictionary recording outcomes of Scenarios A, B, and C.
    """
    now = datetime.now(UTC)
    accounts_port = _DemoAccountsPort()
    settings_port = _DemoSettingsPort()
    service = EnforceMandateService(
        accounts_port=accounts_port,
        settings_port=settings_port,
        clock=lambda: now,
    )

    results: dict[str, object] = {}

    budget = BudgetEnvelope(
        max_input_tokens=10000,
        max_output_tokens=2000,
        max_model_calls=50,
        max_tool_calls=20,
        max_cost=25.0,
    )
    issued_at = now - timedelta(hours=1)
    effective_at = now - timedelta(minutes=30)
    expires_at = now + timedelta(hours=8)

    mandate_payload: dict[str, object] = {
        "mandate_id": "MANDATE-DEMO-001",
        "version": 1,
        "issuer": "firm-risk-authority",
        "issued_at": issued_at,
        "effective_at": effective_at,
        "expires_at": expires_at,
        "objectives": ("evaluate_research",),
        "asset_scopes": ("EURUSD", "GBPUSD"),
        "account_scopes": ("ACC-DEMO-01",),
        "environments": ("demo", "research"),
        "enabled_features": ("FEAT-AGT-OPERATE_RUNS",),
        "enabled_roles": ("analyst", "specialist"),
        "budgets": budget,
        "human_action_policy": "required",
        "prohibited_authority": (
            "broker_credentials",
            "order_construction",
            "risk_approval",
            "kill_switch_clear",
            "live_deployment",
            "receiver_authority",
        ),
        "fallback_policy": "fail_closed",
        "policy_refs": ("POL-RISK-2026-01",),
        "schema_version": 1,
    }
    digest = compute_mandate_digest(mandate_payload)
    valid_mandate = FirmMandate(
        mandate_id="MANDATE-DEMO-001",
        version=1,
        issuer="firm-risk-authority",
        issued_at=issued_at,
        effective_at=effective_at,
        expires_at=expires_at,
        objectives=("evaluate_research",),
        asset_scopes=("EURUSD", "GBPUSD"),
        account_scopes=("ACC-DEMO-01",),
        environments=("demo", "research"),
        enabled_features=("FEAT-AGT-OPERATE_RUNS",),
        enabled_roles=("analyst", "specialist"),
        budgets=budget,
        human_action_policy="required",
        prohibited_authority=(
            "broker_credentials",
            "order_construction",
            "risk_approval",
            "kill_switch_clear",
            "live_deployment",
            "receiver_authority",
        ),
        fallback_policy="fail_closed",
        policy_refs=("POL-RISK-2026-01",),
        integrity_digest=digest,
        schema_version=1,
    )

    # --- Scenario A: Valid Mandate and In-Scope Operation ---
    val_resp = await service.enforce_mandate(
        ValidateMandateRequest(mandate=valid_mandate)
    )
    scope_req = CheckMandateScopeRequest(
        mandate=valid_mandate,
        requested_feature="FEAT-AGT-OPERATE_RUNS",
        requested_role="analyst",
        requested_environment="demo",
        requested_account="ACC-DEMO-01",
        requested_asset="EURUSD",
        auth_account="ACC-DEMO-01",
        requested_budget=BudgetEnvelope(
            max_input_tokens=1000,
            max_output_tokens=200,
            max_model_calls=5,
            max_tool_calls=2,
            max_cost=2.5,
        ),
    )
    scope_resp = await service.enforce_mandate(scope_req)
    results["scenario_a"] = {
        "validate_outcome": val_resp.outcome,
        "scope_outcome": scope_resp.outcome,
    }

    # --- Scenario B: Tampered Mandate (tampered account scope, reused digest) ---
    tampered_mandate = valid_mandate.model_copy(
        update={"account_scopes": ("ACC-MALICIOUS-01",)}
    )
    tampered_resp = await service.enforce_mandate(
        ValidateMandateRequest(mandate=tampered_mandate)
    )
    results["scenario_b"] = {
        "outcome": tampered_resp.outcome,
        "reason_codes": getattr(tampered_resp, "reason_codes", ()),
    }

    # --- Scenario C: Closed Service Scope ---
    service.close()
    closed_resp = await service.enforce_mandate(
        ValidateMandateRequest(mandate=valid_mandate)
    )
    results["scenario_c"] = {
        "outcome": closed_resp.outcome,
        "reason_codes": getattr(closed_resp, "reason_codes", ()),
    }

    return results


if __name__ == "__main__":
    outcomes = asyncio.run(_run_usage_example())
    print(json.dumps(outcomes, indent=2))
