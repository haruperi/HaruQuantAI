"""Private API-owned CRUD persistence boundary."""

# ruff: noqa: E402


class IdentityError(RuntimeError):
    """Bounded API identity-store failure shared with identity callers."""


from app.services.api.persistence.create import (
    create_account_record,
    create_approval_record,
    create_idempotency_record,
    create_settings_record,
    create_watchlist_items,
    create_watchlist_record,
    replace_active_session_record,
)
from app.services.api.persistence.delete import (
    delete_auth_failure_record,
    delete_idempotency_record,
    delete_watchlist_record,
)
from app.services.api.persistence.read import (
    read_account_record,
    read_approval_record,
    read_auth_failure_record,
    read_auth_lock_record,
    read_credential_record,
    read_csrf_record,
    read_idempotency_record,
    read_session_record,
    read_settings_record,
    read_watchlist_items,
    read_watchlist_items_for_account,
    read_watchlist_record,
    read_watchlists_for_account,
)
from app.services.api.persistence.update import (
    consume_approval_record,
    finalize_idempotency_record,
    rename_watchlist_record,
    reorder_watchlists_record,
    replace_watchlist_items_record,
    revoke_session_record,
    set_default_watchlist_record,
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
    "create_watchlist_items",
    "create_watchlist_record",
    "delete_auth_failure_record",
    "delete_idempotency_record",
    "delete_watchlist_record",
    "finalize_idempotency_record",
    "read_account_record",
    "read_approval_record",
    "read_auth_failure_record",
    "read_auth_lock_record",
    "read_credential_record",
    "read_csrf_record",
    "read_idempotency_record",
    "read_session_record",
    "read_settings_record",
    "read_watchlist_items",
    "read_watchlist_items_for_account",
    "read_watchlist_record",
    "read_watchlists_for_account",
    "rename_watchlist_record",
    "reorder_watchlists_record",
    "replace_active_session_record",
    "replace_watchlist_items_record",
    "revoke_session_record",
    "set_default_watchlist_record",
    "update_account_last_login",
    "update_auth_failure_record",
    "update_credential_record",
    "update_settings_record",
]
