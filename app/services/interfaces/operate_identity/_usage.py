"""Usage demonstration for the account identity gateway."""

from __future__ import annotations

import asyncio
from typing import override
from uuid import uuid7

from app.composition.logging import get_logger
from app.contracts.interfaces.models import (
    OperateIdentityRequest,
    OperateIdentitySuccess,
)
from app.contracts.workspace.manage_accounts import ManageAccountsCapability
from app.contracts.workspace.models import (
    AccountRecord,
    ManageAccountsRequest,
    ManageAccountsSuccess,
)
from app.services.interfaces.operate_identity.config import (
    OperateIdentityConfig,
)
from app.services.interfaces.operate_identity.gateway import IdentityGateway

logger = get_logger("app.services.interfaces.operate_identity._usage")


class _MockAccountsProvider(ManageAccountsCapability):
    """Stub workspace provider for the standalone usage demonstration."""

    def __init__(self) -> None:
        self._sessions: dict[str, str] = {}

    @override
    async def manage_accounts(
        self, request: ManageAccountsRequest
    ) -> ManageAccountsSuccess:
        if request.operation in ("REGISTER", "LOGIN"):
            username = request.username or "demo_user"
            token = f"token_{username}"
            self._sessions[token] = username
            user = AccountRecord(
                user_id=f"usr_{username}",
                username=username,
                account_id=request.account_id,
                workspace_id=request.workspace_id,
                authentication_audit_ref="auth_demo_reference",
                expires_at="2026-09-11T00:00:00.000000Z",
                runtime_profile=request.runtime_profile,
            )
            return ManageAccountsSuccess(
                request_id=request.request_id,
                user=user,
                session_token=token,
                csrf_token="demo_csrf_token",  # noqa: S106
            )
        if request.operation == "ME":
            username = self._sessions.get(request.session_token or "", "unknown")
            user = AccountRecord(
                user_id=f"usr_{username}",
                username=username,
                account_id=request.account_id,
                workspace_id=request.workspace_id,
                authentication_audit_ref="auth_demo_reference",
                expires_at="2026-09-11T00:00:00.000000Z",
                runtime_profile=request.runtime_profile,
            )
            return ManageAccountsSuccess(
                request_id=request.request_id,
                user=user,
            )
        # LOGOUT
        self._sessions.pop(request.session_token or "", None)
        return ManageAccountsSuccess(
            request_id=request.request_id,
            revoked=True,
        )


async def _run_auth_scenarios(gateway: IdentityGateway) -> str:
    """Run register and login scenarios, returning the active session token.

    Returns:
        The active session token issued by login.

    Raises:
        TypeError: If an operation result has an unexpected type.
        RuntimeError: If an expected user or session is missing.
    """
    # Scenario 1: Register account with fallback to default_principal
    req_reg = OperateIdentityRequest(
        request_id=str(uuid7()),
        capability_snapshot_id=str(uuid7()),
        operation="REGISTER",
        username="",  # triggers fallback to default_principal ("trader")
        password="demo_password",  # noqa: S106  # pragma: allowlist secret
    )
    res_reg = await gateway.operate_identity(req_reg)
    if not isinstance(res_reg, OperateIdentitySuccess):
        message = "Scenario 1 failed: expected OperateIdentitySuccess"
        raise TypeError(message)
    if res_reg.user is None:
        message = "Scenario 1 failed: user was None"
        raise RuntimeError(message)
    print(f"Scenario 1 (REGISTER): {res_reg.outcome} - User: {res_reg.user.username}")
    logger.info(
        "Scenario 1 complete",
        outcome=res_reg.outcome,
        user=res_reg.user.username,
    )

    # Scenario 2: Login to acquire session token and CSRF token
    req_login = OperateIdentityRequest(
        request_id=str(uuid7()),
        capability_snapshot_id=str(uuid7()),
        operation="LOGIN",
        username="alice",
        password="alice_password",  # noqa: S106  # pragma: allowlist secret
    )
    res_login = await gateway.operate_identity(req_login)
    if not isinstance(res_login, OperateIdentitySuccess):
        message = "Scenario 2 failed: expected OperateIdentitySuccess"
        raise TypeError(message)
    session_token = res_login.session_token
    print(f"Scenario 2 (LOGIN): {res_login.outcome} - Session issued")
    logger.info("Scenario 2 complete", outcome=res_login.outcome)
    return session_token


async def _run_session_scenarios(
    gateway: IdentityGateway,
    session_token: str,
) -> None:
    """Run ME, LOGOUT, and disposal scenarios.

    Raises:
        TypeError: If an operation result has an unexpected type.
        RuntimeError: If an expected assertion fails.
    """
    # Scenario 3: Verify identity (ME) - browser-supplied principal ignored
    req_me = OperateIdentityRequest(
        request_id=str(uuid7()),
        capability_snapshot_id=str(uuid7()),
        operation="ME",
        username="attacker_spoofed_principal",  # should be ignored
        session_token=session_token,
    )
    res_me = await gateway.operate_identity(req_me)
    if not isinstance(res_me, OperateIdentitySuccess):
        message = "Scenario 3 failed: expected OperateIdentitySuccess"
        raise TypeError(message)
    if res_me.user is None or res_me.user.username != "alice":
        message = "Scenario 3 failed: principal spoofing was not prevented"
        raise RuntimeError(message)
    print(
        f"Scenario 3 (ME): {res_me.outcome} - Verified Principal: "
        f"{res_me.user.username}"
    )
    logger.info("Scenario 3 complete", principal=res_me.user.username)

    # Scenario 4: Logout / Revocation
    req_logout = OperateIdentityRequest(
        request_id=str(uuid7()),
        capability_snapshot_id=str(uuid7()),
        operation="LOGOUT",
        session_token=session_token,
    )
    res_logout = await gateway.operate_identity(req_logout)
    if not isinstance(res_logout, OperateIdentitySuccess):
        message = "Scenario 4 failed: expected OperateIdentitySuccess"
        raise TypeError(message)
    if not res_logout.revoked:
        message = "Scenario 4 failed: revoked was False"
        raise RuntimeError(message)
    print(f"Scenario 4 (LOGOUT): {res_logout.outcome} - Revoked: {res_logout.revoked}")
    logger.info("Scenario 4 complete", revoked=res_logout.revoked)

    # Scenario 5: Gateway disposal fail-closed
    gateway.close()
    res_closed = await gateway.operate_identity(req_me)
    if res_closed.outcome == "SUCCESS":
        message = "Scenario 5 failed: gateway allowed call after close"
        raise RuntimeError(message)
    status_code = getattr(res_closed, "code", "FAIL")
    print(f"Scenario 5 (DISPOSAL): Denied with code {status_code}")
    logger.info("Scenario 5 complete")


async def main() -> None:
    """Run the identity gateway usage scenario."""
    logger.info("Starting identity gateway usage demonstration")
    provider = _MockAccountsProvider()
    gateway = IdentityGateway(provider, OperateIdentityConfig())
    session_token = await _run_auth_scenarios(gateway)
    await _run_session_scenarios(gateway, session_token)
    logger.info("All identity gateway usage scenarios succeeded")


if __name__ == "__main__":
    asyncio.run(main())
