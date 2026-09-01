"""Transactional SQLite tests for plugin lifecycle management."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Literal

import pytest
from app.contracts.plugins.errors import PluginFailure
from app.contracts.plugins.models import (
    ManageLifecycleRequest,
    ManageLifecycleSuccess,
    PluginPackageReceipt,
)
from app.services.plugins.lifecycle.config import PluginLifecycleConfig
from app.services.plugins.lifecycle.plugin_lifecycle import PluginLifecycleService, main

_REQUEST_ID = "00000000-0000-7000-8000-000000000010"
_SNAPSHOT_ID = "00000000-0000-7000-8000-000000000011"
_WORKSPACE_ID = "00000000-0000-7000-8000-000000000012"
_PLUGIN_ID = "example.plugin"


def _receipt(
    receipt_suffix: int, version: str, hash_character: str
) -> PluginPackageReceipt:
    """Create a valid deterministic package receipt for one test version."""
    return PluginPackageReceipt(
        receipt_id=f"00000000-0000-7000-8000-{receipt_suffix:012d}",
        plugin_id=_PLUGIN_ID,
        version=version,
        package_hash=hash_character * 64,
        manifest_hash=("b" if hash_character == "a" else "c") * 64,
        installed_at="2026-08-28T00:00:00.000000Z",
    )


def _request(
    operation: Literal["INSTALL", "ENABLE", "DISABLE", "UPGRADE", "REMOVE"],
    *,
    receipt: PluginPackageReceipt | None = None,
    plugin_id: str | None = None,
    workspace_id: str | None = None,
    version: str | None = None,
) -> ManageLifecycleRequest:
    """Create one frozen public lifecycle request."""
    return ManageLifecycleRequest(
        request_id=_REQUEST_ID,
        capability_snapshot_id=_SNAPSHOT_ID,
        operation=operation,
        receipt=receipt,
        plugin_id=plugin_id,
        workspace_id=workspace_id,
        version=version,
    )


def _service(database_path: Path) -> PluginLifecycleService:
    """Build a service bound to one isolated test database."""
    return PluginLifecycleService(PluginLifecycleConfig(database_path=database_path))


def _database_counts(database_path: Path) -> tuple[int, int, int]:
    """Read durable entity counts after a service call closes its connection."""
    connection = sqlite3.connect(database_path)
    try:
        plugins = int(connection.execute("SELECT COUNT(*) FROM plugins").fetchone()[0])
        versions = int(
            connection.execute("SELECT COUNT(*) FROM plugin_versions").fetchone()[0]
        )
        activations = int(
            connection.execute("SELECT COUNT(*) FROM plugin_activations").fetchone()[0]
        )
        return plugins, versions, activations
    finally:
        connection.close()


@pytest.mark.asyncio
async def test_install_is_immutable_and_returns_no_activation(tmp_path: Path) -> None:
    """Verify receipt/version persistence, conflict rollback, and connection release."""
    database_path = tmp_path / "lifecycle.db"
    service = _service(database_path)
    first = _receipt(13, "1.0.0", "a")

    installed = await service.manage_lifecycle(_request("INSTALL", receipt=first))
    assert isinstance(installed, ManageLifecycleSuccess)
    assert installed.activation is None
    assert installed.lifecycle is None
    assert _database_counts(database_path) == (1, 1, 0)

    conflict = await service.manage_lifecycle(
        _request("INSTALL", receipt=_receipt(14, "1.0.0", "d"))
    )
    assert isinstance(conflict, PluginFailure)
    assert conflict.code == "PLUGIN_LIFECYCLE_CONFLICT"
    assert conflict.request_id == _REQUEST_ID
    assert _database_counts(database_path) == (1, 1, 0)


@pytest.mark.asyncio
async def test_enable_disable_upgrade_and_remove_retain_metadata(
    tmp_path: Path,
) -> None:
    """Verify transitions, optimistic versions, durable upgrade, and retention."""
    database_path = tmp_path / "lifecycle.db"
    service = _service(database_path)
    first = _receipt(15, "1.0.0", "a")
    second = _receipt(16, "2.0.0", "d")
    await service.manage_lifecycle(_request("INSTALL", receipt=first))

    enabled = await service.manage_lifecycle(
        _request("ENABLE", plugin_id=_PLUGIN_ID, workspace_id=_WORKSPACE_ID)
    )
    assert isinstance(enabled, ManageLifecycleSuccess)
    assert enabled.activation is not None
    assert enabled.activation.state == "ENABLED"
    assert enabled.activation.row_version == 1

    disabled = await service.manage_lifecycle(
        _request("DISABLE", plugin_id=_PLUGIN_ID, workspace_id=_WORKSPACE_ID)
    )
    assert isinstance(disabled, ManageLifecycleSuccess)
    assert disabled.activation is not None
    assert disabled.activation.state == "DISABLED"
    assert disabled.activation.row_version == 2

    reenabled = await service.manage_lifecycle(
        _request("ENABLE", plugin_id=_PLUGIN_ID, workspace_id=_WORKSPACE_ID)
    )
    assert isinstance(reenabled, ManageLifecycleSuccess)
    assert reenabled.activation is not None
    upgraded = await service.manage_lifecycle(
        _request(
            "UPGRADE",
            receipt=second,
            plugin_id=_PLUGIN_ID,
            workspace_id=_WORKSPACE_ID,
            version="2.0.0",
        )
    )
    assert isinstance(upgraded, ManageLifecycleSuccess)
    assert upgraded.activation is not None
    assert upgraded.activation.installed_version == "2.0.0"
    assert upgraded.activation.previous_version == "1.0.0"
    assert upgraded.activation.state == "ENABLED"
    assert upgraded.activation.row_version == 4

    removed = await service.manage_lifecycle(
        _request("REMOVE", plugin_id=_PLUGIN_ID, workspace_id=_WORKSPACE_ID)
    )
    assert isinstance(removed, ManageLifecycleSuccess)
    assert removed.activation is None
    assert _database_counts(database_path) == (1, 2, 0)


@pytest.mark.asyncio
async def test_failed_upgrade_rolls_back_after_reopen(tmp_path: Path) -> None:
    """Verify a storage failure retains the prior version and usable activation."""
    database_path = tmp_path / "lifecycle.db"
    first = _receipt(17, "1.0.0", "a")
    second = _receipt(18, "2.0.0", "d")
    service = _service(database_path)
    await service.manage_lifecycle(_request("INSTALL", receipt=first))
    await service.manage_lifecycle(
        _request("ENABLE", plugin_id=_PLUGIN_ID, workspace_id=_WORKSPACE_ID)
    )

    def injected_failure(_point: str) -> None:
        raise sqlite3.IntegrityError("test rollback")

    failing_service = PluginLifecycleService(
        PluginLifecycleConfig(database_path=database_path),
        failure_hook=injected_failure,
    )
    failed = await failing_service.manage_lifecycle(
        _request(
            "UPGRADE",
            receipt=second,
            plugin_id=_PLUGIN_ID,
            workspace_id=_WORKSPACE_ID,
        )
    )
    assert isinstance(failed, PluginFailure)
    assert _database_counts(database_path) == (1, 1, 1)

    reopened_service = _service(database_path)
    disabled = await reopened_service.manage_lifecycle(
        _request("DISABLE", plugin_id=_PLUGIN_ID, workspace_id=_WORKSPACE_ID)
    )
    assert isinstance(disabled, ManageLifecycleSuccess)
    assert disabled.activation is not None
    assert disabled.activation.installed_version == "1.0.0"


@pytest.mark.asyncio
async def test_illegal_transitions_and_mismatched_upgrade_do_not_mutate(
    tmp_path: Path,
) -> None:
    """Verify missing and mismatched transitions return the shared conflict shape."""
    database_path = tmp_path / "lifecycle.db"
    service = _service(database_path)
    missing = await service.manage_lifecycle(
        _request("REMOVE", plugin_id=_PLUGIN_ID, workspace_id=_WORKSPACE_ID)
    )
    assert isinstance(missing, PluginFailure)

    first = _receipt(19, "1.0.0", "a")
    second = _receipt(20, "2.0.0", "d")
    await service.manage_lifecycle(_request("INSTALL", receipt=first))
    await service.manage_lifecycle(
        _request("ENABLE", plugin_id=_PLUGIN_ID, workspace_id=_WORKSPACE_ID)
    )
    mismatch = await service.manage_lifecycle(
        _request(
            "UPGRADE",
            receipt=second,
            plugin_id=_PLUGIN_ID,
            workspace_id=_WORKSPACE_ID,
            version="1.0.0",
        )
    )
    assert isinstance(mismatch, PluginFailure)
    assert _database_counts(database_path) == (1, 1, 1)


def test_bounded_usage_scenario(capsys: pytest.CaptureFixture[str]) -> None:
    """Verify the primary module's no-network temporary-database example."""
    main()
    assert "Plugin lifecycle usage scenario passed." in capsys.readouterr().out
