"""Usage demonstration for the system settings gateway."""

from __future__ import annotations

import asyncio
from typing import override
from uuid import uuid7

from app.contracts.interfaces.models import OperateSettingsRequest
from app.contracts.workspace.models import (
    AdministerSettingsRequest,
    AdministerSettingsSuccess,
    SystemSettingsRecord,
)
from app.contracts.workspace.ports import AdministerSettingsCapability
from app.services.interfaces.operate_settings.config import (
    OperateSettingsConfig,
)
from app.services.interfaces.operate_settings.gateway import SettingsGateway


class _MockSettingsProvider(AdministerSettingsCapability):
    """Stub workspace provider for the standalone usage demonstration."""

    @override
    async def administer_settings(
        self, request: AdministerSettingsRequest
    ) -> AdministerSettingsSuccess:
        system = SystemSettingsRecord(
            settings={"SYSTEM_NAME": "HaruQuantAI"},
            version=1,
            updated_at="2026-09-04T00:00:00Z",
        )
        return AdministerSettingsSuccess(
            request_id=request.request_id,
            system=system,
        )


async def main() -> None:
    """Run the settings gateway usage scenario."""
    provider = _MockSettingsProvider()
    gateway = SettingsGateway(provider, OperateSettingsConfig())
    req = OperateSettingsRequest(
        request_id=str(uuid7()),
        capability_snapshot_id=str(uuid7()),
        operation="READ_SYSTEM",
    )
    res = await gateway.administer_settings(req)
    print(f"Outcome: {res.outcome}")
    gateway.close()


if __name__ == "__main__":
    asyncio.run(main())
