"""Update operations for API-owned database records."""

from __future__ import annotations

from typing import Protocol, cast

from app.services.api.persistence import IdentityError
from app.services.data import (
    build_statement_plan,
    build_transaction_request,
    execute_transaction,
)
from app.utils import get_logger

logger = get_logger(__name__)


class _TransactionResult(Protocol):
    """Fields consumed from Data's normalized transaction result."""

    affected_rows: int


def _execute_update(
    statement: str,
    parameters: tuple[object, ...],
    *,
    request_id: str,
) -> int:
    """Execute one bounded API update through Data.

    Args:
        statement: Parameterized update statement.
        parameters: Bound statement parameters.
        request_id: Canonical operation request identifier.

    Returns:
        Number of affected rows.

    Raises:
        IdentityError: If Data cannot confirm the transaction.
    """
    response = execute_transaction(
        build_transaction_request(
            plan=build_statement_plan(
                statements=(statement,),
                parameter_sets=(parameters,),
                max_rows=1,
            ),
            request_id=request_id,
        )
    )
    if response.status != "success" or response.data is None:
        raise IdentityError("IDENTITY_STORE_UNAVAILABLE")
    result = cast("_TransactionResult", response.data)
    return int(result.affected_rows)


def update_auth_failure_record(
    *,
    username_hash: str,
    failure_count: int,
    window_started_at: str,
    locked_until: str | None,
    request_id: str,
) -> None:
    """Upsert one authentication-failure window.

    Args:
        username_hash: Non-reversible normalized username digest.
        failure_count: Failures observed within the current window.
        window_started_at: ISO-formatted window start.
        locked_until: Optional ISO-formatted lock expiry.
        request_id: Canonical operation request identifier.

    Raises:
        IdentityError: If Data cannot confirm the transaction.
    """
    logger.debug("Updating API authentication failure persistence record")
    _execute_update(
        "INSERT INTO api_auth_failures "
        "(username_hash, failure_count, window_started_at, locked_until) "
        "VALUES (?, ?, ?, ?) ON CONFLICT(username_hash) DO UPDATE SET "
        "failure_count=excluded.failure_count, "
        "window_started_at=excluded.window_started_at, "
        "locked_until=excluded.locked_until",
        (username_hash, failure_count, window_started_at, locked_until),
        request_id=request_id,
    )


def update_account_last_login(
    *, user_id: str, last_login_at: str, request_id: str
) -> None:
    """Update one account's last-login evidence.

    Args:
        user_id: Stable account identifier.
        last_login_at: ISO-formatted successful-login instant.
        request_id: Canonical operation request identifier.

    Raises:
        IdentityError: If Data cannot confirm the transaction.
    """
    logger.debug("Updating API account last-login persistence evidence")
    _execute_update(
        "UPDATE api_accounts SET last_login_at = ? WHERE user_id = ?",
        (last_login_at, user_id),
        request_id=request_id,
    )


def revoke_session_record(
    *, session_digest: str, revoked_at: str, request_id: str
) -> None:
    """Idempotently revoke one API session record.

    Args:
        session_digest: One-way opaque-session digest.
        revoked_at: ISO-formatted revocation instant.
        request_id: Canonical operation request identifier.

    Raises:
        IdentityError: If Data cannot confirm the transaction.
    """
    logger.debug("Updating API session revocation persistence state")
    _execute_update(
        "UPDATE api_sessions SET revoked_at = COALESCE(revoked_at, ?) "
        "WHERE session_digest = ?",
        (revoked_at, session_digest),
        request_id=request_id,
    )


def update_credential_record(
    *,
    reference: str,
    owner_id: str,
    key_id: str,
    nonce_b64: str,
    ciphertext_b64: str,
    created_at: str,
    request_id: str,
) -> None:
    """Upsert one encrypted credential persistence record.

    Args:
        reference: Stable opaque credential reference.
        owner_id: Authorized credential owner.
        key_id: External encryption-key identifier.
        nonce_b64: Encoded authenticated-encryption nonce.
        ciphertext_b64: Encoded authenticated ciphertext.
        created_at: ISO-formatted persistence instant.
        request_id: Canonical operation request identifier.

    Raises:
        IdentityError: If Data cannot confirm the transaction.
    """
    logger.debug("Updating API encrypted credential persistence record")
    _execute_update(
        "INSERT INTO api_credentials "
        "(reference, owner_id, key_id, nonce_b64, ciphertext_b64, "
        "created_at, version) VALUES (?, ?, ?, ?, ?, ?, 1) "
        "ON CONFLICT(reference) DO UPDATE SET key_id=excluded.key_id, "
        "nonce_b64=excluded.nonce_b64, ciphertext_b64=excluded.ciphertext_b64, "
        "created_at=excluded.created_at, version=excluded.version",
        (
            reference,
            owner_id,
            key_id,
            nonce_b64,
            ciphertext_b64,
            created_at,
        ),
        request_id=request_id,
    )


def consume_approval_record(
    *, approval_id: str, consumed_at: str, request_id: str
) -> int:
    """Consume one previously unused approval record.

    Args:
        approval_id: Stable approval identifier.
        consumed_at: ISO-formatted consumption instant.
        request_id: Canonical operation request identifier.

    Returns:
        Number of affected rows.

    Raises:
        IdentityError: If Data cannot confirm the transaction.
    """
    logger.debug("Updating API approval consumption persistence state")
    return _execute_update(
        "UPDATE api_approvals SET consumed_at = ? "
        "WHERE approval_id = ? AND consumed_at IS NULL",
        (consumed_at, approval_id),
        request_id=request_id,
    )


def finalize_idempotency_record(
    *,
    scope_key: str,
    response_json: str,
    status_code: int,
    request_id: str,
) -> int:
    """Finalize one pending HTTP idempotency reservation.

    Args:
        scope_key: Canonical request-scope digest.
        response_json: Bounded terminal response.
        status_code: Terminal HTTP status.
        request_id: Canonical operation request identifier.

    Returns:
        Number of affected rows.

    Raises:
        IdentityError: If Data cannot confirm the transaction.
    """
    logger.debug("Updating API idempotency persistence record")
    return _execute_update(
        "UPDATE api_idempotency SET response_json = ?, status_code = ? "
        "WHERE scope_key = ? AND response_json IS NULL",
        (response_json, status_code, scope_key),
        request_id=request_id,
    )


def _execute_update_many(
    statements: tuple[str, ...],
    parameter_sets: tuple[tuple[object, ...], ...],
    *,
    request_id: str,
) -> int:
    """Execute several bounded API update statements as one transaction.

    Args:
        statements: Parameterized update statements.
        parameter_sets: Bound parameters matching the statements.
        request_id: Canonical operation request identifier.

    Returns:
        Number of affected rows across every statement.

    Raises:
        IdentityError: If Data cannot confirm the transaction.
    """
    response = execute_transaction(
        build_transaction_request(
            plan=build_statement_plan(
                statements=statements,
                parameter_sets=parameter_sets,
                max_rows=1,
            ),
            request_id=request_id,
        )
    )
    if response.status != "success" or response.data is None:
        raise IdentityError("IDENTITY_STORE_UNAVAILABLE")
    result = cast("_TransactionResult", response.data)
    return int(result.affected_rows)


def rename_watchlist_record(
    *,
    watchlist_id: str,
    account_id: str,
    name: str,
    updated_at: str,
    request_id: str,
) -> int:
    """Rename one watchlist owned by the given account.

    Args:
        watchlist_id: Stable watchlist identifier.
        account_id: Owning account identifier, enforced in the WHERE clause.
        name: New display name, unique per account.
        updated_at: ISO-formatted update instant.
        request_id: Canonical operation request identifier.

    Returns:
        Number of affected rows; 0 if not found, not owned, or name conflicts.

    Raises:
        IdentityError: If Data cannot confirm the transaction.
    """
    logger.debug("Renaming API watchlist persistence record")
    return _execute_update(
        "UPDATE api_watchlists SET name = ?, updated_at = ? "
        "WHERE watchlist_id = ? AND account_id = ?",
        (name, updated_at, watchlist_id, account_id),
        request_id=request_id,
    )


def reorder_watchlists_record(
    *,
    account_id: str,
    watchlist_id: str,
    sort_order: int,
    updated_at: str,
    request_id: str,
) -> int:
    """Reposition one watchlist among the account's watchlist ordering.

    Args:
        account_id: Owning account identifier, enforced in the WHERE clause.
        watchlist_id: Stable watchlist identifier.
        sort_order: New display order.
        updated_at: ISO-formatted update instant.
        request_id: Canonical operation request identifier.

    Returns:
        Number of affected rows; 0 if not found or not owned.

    Raises:
        IdentityError: If Data cannot confirm the transaction.
    """
    logger.debug("Reordering API watchlist persistence record")
    return _execute_update(
        "UPDATE api_watchlists SET sort_order = ?, updated_at = ? "
        "WHERE watchlist_id = ? AND account_id = ?",
        (sort_order, updated_at, watchlist_id, account_id),
        request_id=request_id,
    )


def set_default_watchlist_record(
    *,
    account_id: str,
    watchlist_id: str,
    updated_at: str,
    request_id: str,
) -> int:
    """Atomically move the account's default flag to one watchlist.

    Clears any prior default before setting the new one so the partial
    unique index (`at most one default per account`) is satisfied at every
    intermediate statement, not only at commit.

    Args:
        account_id: Owning account identifier.
        watchlist_id: Watchlist to become the account's default.
        updated_at: ISO-formatted update instant.
        request_id: Canonical operation request identifier.

    Returns:
        Number of affected rows.

    Raises:
        IdentityError: If Data cannot confirm the transaction.
    """
    logger.debug("Updating API default-watchlist persistence assignment")
    return _execute_update_many(
        (
            "UPDATE api_watchlists SET is_default = 0, updated_at = ? "
            "WHERE account_id = ? AND is_default = 1 AND watchlist_id != ?",
            "UPDATE api_watchlists SET is_default = 1, updated_at = ? "
            "WHERE watchlist_id = ? AND account_id = ?",
        ),
        (
            (updated_at, account_id, watchlist_id),
            (updated_at, watchlist_id, account_id),
        ),
        request_id=request_id,
    )


def replace_watchlist_items_record(
    *,
    watchlist_id: str,
    account_id: str,
    items: tuple[tuple[str, str, int], ...],
    updated_at: str,
    request_id: str,
) -> int:
    """Atomically replace one watchlist's complete item list.

    Args:
        watchlist_id: Stable watchlist identifier.
        account_id: Owning account identifier, enforced in the WHERE clause.
        items: Ordered ``(source_id, symbol, sort_order)`` triples.
        updated_at: ISO-formatted update instant.
        request_id: Canonical operation request identifier.

    Returns:
        Number of affected rows across the delete, inserts, and touch.

    Raises:
        IdentityError: If Data cannot confirm the transaction.
    """
    logger.debug("Replacing API watchlist item persistence records")
    item_statement = (
        "INSERT INTO api_watchlist_items "
        "(watchlist_id, source_id, symbol, sort_order, created_at) "
        "SELECT ?, ?, ?, ?, ? WHERE EXISTS "
        "(SELECT 1 FROM api_watchlists WHERE watchlist_id = ? AND account_id = ?)"
    )
    statements: list[str] = [
        "DELETE FROM api_watchlist_items WHERE watchlist_id = ? AND EXISTS "
        "(SELECT 1 FROM api_watchlists WHERE watchlist_id = ? AND account_id = ?)",
        *(item_statement for _ in items),
        "UPDATE api_watchlists SET updated_at = ? "
        "WHERE watchlist_id = ? AND account_id = ?",
    ]
    parameter_sets: list[tuple[object, ...]] = [
        (watchlist_id, watchlist_id, account_id),
        *(
            (
                watchlist_id,
                source_id,
                symbol,
                sort_order,
                updated_at,
                watchlist_id,
                account_id,
            )
            for source_id, symbol, sort_order in items
        ),
        (updated_at, watchlist_id, account_id),
    ]
    return _execute_update_many(
        tuple(statements),
        tuple(parameter_sets),
        request_id=request_id,
    )


def update_settings_record(
    *,
    scope: str,
    subject_id: str,
    settings_json: str,
    version: int,
    updated_at: str,
    updated_by: str,
    expected_version: int,
    request_id: str,
) -> int:
    """Update one scoped settings record with optimistic locking.

    Args:
        scope: Settings authority scope, system or user.
        subject_id: Global or authenticated-user settings subject.
        settings_json: Canonical serialized settings.
        version: Replacement record version.
        updated_at: ISO-formatted update instant.
        updated_by: Authenticated actor responsible for the write.
        expected_version: Persisted version required by the caller.
        request_id: Canonical operation request identifier.

    Returns:
        Number of affected rows.

    Raises:
        IdentityError: If Data cannot confirm the transaction.
    """
    logger.debug("Updating API settings persistence record")
    return _execute_update(
        "UPDATE api_settings SET settings_json = ?, version = ?, updated_at = ?, "
        "updated_by = ?, request_id = ? WHERE scope = ? AND subject_id = ? "
        "AND version = ?",
        (
            settings_json,
            version,
            updated_at,
            updated_by,
            request_id,
            scope,
            subject_id,
            expected_version,
        ),
        request_id=request_id,
    )


__all__ = [
    "consume_approval_record",
    "finalize_idempotency_record",
    "rename_watchlist_record",
    "reorder_watchlists_record",
    "replace_watchlist_items_record",
    "revoke_session_record",
    "set_default_watchlist_record",
    "update_account_last_login",
    "update_auth_failure_record",
    "update_credential_record",
    "update_settings_record",
]
