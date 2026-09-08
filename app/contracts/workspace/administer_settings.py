"""Public contract for system settings administration, revisions, and manifests.

Behind the ``workspace.administer-settings@1`` capability, this contract owns
the workstation's setting-definition manifest, versioned system settings
persistence under legacy wire keys, write-only credential slots, and the
MT5 snapshot bridge runtime projection.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

from app.contracts.workspace.errors import WorkspaceError
from app.contracts.workspace.models import (
    AdministerSettingsRequest,
    AdministerSettingsSuccess,
    BridgeRuntimeSettings,
    CredentialSlotStatus,
    SettingDefinition,
    SystemSettingsRecord,
)

if TYPE_CHECKING:
    from app.contracts.workspace.errors import WorkspaceFailure


class SettingsConflictError(WorkspaceError):
    """Raised when an update conflicts with the current revision."""

    def __init__(
        self,
        message: str = (
            "Settings update conflict: expected revision does not match "
            "current revision"
        ),
        expected_revision: int | None = None,
        current_revision: int | None = None,
    ) -> None:
        """Initialize settings conflict error.

        Args:
            message: Error description.
            expected_revision: Expected revision specified in request.
            current_revision: Current revision in the store.
        """
        self.expected_revision = expected_revision
        self.current_revision = current_revision
        details = []
        if expected_revision is not None:
            details.append(f"expected={expected_revision}")
        if current_revision is not None:
            details.append(f"current={current_revision}")
        suffix = f" ({', '.join(details)})" if details else ""
        super().__init__(f"{message}{suffix}", error_code="SETTINGS_CONFLICT")


class SettingsValidationError(WorkspaceError):
    """Raised when setting keys, values, or combinations violate validation rules."""

    def __init__(
        self,
        message: str = "Settings validation failed",
        key: str | None = None,
        value: str | None = None,
    ) -> None:
        """Initialize settings validation error.

        Args:
            message: Error description.
            key: Setting key that failed validation.
            value: Value that failed validation.
        """
        self.key = key
        self.value = value
        details = []
        if key is not None:
            details.append(f"key={key}")
        if value is not None:
            details.append(f"value={value}")
        suffix = f" ({', '.join(details)})" if details else ""
        super().__init__(f"{message}{suffix}", error_code="SETTINGS_VALIDATION_FAILED")


@runtime_checkable
class AdministerSettingsCapability(Protocol):
    """Capability protocol for system settings administration."""

    async def administer_settings(
        self, request: AdministerSettingsRequest
    ) -> AdministerSettingsSuccess | WorkspaceFailure:
        """Serve one operation-discriminated settings request.

        Args:
            request: Settings read/update/manifest/credentials/bridge request.

        Returns:
            Settings operation success, or a structured workspace failure.
        """
        ...


__all__ = [
    "AdministerSettingsCapability",
    "AdministerSettingsRequest",
    "AdministerSettingsSuccess",
    "BridgeRuntimeSettings",
    "CredentialSlotStatus",
    "SettingDefinition",
    "SettingsConflictError",
    "SettingsValidationError",
    "SystemSettingsRecord",
]
