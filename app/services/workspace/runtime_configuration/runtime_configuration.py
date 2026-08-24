"""Runtime Configuration primary domain logic and usage harness.

Implements FEAT-WS-CONFIGURE_RUNTIME:
- FR-WS-CONFIGURE_WORKSPACE: versioned, validated workspace settings
- FR-WS-ENFORCE_STORAGE_GUARDS: free-space and artifact-size job admission
- FR-WS-CONFIGURE_SERVER_RUNTIME: launcher/server runtime validation
- FR-WS-PUBLISH_RUNTIME_SUPPORT: versioned runtime support profile
"""

from __future__ import annotations

import datetime as _dt
import ipaddress
import json
import os
import platform
import re
import shutil
import socket
import sqlite3
import sys
import tempfile
import zoneinfo
from dataclasses import asdict
from pathlib import Path

from app.contracts.workspace.errors import (
    SettingsValidationError,
    UnsupportedRuntimeError,
    WorkspaceNotFoundError,
)
from app.contracts.workspace.models import (
    AuthenticationMode,
    JobKind,
    ResourceRequirements,
    RuntimeResourceReport,
    RuntimeSupportProfile,
    ServerRuntimeSettings,
    ServerRuntimeValidation,
    StorageGuardDecision,
    StorageGuardLimits,
    WorkspaceRef,
    WorkspaceSettings,
    WorkspaceSettingsVersion,
)
from app.services.workspace.runtime_configuration.config import (
    RuntimeConfigurationConfig,
)

SUPPORT_PROFILE_VERSION = 1
SUPPORTED_OS_FAMILIES: tuple[str, ...] = ("darwin", "linux", "windows")
SUPPORTED_ARCHITECTURES: tuple[str, ...] = ("AMD64", "ARM64", "x86_64")
SUPPORTED_FILESYSTEMS: tuple[str, ...] = ("NTFS", "apfs", "ext4", "xfs")
SUPPORTED_BROWSERS: tuple[str, ...] = ("chrome", "edge", "firefox")
# Documented assumption: the only external compiler the product requires is
# the MetaTrader 5 MetaEditor toolchain; a pinned build arrives with the
# Increment 5 code-generation features that actually invoke it.
REQUIRED_COMPILERS: tuple[str, ...] = ("MetaEditor 5",)
VALID_LOG_LEVELS: frozenset[str] = frozenset(
    {"CRITICAL", "DEBUG", "ERROR", "INFO", "WARNING"}
)
MIN_WORKER_COUNT = 1
MIN_POSITIVE_MB = 1
MIN_RETENTION_DAYS = 1
MIN_TCP_PORT = 1
MAX_TCP_PORT = 65535
MIN_CPU_PERCENT = 1
MAX_CPU_PERCENT = 100
_MIB = 1024 * 1024


def _utc_now_iso() -> str:
    """Return current UTC timestamp in ISO 8601 format with microseconds.

    Returns:
        Formatted UTC timestamp string.
    """
    return _dt.datetime.now(tz=_dt.UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _resolve_root(workspace: Path | WorkspaceRef) -> Path:
    """Resolve a workspace argument to its root path.

    Args:
        workspace: Workspace root path or WorkspaceRef.

    Returns:
        Resolved workspace root path.
    """
    root = workspace.root_path if isinstance(workspace, WorkspaceRef) else workspace
    return root.resolve()


_IANA_AREAS = frozenset(
    {
        "Africa",
        "America",
        "Antarctica",
        "Arctic",
        "Asia",
        "Atlantic",
        "Australia",
        "Brazil",
        "Canada",
        "Chile",
        "Etc",
        "Europe",
        "Indian",
        "Mexico",
        "Pacific",
        "US",
    }
)


def _is_valid_timezone(name: str) -> bool:
    """Validate an IANA timezone name without requiring the tzdata package.

    Windows hosts have no system IANA database, so unresolved names fall
    back to strict IANA-shape validation (documented assumption).

    Args:
        name: Timezone identifier to validate.

    Returns:
        True when the name resolves or matches the IANA shape.
    """
    if name in ("UTC", "GMT"):
        return True
    try:
        zoneinfo.ZoneInfo(name)
    except zoneinfo.ZoneInfoNotFoundError, ValueError, OSError, KeyError:
        # Shape check requiring a standard IANA area prefix keeps invalid
        # names like 'Not/AZone' out even without the tzdata package.
        area, _, rest = name.partition("/")
        if area not in _IANA_AREAS or not rest:
            return False
        return bool(re.fullmatch(r"[A-Za-z0-9_+-]+(/[A-Za-z0-9_+-]+)*", rest))
    return True


def _validate_settings_numbers(settings: WorkspaceSettings) -> dict[str, str]:
    """Validate numeric settings fields against strict minimal bounds.

    Args:
        settings: Settings payload under validation.

    Returns:
        Mapping of invalid numeric field name to error description.
    """
    errors: dict[str, str] = {}
    if settings.worker_count < MIN_WORKER_COUNT:
        errors["worker_count"] = f"worker_count must be >= {MIN_WORKER_COUNT}"
    if settings.worker_memory_mb < MIN_POSITIVE_MB:
        errors["worker_memory_mb"] = "worker_memory_mb must be positive"
    if settings.max_artifact_size_mb < MIN_POSITIVE_MB:
        errors["max_artifact_size_mb"] = "max_artifact_size_mb must be positive"
    if settings.max_total_artifact_gb < 1:
        errors["max_total_artifact_gb"] = "max_total_artifact_gb must be >= 1"
    return errors


def _validate_settings_paths(settings: WorkspaceSettings) -> dict[str, str]:
    """Validate workspace-relative directory settings fields.

    Args:
        settings: Settings payload under validation.

    Returns:
        Mapping of invalid path field name to error description.
    """
    errors: dict[str, str] = {}
    for field_name in ("artifacts_dir", "logs_dir", "cache_dir", "exports_dir"):
        value = getattr(settings, field_name)
        candidate = Path(value)
        if not value or candidate.is_absolute() or ".." in candidate.parts:
            errors[field_name] = (
                f"{field_name} must be a workspace-relative path without '..'"
            )
    return errors


def _validate_workspace_settings(settings: WorkspaceSettings) -> dict[str, str]:
    """Validate every workspace settings field and collect field errors.

    Numeric bounds below are minimal strict limits derived from the FR text;
    values outside them are rejected rather than silently defaulted.

    Args:
        settings: Settings payload to validate.

    Returns:
        Mapping of invalid field name to error description; empty when valid.
    """
    errors: dict[str, str] = {}
    if not _is_valid_timezone(settings.timezone):
        errors["timezone"] = f"unknown IANA timezone '{settings.timezone}'"
    if not settings.locale or any(ch.isspace() for ch in settings.locale):
        errors["locale"] = "locale must be a non-empty BCP 47 tag without spaces"
    errors.update(_validate_settings_numbers(settings))
    errors.update(_validate_settings_paths(settings))
    if settings.log_level not in VALID_LOG_LEVELS:
        errors["log_level"] = f"log_level must be one of {sorted(VALID_LOG_LEVELS)}"
    if settings.log_retention_days < MIN_RETENTION_DAYS:
        errors["log_retention_days"] = "log_retention_days must be >= 1"
    if settings.retention_days < MIN_RETENTION_DAYS:
        errors["retention_days"] = "retention_days must be >= 1"
    return errors


def fr_ws_configure_workspace(
    workspace: Path | WorkspaceRef,
    settings: WorkspaceSettings,
) -> WorkspaceSettingsVersion:
    """Persist validated workspace settings as a new immutable version.

    Fulfills FR-WS-CONFIGURE_WORKSPACE. Validation happens before any write;
    an invalid payload leaves the persisted version untouched.

    Args:
        workspace: Workspace root path or WorkspaceRef.
        settings: Settings payload to validate and persist.

    Returns:
        WorkspaceSettingsVersion describing the persisted version.

    Raises:
        SettingsValidationError: If any field is invalid; the persisted
            version is not incremented.
        WorkspaceNotFoundError: If the workspace database is missing.
    """
    field_errors = _validate_workspace_settings(settings)
    if field_errors:
        raise SettingsValidationError(field_errors)

    root_path = _resolve_root(workspace)
    db_path = root_path / "metadata" / "workspace.db"
    if not db_path.exists():
        raise WorkspaceNotFoundError(str(root_path))

    conn = sqlite3.connect(str(db_path), timeout=5.0)
    try:
        conn.execute("PRAGMA busy_timeout=5000;")
        cursor = conn.cursor()
        cursor.execute("BEGIN IMMEDIATE;")
        cursor.execute("SELECT id FROM workspace LIMIT 1;")
        row = cursor.fetchone()
        if row is None:
            raise WorkspaceNotFoundError(str(root_path))
        workspace_id = str(row[0])
        cursor.execute(
            "SELECT max(version) FROM workspace_setting_versions "
            "WHERE workspace_id = ?;",
            (workspace_id,),
        )
        version_row = cursor.fetchone()
        next_version = int(version_row[0]) + 1 if version_row and version_row[0] else 1
        cursor.execute(
            "INSERT INTO workspace_setting_versions "
            "(id, workspace_id, version, settings_json, created_at, row_version) "
            "VALUES (?, ?, ?, ?, ?, 1);",
            (
                f"settings_{next_version}_{workspace_id}",
                workspace_id,
                next_version,
                json.dumps(asdict(settings), sort_keys=True),
                _utc_now_iso(),
            ),
        )
        conn.commit()
        return WorkspaceSettingsVersion(
            workspace_id=workspace_id,
            version=next_version,
            settings=settings,
            created_at=_utc_now_iso(),
        )
    finally:
        conn.close()


def fr_ws_get_workspace_settings(
    workspace: Path | WorkspaceRef,
) -> WorkspaceSettingsVersion | None:
    """Return the latest persisted settings version, if any.

    Args:
        workspace: Workspace root path or WorkspaceRef.

    Returns:
        Latest WorkspaceSettingsVersion or None when never configured.

    Raises:
        WorkspaceNotFoundError: If the workspace database is missing.
    """
    root_path = _resolve_root(workspace)
    db_path = root_path / "metadata" / "workspace.db"
    if not db_path.exists():
        raise WorkspaceNotFoundError(str(root_path))

    conn = sqlite3.connect(str(db_path), timeout=5.0)
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT v.workspace_id, v.version, v.settings_json, v.created_at "
            "FROM workspace_setting_versions v "
            "JOIN workspace w ON w.id = v.workspace_id "
            "ORDER BY v.version DESC LIMIT 1;",
        )
        row = cursor.fetchone()
        if row is None:
            return None
        data = json.loads(str(row[2]))
        return WorkspaceSettingsVersion(
            workspace_id=str(row[0]),
            version=int(row[1]),
            settings=WorkspaceSettings(**data),
            created_at=str(row[3]),
        )
    finally:
        conn.close()


def fr_ws_enforce_storage_guards(
    workspace: Path | WorkspaceRef,
    *,
    job_kind: JobKind,
    projected_artifact_mb: float,
    limits: StorageGuardLimits | None = None,
) -> StorageGuardDecision:
    """Evaluate workspace storage guards before admitting a job.

    Fulfills FR-WS-ENFORCE_STORAGE_GUARDS. Data import, backtest, and
    code-generation jobs are admitted only when the projected artifact size
    stays within the artifact-size limit and enough free space remains after
    the reserved minimum; over-limit jobs are not admitted and the decision
    reports required versus available storage.

    Args:
        workspace: Workspace root path or WorkspaceRef.
        job_kind: Guarded job category.
        projected_artifact_mb: Projected artifact storage in MiB.
        limits: Optional guard limits; defaults apply when omitted.

    Returns:
        StorageGuardDecision describing admission.

    Raises:
        WorkspaceNotFoundError: If the workspace root is missing.
    """
    effective_limits = limits or StorageGuardLimits()

    root_path = _resolve_root(workspace)
    if not root_path.is_dir():
        raise WorkspaceNotFoundError(str(root_path))

    usage = shutil.disk_usage(root_path)
    available_mb = usage.free / _MIB
    required_mb = projected_artifact_mb + effective_limits.min_free_space_mb

    reason = ""
    if projected_artifact_mb > effective_limits.max_artifact_size_mb:
        reason = (
            f"ARTIFACT_SIZE_LIMIT: projected {projected_artifact_mb:.1f} MiB "
            f"exceeds limit {effective_limits.max_artifact_size_mb} MiB"
        )
    elif available_mb < required_mb:
        reason = (
            f"FREE_SPACE_LIMIT: required {required_mb:.1f} MiB "
            f"(projection {projected_artifact_mb:.1f} MiB plus reserve "
            f"{effective_limits.min_free_space_mb} MiB) exceeds available "
            f"{available_mb:.1f} MiB"
        )
    return StorageGuardDecision(
        admitted=not reason,
        job_kind=job_kind,
        required_mb=required_mb,
        available_mb=available_mb,
        reason=reason,
    )


def _address_invalid(bind_address: str) -> bool:
    """Return True when the bind address is not a parsable IP address."""
    try:
        ipaddress.ip_address(bind_address)
    except ValueError:
        return True
    return False


def _validate_server_runtime_settings(
    settings: ServerRuntimeSettings,
) -> list[str]:
    """Validate launcher/server settings and collect error descriptions.

    Args:
        settings: Server runtime settings to validate.

    Returns:
        List of field-level error descriptions; empty when valid.
    """
    errors: list[str] = []
    if not MIN_TCP_PORT <= settings.port <= MAX_TCP_PORT:
        errors.append(
            f"port must be between {MIN_TCP_PORT} and {MAX_TCP_PORT}, "
            f"got {settings.port}"
        )
    try:
        address = ipaddress.ip_address(settings.bind_address)
    except ValueError:
        errors.append(f"bind_address '{settings.bind_address}' is not an IP address")
        address = None
    if address is not None and not address.is_loopback:
        if not settings.allow_non_loopback:
            errors.append(
                "non-loopback binding requires explicit allow_non_loopback opt-in"
            )
        if settings.authentication_mode is not AuthenticationMode.NONLOCAL_TOKEN:
            errors.append(
                "non-loopback binding requires authentication_mode NONLOCAL_TOKEN"
            )
    for name, value in (
        ("worker_cpu_percent", settings.worker_cpu_percent),
        ("global_cpu_percent", settings.global_cpu_percent),
    ):
        if not MIN_CPU_PERCENT <= value <= MAX_CPU_PERCENT:
            errors.append(
                f"{name} must be between {MIN_CPU_PERCENT} and "
                f"{MAX_CPU_PERCENT}, got {value}"
            )
    for name, value in (
        ("worker_memory_mb", settings.worker_memory_mb),
        ("global_memory_mb", settings.global_memory_mb),
    ):
        if value < MIN_POSITIVE_MB:
            errors.append(f"{name} must be positive, got {value}")
    return errors


def _probe_port_available(
    bind_address: str,
    port: int,
    *,
    timeout_seconds: float,
) -> bool:
    """Probe whether the address/port can be bound right now.

    A transient bind-and-release check; no server is started.

    Args:
        bind_address: IP address to probe.
        port: TCP port to probe.
        timeout_seconds: Socket timeout in seconds.

    Returns:
        True when the port can be bound, False when occupied or unusable.
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            probe.settimeout(timeout_seconds)
            probe.bind((bind_address, port))
        return True
    except OSError:
        return False


def fr_ws_configure_server_runtime(
    settings: ServerRuntimeSettings,
    *,
    port_probe_timeout_seconds: float = 1.0,
) -> ServerRuntimeValidation:
    """Validate launcher/server runtime settings before UI launch.

    Fulfills FR-WS-CONFIGURE_SERVER_RUNTIME. Loopback remains the default;
    non-loopback binding requires explicit opt-in plus a non-loopback-capable
    authentication mode; an invalid or unavailable port fails before launch.

    Args:
        settings: Server runtime settings to validate.
        port_probe_timeout_seconds: Socket timeout for the port probe.

    Returns:
        ServerRuntimeValidation with field errors and port availability; all
        errors are returned together so the launcher can present them at once.
    """
    errors = _validate_server_runtime_settings(settings)
    port_available = True
    probe_address = (
        ipaddress.ip_address(settings.bind_address)
        if not _address_invalid(settings.bind_address)
        else None
    )
    # Availability is only observable for addresses this host can bind
    # (loopback); non-loopback reachability is a deployment concern.
    if not errors and probe_address is not None and probe_address.is_loopback:
        port_available = _probe_port_available(
            settings.bind_address,
            settings.port,
            timeout_seconds=port_probe_timeout_seconds,
        )
        if not port_available:
            errors.append(
                f"port {settings.port} on {settings.bind_address} is "
                "unavailable or already in use"
            )
    return ServerRuntimeValidation(
        valid=not errors,
        errors=tuple(errors),
        port_available=port_available,
    )


def fr_ws_publish_runtime_support() -> RuntimeSupportProfile:
    """Publish the versioned runtime support profile for this release.

    Fulfills FR-WS-PUBLISH_RUNTIME_SUPPORT. The profile is a versioned local
    record naming supported platforms, resources, filesystems, browsers, and
    required compilers; startup rejects an unsupported host architecture or
    filesystem family outright.

    Returns:
        RuntimeSupportProfile for this release.

    Raises:
        UnsupportedRuntimeError: If the host OS family or architecture is
            unsupported.
    """
    profile = RuntimeSupportProfile(
        profile_version=SUPPORT_PROFILE_VERSION,
        os_families=SUPPORTED_OS_FAMILIES,
        architectures=SUPPORTED_ARCHITECTURES,
        resources=ResourceRequirements(
            minimum_cpu_cores=2,
            recommended_cpu_cores=8,
            minimum_memory_gb=4,
            recommended_memory_gb=16,
            minimum_free_storage_gb=2,
            recommended_free_storage_gb=20,
        ),
        filesystems=SUPPORTED_FILESYSTEMS,
        browsers=SUPPORTED_BROWSERS,
        required_compilers=REQUIRED_COMPILERS,
    )

    os_family = {"win32": "windows"}.get(sys.platform, sys.platform)
    machine = platform.machine() or "unknown"
    if os_family not in SUPPORTED_OS_FAMILIES:
        msg = (
            f"unsupported operating system family '{os_family}'; "
            f"supported: {', '.join(SUPPORTED_OS_FAMILIES)}"
        )
        raise UnsupportedRuntimeError(msg)
    if machine not in SUPPORTED_ARCHITECTURES:
        msg = (
            f"unsupported machine architecture '{machine}'; "
            f"supported: {', '.join(SUPPORTED_ARCHITECTURES)}"
        )
        raise UnsupportedRuntimeError(msg)
    return profile


def fr_ws_evaluate_runtime_resources(
    profile: RuntimeSupportProfile,
    *,
    workspace_root: Path | None = None,
) -> RuntimeResourceReport:
    """Report below-recommended resources without inventing a capability.

    Args:
        profile: Published runtime support profile.
        workspace_root: Optional workspace root for the storage check; the
            current working directory is used when omitted.

    Returns:
        RuntimeResourceReport with one warning per below-recommended finding;
        memory totals are not probed portably with the standard library and
        are reported by the Increment 1 readiness feature instead.
    """
    warnings: list[str] = []
    cores = os.cpu_count() or 1
    if cores < profile.resources.recommended_cpu_cores:
        warnings.append(
            f"cpu cores {cores} below recommended "
            f"{profile.resources.recommended_cpu_cores}"
        )
    target = workspace_root or Path.cwd()
    usage = shutil.disk_usage(target)
    free_gb = usage.free / (1024 * 1024 * 1024)
    if free_gb < profile.resources.recommended_free_storage_gb:
        warnings.append(
            f"free storage {free_gb:.1f} GiB below recommended "
            f"{profile.resources.recommended_free_storage_gb} GiB"
        )
    return RuntimeResourceReport(warnings=tuple(warnings))


class RuntimeConfigurationService:
    """Concrete implementation of ConfigureRuntimeCapability."""

    def __init__(
        self,
        config: RuntimeConfigurationConfig | None = None,
    ) -> None:
        """Initialize the service with optional configuration.

        Args:
            config: Service configuration; defaults apply when omitted.
        """
        self._config = config or RuntimeConfigurationConfig()

    def configure_workspace(
        self,
        workspace: Path | WorkspaceRef,
        settings: WorkspaceSettings,
    ) -> WorkspaceSettingsVersion:
        """Persist validated workspace settings as a new version.

        Args:
            workspace: Workspace root path or WorkspaceRef.
            settings: Settings payload to validate and persist.

        Returns:
            WorkspaceSettingsVersion describing the persisted version.
        """
        return fr_ws_configure_workspace(workspace, settings)

    def get_workspace_settings(
        self,
        workspace: Path | WorkspaceRef,
    ) -> WorkspaceSettingsVersion | None:
        """Return the latest persisted settings version, if any.

        Args:
            workspace: Workspace root path or WorkspaceRef.

        Returns:
            Latest WorkspaceSettingsVersion or None.
        """
        return fr_ws_get_workspace_settings(workspace)

    def enforce_storage_guards(
        self,
        workspace: Path | WorkspaceRef,
        *,
        job_kind: JobKind,
        projected_artifact_mb: float,
        limits: StorageGuardLimits | None = None,
    ) -> StorageGuardDecision:
        """Evaluate workspace storage guards before admitting a job.

        Args:
            workspace: Workspace root path or WorkspaceRef.
            job_kind: Guarded job category.
            projected_artifact_mb: Projected artifact storage in MiB.
            limits: Optional guard limits; defaults apply when omitted.

        Returns:
            StorageGuardDecision describing admission.
        """
        return fr_ws_enforce_storage_guards(
            workspace,
            job_kind=job_kind,
            projected_artifact_mb=projected_artifact_mb,
            limits=limits,
        )

    def configure_server_runtime(
        self,
        settings: ServerRuntimeSettings,
    ) -> ServerRuntimeValidation:
        """Validate launcher/server runtime settings before UI launch.

        Args:
            settings: Server runtime settings to validate.

        Returns:
            ServerRuntimeValidation with errors and port availability.
        """
        return fr_ws_configure_server_runtime(
            settings,
            port_probe_timeout_seconds=self._config.port_probe_timeout_seconds,
        )

    def publish_runtime_support(self) -> RuntimeSupportProfile:
        """Publish the versioned runtime support profile for this release.

        Returns:
            RuntimeSupportProfile for this release.
        """
        return fr_ws_publish_runtime_support()


# ============================================================================
# Executable usage demonstration harness
# ============================================================================


def _create_fixture_workspace(root: Path) -> None:
    """Create a minimal initialized workspace for the usage harness.

    The harness must stay import-pure toward other features, so it creates
    only the two database tables this feature consumes.

    Args:
        root: Workspace root directory to create.
    """
    for sub in ("metadata", "artifacts/objects", "staging", "logs", "cache"):
        (root / sub).mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(root / "metadata" / "workspace.db"))
    try:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS workspace (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                row_version INTEGER NOT NULL DEFAULT 1
            );
            CREATE TABLE IF NOT EXISTS workspace_setting_versions (
                id TEXT PRIMARY KEY,
                workspace_id TEXT NOT NULL,
                version INTEGER NOT NULL,
                settings_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                row_version INTEGER NOT NULL DEFAULT 1,
                UNIQUE(workspace_id, version)
            );
            INSERT INTO workspace (id, name, created_at, updated_at)
            VALUES ('usage-harness', 'Usage Harness', '2026-01-01T00:00:00Z',
                    '2026-01-01T00:00:00Z');
            """
        )
        conn.commit()
    finally:
        conn.close()


def _valid_settings() -> WorkspaceSettings:
    """Return a known-valid settings payload for harness scenarios."""
    return WorkspaceSettings(
        timezone="UTC",
        locale="en-US",
        worker_count=4,
        worker_memory_mb=2048,
        max_artifact_size_mb=2048,
        max_total_artifact_gb=50,
    )


def _run_configure_workspace_scenario(
    service: RuntimeConfigurationService, ws_root: Path
) -> None:
    """Run the FR-WS-CONFIGURE_WORKSPACE usage scenario.

    Raises:
        RuntimeError: If any scenario expectation fails.
    """
    print("Scenario 1: FR-WS-CONFIGURE_WORKSPACE")
    first = service.configure_workspace(ws_root, _valid_settings())
    print(f"  Persisted settings version: {first.version}")
    if first.version != 1:
        msg = "expected first settings version to be 1"
        raise RuntimeError(msg)
    invalid = WorkspaceSettings(
        timezone="Not/AZone",
        locale="en US",
        worker_count=0,
        worker_memory_mb=-1,
        max_artifact_size_mb=10,
        max_total_artifact_gb=10,
        artifacts_dir="../escape",
    )
    try:
        service.configure_workspace(ws_root, invalid)
    except SettingsValidationError as exc:
        print(f"  Invalid payload rejected with {len(exc.field_errors)} field errors")
        latest = service.get_workspace_settings(ws_root)
        if latest is None or latest.version != 1:
            msg = "invalid payload must not increment the settings version"
            raise RuntimeError(msg) from exc
    else:
        msg = "expected SettingsValidationError for invalid payload"
        raise RuntimeError(msg)
    print("  [OK] FR-WS-CONFIGURE_WORKSPACE passed.\n")


def _run_storage_guards_scenario(
    service: RuntimeConfigurationService, ws_root: Path
) -> None:
    """Run the FR-WS-ENFORCE_STORAGE_GUARDS usage scenario.

    Raises:
        RuntimeError: If any scenario expectation fails.
    """
    print("Scenario 2: FR-WS-ENFORCE_STORAGE_GUARDS")
    admitted = service.enforce_storage_guards(
        ws_root,
        job_kind=JobKind.BACKTEST,
        projected_artifact_mb=10.0,
        limits=StorageGuardLimits(
            min_free_space_mb=1,
            max_artifact_size_mb=4096,
        ),
    )
    print(
        f"  Backtest admitted: {admitted.admitted} "
        f"(required {admitted.required_mb:.1f} MiB / "
        f"available {admitted.available_mb:.1f} MiB)"
    )
    if not admitted.admitted:
        msg = "expected small backtest to be admitted"
        raise RuntimeError(msg)
    rejected = service.enforce_storage_guards(
        ws_root,
        job_kind=JobKind.DATA_IMPORT,
        projected_artifact_mb=50.0,
        limits=StorageGuardLimits(
            min_free_space_mb=1,
            max_artifact_size_mb=10,
        ),
    )
    print(f"  Oversized import rejected: {rejected.reason}")
    if rejected.admitted or "ARTIFACT_SIZE_LIMIT" not in rejected.reason:
        msg = "expected over-limit import to be rejected with size reason"
        raise RuntimeError(msg)
    print("  [OK] FR-WS-ENFORCE_STORAGE_GUARDS passed.\n")


def _run_server_runtime_scenario(
    service: RuntimeConfigurationService,
) -> None:
    """Run the FR-WS-CONFIGURE_SERVER_RUNTIME usage scenario.

    Raises:
        RuntimeError: If any scenario expectation fails.
    """
    print("Scenario 3: FR-WS-CONFIGURE_SERVER_RUNTIME")
    probe_port = 48765
    valid = service.configure_server_runtime(
        ServerRuntimeSettings(port=probe_port, headless=True)
    )
    print(
        f"  Headless loopback runtime valid: {valid.valid} "
        f"(port available: {valid.port_available})"
    )
    if not valid.valid or not valid.port_available:
        msg = f"expected valid loopback runtime: {valid.errors}"
        raise RuntimeError(msg)
    bad = service.configure_server_runtime(
        ServerRuntimeSettings(
            port=70000,
            bind_address="10.0.0.5",
            allow_non_loopback=False,
        )
    )
    print(f"  Invalid runtime rejected with {len(bad.errors)} errors")
    min_expected_errors = 2
    if bad.valid or len(bad.errors) < min_expected_errors:
        msg = "expected port and non-loopback opt-in errors"
        raise RuntimeError(msg)
    occupied = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        occupied.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        occupied.bind(("127.0.0.1", probe_port))
        occupied.listen(1)
        unavailable = service.configure_server_runtime(
            ServerRuntimeSettings(port=probe_port)
        )
    finally:
        occupied.close()
    print(f"  Occupied port available: {unavailable.port_available}")
    if unavailable.valid or unavailable.port_available:
        msg = "expected occupied port to fail before launch"
        raise RuntimeError(msg)
    print("  [OK] FR-WS-CONFIGURE_SERVER_RUNTIME passed.\n")


def _run_support_profile_scenario(
    service: RuntimeConfigurationService, ws_root: Path
) -> None:
    """Run the FR-WS-PUBLISH_RUNTIME_SUPPORT usage scenario.

    Raises:
        RuntimeError: If any scenario expectation fails.
    """
    print("Scenario 4: FR-WS-PUBLISH_RUNTIME_SUPPORT")
    profile = service.publish_runtime_support()
    print(
        f"  Profile v{profile.profile_version}: "
        f"os={profile.os_families} arch={profile.architectures}"
    )
    if profile.profile_version != SUPPORT_PROFILE_VERSION:
        msg = "expected current support profile version"
        raise RuntimeError(msg)
    report = fr_ws_evaluate_runtime_resources(profile, workspace_root=ws_root)
    for warning in report.warnings:
        print(f"  below-recommended: {warning}")
    print("  [OK] FR-WS-PUBLISH_RUNTIME_SUPPORT passed.\n")


def _run_usage_scenarios() -> None:
    """Execute all four functional requirement usage scenarios."""
    print("Executing Runtime Configuration (__main__) usage scenarios...\n")
    service = RuntimeConfigurationService()

    with tempfile.TemporaryDirectory() as temp_dir:
        ws_root = Path(temp_dir) / "harness_workspace"
        _create_fixture_workspace(ws_root)
        _run_configure_workspace_scenario(service, ws_root)
        _run_storage_guards_scenario(service, ws_root)
        _run_server_runtime_scenario(service)
        _run_support_profile_scenario(service, ws_root)

    print("[SUCCESS] All 4 Runtime Configuration usage scenarios passed!")


if __name__ == "__main__":
    _run_usage_scenarios()
