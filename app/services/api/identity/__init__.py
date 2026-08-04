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
    resolve_credential_reference,
    store_credential,
)
from app.services.api.identity.errors import IdentityError
from app.services.api.identity.idempotency import (
    IdempotencyDecision,
    finalize_idempotency_key,
    reserve_idempotency_key,
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
from app.services.api.migrations import (
    get_api_migration_steps,
    run_api_migrations,
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
    "get_api_migration_steps",
    "get_system_settings",
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
    "run_api_migrations",
    "store_credential",
    "update_system_settings",
    "update_user_settings",
    "validate_csrf",
    "validate_governed_request",
    "validate_session",
    "verify_password",
)
