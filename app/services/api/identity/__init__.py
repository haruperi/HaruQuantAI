"""UI/API identity, session, credential, and governance operations."""

from app.services.api.identity.accounts import (
    AuthenticatedUser,
    authenticate_user,
    register_user,
)
from app.services.api.identity.approvals import (
    ApprovalRecord,
    consume_approval,
    create_approval,
)
from app.services.api.identity.authorization import (
    build_auth_context,
    require_auth_context,
    require_human_permission,
    require_permission,
    validate_governed_request,
)
from app.services.api.identity.credentials import (
    CredentialRecord,
    get_system_credential_statuses,
    resolve_credential_reference,
    store_credential,
    store_system_credential,
)
from app.services.api.identity.errors import IdentityError
from app.services.api.identity.idempotency import (
    IdempotencyDecision,
    finalize_idempotency_key,
    reserve_idempotency_key,
    run_idempotent_write,
    run_idempotent_write_async,
)
from app.services.api.identity.passwords import hash_password, verify_password
from app.services.api.identity.sessions import (
    SessionCredential,
    SessionIdentity,
    create_session,
    recover_session_identity,
    revoke_session,
    validate_csrf,
    validate_session,
)
from app.services.api.identity.settings import (
    SettingsRecord,
    get_system_settings,
    get_user_settings,
    update_system_settings,
    update_user_settings,
)
from app.services.api.identity.system_settings import (
    get_credential_manifest,
    get_legacy_settings_classification,
    get_system_settings_manifest,
    validate_credential_material,
    validate_system_settings,
)

__all__ = (
    "ApprovalRecord",
    "AuthenticatedUser",
    "CredentialRecord",
    "IdempotencyDecision",
    "IdentityError",
    "SessionCredential",
    "SessionIdentity",
    "SettingsRecord",
    "authenticate_user",
    "build_auth_context",
    "consume_approval",
    "create_approval",
    "create_session",
    "finalize_idempotency_key",
    "get_credential_manifest",
    "get_legacy_settings_classification",
    "get_legacy_settings_classification",
    "get_system_credential_statuses",
    "get_system_settings",
    "get_system_settings_manifest",
    "get_user_settings",
    "hash_password",
    "recover_session_identity",
    "register_user",
    "require_auth_context",
    "require_human_permission",
    "require_permission",
    "reserve_idempotency_key",
    "resolve_credential_reference",
    "revoke_session",
    "run_idempotent_write",
    "run_idempotent_write_async",
    "store_credential",
    "store_system_credential",
    "update_system_settings",
    "update_user_settings",
    "validate_credential_material",
    "validate_csrf",
    "validate_governed_request",
    "validate_session",
    "validate_system_settings",
    "verify_password",
)
