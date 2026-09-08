"""Traceability test suite for FEAT-WS-SECURE_LOCAL_ACCESS."""

from __future__ import annotations

import tempfile
from pathlib import Path
from uuid import uuid7

import pytest
from app.contracts.workspace.errors import (
    NonLoopbackAccessDeniedError,
    SecretNotFoundError,
    SecretResolutionDeniedError,
    SecretRevokedError,
    SessionDeniedError,
)
from app.contracts.workspace.models import (
    SecretName,
    WorkspaceRef,
    WorkspaceStatus,
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

SAMPLE_PURPOSE = "broker-order-execution"
SAMPLE_GEN_1 = "adapter-v1"
SAMPLE_GEN_2 = "adapter-v2"
SAMPLE_SECRET_PLAINTEXT = "secret-broker-api-token-998"  # pragma: allowlist secret
LOOPBACK_HOST = "127.0.0.1"
REMOTE_HOST = "10.0.0.50"


def _create_service(
    *,
    enforce_loopback: bool = True,
    allowed_remote_subnets: tuple[str, ...] = (),
) -> SecureLocalAccessService:
    """Helper to build a configured SecureLocalAccessService."""
    config = SecureLocalAccessConfig(
        default_session_ttl_seconds=3600,
        enforce_loopback=enforce_loopback,
        allowed_remote_subnets=allowed_remote_subnets,
    )
    return SecureLocalAccessService(config=config)


def test_trc_secure_local_access_001() -> None:
    """AT-WS-SECURE_LOCAL_ACCESS-001: Resolve secrets only for authorized adapters.

    Verifies:
    1. Creating a secret reference yields an opaque SecretRef without secret plaintext.
    2. An authorized adapter with matching generation and purpose can resolve the secret.
    3. UI, Agentic, and unauthorized caller roles are rejected.
    4. Mismatched purpose and generation are rejected.
    5. Nonexistent secret references raise SecretNotFoundError.
    """
    service = _create_service()
    workspace_id = str(uuid7())
    secret_name: SecretName = "binance_production_key"  # pragma: allowlist secret

    create_req = SecretCreateRequest(
        workspace_id=workspace_id,
        name=secret_name,
        secret_value=SAMPLE_SECRET_PLAINTEXT,
        allowed_adapter_generation=SAMPLE_GEN_1,
        allowed_purpose=SAMPLE_PURPOSE,
    )
    secret_ref = service.create_secret_reference(create_req)

    # 1. Verify opacity: SecretRef must not expose the secret value
    assert secret_ref.secret_id
    assert secret_ref.workspace_id == workspace_id
    assert secret_ref.name == secret_name
    assert secret_ref.row_version == 1
    assert not hasattr(secret_ref, "secret_value")

    # 2. Authorized adapter resolution
    resolve_req = SecretResolveRequest(
        workspace_id=workspace_id,
        secret_id=secret_ref.secret_id,
        adapter_generation=SAMPLE_GEN_1,
        purpose=SAMPLE_PURPOSE,
        caller_role="adapter",
    )
    resolved = service.resolve_secret_reference(resolve_req)
    assert resolved.secret_value == SAMPLE_SECRET_PLAINTEXT
    assert resolved.name == secret_name
    assert resolved.adapter_generation == SAMPLE_GEN_1
    assert resolved.purpose == SAMPLE_PURPOSE

    # 3. Deny resolution to UI, agentic, and unauthorized caller roles
    for forbidden_role in ("ui", "agentic", "unauthorized", "external"):
        denied_req = SecretResolveRequest(
            workspace_id=workspace_id,
            secret_id=secret_ref.secret_id,
            adapter_generation=SAMPLE_GEN_1,
            purpose=SAMPLE_PURPOSE,
            caller_role=forbidden_role,
        )
        with pytest.raises(SecretResolutionDeniedError) as exc_info:
            service.resolve_secret_reference(denied_req)
        assert exc_info.value.error_code == "SECRET_RESOLUTION_DENIED"

    # 4. Deny resolution on generation or purpose mismatch
    bad_gen_req = SecretResolveRequest(
        workspace_id=workspace_id,
        secret_id=secret_ref.secret_id,
        adapter_generation="adapter-v999",
        purpose=SAMPLE_PURPOSE,
        caller_role="adapter",
    )
    with pytest.raises(SecretResolutionDeniedError):
        service.resolve_secret_reference(bad_gen_req)

    bad_purpose_req = SecretResolveRequest(
        workspace_id=workspace_id,
        secret_id=secret_ref.secret_id,
        adapter_generation=SAMPLE_GEN_1,
        purpose="unauthorized-purpose",
        caller_role="adapter",
    )
    with pytest.raises(SecretResolutionDeniedError):
        service.resolve_secret_reference(bad_purpose_req)

    # 5. Nonexistent secret reference
    unknown_req = SecretResolveRequest(
        workspace_id=workspace_id,
        secret_id=str(uuid7()),
        adapter_generation=SAMPLE_GEN_1,
        purpose=SAMPLE_PURPOSE,
        caller_role="adapter",
    )
    with pytest.raises(SecretNotFoundError) as not_found_exc:
        service.resolve_secret_reference(unknown_req)
    assert not_found_exc.value.error_code == "SECRET_NOT_FOUND"


def test_trc_secure_local_access_002() -> None:
    """AT-WS-SECURE_LOCAL_ACCESS-002: Enforce loopback and host policies.

    Verifies:
    1. Launcher-connected clients on loopback successfully obtain and verify sessions.
    2. Unconnected launcher clients are denied with SessionDeniedError.
    3. Non-loopback client access is rejected with NonLoopbackAccessDeniedError.
    4. Readiness and health reports redact secrets, tokens, and filesystem paths.
    """
    service = _create_service(enforce_loopback=True)

    # 1. Valid local session issuance and verification
    session = service.issue_local_session(
        client_id="desktop_launcher_01",
        is_launcher_connected=True,
        client_host=LOOPBACK_HOST,
        ttl_seconds=1200,
    )
    assert session.session_id
    assert session.token
    assert session.is_loopback is True
    assert session.is_launcher_connected is True

    verified = service.verify_local_session(
        token=session.token,
        client_host=LOOPBACK_HOST,
    )
    assert verified.client_id == "desktop_launcher_01"
    assert verified.token == session.token

    # 2. Reject unconnected clients
    with pytest.raises(SessionDeniedError) as denied_info:
        service.issue_local_session(
            client_id="unauthorized_client",
            is_launcher_connected=False,
            client_host=LOOPBACK_HOST,
        )
    assert denied_info.value.error_code == "SESSION_DENIED"

    # 3. Reject non-loopback host source
    with pytest.raises(NonLoopbackAccessDeniedError) as loopback_info:
        service.verify_local_session(
            token=session.token,
            client_host=REMOTE_HOST,
        )
    assert loopback_info.value.error_code == "NON_LOOPBACK_ACCESS_DENIED"

    # 4. Operational readiness and health check redacts secrets and absolute paths
    health = service.check_system_health()
    assert health.healthy is True

    with tempfile.TemporaryDirectory() as tmp_dir:
        fake_ws_path = Path(tmp_dir) / "test_workspace"
        ws_ref = WorkspaceRef(
            workspace_id=str(uuid7()),
            name="Test WS",
            root_path=fake_ws_path,
            status=WorkspaceStatus.READY,
            created_at="2026-01-01T00:00:00.000000Z",
        )
        readiness = service.report_system_readiness(workspace=ws_ref)
        reasons_str = " ".join(readiness.reasons)

        assert fake_ws_path.as_posix() not in reasons_str
        assert str(fake_ws_path) not in reasons_str
        assert session.token not in reasons_str


def test_trc_secure_local_access_003() -> None:
    """AT-WS-SECURE_LOCAL_ACCESS-003: Rotate and revoke secret references.

    Verifies:
    1. Rotating a secret updates the generation and increments row_version.
    2. Old generation loses resolution ability immediately.
    3. New generation resolves successfully.
    4. Revoking a secret prevents any future resolution attempts.
    5. Revoked secret zeroizes in-memory plaintext.
    """
    service = _create_service()
    workspace_id = str(uuid7())
    secret_name: SecretName = "coinbase_api_secret"  # pragma: allowlist secret
    new_plaintext = "new-rotated-secret-value-456"  # pragma: allowlist secret

    # 1. Initial creation
    ref = service.create_secret_reference(
        SecretCreateRequest(
            workspace_id=workspace_id,
            name=secret_name,
            secret_value=SAMPLE_SECRET_PLAINTEXT,
            allowed_adapter_generation=SAMPLE_GEN_1,
            allowed_purpose=SAMPLE_PURPOSE,
        )
    )
    assert ref.row_version == 1

    # 2. Rotate to advance generation
    rotated_ref = service.rotate_secret_reference(
        SecretRotateRequest(
            workspace_id=workspace_id,
            secret_id=ref.secret_id,
            new_secret_value=new_plaintext,
            new_adapter_generation=SAMPLE_GEN_2,
            allowed_purpose=SAMPLE_PURPOSE,
        )
    )
    assert rotated_ref.row_version == 2
    assert rotated_ref.secret_id == ref.secret_id

    # 3. Old generation is denied resolution
    old_gen_req = SecretResolveRequest(
        workspace_id=workspace_id,
        secret_id=ref.secret_id,
        adapter_generation=SAMPLE_GEN_1,
        purpose=SAMPLE_PURPOSE,
        caller_role="adapter",
    )
    with pytest.raises(SecretResolutionDeniedError) as old_exc:
        service.resolve_secret_reference(old_gen_req)
    assert old_exc.value.error_code == "SECRET_RESOLUTION_DENIED"

    # 4. New generation resolves updated secret
    new_gen_req = SecretResolveRequest(
        workspace_id=workspace_id,
        secret_id=ref.secret_id,
        adapter_generation=SAMPLE_GEN_2,
        purpose=SAMPLE_PURPOSE,
        caller_role="adapter",
    )
    resolved_v2 = service.resolve_secret_reference(new_gen_req)
    assert resolved_v2.secret_value == new_plaintext
    assert resolved_v2.row_version == 2

    # 5. Revocation
    service.revoke_secret_reference(
        SecretRevokeRequest(
            workspace_id=workspace_id,
            secret_id=ref.secret_id,
            reason="Scheduled decommission",
        )
    )

    with pytest.raises(SecretRevokedError) as revoked_exc:
        service.resolve_secret_reference(new_gen_req)
    assert revoked_exc.value.error_code == "SECRET_REVOKED"

    # 6. Verify stored secret bytes were zeroized
    stored = service._secrets[(workspace_id, ref.secret_id)]
    assert len(stored.secret_bytes) == 0
