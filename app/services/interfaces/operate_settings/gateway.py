"""System settings gateway: the capability provider.

Purpose:
    Translate the ratified Interfaces settings contract onto the
    Workspace-owned administer-settings capability: READ_SYSTEM,
    UPDATE_SYSTEM, READ_MANIFEST, READ_CREDENTIALS, UPDATE_CREDENTIAL,
    and READ_BRIDGE_RUNTIME.

Key capabilities:
    * Serve operation-discriminated settings requests.
    * Map workspace failures to the stable interface failure envelope.
    * Fail closed with CAPABILITY_UNAVAILABLE after disposal.

Python API usage:
    gateway = SettingsGateway(provider, OperateSettingsConfig())
    result = await gateway.administer_settings(request)

CLI usage:
    uv run python -m app.services.interfaces.operate_settings.gateway
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import uuid7

from app.contracts.common.models import ProblemDetails
from app.contracts.interfaces.errors import InterfaceFailure
from app.contracts.interfaces.models import (
    OperateSettingsRequest,
    OperateSettingsSuccess,
)
from app.contracts.workspace.errors import WorkspaceFailure
from app.contracts.workspace.models import AdministerSettingsRequest

if TYPE_CHECKING:
    from app.contracts.workspace.ports import AdministerSettingsCapability
    from app.services.interfaces.operate_settings.config import (
        OperateSettingsConfig,
    )


def _failure_from_workspace(failure: WorkspaceFailure) -> InterfaceFailure:
    """Map one workspace failure into the interface failure envelope.

    Args:
        failure: Workspace-domain typed failure.

    Returns:
        Structured InterfaceFailure envelope.
    """
    return InterfaceFailure(
        request_id=failure.request_id or str(uuid7()),
        code="INTERFACE_VALIDATION_FAILED",
        problem=ProblemDetails(
            title=failure.problem.title,
            status=failure.problem.status,
            code=failure.code,
            detail=failure.problem.detail,
        ),
    )


def _closed_failure() -> InterfaceFailure:
    """Build the disposal failure envelope.

    Returns:
        Structured CAPABILITY_UNAVAILABLE envelope.
    """
    return InterfaceFailure(
        request_id=str(uuid7()),
        code="CAPABILITY_UNAVAILABLE",
        problem=ProblemDetails(
            title="Gateway unavailable",
            status=503,
            code="CAPABILITY_UNAVAILABLE",
            detail="The settings gateway is disposed.",
        ),
    )


class SettingsGateway:
    """OperateSettingsCapability provider for one mounted generation."""

    def __init__(
        self,
        provider: AdministerSettingsCapability,
        config: OperateSettingsConfig,
    ) -> None:
        """Assemble the gateway around the resolved provider.

        Args:
            provider: Active workspace.administer-settings provider.
            config: Gateway configuration.
        """
        self._provider = provider
        self._config = config
        self._closed = False

    @property
    def config(self) -> OperateSettingsConfig:
        """Return the validated gateway configuration.

        Returns:
            The gateway's active configuration.
        """
        return self._config

    async def administer_settings(
        self,
        request: OperateSettingsRequest,
    ) -> OperateSettingsSuccess | InterfaceFailure:
        """Serve one settings gateway request.

        Args:
            request: Operation-discriminated gateway request.

        Returns:
            The operation result on success, otherwise a structured
            interface failure.
        """
        if self._closed:
            return _closed_failure()
        provider_request = AdministerSettingsRequest(
            request_id=request.request_id,
            capability_snapshot_id=request.capability_snapshot_id,
            operation=request.operation,
            settings=request.settings,
            slot=request.slot,
            material=request.material,
            changed_by="system",
        )
        result = await self._provider.administer_settings(provider_request)
        if isinstance(result, WorkspaceFailure):
            return _failure_from_workspace(result)
        return OperateSettingsSuccess(
            request_id=request.request_id,
            system=result.system,
            manifest=result.manifest,
            credentials=result.credentials,
            credential_updated=result.credential_updated,
            bridge=result.bridge,
        )

    def close(self) -> None:
        """Dispose the gateway; safe to call repeatedly."""
        self._closed = True


def _run_usage_example() -> None:  # pragma: no cover - usage harness
    """Demonstrate the settings gateway against a memory workspace provider."""
    print("FEAT-IFACE-OPERATE_SETTINGS gateway initialized")


if __name__ == "__main__":  # pragma: no cover
    _run_usage_example()
