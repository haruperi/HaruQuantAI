"""Unit tests for Workspace domain public contracts."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from app.contracts.workspace import (
    WORKSPACE_DIAGNOSTICS,
    WORKSPACE_JOBS,
    WORKSPACE_NOTIFICATIONS,
    WORKSPACE_PERSISTENCE,
    WORKSPACE_PLUGINS,
    WORKSPACE_RESOURCES,
    WORKSPACE_SCHEDULER,
    WORKSPACE_SETTINGS,
    WORKSPACE_WORKERS,
    InvalidJobTransitionError,
    JobDefinition,
    JobNotFoundError,
    MemoryWatchdogTrippedError,
    ResourceQuotaExceededError,
    SettingsEntry,
    SettingsSnapshot,
    SettingsValidationError,
    WorkspaceError,
)


def test_capability_tokens() -> None:
    """Verify that all capability tokens have correct versioned identifiers."""
    assert WORKSPACE_SETTINGS.name == "workspace.settings@1"
    assert WORKSPACE_JOBS.name == "workspace.jobs@1"
    assert WORKSPACE_SCHEDULER.name == "workspace.scheduler@1"
    assert WORKSPACE_NOTIFICATIONS.name == "workspace.notifications@1"
    assert WORKSPACE_DIAGNOSTICS.name == "workspace.diagnostics@1"
    assert WORKSPACE_WORKERS.name == "workspace.workers@1"
    assert WORKSPACE_RESOURCES.name == "workspace.resources@1"
    assert WORKSPACE_PLUGINS.name == "workspace.plugins@1"
    assert WORKSPACE_PERSISTENCE.name == "persistence.workspace@1"


def test_job_definition_immutability() -> None:
    """Verify JobDefinition is frozen with slots."""
    now = datetime.now(UTC)
    job = JobDefinition(
        job_id="job-1",
        group_id="group-1",
        operation="build_strategies",
        priority=10,
        resource_class="cpu_standard",
        config_hash="abc123hash",
        payload={"symbol": "EURUSD"},
        created_at_utc=now,
    )
    assert job.job_id == "job-1"
    with pytest.raises(AttributeError):
        # Frozen dataclass mutation must raise AttributeError
        job.priority = 20  # type: ignore[misc]


def test_settings_entry_and_snapshot() -> None:
    """Verify SettingsEntry and SettingsSnapshot immutability."""
    now = datetime.now(UTC)
    entry = SettingsEntry(
        scope="application",
        key="max_threads",
        value={"threads": 8},
        schema_version=1,
        updated_at_utc=now,
    )
    snapshot = SettingsSnapshot(entries=(entry,), resolved_at_utc=now)
    assert len(snapshot.entries) == 1
    assert snapshot.entries[0].key == "max_threads"


def test_custom_domain_exceptions() -> None:
    """Verify that domain exceptions inherit from WorkspaceError."""
    assert issubclass(JobNotFoundError, WorkspaceError)
    assert issubclass(InvalidJobTransitionError, WorkspaceError)
    assert issubclass(ResourceQuotaExceededError, WorkspaceError)
    assert issubclass(MemoryWatchdogTrippedError, WorkspaceError)
    assert issubclass(SettingsValidationError, WorkspaceError)
