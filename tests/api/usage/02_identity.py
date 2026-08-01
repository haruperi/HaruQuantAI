"""Standalone API identity, session, credential, and settings usage."""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.api import (
    authenticate_api_user,
    build_authoritative_auth_context,
    build_broker_connection_config,
    build_governed_request_context,
    consume_api_approval,
    create_api_approval,
    create_api_session,
    finalize_api_idempotency_key,
    get_user_settings,
    register_api_user,
    require_api_permission,
    reserve_api_idempotency_key,
    resolve_api_credential_reference,
    revoke_api_session,
    run_api_migrations,
    store_api_credential,
    update_user_settings,
    validate_api_csrf,
    validate_api_session,
    validate_governed_api_request,
)
from app.services.data import build_data_settings, data_settings_context
from app.utils import generate_id
from pydantic import SecretStr


def main() -> None:
    """Run public identity operations against isolated durable state."""
    with TemporaryDirectory() as directory:
        settings = build_data_settings(
            database_url="sqlite:///api-usage.db",
            data_dir=Path(directory),
            sqlite_busy_timeout_seconds=1.0,
            write_lock_lease_seconds=10.0,
            approved_storage_roots=(Path(),),
        )
        with data_settings_context(settings):
            assert run_api_migrations(generate_id("req")).status == "success"
            user = register_api_user(
                username="api-usage-user",
                password="bounded usage password",  # pragma: allowlist secret
                permissions=("settings:read", "settings:write"),
                request_id=generate_id("req"),
            )
            user = authenticate_api_user(
                username=user.username,
                password="bounded usage password",  # pragma: allowlist secret
                request_id=generate_id("req"),
            )
            session = create_api_session(
                user,
                request_id=generate_id("req"),
                ttl_seconds=60,
            )
            assert (
                validate_api_session(
                    session.session_token,
                    request_id=generate_id("req"),
                ).user_id
                == user.user_id
            )
            validate_api_csrf(
                session.session_token,
                session.csrf_token,
                request_id=generate_id("req"),
            )
            context = build_authoritative_auth_context(
                principal={
                    "principal_id": user.user_id,
                    "principal_type": "USER",
                    "roles": user.roles,
                    "permissions": user.permissions,
                    "scopes": user.scopes,
                    "tenant_or_environment": user.tenant_or_environment,
                },
                trace={
                    "issued_at": datetime.now(UTC),
                    "request_id": generate_id("req"),
                    "workflow_id": generate_id("wf"),
                    "correlation_id": generate_id("cor"),
                },
            )
            require_api_permission(context, "settings:write")
            governed = build_governed_request_context(
                workflow="settings.update",
                permission="settings:write",
                actor_id=user.user_id,
                evidence_id="evidence-settings-usage",
                idempotency_key="idem-settings-usage",
                route_id="api.settings.update",
                audit_reference="audit-settings-usage",
                request_id=context.request_id,
                trace_id=context.correlation_id,
                stale_after_seconds=30,
            )
            validate_governed_api_request(context, governed)
            evidence = {"settings_version": 0}
            approval = create_api_approval(
                issuer_id="usage-approver",
                subject_id=user.user_id,
                scope="settings.update",
                evidence=evidence,
                ttl_seconds=60,
                request_id=generate_id("req"),
            )
            consume_api_approval(
                approval.approval_id,
                subject_id=user.user_id,
                scope="settings.update",
                evidence=evidence,
                request_id=generate_id("req"),
            )
            reservation = reserve_api_idempotency_key(
                principal_id=user.user_id,
                method="PUT",
                route="/api/v1/settings",
                key="settings-usage-key",
                request_material=evidence,
                request_id=generate_id("req"),
            )
            assert reservation.state == "reserved"
            finalize_api_idempotency_key(
                principal_id=user.user_id,
                method="PUT",
                route="/api/v1/settings",
                key="settings-usage-key",
                response_json='{"status":"success"}',
                status_code=200,
                request_id=generate_id("req"),
            )
            current = get_user_settings(user.user_id, request_id=generate_id("req"))
            updated = update_user_settings(
                user.user_id,
                {"theme": "dark"},
                expected_version=current.version,
                request_id=generate_id("req"),
            )
            key = b"u" * 32
            credential = store_api_credential(
                owner_id=user.user_id,
                label="paper",
                material={"api_key": SecretStr("usage-only-value")},
                key_set={"active": key},
                active_key_id="active",
                request_id=generate_id("req"),
            )
            resolved = resolve_api_credential_reference(
                credential.reference,
                owner_id=user.user_id,
                key_set={"active": key},
                request_id=generate_id("req"),
            )
            assert resolved["api_key"].get_secret_value() == "usage-only-value"
            broker_config = build_broker_connection_config(
                credential_reference=credential.reference,
                owner_id=user.user_id,
                key_set={"active": key},
                request_id=generate_id("req"),
                broker_id="mt5",
                environment="demo",
                account_reference="usage-paper-account",
                provider_enabled=False,
            )
            assert broker_config.broker_id == "mt5"
            revoke_api_session(session.session_token, request_id=generate_id("req"))
            print({"user_id": user.user_id, "settings_version": updated.version})


if __name__ == "__main__":
    main()
