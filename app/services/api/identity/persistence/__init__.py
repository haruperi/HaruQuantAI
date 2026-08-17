"""Private Identity-owned CRUD persistence boundary."""

# ruff: noqa: E402


class IdentityError(RuntimeError):
    """Bounded API identity-store failure shared with identity callers."""


from app.services.api.identity.persistence.create import (
    create_account_record,
    create_approval_record,
    create_idempotency_record,
    create_settings_record,
    replace_active_session_record,
)
from app.services.api.identity.persistence.delete import (
    delete_auth_failure_record,
    delete_idempotency_record,
)
from app.services.api.identity.persistence.read import (
    read_account_identity_by_user_id,
    read_account_record,
    read_approval_record,
    read_auth_failure_record,
    read_auth_lock_record,
    read_credential_record,
    read_csrf_record,
    read_idempotency_record,
    read_session_record,
    read_settings_record,
)
from app.services.api.identity.persistence.update import (
    consume_approval_record,
    finalize_idempotency_record,
    revoke_session_record,
    update_account_last_login,
    update_auth_failure_record,
    update_credential_record,
    update_settings_record,
)

__all__ = [
    "consume_approval_record",
    "create_account_record",
    "create_approval_record",
    "create_idempotency_record",
    "create_settings_record",
    "delete_auth_failure_record",
    "delete_idempotency_record",
    "finalize_idempotency_record",
    "read_account_identity_by_user_id",
    "read_account_record",
    "read_approval_record",
    "read_auth_failure_record",
    "read_auth_lock_record",
    "read_credential_record",
    "read_csrf_record",
    "read_idempotency_record",
    "read_session_record",
    "read_settings_record",
    "replace_active_session_record",
    "revoke_session_record",
    "update_account_last_login",
    "update_auth_failure_record",
    "update_credential_record",
    "update_settings_record",
]
