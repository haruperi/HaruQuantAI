"""Tests for trading configuration and security controls."""

from __future__ import annotations

from decimal import Decimal

import pytest
from app.services.trading.config import (
    BrokerCapabilityEvidence,
    BrokerSecurityProfile,
    CostBudgetSettings,
    CredentialRotationResult,
    NotificationChannel,
    NotificationConfig,
    SecretReference,
    SecretResolutionResult,
    StoreConnectionTargets,
    TradingRuntimeConfig,
    apply_trading_config_reload,
    build_config_change_event,
    build_notification_payload,
    handle_credential_rotation,
    load_trading_config,
    resolve_secret_reference,
    validate_live_security_profile,
)
from app.services.trading.contracts import MutationCapability, SideEffectMode


class DummyResolver:
    def resolve_metadata(self, reference: SecretReference) -> SecretResolutionResult:
        return SecretResolutionResult(
            reference=reference.reference,
            version=reference.version,
            resolved=True,
            expires_at="2026-07-09T11:00:00Z",
        )


class LeakyResolver:
    def resolve_metadata(self, reference: SecretReference) -> SecretResolutionResult:
        return SecretResolutionResult(
            reference=reference.reference,
            resolved=True,
            redacted_value="raw-secret",
        )


class SuccessfulAdapter:
    def reauthenticate(self, reference: SecretReference) -> bool:
        return reference.reference == "vault://broker"


class FailingAdapter:
    def reauthenticate(self, reference: SecretReference) -> bool:
        _ = reference
        raise RuntimeError("rotation unavailable")


def _raw_config() -> dict[str, object]:
    return {
        "config_version": "1.0.0",
        "active_broker": "mt5",
        "store_targets": {
            "trade_store_ref": "store://trade",
            "state_store_ref": "store://state",
            "audit_sink_ref": "store://audit",
            "idempotency_store_ref": "store://idempotency",
            "event_journal_ref": "store://journal",
        },
        "secret_references": {
            "broker_credentials": {"reference": "vault://broker"},
            "database_credentials": {"reference": "vault://database"},
        },
        "broker_capability_evidence": {
            "broker_name": "mt5",
            "captured_at": "2026-07-09T10:00:00Z",
            "age_ms": 10,
            "ttl_ms": 1_000,
            "capabilities": {"market_order": True},
        },
    }


def test_config_model_defaults_disable_live_mutation() -> None:
    config = load_trading_config(_raw_config())

    assert config.live_mutation_side_effect() is SideEffectMode.PACKAGED_ONLY
    assert config.route_settings.allow_live_mutations is False


def test_stale_broker_capability_evidence_fails_closed() -> None:
    raw = _raw_config()
    raw["broker_capability_evidence"] = {
        "broker_name": "mt5",
        "captured_at": "2026-07-09T10:00:00Z",
        "age_ms": 2_000,
        "ttl_ms": 1_000,
        "capabilities": {"market_order": True},
    }

    with pytest.raises(ValueError, match="stale"):
        load_trading_config(raw)


def test_strict_loader_rejects_unknown_keys_and_missing_secret_refs() -> None:
    raw = _raw_config()
    raw["unexpected"] = True

    with pytest.raises(ValueError, match="unexpected"):
        load_trading_config(raw)

    missing = _raw_config()
    missing["secret_references"] = {
        "broker_credentials": {"reference": "vault://broker"}
    }

    with pytest.raises(ValueError, match="missing required secret references"):
        load_trading_config(missing)


def test_config_change_event_contains_redacted_hash_and_version() -> None:
    config = load_trading_config(_raw_config())
    event = build_config_change_event(
        config=config,
        actor="operator-a",
        effective_at="2026-07-09T10:00:00Z",
    )

    assert event.config_version == "1.0.0"
    assert len(event.config_hash) == 64
    assert "raw-secret" not in str(event.redacted_config)
    assert "[REDACTED]" in str(event.redacted_config)


def test_running_reload_rejects_immutable_key_changes() -> None:
    current = load_trading_config(_raw_config())
    proposed_raw = _raw_config()
    proposed_raw["active_broker"] = "ctrader"
    proposed = load_trading_config(proposed_raw)

    with pytest.raises(ValueError, match="immutable config keys"):
        apply_trading_config_reload(
            current=current,
            proposed=proposed,
            session_state="running",
            actor="operator-a",
            effective_at="2026-07-09T10:00:00Z",
        )


def test_stopped_reload_allows_mutable_config_event() -> None:
    current = load_trading_config(_raw_config())
    proposed_raw = _raw_config()
    proposed_raw["rate_limits"] = {
        "max_requests": 20,
        "per_seconds": "1.0",
        "burst": 20,
    }
    proposed = load_trading_config(proposed_raw)

    event = apply_trading_config_reload(
        current=current,
        proposed=proposed,
        session_state="running",
        actor="operator-a",
        effective_at="2026-07-09T10:00:00Z",
    )

    assert event.config_hash


def test_secret_resolution_never_returns_raw_values() -> None:
    reference = SecretReference(reference="vault://broker", version="v1")
    result = resolve_secret_reference(reference=reference, resolver=DummyResolver())

    assert result.redacted_value == "[REDACTED]"

    with pytest.raises(ValueError, match="raw secret"):
        resolve_secret_reference(reference=reference, resolver=LeakyResolver())


def test_credential_rotation_success_and_failure_paths() -> None:
    reference = SecretReference(reference="vault://broker")

    success = handle_credential_rotation(
        reference=reference,
        adapter=SuccessfulAdapter(),
    )
    failure = handle_credential_rotation(reference=reference, adapter=FailingAdapter())

    assert isinstance(success, CredentialRotationResult)
    assert success.status == "success"
    assert failure.mutation_capability is MutationCapability.READ_ONLY
    assert failure.severity == "high"
    assert failure.retry_with_stale_credentials is False


def test_notification_payload_routes_only_to_approved_redacted_channels() -> None:
    config = NotificationConfig(
        channels=(
            NotificationChannel(
                name="ops",
                kind="email",
                approved=True,
                target_ref="notify://ops",
            ),
        )
    )

    payload = build_notification_payload(
        config=config,
        channel_name="ops",
        event_type="incident",
        payload={"api_key": "abcdefabcdefabcdefabcdefabcdef12", "status": "failed"},
    )

    payload_body = payload["payload"]
    assert isinstance(payload_body, dict)
    assert payload_body["api_key"] == "[REDACTED]"

    with pytest.raises(ValueError, match="approved"):
        build_notification_payload(
            config=config,
            channel_name="missing",
            event_type="incident",
            payload={},
        )


def test_live_security_profile_requires_encrypted_compliant_adapter() -> None:
    profile = BrokerSecurityProfile(
        profile_name="live-secure",
        adapter_attestation="signed-attestation",
        compliant_adapters=frozenset({"mt5"}),
    )

    validate_live_security_profile(profile=profile, adapter_name="mt5")

    with pytest.raises(ValueError, match="encrypted transport"):
        validate_live_security_profile(
            profile=profile.model_copy(update={"encrypted_transport_required": False}),
            adapter_name="mt5",
        )

    with pytest.raises(ValueError, match="not approved"):
        validate_live_security_profile(profile=profile, adapter_name="ctrader")


def test_explicit_model_construction_covers_budget_and_targets() -> None:
    config = TradingRuntimeConfig(
        active_broker="mt5",
        store_targets=StoreConnectionTargets(
            trade_store_ref="store://trade",
            state_store_ref="store://state",
            audit_sink_ref="store://audit",
            idempotency_store_ref="store://idempotency",
            event_journal_ref="store://journal",
        ),
        secret_references={
            "broker_credentials": SecretReference(reference="vault://broker"),
            "database_credentials": SecretReference(reference="vault://database"),
        },
        cost_budgets=CostBudgetSettings(
            max_order_notional=Decimal(1000),
            max_daily_transaction_cost=Decimal(10),
            currency="USD",
        ),
        broker_capability_evidence=BrokerCapabilityEvidence(
            broker_name="mt5",
            captured_at="2026-07-09T10:00:00Z",
            age_ms=0,
            ttl_ms=1_000,
        ),
    )

    assert config.cost_budgets.max_order_notional == Decimal(1000)
