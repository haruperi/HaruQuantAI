"""Traceability acceptance tests for FEAT-IFACE-OPERATE_IDENTITY."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING
from uuid import uuid7

import pytest
from app.contracts.interfaces.errors import InterfaceFailure
from app.contracts.interfaces.models import (
    OperateIdentityRequest,
    OperateIdentitySuccess,
)
from app.services.interfaces.operate_identity.config import OperateIdentityConfig
from app.services.interfaces.operate_identity.gateway import IdentityGateway
from app.services.workspace.execute_persistence.execute_persistence import (
    ExecutePersistenceService,
)
from app.services.workspace.manage_accounts.accounts import AccountService
from app.services.workspace.manage_accounts.config import ManageAccountsConfig

if TYPE_CHECKING:
    from pathlib import Path


def _make_request(operation: str, **kwargs: object) -> OperateIdentityRequest:
    """Construct one typed operate-identity request."""
    return OperateIdentityRequest(
        request_id=str(uuid7()),
        capability_snapshot_id=str(uuid7()),
        operation=operation,  # type: ignore[arg-type]
        **kwargs,  # type: ignore[arg-type]
    )


@pytest.mark.asyncio
async def test_trc_operate_identity_001(tmp_path: Path) -> None:
    """AT-IFACE-OPERATE_IDENTITY-001: Forgery, expiry, revocation, and cross-account deny before mutation.

    Covers:
        FR-TRC-IFACE-OPERATE_IDENTITY-001
        AT-IFACE-OPERATE_IDENTITY-001
    """
    current_time = datetime(2026, 9, 8, 12, 0, 0, tzinfo=UTC)

    def mock_clock() -> datetime:
        return current_time

    store = AccountService(
        ExecutePersistenceService(),
        ManageAccountsConfig(database_path=tmp_path / "trc_001_db"),
        clock=mock_clock,
    )
    gateway = IdentityGateway(store, OperateIdentityConfig())

    # 1. Successful registration and login
    reg_req = _make_request(
        "REGISTER",
        username="carol",
        password="ValidPassword123",  # pragma: allowlist secret
    )
    reg_res = await gateway.operate_identity(reg_req)
    assert isinstance(reg_res, OperateIdentitySuccess)
    assert reg_res.user is not None
    assert reg_res.user.username == "carol"
    assert reg_res.session_token
    assert reg_res.csrf_token

    # Verify secret tokens are not leaked in string representation / serialization
    res_repr = repr(reg_res)
    assert reg_res.session_token not in res_repr
    assert reg_res.csrf_token not in res_repr

    login_req = _make_request(
        "LOGIN",
        username="carol",
        password="ValidPassword123",  # pragma: allowlist secret
    )
    login_res = await gateway.operate_identity(login_req)
    assert isinstance(login_res, OperateIdentitySuccess)
    session_token = login_res.session_token
    assert session_token

    # 2. Forged session token is denied
    forged_req = _make_request("ME", session_token="forged_token_material_xyz")
    forged_res = await gateway.operate_identity(forged_req)
    assert isinstance(forged_res, InterfaceFailure)
    assert forged_res.problem.status in (401, 403, 400)
    assert "forged_token_material_xyz" not in str(forged_res.problem.detail)

    # 3. Cross-account access denied (wrong workspace_id / account_id)
    cross_req = _make_request(
        "ME",
        session_token=session_token,
        workspace_id="other_workspace",
    )
    cross_res = await gateway.operate_identity(cross_req)
    assert isinstance(cross_res, InterfaceFailure)

    # 4. Session revocation (LOGOUT then ME)
    logout_req = _make_request("LOGOUT", session_token=session_token)
    logout_res = await gateway.operate_identity(logout_req)
    assert isinstance(logout_res, OperateIdentitySuccess)
    assert logout_res.revoked is True

    # After revocation, ME must fail
    me_after_logout = _make_request("ME", session_token=session_token)
    res_after_logout = await gateway.operate_identity(me_after_logout)
    assert isinstance(res_after_logout, InterfaceFailure)

    # 5. Expired session token
    # Advance mock clock by 35 days (exceeding default 30-day session TTL)
    current_time += timedelta(days=35)
    expired_req = _make_request("ME", session_token=reg_res.session_token)
    expired_res = await gateway.operate_identity(expired_req)
    assert isinstance(expired_res, InterfaceFailure)


@pytest.mark.asyncio
async def test_trc_operate_identity_002(tmp_path: Path) -> None:
    """AT-IFACE-OPERATE_IDENTITY-002: Browser-supplied principal cannot replace verified session principal.

    Covers:
        FR-TRC-IFACE-OPERATE_IDENTITY-002
        AT-IFACE-OPERATE_IDENTITY-002
    """
    store = AccountService(
        ExecutePersistenceService(),
        ManageAccountsConfig(database_path=tmp_path / "trc_002_db"),
    )
    gateway = IdentityGateway(
        store, OperateIdentityConfig(default_principal="trader_default")
    )

    # Register legitimate user "alice"
    alice_reg = await gateway.operate_identity(
        _make_request(
            "REGISTER",
            username="alice",
            password="AlicePassword123",  # pragma: allowlist secret
        )
    )
    assert isinstance(alice_reg, OperateIdentitySuccess)
    alice_token = alice_reg.session_token

    # Register another user "bob"
    bob_reg = await gateway.operate_identity(
        _make_request(
            "REGISTER",
            username="bob",
            password="BobPassword123",  # pragma: allowlist secret
        )
    )
    assert isinstance(bob_reg, OperateIdentitySuccess)

    # Attacker supplies Alice's valid session token but specifies username="bob" in ME request
    spoof_me_req = _make_request(
        "ME",
        session_token=alice_token,
        username="bob",
    )
    spoof_me_res = await gateway.operate_identity(spoof_me_req)
    assert isinstance(spoof_me_res, OperateIdentitySuccess)
    assert spoof_me_res.user is not None
    # Verified principal MUST remain alice, NOT the browser-supplied "bob"
    assert spoof_me_res.user.username == "alice"
    assert spoof_me_res.user.username != "bob"

    # Verify fallback to default_principal when username is unspecified for REGISTER
    default_reg = await gateway.operate_identity(
        _make_request(
            "REGISTER",
            username=None,
            password="DefaultPassword123",  # pragma: allowlist secret
        )
    )
    assert isinstance(default_reg, OperateIdentitySuccess)
    assert default_reg.user is not None
    assert default_reg.user.username == "trader_default"
