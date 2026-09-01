"""Transactional lifecycle operations for retained plugin packages.

The module owns the ``plugins``, ``plugin_versions``, and
``plugin_activations`` SQLite tables declared by ``plugins.lifecycle``. It
does not execute plugin code or own sandbox lifecycle observations.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import sqlite3
import tempfile
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal, NoReturn, cast

from app.contracts.common.models import ProblemDetails
from app.contracts.plugins.errors import PluginFailure
from app.contracts.plugins.models import (
    ManageLifecycleRequest,
    ManageLifecycleSuccess,
    PluginActivation,
    PluginPackageReceipt,
)
from app.services.plugins.lifecycle.config import PluginLifecycleConfig

_CAPABILITY_KEY = "plugins.manage-lifecycle@1"
_SCHEMA_STATEMENTS = (
    """
    CREATE TABLE IF NOT EXISTS plugins (
        plugin_id TEXT PRIMARY KEY,
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS plugin_versions (
        plugin_id TEXT NOT NULL,
        version TEXT NOT NULL,
        receipt_id TEXT NOT NULL UNIQUE,
        receipt_json TEXT NOT NULL,
        receipt_hash TEXT NOT NULL,
        package_hash TEXT NOT NULL,
        manifest_hash TEXT NOT NULL,
        installed_at TEXT NOT NULL,
        PRIMARY KEY (plugin_id, version),
        FOREIGN KEY (plugin_id) REFERENCES plugins(plugin_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS plugin_activations (
        plugin_id TEXT NOT NULL,
        workspace_id TEXT NOT NULL,
        installed_version TEXT NOT NULL,
        previous_version TEXT,
        state TEXT NOT NULL CHECK (state IN ('INSTALLED', 'ENABLED', 'DISABLED')),
        enabled_at TEXT,
        disabled_at TEXT,
        row_version INTEGER NOT NULL CHECK (row_version >= 1),
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        PRIMARY KEY (plugin_id, workspace_id),
        FOREIGN KEY (plugin_id, installed_version)
            REFERENCES plugin_versions(plugin_id, version)
    )
    """,
)


class _LifecycleConflictError(Exception):
    """Expected lifecycle transition failure that must not mutate state."""


def _utc_timestamp() -> str:
    """Return a UTC timestamp accepted by the public wire contract."""
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _canonical_receipt(receipt: PluginPackageReceipt) -> tuple[str, str]:
    """Serialize and hash an immutable receipt deterministically.

    Returns:
        The canonical JSON representation and its SHA-256 hash.
    """
    serialized = json.dumps(
        receipt.model_dump(mode="json"),
        sort_keys=True,
        separators=(",", ":"),
    )
    return serialized, hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _conflict(detail: str) -> NoReturn:
    """Raise the internal signal for an expected lifecycle conflict.

    Raises:
        _LifecycleConflictError: Always, with the structured failure detail.
    """
    raise _LifecycleConflictError(detail)


def _failure(request_id: str, detail: str) -> PluginFailure:
    """Create the stable structured failure shape for lifecycle conflicts.

    Returns:
        A public failure envelope that preserves the request identity.
    """
    return PluginFailure(
        request_id=request_id,
        code="PLUGIN_LIFECYCLE_CONFLICT",
        problem=ProblemDetails(
            type="urn:haruquantai:plugins:lifecycle-conflict",
            title="Plugin lifecycle conflict",
            status=409,
            code="PLUGIN_LIFECYCLE_CONFLICT",
            detail=detail,
            request_id=request_id,
            capability_key=_CAPABILITY_KEY,
        ),
    )


class PluginLifecycleService:
    """SQLite-backed implementation of ``ManageLifecycleCapability``."""

    def __init__(
        self,
        config: PluginLifecycleConfig,
        failure_hook: Callable[[str], None] | None = None,
    ) -> None:
        """Bind the service to its explicit durable-state database.

        Args:
            config: Validated explicit lifecycle database configuration.
            failure_hook: Test-only deterministic fault hook invoked within a write
                transaction; production callers leave this unset.
        """
        self._database_path = config.database_path
        self._failure_hook = failure_hook

    async def manage_lifecycle(
        self,
        request: ManageLifecycleRequest,
    ) -> ManageLifecycleSuccess | PluginFailure:
        """Apply one lifecycle operation within a single SQLite transaction.

        Returns:
            The public success result or a structured lifecycle conflict.
        """
        return await fr_plug_replace_plugins_transactionally(self, request)

    async def execute(
        self,
        request: ManageLifecycleRequest,
    ) -> ManageLifecycleSuccess | PluginFailure:
        """Execute the named FR trace and map all storage failures safely.

        Returns:
            The public success result or a structured lifecycle conflict.
        """
        connection: sqlite3.Connection | None = None
        try:
            connection = sqlite3.connect(self._database_path)
            connection.row_factory = sqlite3.Row
            connection.execute("PRAGMA foreign_keys = ON")
            connection.execute("BEGIN IMMEDIATE")
            self._ensure_schema(connection)
            result = self._apply_operation(connection, request)
            connection.commit()
            return result
        except _LifecycleConflictError as error:
            if connection is not None:
                connection.rollback()
            return _failure(request.request_id, str(error))
        except OSError, sqlite3.Error:
            if connection is not None:
                connection.rollback()
            return _failure(
                request.request_id,
                "Transactional lifecycle operation could not be committed.",
            )
        finally:
            if connection is not None:
                connection.close()

    def _ensure_schema(self, connection: sqlite3.Connection) -> None:
        """Create only the lifecycle-owned tables inside the active transaction."""
        for statement in _SCHEMA_STATEMENTS:
            connection.execute(statement)

    def _apply_operation(
        self,
        connection: sqlite3.Connection,
        request: ManageLifecycleRequest,
    ) -> ManageLifecycleSuccess:
        """Dispatch one validated public operation within the write transaction.

        Returns:
            The successful lifecycle operation result.
        """
        match request.operation:
            case "INSTALL":
                self._install(connection, self._required_receipt(request))
                activation = None
            case "ENABLE":
                activation = self._enable(
                    connection, *self._required_addressors(request)
                )
            case "DISABLE":
                activation = self._disable(
                    connection, *self._required_addressors(request)
                )
            case "UPGRADE":
                activation = self._upgrade(connection, request)
            case "REMOVE":
                self._remove(connection, *self._required_addressors(request))
                activation = None
            case _:
                _conflict("Unsupported plugin lifecycle operation.")
        return ManageLifecycleSuccess(
            request_id=request.request_id, activation=activation
        )

    def _required_receipt(
        self, request: ManageLifecycleRequest
    ) -> PluginPackageReceipt:
        """Return the required receipt after a defensive operation check."""
        if request.receipt is None:
            _conflict("A package receipt is required for this operation.")
        return request.receipt

    def _required_addressors(self, request: ManageLifecycleRequest) -> tuple[str, str]:
        """Return required plugin and workspace addressors."""
        if request.plugin_id is None or request.workspace_id is None:
            _conflict(
                "Plugin and workspace addressors are required for this operation."
            )
        return request.plugin_id, request.workspace_id

    def _install(
        self, connection: sqlite3.Connection, receipt: PluginPackageReceipt
    ) -> None:
        """Persist an immutable receipt and version without changing activation."""
        serialized, receipt_hash = _canonical_receipt(receipt)
        existing_version = connection.execute(
            "SELECT receipt_json FROM plugin_versions "
            "WHERE plugin_id = ? AND version = ?",
            (receipt.plugin_id, receipt.version),
        ).fetchone()
        if (
            existing_version is not None
            and existing_version["receipt_json"] != serialized
        ):
            _conflict("An immutable receipt already exists for this plugin version.")

        existing_receipt = connection.execute(
            "SELECT plugin_id, version, receipt_json FROM plugin_versions "
            "WHERE receipt_id = ?",
            (receipt.receipt_id,),
        ).fetchone()
        if existing_receipt is not None and (
            existing_receipt["plugin_id"] != receipt.plugin_id
            or existing_receipt["version"] != receipt.version
            or existing_receipt["receipt_json"] != serialized
        ):
            _conflict(
                "Receipt identity is already bound to a different immutable version."
            )

        connection.execute(
            "INSERT OR IGNORE INTO plugins (plugin_id, created_at) VALUES (?, ?)",
            (receipt.plugin_id, _utc_timestamp()),
        )
        if existing_version is None:
            connection.execute(
                """
                INSERT INTO plugin_versions (
                    plugin_id, version, receipt_id, receipt_json, receipt_hash,
                    package_hash, manifest_hash, installed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    receipt.plugin_id,
                    receipt.version,
                    receipt.receipt_id,
                    serialized,
                    receipt_hash,
                    receipt.package_hash,
                    receipt.manifest_hash,
                    receipt.installed_at,
                ),
            )

    def _enable(
        self,
        connection: sqlite3.Connection,
        plugin_id: str,
        workspace_id: str,
    ) -> PluginActivation:
        """Create or enable the workspace's unique plugin activation.

        Returns:
            The committed enabled activation.
        """
        existing = self._activation_row(connection, plugin_id, workspace_id)
        if existing is not None and existing["state"] == "ENABLED":
            _conflict("Plugin activation is already enabled.")

        if existing is None:
            version_row = connection.execute(
                """
                SELECT version FROM plugin_versions
                WHERE plugin_id = ?
                ORDER BY installed_at DESC, version DESC LIMIT 1
                """,
                (plugin_id,),
            ).fetchone()
            if version_row is None:
                _conflict("An installed plugin version is required before enablement.")
            now = _utc_timestamp()
            connection.execute(
                """
                INSERT INTO plugin_activations (
                    plugin_id, workspace_id, installed_version, previous_version, state,
                    enabled_at, disabled_at, row_version, created_at, updated_at
                ) VALUES (?, ?, ?, NULL, 'ENABLED', ?, NULL, 1, ?, ?)
                """,
                (plugin_id, workspace_id, version_row["version"], now, now, now),
            )
        else:
            now = _utc_timestamp()
            connection.execute(
                """
                UPDATE plugin_activations
                SET state = 'ENABLED', enabled_at = ?, updated_at = ?,
                    row_version = row_version + 1
                WHERE plugin_id = ? AND workspace_id = ?
                """,
                (now, now, plugin_id, workspace_id),
            )
        return self._require_activation(connection, plugin_id, workspace_id)

    def _disable(
        self,
        connection: sqlite3.Connection,
        plugin_id: str,
        workspace_id: str,
    ) -> PluginActivation:
        """Disable an active workspace activation while retaining package metadata.

        Returns:
            The committed disabled activation.
        """
        existing = self._activation_row(connection, plugin_id, workspace_id)
        if existing is None or existing["state"] != "ENABLED":
            _conflict("Only an enabled plugin activation can be disabled.")
        now = _utc_timestamp()
        connection.execute(
            """
            UPDATE plugin_activations
            SET state = 'DISABLED', disabled_at = ?, updated_at = ?,
                row_version = row_version + 1
            WHERE plugin_id = ? AND workspace_id = ?
            """,
            (now, now, plugin_id, workspace_id),
        )
        return self._require_activation(connection, plugin_id, workspace_id)

    def _upgrade(
        self,
        connection: sqlite3.Connection,
        request: ManageLifecycleRequest,
    ) -> PluginActivation:
        """Atomically store a new version and replace its workspace activation.

        Returns:
            The committed replacement activation.
        """
        receipt = self._required_receipt(request)
        plugin_id, workspace_id = self._required_addressors(request)
        if plugin_id != receipt.plugin_id:
            _conflict("Upgrade plugin addressor must match the receipt plugin ID.")
        if request.version is not None and request.version != receipt.version:
            _conflict("Upgrade target version must match the receipt version.")

        existing = self._activation_row(connection, plugin_id, workspace_id)
        if existing is None:
            _conflict("An existing workspace activation is required for upgrade.")
        if existing["installed_version"] == receipt.version:
            _conflict("Upgrade target version is already active.")

        self._install(connection, receipt)
        if self._failure_hook is not None:
            self._failure_hook("before_activation_replace")
        now = _utc_timestamp()
        connection.execute(
            """
            UPDATE plugin_activations
            SET installed_version = ?, previous_version = ?, updated_at = ?,
                row_version = row_version + 1
            WHERE plugin_id = ? AND workspace_id = ?
            """,
            (
                receipt.version,
                existing["installed_version"],
                now,
                plugin_id,
                workspace_id,
            ),
        )
        return self._require_activation(connection, plugin_id, workspace_id)

    def _remove(
        self,
        connection: sqlite3.Connection,
        plugin_id: str,
        workspace_id: str,
    ) -> None:
        """Remove only the workspace activation and retain package/version rows."""
        if self._activation_row(connection, plugin_id, workspace_id) is None:
            _conflict("A workspace activation is required for removal.")
        connection.execute(
            "DELETE FROM plugin_activations WHERE plugin_id = ? AND workspace_id = ?",
            (plugin_id, workspace_id),
        )

    def _activation_row(
        self,
        connection: sqlite3.Connection,
        plugin_id: str,
        workspace_id: str,
    ) -> sqlite3.Row | None:
        """Look up the unique activation without widening public query scope.

        Returns:
            The activation row when it exists, otherwise None.
        """
        row = connection.execute(
            "SELECT * FROM plugin_activations WHERE plugin_id = ? AND workspace_id = ?",
            (plugin_id, workspace_id),
        ).fetchone()
        return cast("sqlite3.Row | None", row)

    def _require_activation(
        self,
        connection: sqlite3.Connection,
        plugin_id: str,
        workspace_id: str,
    ) -> PluginActivation:
        """Load the committed activation into the frozen public wire record.

        Returns:
            The validated public activation model.
        """
        row = self._activation_row(connection, plugin_id, workspace_id)
        if row is None:
            _conflict("Lifecycle activation was not committed.")
        values = dict(row)
        return PluginActivation(
            plugin_id=cast("str", values["plugin_id"]),
            workspace_id=cast("str", values["workspace_id"]),
            installed_version=cast("str", values["installed_version"]),
            previous_version=cast("str | None", values["previous_version"]),
            state=cast(
                "Literal['INSTALLED', 'ENABLED', 'DISABLED']",
                values["state"],
            ),
            enabled_at=cast("str | None", values["enabled_at"]),
            disabled_at=cast("str | None", values["disabled_at"]),
            row_version=cast("int", values["row_version"]),
            created_at=cast("str", values["created_at"]),
            updated_at=cast("str", values["updated_at"]),
        )


async def fr_plug_replace_plugins_transactionally(
    service: PluginLifecycleService,
    request: ManageLifecycleRequest,
) -> ManageLifecycleSuccess | PluginFailure:
    """Trace the implementation of FR-PLUG-REPLACE_PLUGINS_TRANSACTIONALLY.

    Returns:
        The public success result or a structured lifecycle conflict.
    """
    return await service.execute(request)


def _receipt(receipt_id: str, version: str, content: str) -> PluginPackageReceipt:
    """Create a deterministic receipt used only by the bounded usage scenario.

    Returns:
        A valid immutable receipt for the requested version.
    """
    return PluginPackageReceipt(
        receipt_id=receipt_id,
        plugin_id="example.plugin",
        version=version,
        package_hash=content * 64,
        manifest_hash=("b" if content == "a" else "c") * 64,
        installed_at="2026-08-28T00:00:00.000000Z",
    )


async def _usage_scenario(database_path: Path) -> None:
    """Prove install, upgrade rollback, disable/remove, and retained metadata.

    Raises:
        RuntimeError: If retained-metadata verification fails.
        TypeError: If an operation returns an unexpected public result shape.
    """
    config = PluginLifecycleConfig(database_path=database_path)
    service = PluginLifecycleService(config)
    request_id = "00000000-0000-7000-8000-000000000001"
    snapshot_id = "00000000-0000-7000-8000-000000000002"
    workspace_id = "00000000-0000-7000-8000-000000000003"
    first = _receipt("00000000-0000-7000-8000-000000000004", "1.0.0", "a")
    second = _receipt("00000000-0000-7000-8000-000000000005", "2.0.0", "d")

    installed = await service.manage_lifecycle(
        ManageLifecycleRequest(
            request_id=request_id,
            capability_snapshot_id=snapshot_id,
            operation="INSTALL",
            receipt=first,
        )
    )
    if not isinstance(installed, ManageLifecycleSuccess):
        raise TypeError("Usage scenario install returned an unexpected result.")
    enabled = await service.manage_lifecycle(
        ManageLifecycleRequest(
            request_id=request_id,
            capability_snapshot_id=snapshot_id,
            operation="ENABLE",
            plugin_id=first.plugin_id,
            workspace_id=workspace_id,
        )
    )
    if not isinstance(enabled, ManageLifecycleSuccess):
        raise TypeError("Usage scenario enable returned an unexpected result.")
    upgraded = await service.manage_lifecycle(
        ManageLifecycleRequest(
            request_id=request_id,
            capability_snapshot_id=snapshot_id,
            operation="UPGRADE",
            receipt=second,
            plugin_id=first.plugin_id,
            workspace_id=workspace_id,
            version=second.version,
        )
    )
    if not isinstance(upgraded, ManageLifecycleSuccess):
        raise TypeError("Usage scenario upgrade returned an unexpected result.")

    def fail_replace(_point: str) -> None:
        raise sqlite3.IntegrityError("injected rollback")

    failed_service = PluginLifecycleService(config, failure_hook=fail_replace)
    failed = await failed_service.manage_lifecycle(
        ManageLifecycleRequest(
            request_id="00000000-0000-7000-8000-000000000006",
            capability_snapshot_id=snapshot_id,
            operation="UPGRADE",
            receipt=_receipt("00000000-0000-7000-8000-000000000007", "3.0.0", "e"),
            plugin_id=first.plugin_id,
            workspace_id=workspace_id,
        )
    )
    if not isinstance(failed, PluginFailure):
        raise TypeError("Usage scenario rollback returned an unexpected result.")
    disabled = await service.manage_lifecycle(
        ManageLifecycleRequest(
            request_id=request_id,
            capability_snapshot_id=snapshot_id,
            operation="DISABLE",
            plugin_id=first.plugin_id,
            workspace_id=workspace_id,
        )
    )
    if not isinstance(disabled, ManageLifecycleSuccess):
        raise TypeError("Usage scenario disable returned an unexpected result.")
    removed = await service.manage_lifecycle(
        ManageLifecycleRequest(
            request_id=request_id,
            capability_snapshot_id=snapshot_id,
            operation="REMOVE",
            plugin_id=first.plugin_id,
            workspace_id=workspace_id,
        )
    )
    if not isinstance(removed, ManageLifecycleSuccess):
        raise TypeError("Usage scenario remove returned an unexpected result.")
    connection = sqlite3.connect(database_path)
    try:
        versions = connection.execute("SELECT COUNT(*) FROM plugin_versions").fetchone()
        activations = connection.execute(
            "SELECT COUNT(*) FROM plugin_activations"
        ).fetchone()
    finally:
        connection.close()
    if versions != (2,) or activations != (0,):
        raise RuntimeError("Usage scenario did not retain the expected metadata.")


def main() -> None:
    """Run the isolated lifecycle usage scenario without external side effects."""
    with tempfile.TemporaryDirectory() as temporary_directory:
        database_path = Path(temporary_directory) / "plugin-lifecycle.sqlite3"
        asyncio.run(_usage_scenario(database_path))
    print("Plugin lifecycle usage scenario passed.")


if __name__ == "__main__":
    main()
