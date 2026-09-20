"""Public contracts, protocols, DTOs, and capabilities for the Workspace domain.

Purpose:
    Defines the public boundaries, immutable data transfer objects, typed
    protocols, capability tokens, and stable error types for application
    settings, durable job lifecycles, bounded scheduling, multi-channel
    notifications, operational diagnostics, remote grid workers, resource
    governance, and sandboxed plugin hosting.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import Any, Protocol, TypeVar

from pydantic import BaseModel

from app.kernel.capability import Capability

# ---------------------------------------------------------------------------
# Enums and Value Types
# ---------------------------------------------------------------------------


class JobState(StrEnum):
    """Execution state machine states for durable jobs."""

    QUEUED = "queued"
    RUNNING = "running"
    PAUSING = "pausing"
    PAUSED = "paused"
    CANCELLING = "cancelling"
    CANCELLED = "cancelled"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    INTERRUPTED = "interrupted"


class NotificationChannel(StrEnum):
    """Supported communication channels for workspace notifications."""

    DESKTOP = "desktop"
    EMAIL = "email"
    SOUND = "sound"
    TELEGRAM = "telegram"
    WEBHOOK = "webhook"


class CpuCoreMode(StrEnum):
    """CPU core allocation strategies matching SQX performance options."""

    SINGLE_CORE = "singleCore"
    RESERVE_1_CORE = "reserve1Core"
    CUSTOM_CORES = "customCores"
    MAX_PERFORMANCE = "maxPerformance"


class SettingsScope(StrEnum):
    """Hierarchical resolution scopes for application settings."""

    APPLICATION = "application"
    PROJECT = "project"
    RUN = "run"


class GridNodeState(StrEnum):
    """Operating status of a distributed grid worker node."""

    ONLINE = "online"
    BUSY = "busy"
    OFFLINE = "offline"


class LeaseState(StrEnum):
    """Status of a remote worker job lease."""

    ACTIVE = "active"
    COMPLETED = "completed"
    EXPIRED = "expired"
    REVOKED = "revoked"


# ---------------------------------------------------------------------------
# Typed Domain Exceptions
# ---------------------------------------------------------------------------


class WorkspaceError(Exception):
    """Base exception for all workspace domain errors."""


class JobNotFoundError(WorkspaceError):
    """Raised when a referenced job cannot be found in persistence."""


class InvalidJobTransitionError(WorkspaceError):
    """Raised when an invalid state transition is attempted on a job."""


class ResourceQuotaExceededError(WorkspaceError):
    """Raised when a job or worker exceeds admitted CPU/memory quotas."""


class MemoryWatchdogTrippedError(WorkspaceError):
    """Raised when the 85% RAM memory protection watchdog trips."""


class SettingsValidationError(WorkspaceError):
    """Raised when configuration values fail schema or bounds validation."""


class PluginError(WorkspaceError):
    """Base error for plugin host operations."""


class PluginSecurityError(PluginError):
    """Raised when an untrusted plugin attempts an unauthorized action."""


class WorkerLeaseError(WorkspaceError):
    """Raised when a remote worker lease cannot be acquired or refreshed."""


class ConfigurationError(WorkspaceError):
    """Raised when configuration values or notification templates are invalid."""


# ---------------------------------------------------------------------------
# Immutable Data Transfer Objects
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class SettingsEntry:
    """Individual typed configuration setting entry."""

    scope: str
    key: str
    value: dict[str, Any]
    schema_version: int
    updated_at_utc: datetime


@dataclass(frozen=True, slots=True)
class SettingsSnapshot:
    """Immutable snapshot of resolved effective settings."""

    entries: tuple[SettingsEntry, ...]
    resolved_at_utc: datetime


@dataclass(frozen=True, slots=True)
class JobDefinition:
    """Immutable specification for a durable job."""

    job_id: str
    group_id: str
    operation: str
    priority: int
    resource_class: str
    config_hash: str
    payload: dict[str, Any]
    created_at_utc: datetime


@dataclass(frozen=True, slots=True)
class JobAttempt:
    """Tracked execution attempt for a durable job."""

    attempt_id: str
    job_id: str
    worker_id: str
    sequence: int
    state: JobState
    heartbeat_at_utc: datetime | None
    checkpoint: dict[str, Any] | None
    created_at_utc: datetime
    completed_at_utc: datetime | None


@dataclass(frozen=True, slots=True)
class JobEvent:
    """Audit log entry representing a discrete job transition or checkpoint."""

    event_id: str
    job_id: str
    attempt_id: str | None
    from_state: JobState | None
    to_state: JobState
    details: dict[str, Any]
    created_at_utc: datetime


@dataclass(frozen=True, slots=True)
class JobReceipt:
    """Status receipt and progression snapshot of an active or completed job."""

    job_id: str
    state: JobState
    progress_percent: float
    message: str
    updated_at_utc: datetime


@dataclass(frozen=True, slots=True)
class JobProgress:
    """Progress report emitted by a running job attempt."""

    job_id: str
    attempt_id: str
    progress_percent: float
    message: str
    checkpoint: dict[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class QueueStats:
    """Snapshot of active scheduler queues and concurrency limits."""

    queued_count: int
    running_count: int
    paused_count: int
    max_concurrency: int


@dataclass(frozen=True, slots=True)
class NotificationMessage:
    """User notification payload with channel targeting."""

    message_id: str
    channel: NotificationChannel
    recipient: str
    title: str
    body: str
    require_user_action: bool
    metadata: dict[str, Any]
    created_at_utc: datetime


@dataclass(frozen=True, slots=True)
class NotificationReceipt:
    """Delivery confirmation for an emitted notification."""

    message_id: str
    delivered: bool
    error: str | None
    sent_at_utc: datetime


@dataclass(frozen=True, slots=True)
class BenchmarkResult:
    """Empirical hardware throughput benchmark metrics."""

    time_per_tick_ms: float
    avg_strategies_per_hour: float
    total_ticks: int
    elapsed_seconds: float
    cores_used: int
    executed_at_utc: datetime


@dataclass(frozen=True, slots=True)
class SystemHealth:
    """Telemetry snapshot of application health and memory metrics."""

    status: str
    version: str
    memory_used_mb: float
    total_memory_mb: float
    memory_pct: float
    active_jobs: int
    timestamp_utc: datetime


@dataclass(frozen=True, slots=True)
class ResourceQuota:
    """Resource admission quotas and memory protection thresholds."""

    cpu_mode: CpuCoreMode
    max_threads: int
    max_memory_mb: int
    memory_watchdog_threshold_pct: float


@dataclass(frozen=True, slots=True)
class ResourceUsage:
    """Current system resource utilization snapshot."""

    used_memory_mb: float
    memory_pct: float
    watchdog_tripped: bool
    active_workers: int


@dataclass(frozen=True, slots=True)
class GridNodeInfo:
    """Remote compute node in the distributed worker grid."""

    node_id: str
    host: str
    port: int
    cores: int
    memory_mb: int
    state: GridNodeState
    last_heartbeat_utc: datetime


@dataclass(frozen=True, slots=True)
class WorkerLease:
    """Time-bounded lease granting a worker node permission to run a job."""

    lease_id: str
    node_id: str
    job_id: str
    leased_at_utc: datetime
    expires_at_utc: datetime
    state: LeaseState


@dataclass(frozen=True, slots=True)
class PluginManifest:
    """Metadata describing a sandboxed plugin or extension."""

    plugin_id: str
    name: str
    version: str
    author: str
    entry_point: str
    permissions: tuple[str, ...]
    is_sandboxed: bool = True


@dataclass(frozen=True, slots=True)
class PluginInstance:
    """Active runtime record of a loaded plugin."""

    manifest: PluginManifest
    loaded_at_utc: datetime
    active: bool


# ---------------------------------------------------------------------------
# Protocols (Public Service Boundaries)
# ---------------------------------------------------------------------------

_T = TypeVar("_T", bound=BaseModel)


class SettingsService(Protocol):
    """Manage scoped typed application settings and snapshots."""

    def get_setting(
        self, key: str, scope: str = "application"
    ) -> dict[str, Any] | None:
        """Retrieve a raw setting value dictionary by scope and key.

        Args:
            key: Unique setting identifier.
            scope: Scope namespace (application, project, or run).

        Returns:
            Setting payload dictionary or None if not set.
        """
        ...

    def set_setting(
        self,
        key: str,
        value: dict[str, Any],
        scope: str = "application",
        schema_version: int = 1,
    ) -> None:
        """Store or update a setting value.

        Args:
            key: Unique setting identifier.
            value: JSON-serializable dictionary.
            scope: Target hierarchy scope.
            schema_version: Version of the payload schema.
        """
        ...

    def resolve_effective(
        self,
        keys: tuple[str, ...],
        project_id: str | None = None,
        run_id: str | None = None,
    ) -> SettingsSnapshot:
        """Resolve settings with hierarchical precedence: run > project > app.

        Args:
            keys: Tuple of setting keys to retrieve.
            project_id: Optional project context ID.
            run_id: Optional run context ID.

        Returns:
            Immutable SettingsSnapshot containing effective entries.
        """
        ...

    def export_preset(self, preset_name: str) -> dict[str, Any]:
        """Export current settings as a portable JSON preset.

        Args:
            preset_name: Name of the preset configuration.

        Returns:
            Dictionary payload ready for JSON serialization.
        """
        ...

    def import_preset(self, preset_data: dict[str, Any]) -> None:
        """Import a JSON preset into the application scope.

        Args:
            preset_data: Validated preset dictionary.
        """
        ...

    def get_model(
        self,
        key: str,
        model_cls: type[_T],
        scope: str = "application",
    ) -> _T | None:
        """Retrieve and parse setting value using a strongly-typed model.

        Args:
            key: Setting identifier.
            model_cls: Target model class.
            scope: Target hierarchy scope.

        Returns:
            Validated model instance or None if not set.
        """
        ...

    def set_model(
        self,
        key: str,
        model: BaseModel,
        scope: str = "application",
        schema_version: int = 1,
    ) -> None:
        """Store a strongly-typed model into the settings store.

        Args:
            key: Setting identifier.
            model: Model instance supporting serialization.
            scope: Target hierarchy scope.
            schema_version: Version of the payload schema.
        """
        ...

    def export_preset_file(
        self, preset_name: str, file_path: Path | str | None = None
    ) -> Path:
        """Export current settings to a JSON preset file on disk.

        Args:
            preset_name: Preset label.
            file_path: Optional output file path
                (defaults to data/user/presets/).

        Returns:
            Resolved Path of the written file.
        """
        ...

    def import_preset_file(self, file_path: Path | str) -> None:
        """Import settings from a JSON preset file on disk.

        Args:
            file_path: Path to existing preset JSON file.
        """
        ...

    def load_user_override_file(self, file_path: Path | str | None = None) -> bool:
        """Optionally load user overrides from a JSON file.

        Args:
            file_path: Optional path to user override file
                (defaults to configured user_override_file or None).

        Returns:
            True if file existed and was loaded; False otherwise.
        """
        ...


class JobService(Protocol):
    """Manage the durable state and lifecycle transitions of background jobs."""

    def create_job(self, definition: JobDefinition) -> JobReceipt:
        """Register a new job in the durable ledger with queued state.

        Args:
            definition: Immutable job specification.

        Returns:
            Initial JobReceipt.
        """
        ...

    def get_job(self, job_id: str) -> JobDefinition | None:
        """Retrieve the immutable job definition by ID.

        Args:
            job_id: Unique job identifier.

        Returns:
            JobDefinition or None if not found.
        """
        ...

    def get_receipt(self, job_id: str) -> JobReceipt | None:
        """Retrieve the latest receipt and progress snapshot for a job.

        Args:
            job_id: Unique job identifier.

        Returns:
            JobReceipt or None if not found.
        """
        ...

    def transition_state(
        self,
        job_id: str,
        from_state: JobState | None,
        to_state: JobState,
        details: dict[str, Any] | None = None,
    ) -> bool:
        """Perform a compare-and-swap state transition and record an audit event.

        Args:
            job_id: Target job ID.
            from_state: Expected current state (or None to bypass CAS guard).
            to_state: Target destination state.
            details: Optional transition metadata.

        Returns:
            True if transition succeeded; False if CAS state mismatched.
        """
        ...

    def record_progress(self, progress: JobProgress) -> None:
        """Update job progression percentage, message, and checkpoint.

        Args:
            progress: Progress details emitted by worker.
        """
        ...

    def create_attempt(self, job_id: str, worker_id: str) -> JobAttempt:
        """Record the start of a worker execution attempt.

        Args:
            job_id: Target job ID.
            worker_id: Assigned worker identity.

        Returns:
            Created JobAttempt instance.
        """
        ...

    def update_heartbeat(self, attempt_id: str) -> None:
        """Refresh the liveness heartbeat timestamp on an attempt.

        Args:
            attempt_id: Active attempt ID.
        """
        ...

    def list_attempts(self, job_id: str) -> tuple[JobAttempt, ...]:
        """Return all historical attempts for a job.

        Args:
            job_id: Target job ID.

        Returns:
            Ordered tuple of JobAttempt records.
        """
        ...

    def list_events(self, job_id: str) -> tuple[JobEvent, ...]:
        """Return all audit events associated with a job.

        Args:
            job_id: Target job ID.

        Returns:
            Ordered tuple of JobEvent records.
        """
        ...

    def recover_orphans(self, interrupted_reason: str = "Coordinator restart") -> int:
        """Mark all uncompleted attempts from previous runs as interrupted.

        Args:
            interrupted_reason: Audit note for the recovery action.

        Returns:
            Number of recovered orphan jobs.
        """
        ...


class SchedulerService(Protocol):
    """Coordinate bounded job dispatch, concurrency limits, and supervision."""

    def submit_job(self, definition: JobDefinition) -> JobReceipt:
        """Submit a job to the scheduling queue.

        Args:
            definition: Immutable job definition.

        Returns:
            Receipt confirming admission.
        """
        ...

    def pause_job(self, job_id: str) -> bool:
        """Request a cooperative pause on an active or queued job.

        Args:
            job_id: Target job ID.

        Returns:
            True if pause initiated successfully.
        """
        ...

    def resume_job(self, job_id: str) -> bool:
        """Resume a paused job from its latest checkpoint.

        Args:
            job_id: Target job ID.

        Returns:
            True if resume initiated successfully.
        """
        ...

    def cancel_job(self, job_id: str) -> bool:
        """Request cooperative cancellation of a job.

        Args:
            job_id: Target job ID.

        Returns:
            True if cancellation initiated.
        """
        ...

    def get_queue_stats(self) -> QueueStats:
        """Return current metrics on queued, active, and paused jobs.

        Returns:
            QueueStats snapshot.
        """
        ...

    def dispatch_next(self) -> JobDefinition | None:
        """Select and dequeue the highest-priority pending job.

        Returns:
            JobDefinition or None if queue is empty or at capacity.
        """
        ...


class NotificationService(Protocol):
    """Multi-channel user notification dispatch and human-in-the-loop pause gates."""

    def send_notification(
        self,
        channel: NotificationChannel,
        recipient: str,
        title: str,
        body: str,
        *,
        require_user_action: bool = False,
        metadata: dict[str, Any] | None = None,
    ) -> NotificationReceipt:
        """Dispatch a notification message across a targeted channel.

        Args:
            channel: Target medium (email, sound, webhook).
            recipient: Destination address, URL, or chime sound name.
            title: Short subject title.
            body: Full message text (secret-safe).
            require_user_action: Whether this triggers a workflow pause gate.
            metadata: Optional contextual parameters.

        Returns:
            Delivery receipt.
        """
        ...

    def send_templated_notification(
        self,
        channel: NotificationChannel,
        recipient: str,
        template_name: str,
        values: Mapping[str, object],
        *,
        require_user_action: bool = False,
        metadata: dict[str, Any] | None = None,
    ) -> NotificationReceipt:
        """Dispatch a notification rendered from a named template.

        Args:
            channel: Target medium (email, sound, webhook, telegram, desktop).
            recipient: Destination address, chat ID, or target.
            template_name: Registered template identifier.
            values: Values used to populate template placeholders.
            require_user_action: Whether this triggers a workflow pause gate.
            metadata: Optional contextual parameters.

        Returns:
            Delivery receipt.
        """
        ...

    def wait_for_user_action(self, prompt_id: str, timeout_seconds: float) -> bool:
        """Block or poll until the user unpauses a prompt gate.

        Args:
            prompt_id: Unique pause gate identifier.
            timeout_seconds: Maximum time to wait.

        Returns:
            True if approved/unpaused by user; False on timeout.
        """
        ...

    def resume_user_action(self, prompt_id: str) -> None:
        """Unpause an active user action gate.

        Args:
            prompt_id: Gate identifier to resolve.
        """
        ...


class DiagnosticsService(Protocol):
    """System health monitoring, logs, and throughput calibration."""

    def get_health(self) -> SystemHealth:
        """Compute and return an active snapshot of system health.

        Returns:
            SystemHealth telemetry snapshot.
        """
        ...

    def run_benchmark(
        self,
        tick_count: int = 1000,
        core_mode: CpuCoreMode = CpuCoreMode.MAX_PERFORMANCE,
    ) -> BenchmarkResult:
        """Execute a hardware throughput benchmark to calibrate time-per-tick.

        Args:
            tick_count: Number of synthetic ticks to compute.
            core_mode: CPU core strategy to evaluate.

        Returns:
            Empirical BenchmarkResult.
        """
        ...

    def get_last_benchmark(self) -> BenchmarkResult | None:
        """Return the most recently calibrated benchmark result, if any.

        Returns:
            BenchmarkResult or None.
        """
        ...


class ResourceGovernorService(Protocol):
    """Finite resource allocation governor and memory protection watchdog."""

    def get_quota(self) -> ResourceQuota:
        """Return the active admission quotas and thresholds.

        Returns:
            Current ResourceQuota.
        """
        ...

    def check_admission(self, required_threads: int, required_memory_mb: int) -> bool:
        """Evaluate if resources are available to admit new work.

        Args:
            required_threads: Number of CPU threads requested.
            required_memory_mb: Estimated memory required.

        Returns:
            True if admitted; False if capacity is exceeded.
        """
        ...

    def get_usage(self) -> ResourceUsage:
        """Sample current CPU and memory utilization.

        Returns:
            ResourceUsage snapshot.
        """
        ...

    def cleanup_memory(self) -> int:
        """Explicitly invoke garbage collection and return freed object count.

        Returns:
            Number of unreachable objects collected.
        """
        ...

    def is_watchdog_tripped(self) -> bool:
        """Return whether RAM usage has breached the 85% safety threshold.

        Returns:
            True if memory watchdog is currently tripped.
        """
        ...


class RemoteWorkerService(Protocol):
    """Manage distributed remote worker nodes and job leasing."""

    def register_node(self, node_info: GridNodeInfo) -> None:
        """Register or update a compute node in the grid ledger.

        Args:
            node_info: Remote worker node details.
        """
        ...

    def heartbeat_node(self, node_id: str) -> bool:
        """Record a heartbeat signal from a worker node.

        Args:
            node_id: Reporting node ID.

        Returns:
            True if recognized; False if node is unknown.
        """
        ...

    def acquire_lease(
        self, node_id: str, job_id: str, duration_seconds: float
    ) -> WorkerLease:
        """Lease a job to an online worker node for a fixed duration.

        Args:
            node_id: Target node.
            job_id: Target job.
            duration_seconds: Lease validity period.

        Returns:
            WorkerLease instance.
        """
        ...

    def release_lease(self, lease_id: str, completed: bool) -> None:
        """Release or settle an active job lease.

        Args:
            lease_id: Lease identifier.
            completed: Whether the leased job completed successfully.
        """
        ...

    def list_nodes(self) -> tuple[GridNodeInfo, ...]:
        """List all known worker nodes and their status.

        Returns:
            Tuple of registered nodes.
        """
        ...

    def reconcile_expired_leases(self) -> int:
        """Revoke all expired leases and reset associated jobs.

        Returns:
            Count of reclaimed leases.
        """
        ...


class PluginHostService(Protocol):
    """Host and execute sandboxed plugins and extensions."""

    def load_plugin(self, manifest: PluginManifest, code: str) -> PluginInstance:
        """Validate, sandbox, and load an extension plugin.

        Args:
            manifest: Metadata and permission declarations.
            code: Python code string.

        Returns:
            Loaded PluginInstance.
        """
        ...

    def unload_plugin(self, plugin_id: str) -> bool:
        """Unload and teardown a registered plugin.

        Args:
            plugin_id: Target plugin ID.

        Returns:
            True if successfully removed.
        """
        ...

    def list_plugins(self) -> tuple[PluginInstance, ...]:
        """Return all loaded plugins.

        Returns:
            Tuple of loaded PluginInstance records.
        """
        ...

    def execute_plugin_hook(
        self, plugin_id: str, hook_name: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute a designated hook inside the plugin sandbox.

        Args:
            plugin_id: Target plugin ID.
            hook_name: Function/hook symbol name.
            payload: Input parameter payload.

        Returns:
            Output returned by the plugin hook.
        """
        ...


class WorkspacePersistenceService(Protocol):
    """Direct SQLite transactional persistence boundary for the workspace domain."""

    def get_schema_version(self) -> int:
        """Return the PRAGMA user_version persisted in the database."""
        ...

    # Settings Persistence
    def load_all_settings(self) -> list[tuple[str, str, str, int, str]]:
        """Load all persisted settings records.

        Returns tuples of (scope, key, value_json, version, updated_at).
        """
        ...

    def save_setting(
        self,
        scope: str,
        key: str,
        value_json: str,
        schema_version: int,
        updated_at_utc: str,
    ) -> None:
        """Upsert a setting entry inside a transaction."""
        ...

    def delete_setting(self, scope: str, key: str) -> bool:
        """Delete a setting entry."""
        ...

    # Jobs Persistence
    def insert_job(
        self,
        *,
        job_id: str,
        group_id: str | None,
        operation: str,
        state: str,
        priority: int,
        resource_class: str,
        config_hash: str,
        payload_json: str,
        created_at_utc: str,
        event_id: str,
        event_details_json: str,
    ) -> None:
        """Register a new job and append initial audit event."""
        ...

    def get_job_record(self, job_id: str) -> tuple[Any, ...] | None:
        """Retrieve durable job tuple by ID."""
        ...

    def transition_job_state_cas(
        self,
        *,
        job_id: str,
        expected_state: str | None,
        new_state: str,
        updated_at_utc: str,
        event_id: str,
        event_details_json: str,
        attempt_id: str | None = None,
        terminal_reason: str | None = None,
    ) -> bool:
        """Perform a single-statement atomic compare-and-swap transition."""
        ...

    def update_job_progress(
        self,
        job_id: str,
        progress_percent: float,
        progress_message: str,
        checkpoint_json: str | None = None,
    ) -> bool:
        """Update job execution progress."""
        ...

    def create_job_attempt(
        self,
        *,
        attempt_id: str,
        job_id: str,
        worker_id: str,
        sequence: int,
        state: str,
        created_at_utc: str,
    ) -> None:
        """Record a new worker attempt for a job."""
        ...

    def update_attempt_heartbeat(self, attempt_id: str, heartbeat_at_utc: str) -> bool:
        """Record worker attempt heartbeat timestamp."""
        ...

    def update_attempt_checkpoint(
        self, attempt_id: str, heartbeat_at_utc: str, checkpoint_json: str
    ) -> bool:
        """Update durable attempt checkpoint state."""
        ...

    def complete_job_attempt(
        self,
        *,
        attempt_id: str,
        state: str,
        completed_at_utc: str,
    ) -> bool:
        """Mark attempt as completed, failed, or cancelled."""
        ...

    def get_job_attempts(self, job_id: str) -> list[tuple[Any, ...]]:
        """Retrieve attempt history for a job ordered by attempt sequence."""
        ...

    def get_job_events(self, job_id: str) -> list[tuple[Any, ...]]:
        """Retrieve immutable audit events for a job."""
        ...

    def record_job_event(
        self,
        *,
        event_id: str,
        job_id: str,
        attempt_id: str | None,
        from_state: str | None,
        to_state: str,
        details_json: str,
        created_at_utc: str,
    ) -> None:
        """Record an immutable audit event for a job."""
        ...

    def recover_orphaned_jobs(
        self,
        *,
        running_states: tuple[str, ...],
        interrupted_state: str,
        interrupted_reason: str,
        now_utc: str,
    ) -> int:
        """Identify uncompleted jobs from previous runs and mark them interrupted."""
        ...

    # Grid Nodes & Leases Persistence
    def upsert_grid_node(
        self,
        *,
        node_id: str,
        host: str,
        port: int,
        cores: int,
        memory_mb: int,
        state: str,
        last_heartbeat_utc: str,
    ) -> None:
        """Register or update a remote worker node in the grid ledger."""
        ...

    def get_grid_nodes(self) -> list[tuple[Any, ...]]:
        """List all registered grid compute nodes."""
        ...

    def get_grid_node(self, node_id: str) -> tuple[Any, ...] | None:
        """Retrieve a specific grid node."""
        ...

    def update_node_heartbeat(
        self, node_id: str, heartbeat_at_utc: str, state: str | None = None
    ) -> bool:
        """Record heartbeat and optionally update node status."""
        ...

    def acquire_grid_lease(
        self,
        *,
        lease_id: str,
        node_id: str,
        job_id: str,
        acquired_at_utc: str,
        expires_at_utc: str,
        state: str,
        now_utc: str,
    ) -> bool:
        """Atomically check for conflicting active leases and insert new lease."""
        ...

    def release_grid_lease(
        self, lease_id: str, completed_state: str, now_utc: str
    ) -> bool:
        """Mark lease as completed/released and restore node to online."""
        ...

    def get_active_leases(self) -> list[tuple[Any, ...]]:
        """List all active leases."""
        ...

    def reconcile_expired_leases(self, now_utc: str) -> list[tuple[str, str]]:
        """Mark expired leases and reconcile node statuses.

        Returns list of (lease_id, job_id).
        """
        ...

    def count_active_jobs(self) -> int:
        """Count the number of currently running jobs in the ledger."""
        ...


# ---------------------------------------------------------------------------
# Versioned Capability Tokens
# ---------------------------------------------------------------------------

WORKSPACE_SETTINGS: Capability[SettingsService] = Capability("workspace.settings@1")
WORKSPACE_JOBS: Capability[JobService] = Capability("workspace.jobs@1")
WORKSPACE_SCHEDULER: Capability[SchedulerService] = Capability("workspace.scheduler@1")
WORKSPACE_NOTIFICATIONS: Capability[NotificationService] = Capability(
    "workspace.notifications@1"
)
WORKSPACE_DIAGNOSTICS: Capability[DiagnosticsService] = Capability(
    "workspace.diagnostics@1"
)
WORKSPACE_WORKERS: Capability[RemoteWorkerService] = Capability("workspace.workers@1")
WORKSPACE_RESOURCES: Capability[ResourceGovernorService] = Capability(
    "workspace.resources@1"
)
WORKSPACE_PLUGINS: Capability[PluginHostService] = Capability("workspace.plugins@1")
WORKSPACE_PERSISTENCE: Capability[WorkspacePersistenceService] = Capability(
    "persistence.workspace@1"
)

__all__ = [
    "WORKSPACE_DIAGNOSTICS",
    "WORKSPACE_JOBS",
    "WORKSPACE_NOTIFICATIONS",
    "WORKSPACE_PERSISTENCE",
    "WORKSPACE_PLUGINS",
    "WORKSPACE_RESOURCES",
    "WORKSPACE_SCHEDULER",
    "WORKSPACE_SETTINGS",
    "WORKSPACE_WORKERS",
    "BenchmarkResult",
    "ConfigurationError",
    "CpuCoreMode",
    "DiagnosticsService",
    "GridNodeInfo",
    "GridNodeState",
    "InvalidJobTransitionError",
    "JobAttempt",
    "JobDefinition",
    "JobEvent",
    "JobNotFoundError",
    "JobProgress",
    "JobReceipt",
    "JobService",
    "JobState",
    "LeaseState",
    "MemoryWatchdogTrippedError",
    "NotificationChannel",
    "NotificationMessage",
    "NotificationReceipt",
    "NotificationService",
    "PluginError",
    "PluginHostService",
    "PluginInstance",
    "PluginManifest",
    "PluginSecurityError",
    "QueueStats",
    "RemoteWorkerService",
    "ResourceGovernorService",
    "ResourceQuota",
    "ResourceQuotaExceededError",
    "ResourceUsage",
    "SchedulerService",
    "SettingsEntry",
    "SettingsScope",
    "SettingsService",
    "SettingsSnapshot",
    "SettingsValidationError",
    "SystemHealth",
    "WorkerLease",
    "WorkerLeaseError",
    "WorkspaceError",
    "WorkspacePersistenceService",
]
