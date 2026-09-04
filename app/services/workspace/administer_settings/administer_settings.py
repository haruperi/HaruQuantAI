"""System settings administration service.

Purpose:
    Own the workstation's administrator settings surface behind the
    ``workspace.administer-settings@1`` capability: the authoritative
    setting-definition manifest, versioned system settings persistence
    under legacy wire keys, write-only credential slots, and the MT5
    snapshot bridge runtime projection.

Key capabilities:
    * Project the manifest and the legacy-keyed system settings document.
    * Apply governed settings updates with audit history.
    * Report credential-slot status and store credential material
      write-only.
    * Resolve the TickBridge EA runtime settings for the composition root.

Python API usage:
    service = SettingsService(AdministerSettingsConfig())
    result = await service.administer_settings(request)

CLI usage:
    uv run python -m app.services.workspace.administer_settings.administer_settings
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Final, Literal, cast
from uuid import uuid7

from app.contracts.workspace.errors import WorkspaceFailure
from app.contracts.workspace.models import (
    AdministerSettingsRequest,
    AdministerSettingsSuccess,
    BridgeRuntimeSettings,
    CredentialSlotStatus,
    SettingDefinition,
    SystemSettingsRecord,
)
from app.services.workspace.administer_settings import _store

if TYPE_CHECKING:
    from pathlib import Path

    from app.services.workspace.administer_settings.config import (
        AdministerSettingsConfig,
    )

_TIMESTAMP_FORMAT: Final = "%Y-%m-%dT%H:%M:%S.%fZ"


def _normalize_iso(val: object) -> str:
    """Normalize any date/time value to canonical UtcTimestamp wire format.

    Args:
        val: Input datetime, string, or None.

    Returns:
        Canonical UtcTimestamp formatted string.
    """
    if not val:
        return datetime.now(UTC).strftime(_TIMESTAMP_FORMAT)
    text = str(val)
    try:
        dt = datetime.fromisoformat(text)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return dt.astimezone(UTC).strftime(_TIMESTAMP_FORMAT)
    except ValueError, TypeError:
        return datetime.now(UTC).strftime(_TIMESTAMP_FORMAT)


def read_bridge_runtime(db_path: Path | str | None = None) -> BridgeRuntimeSettings:
    """Read the MT5 snapshot bridge runtime settings from the store.

    Args:
        db_path: Optional explicit database path.

    Returns:
        Bridge runtime settings with the TickBridge EA defaults for
        absent rows.
    """
    runtime = _store.get_mt5_snapshot_bridge_runtime(db_path)
    return BridgeRuntimeSettings(
        host=runtime["host"],
        port=int(runtime["port"]),
        source_id=runtime["source_id"],
        auth_token=runtime["auth_token"],
        symbols=runtime["symbols"],
    )


class SettingsService:
    """Settings administration provider for the administer-settings capability."""

    def __init__(self, config: AdministerSettingsConfig | None = None) -> None:
        """Initialize the service against its configured database path.

        Args:
            config: Service configuration carrying the database path.
        """
        self._config = config

    async def administer_settings(
        self, request: AdministerSettingsRequest
    ) -> AdministerSettingsSuccess | WorkspaceFailure:
        """Serve one operation-discriminated settings request.

        Args:
            request: Settings read/update/manifest/credentials/bridge
                request.

        Returns:
            Settings operation success, or a structured workspace failure.
        """
        db_path = self._config.database_path if self._config is not None else None
        if request.operation == "READ_SYSTEM":
            record = _store.get_system_settings(db_path=db_path)
            return AdministerSettingsSuccess(
                request_id=request.request_id,
                system=self._system_record(record),
            )
        if request.operation == "UPDATE_SYSTEM":
            record = _store.update_system_settings(
                dict(request.settings),
                changed_by=request.changed_by,
                db_path=db_path,
            )
            return AdministerSettingsSuccess(
                request_id=request.request_id,
                system=self._system_record(record),
            )
        if request.operation == "READ_MANIFEST":
            definitions = _store.get_settings_manifest(db_path=db_path)
            return AdministerSettingsSuccess(
                request_id=request.request_id,
                manifest=tuple(
                    SettingDefinition(
                        key=str(item["key"]),
                        label=str(item["label"]),
                        description=str(item["description"]),
                        value_kind=cast(
                            "Literal['string', 'boolean', 'decimal', 'integer']",
                            str(item["value_kind"]),
                        ),
                        allowed_values=tuple(
                            str(v) for v in item.get("allowed_values", ())
                        ),
                        minimum=(
                            float(item["minimum"])
                            if item.get("minimum") is not None
                            else None
                        ),
                        maximum=(
                            float(item["maximum"])
                            if item.get("maximum") is not None
                            else None
                        ),
                        activation=cast(
                            "Literal['hot', 'restart_required']",
                            str(item["activation"]),
                        ),
                    )
                    for item in definitions
                ),
            )
        if request.operation == "READ_CREDENTIALS":
            statuses = _store.get_credentials_status(db_path=db_path)
            return AdministerSettingsSuccess(
                request_id=request.request_id,
                credentials=tuple(
                    CredentialSlotStatus(
                        slot=str(item["slot"]),
                        label=str(item["label"]),
                        fields=tuple(item["fields"]),
                        configured=bool(item["configured"]),
                        version=int(item["version"]),
                        updated_at=(
                            _normalize_iso(item["updated_at"])
                            if item.get("updated_at")
                            else None
                        ),
                    )
                    for item in statuses
                ),
            )
        if request.operation == "UPDATE_CREDENTIAL":
            updated = _store.update_credential_slot(
                str(request.slot),
                dict(request.material),
                changed_by=request.changed_by,
                db_path=db_path,
            )
            return AdministerSettingsSuccess(
                request_id=request.request_id,
                credential_updated=bool(updated.get("configured")),
            )
        return AdministerSettingsSuccess(
            request_id=request.request_id,
            bridge=read_bridge_runtime(db_path=db_path),
        )

    @staticmethod
    def _system_record(record: dict[str, object]) -> SystemSettingsRecord:
        """Project one store settings projection into its wire record.

        Args:
            record: Store projection mapping.

        Returns:
            Wire ``SystemSettingsRecord``.
        """
        raw_settings = record.get("settings")
        settings_dict = raw_settings if isinstance(raw_settings, dict) else {}
        raw_version = record.get("version")
        version = int(raw_version) if isinstance(raw_version, (int, str)) else 0
        return SystemSettingsRecord(
            settings={str(key): str(value) for key, value in settings_dict.items()},
            version=version,
            updated_at=_normalize_iso(record.get("updated_at")),
        )


def _run_usage_example() -> None:  # pragma: no cover - usage harness
    """Demonstrate the settings operations against the workspace store."""
    import asyncio

    async def scenario() -> None:
        service = SettingsService()
        manifest = await service.administer_settings(
            AdministerSettingsRequest(
                request_id=str(uuid7()),
                capability_snapshot_id=str(uuid7()),
                operation="READ_MANIFEST",
            )
        )
        if isinstance(manifest, WorkspaceFailure):
            print(f"failure={manifest.code}")
        else:
            print(f"definitions={len(manifest.manifest)}")

    asyncio.run(scenario())


if __name__ == "__main__":  # pragma: no cover
    _run_usage_example()
