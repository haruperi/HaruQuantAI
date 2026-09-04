"""CRUD and lifecycle tests for the manage-accounts feature."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import uuid7

import pytest
from app.contracts.workspace.errors import WorkspaceFailure
from app.contracts.workspace.models import (
    ManageAccountsRequest,
    ManageAccountsSuccess,
)
from app.services.workspace.manage_accounts.accounts import (
    AccountService,
    hash_password,
    verify_password,
)
from app.services.workspace.manage_accounts.config import ManageAccountsConfig
from app.services.workspace.manage_accounts.manifest import SPEC

if TYPE_CHECKING:
    from pathlib import Path


def _request(operation: str, **kwargs: object) -> ManageAccountsRequest:
    """Build one operation request."""
    return ManageAccountsRequest(
        request_id=str(uuid7()),
        capability_snapshot_id=str(uuid7()),
        operation=operation,  # type: ignore[arg-type]
        **kwargs,  # type: ignore[arg-type]
    )


def test_manifest_spec() -> None:
    """Verify feature specification and declared durable state."""
    assert SPEC.feature_id == "FEAT-WS-MANAGE_ACCOUNTS"
    (provided,) = SPEC.provides
    assert provided.identifier == "workspace.manage-accounts@1"
    assert SPEC.state is not None
    assert SPEC.state.namespace == "workspace.manage_accounts"
    SPEC.validate()


def test_password_hashing_and_verification() -> None:
    """Verify standard scrypt hashing and verification."""
    raw = "MySecretPassword123!"  # pragma: allowlist secret
    hashed = hash_password(raw)
    assert hashed.startswith("scrypt$16384$8$1$")
    assert verify_password(raw, hashed) is True
    assert verify_password("wrong", hashed) is False  # pragma: allowlist secret
    assert verify_password("", hashed) is False
    assert verify_password(raw, "disabled") is False
    assert verify_password(raw, "invalid_hash_format") is False

    with pytest.raises(ValueError, match="Password must not be empty"):
        hash_password("")


@pytest.mark.asyncio
async def test_register_and_login_flow(tmp_path: Path) -> None:
    """Verify registering a user, creating session, and logging in."""
    db_file = tmp_path / "test_accounts.db"
    service = AccountService(ManageAccountsConfig(database_path=db_file))

    reg_req = _request(
        "REGISTER",
        username="alice_quant",
        password="P@ssword123",  # pragma: allowlist secret
        runtime_profile="simulation",
    )
    reg_result = await service.manage_accounts(reg_req)
    assert isinstance(reg_result, ManageAccountsSuccess)
    assert reg_result.user is not None
    assert reg_result.user.username == "alice_quant"
    assert reg_result.user.runtime_profile == "simulation"
    sess_tok = reg_result.session_token
    csrf_tok = reg_result.csrf_token
    assert len(sess_tok) > 20
    assert len(csrf_tok) > 20

    # Test identity recovery via ME
    me_req = _request("ME", session_token=sess_tok)
    me_result = await service.manage_accounts(me_req)
    assert isinstance(me_result, ManageAccountsSuccess)
    assert me_result.user is not None
    assert me_result.user.username == "alice_quant"
    assert me_result.user.runtime_profile == "simulation"

    # Duplicate registration fails
    dup_result = await service.manage_accounts(
        _request(
            "REGISTER",
            username="ALICE_QUANT",
            password="P@ssword123",  # pragma: allowlist secret
        )
    )
    assert isinstance(dup_result, WorkspaceFailure)
    assert dup_result.code == "ACCOUNT_REGISTRATION_FAILED"

    # Login succeeds
    login_req = _request(
        "LOGIN",
        username="alice_quant",
        password="P@ssword123",  # pragma: allowlist secret
    )
    login_result = await service.manage_accounts(login_req)
    assert isinstance(login_result, ManageAccountsSuccess)
    assert login_result.user is not None
    assert login_result.user.username == "alice_quant"
    assert login_result.session_token != sess_tok

    # Bad login fails
    bad_login = await service.manage_accounts(
        _request(
            "LOGIN",
            username="alice_quant",
            password="WrongPassword",  # pragma: allowlist secret
        )
    )
    assert isinstance(bad_login, WorkspaceFailure)
    assert bad_login.code == "ACCOUNT_AUTHENTICATION_FAILED"

    service.close()


@pytest.mark.asyncio
async def test_registration_validation(tmp_path: Path) -> None:
    """Verify username and password validation constraints."""
    db_file = tmp_path / "test_accounts.db"
    service = AccountService(ManageAccountsConfig(database_path=db_file))

    short_user = await service.manage_accounts(
        _request(
            "REGISTER",
            username="a",
            password="ValidPassword123",  # pragma: allowlist secret
        )
    )
    assert isinstance(short_user, WorkspaceFailure)
    assert short_user.code == "ACCOUNT_REGISTRATION_FAILED"

    bad_user = await service.manage_accounts(
        _request(
            "REGISTER",
            username="bad username with spaces",
            password="ValidPassword123",  # pragma: allowlist secret
        )
    )
    assert isinstance(bad_user, WorkspaceFailure)
    assert bad_user.code == "ACCOUNT_REGISTRATION_FAILED"

    short_pass = await service.manage_accounts(
        _request(
            "REGISTER", username="valid_user", password="123"
        )  # pragma: allowlist secret
    )
    assert isinstance(short_pass, WorkspaceFailure)
    assert short_pass.code == "ACCOUNT_REGISTRATION_FAILED"

    service.close()


@pytest.mark.asyncio
async def test_session_revocation(tmp_path: Path) -> None:
    """Verify session revocation via LOGOUT."""
    db_file = tmp_path / "test_accounts.db"
    service = AccountService(ManageAccountsConfig(database_path=db_file))

    reg_result = await service.manage_accounts(
        _request(
            "REGISTER",
            username="bob_trader",
            password="SecurePassword123",  # pragma: allowlist secret
        )
    )
    assert isinstance(reg_result, ManageAccountsSuccess)
    sess_tok = reg_result.session_token

    # Verify session is valid
    me_result = await service.manage_accounts(_request("ME", session_token=sess_tok))
    assert isinstance(me_result, ManageAccountsSuccess)

    # Revoke session
    logout_result = await service.manage_accounts(
        _request("LOGOUT", session_token=sess_tok)
    )
    assert isinstance(logout_result, ManageAccountsSuccess)
    assert logout_result.revoked is True

    # Now ME fails
    me_after = await service.manage_accounts(_request("ME", session_token=sess_tok))
    assert isinstance(me_after, WorkspaceFailure)
    assert me_after.code == "ACCOUNT_AUTHENTICATION_FAILED"

    # Nonexistent token
    fake_me = await service.manage_accounts(
        _request("ME", session_token="nonexistent_token")
    )
    assert isinstance(fake_me, WorkspaceFailure)
    assert fake_me.code == "ACCOUNT_AUTHENTICATION_FAILED"

    service.close()
