"""Usage demonstration for the account identity gateway."""

from __future__ import annotations

import asyncio
from typing import override
from uuid import uuid7

from app.contracts.interfaces.models import OperateIdentityRequest
from app.contracts.workspace.models import (
    AccountRecord,
    ManageAccountsRequest,
    ManageAccountsSuccess,
)
from app.contracts.workspace.ports import ManageAccountsCapability
from app.services.interfaces.operate_identity.config import (
    OperateIdentityConfig,
)
from app.services.interfaces.operate_identity.gateway import IdentityGateway


class _MockAccountsProvider(ManageAccountsCapability):
    """Stub workspace provider for the standalone usage demonstration."""

    @override
    async def manage_accounts(
        self, request: ManageAccountsRequest
    ) -> ManageAccountsSuccess:
        user = AccountRecord(
            user_id="usr_demo_1",
            username=request.username or "demo_user",
            expires_at="2026-09-11T00:00:00Z",
            runtime_profile=request.runtime_profile,
        )
        return ManageAccountsSuccess(
            request_id=request.request_id,
            user=user,
            session_token="demo_session_token",  # noqa: S106
            csrf_token="demo_csrf_token",  # noqa: S106
        )


async def main() -> None:
    """Run the identity gateway usage scenario."""
    provider = _MockAccountsProvider()
    gateway = IdentityGateway(provider, OperateIdentityConfig())
    req = OperateIdentityRequest(
        request_id=str(uuid7()),
        capability_snapshot_id=str(uuid7()),
        operation="REGISTER",
        username="trader",
        password="demo_password",  # noqa: S106  # pragma: allowlist secret
    )
    res = await gateway.operate_identity(req)
    print(f"Outcome: {res.outcome}")
    gateway.close()


if __name__ == "__main__":
    asyncio.run(main())
