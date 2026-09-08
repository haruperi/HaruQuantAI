"""Executable usage demonstrations for FEAT-WS-SECURE_LOCAL_ACCESS."""

from __future__ import annotations

from uuid import uuid7

from app.contracts.workspace.errors import (
    NonLoopbackAccessDeniedError,
    SecretResolutionDeniedError,
    SecretRevokedError,
    SessionDeniedError,
)
from app.contracts.workspace.secure_local_access import (
    SecretCreateRequest,
    SecretResolveRequest,
    SecretRevokeRequest,
    SecretRotateRequest,
)
from app.services.workspace.secure_local_access.config import (
    SecureLocalAccessConfig,
)
from app.services.workspace.secure_local_access.secure_local_access import (
    SecureLocalAccessService,
)

SAMPLE_GENERATION_V1 = "gen-1"
SAMPLE_GENERATION_V2 = "gen-2"
SAMPLE_PURPOSE = "broker-auth"
SAMPLE_SECRET_VAL_1 = "super-secret-token-v1"  # pragma: allowlist secret # noqa: S105
SAMPLE_SECRET_VAL_2 = "super-secret-token-v2"  # pragma: allowlist secret # noqa: S105
LOOPBACK_ADDR = "127.0.0.1"
REMOTE_ADDR = "192.168.1.100"
SESSION_TTL_SECONDS = 300
EXPECTED_ROTATED_ROW_VERSION = 2


def _scenario_1_resolve_secrets(
    service: SecureLocalAccessService,
) -> tuple[str, str]:
    """Execute scenario 1: FR-TRC-WS-SECURE_LOCAL_ACCESS-001.

    Args:
        service: Active SecureLocalAccessService instance.

    Returns:
        Tuple of (workspace_id, secret_id) created in scenario 1.

    Raises:
        RuntimeError: If secret lifecycle behavior deviates from requirements.
    """
    workspace_id = str(uuid7())
    sample_secret_name = "binance_api_key"  # pragma: allowlist secret # noqa: S105

    # 1. Create opaque secret reference
    create_req = SecretCreateRequest(
        workspace_id=workspace_id,
        name=sample_secret_name,
        secret_value=SAMPLE_SECRET_VAL_1,
        allowed_adapter_generation=SAMPLE_GENERATION_V1,
        allowed_purpose=SAMPLE_PURPOSE,
    )
    secret_ref = service.create_secret_reference(create_req)
    if hasattr(secret_ref, "secret_value"):
        msg = "SecretRef must remain opaque and not contain secret_value"
        raise RuntimeError(msg)

    # 2. Authorized adapter resolution succeeds
    resolve_req = SecretResolveRequest(
        workspace_id=workspace_id,
        secret_id=secret_ref.secret_id,
        adapter_generation=SAMPLE_GENERATION_V1,
        purpose=SAMPLE_PURPOSE,
        caller_role="adapter",
    )
    resolved = service.resolve_secret_reference(resolve_req)
    if resolved.secret_value != SAMPLE_SECRET_VAL_1:
        msg = "Resolved secret value does not match provisioned plaintext"
        raise RuntimeError(msg)

    # 3. Caller role isolation (UI caller denied)
    try:
        ui_req = SecretResolveRequest(
            workspace_id=workspace_id,
            secret_id=secret_ref.secret_id,
            adapter_generation=SAMPLE_GENERATION_V1,
            purpose=SAMPLE_PURPOSE,
            caller_role="ui",
        )
        service.resolve_secret_reference(ui_req)
        msg = "UI caller was unexpectedly permitted to resolve secret"
        raise RuntimeError(msg)
    except SecretResolutionDeniedError:
        pass

    # 4. Caller role isolation (Agentic caller denied)
    try:
        agent_req = SecretResolveRequest(
            workspace_id=workspace_id,
            secret_id=secret_ref.secret_id,
            adapter_generation=SAMPLE_GENERATION_V1,
            purpose=SAMPLE_PURPOSE,
            caller_role="agentic",
        )
        service.resolve_secret_reference(agent_req)
        msg = "Agentic caller was unexpectedly permitted to resolve secret"
        raise RuntimeError(msg)
    except SecretResolutionDeniedError:
        pass

    # 5. Purpose mismatch isolation
    try:
        mismatch_req = SecretResolveRequest(
            workspace_id=workspace_id,
            secret_id=secret_ref.secret_id,
            adapter_generation=SAMPLE_GENERATION_V1,
            purpose="different-purpose",
            caller_role="adapter",
        )
        service.resolve_secret_reference(mismatch_req)
        msg = "Purpose mismatch was unexpectedly permitted"
        raise RuntimeError(msg)
    except SecretResolutionDeniedError:
        pass

    return workspace_id, secret_ref.secret_id


def _scenario_2_host_protection(
    service: SecureLocalAccessService,
) -> None:
    """Execute scenario 2: FR-TRC-WS-SECURE_LOCAL_ACCESS-002.

    Args:
        service: Active SecureLocalAccessService instance.

    Raises:
        RuntimeError: If host protection or readiness sanitization fails.
    """
    # 1. Issue local session on loopback
    session = service.issue_local_session(
        client_id="launcher_client",
        is_launcher_connected=True,
        client_host=LOOPBACK_ADDR,
        ttl_seconds=SESSION_TTL_SECONDS,
    )
    verified = service.verify_local_session(
        token=session.token,
        client_host=LOOPBACK_ADDR,
    )
    if verified.client_id != "launcher_client":
        msg = "Verified session client ID mismatch"
        raise RuntimeError(msg)

    # 2. Reject unauthenticated / unconnected launcher client
    try:
        service.issue_local_session(
            client_id="unverified_client",
            is_launcher_connected=False,
            client_host=LOOPBACK_ADDR,
        )
        msg = "Unconnected launcher client was unexpectedly issued a session"
        raise RuntimeError(msg)
    except SessionDeniedError:
        pass

    # 3. Reject non-loopback verification
    try:
        service.verify_local_session(
            token=session.token,
            client_host=REMOTE_ADDR,
        )
        msg = "Non-loopback client was unexpectedly verified"
        raise RuntimeError(msg)
    except NonLoopbackAccessDeniedError:
        pass

    # 4. Immediate session revocation
    service.revoke_local_session(session.token)
    try:
        service.verify_local_session(
            token=session.token,
            client_host=LOOPBACK_ADDR,
        )
        msg = "Revoked session was unexpectedly verified"
        raise RuntimeError(msg)
    except SessionDeniedError:
        pass

    # 5. Readiness report sanitization
    health = service.check_system_health()
    if not health.healthy:
        msg = "Service health check failed"
        raise RuntimeError(msg)

    readiness = service.report_system_readiness()
    if not readiness.healthy:
        msg = "Service should be operational and healthy"
        raise RuntimeError(msg)
    reasons_blob = " ".join(readiness.reasons)
    if session.token in reasons_blob:
        msg = "Session token leaked in readiness report reasons"
        raise RuntimeError(msg)


def _scenario_3_rotation_and_revocation(
    service: SecureLocalAccessService,
    workspace_id: str,
    secret_id: str,
) -> None:
    """Execute scenario 3: FR-TRC-WS-SECURE_LOCAL_ACCESS-003.

    Args:
        service: Active SecureLocalAccessService instance.
        workspace_id: Workspace ID containing the secret.
        secret_id: Secret ID to rotate and revoke.

    Raises:
        RuntimeError: If rotation, revocation, or zeroization fails.
    """
    # 1. Rotate secret to advance generation
    rot_req = SecretRotateRequest(
        workspace_id=workspace_id,
        secret_id=secret_id,
        new_secret_value=SAMPLE_SECRET_VAL_2,
        new_adapter_generation=SAMPLE_GENERATION_V2,
        allowed_purpose=SAMPLE_PURPOSE,
    )
    updated_ref = service.rotate_secret_reference(rot_req)
    if updated_ref.row_version != EXPECTED_ROTATED_ROW_VERSION:
        msg = "Rotated SecretRef row_version did not increment to 2"
        raise RuntimeError(msg)

    # 2. Old generation resolution is denied
    try:
        old_req = SecretResolveRequest(
            workspace_id=workspace_id,
            secret_id=secret_id,
            adapter_generation=SAMPLE_GENERATION_V1,
            purpose=SAMPLE_PURPOSE,
            caller_role="adapter",
        )
        service.resolve_secret_reference(old_req)
        msg = "Old generation resolution was unexpectedly permitted"
        raise RuntimeError(msg)
    except SecretResolutionDeniedError:
        pass

    # 3. New generation resolution succeeds
    new_req = SecretResolveRequest(
        workspace_id=workspace_id,
        secret_id=secret_id,
        adapter_generation=SAMPLE_GENERATION_V2,
        purpose=SAMPLE_PURPOSE,
        caller_role="adapter",
    )
    resolved_v2 = service.resolve_secret_reference(new_req)
    if resolved_v2.secret_value != SAMPLE_SECRET_VAL_2:
        msg = "Resolved v2 secret value does not match updated secret"
        raise RuntimeError(msg)

    # 4. Revoke secret reference
    service.revoke_secret_reference(
        SecretRevokeRequest(
            workspace_id=workspace_id,
            secret_id=secret_id,
            reason="Compromised credential rotation test",
        )
    )

    # 5. Revoked secret resolution is denied
    try:
        service.resolve_secret_reference(new_req)
        msg = "Revoked secret was unexpectedly resolved"
        raise RuntimeError(msg)
    except SecretRevokedError:
        pass


def run_usage_scenarios() -> None:
    """Run all three usage scenarios sequentially.

    Raises:
        RuntimeError: If any scenario assertion fails.
    """
    config = SecureLocalAccessConfig(
        default_session_ttl_seconds=3600,
        enforce_loopback=True,
    )
    service = SecureLocalAccessService(config=config)
    try:
        workspace_id, secret_id = _scenario_1_resolve_secrets(service)
        _scenario_2_host_protection(service)
        _scenario_3_rotation_and_revocation(service, workspace_id, secret_id)
    finally:
        service.close()


if __name__ == "__main__":
    run_usage_scenarios()
