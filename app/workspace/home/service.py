"""Business logic service for the AppHome workspace.

Description:
    Provides HomeService coordinating application landing metadata, host
    environment diagnostics, recent project discovery, optimistic-concurrency
    project/settings/notes persistence, template application, resource
    resolution, engine controls via JobManager, and dashboard strategy
    rankings from ResultStore.

Purpose:
    FEAT-HOME-SERVICE: Unified workspace service for landing, shared project
    workflows, and execution telemetry.

Key Capabilities:
    - FR-home-landing: Aggregate and return recent projects from .haru project
      files and metadata.
    - FR-home-system-about: Return application metadata, versioning, runtime,
      and license status from host settings or runtime.
    - FR-home-updates-check: Query release information; safely report
      unavailable when unconfigured.
    - FR-home-host-diagnostics: Inspect database accessibility, memory
      headroom, and workspace directories.
    - FR-home-project-persistence: Load and save .haru project documents with
      dedicated revision concurrency checking and path containment.
    - FR-home-notes-persistence: Load and save project notes with revision
      conflict prevention.
    - FR-home-template-manager: Apply simple/advanced templates with atomic
      rollback on validation failure and revision check.
    - FR-home-resource-resolver: Check and resolve symbol/dataset references
      against DataCatalog.
    - FR-home-engine-controls: Manage execution lifecycle (start, pause,
      resume, stop) through Core JobManager.
    - FR-home-dashboard-ranking: Query and rank strategy candidates from
      ResultStore by sample type and metrics.

Python API Usage:
    from app.workspace.home.service import HomeService
    service = HomeService(persistence=gateway)
    index = service.get_recent_projects()

CLI Usage:
    uv run python -m pytest tests/workspace/home/test_project_actions.py -q
"""

from __future__ import annotations

import functools
import re
import sys
import threading
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import psutil

from app.core.data.catalog import DataCatalog, DatasetRef
from app.core.host.logging import get_logger
from app.core.host.persistence import HostPersistence
from app.core.host.settings import SettingsManager
from app.core.jobs.manager import JobManager, JobRecord, JobState
from app.core.lib.errors import DomainError, copy_json
from app.core.trading.project.contracts import (
    ProjectDocument,
    ProjectManifest,
    TaskDocument,
)
from app.core.trading.project.envelope import read_project_envelope
from app.core.trading.project.store import ProjectStore
from app.core.trading.results.store import ResultStore
from app.workspace.home.execution import ProjectExecutor
from app.workspace.home.project_repository import (
    HomeProjectRepository,
    _project_file_lock,
    update_project_metadata,
)
from app.workspace.home.result_projection import ResultProjection
from app.workspace.home.settings_contracts import require_revision, validate_settings

logger = get_logger(__name__)

_MAX_ANALYSIS_TABS = 32
_MAX_ANALYSIS_NAME = 80

PROJECT_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]+$")
ALLOWED_METRICS = {
    "net_profit",
    "sharpe_ratio",
    "drawdown",
    "profit_factor",
    "win_rate",
    "trades_count",
}
ALLOWED_SAMPLE_TYPES = {"ALL", "IS", "OOS"}


@dataclass(frozen=True, slots=True)
class RecentProjectItem:
    """Project summary descriptor for the Home landing list."""

    id: str
    name: str
    workspace: str
    last_activity: str

    def to_dict(self) -> dict[str, str]:
        """Convert descriptor to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "workspace": self.workspace,
            "last_activity": self.last_activity,
        }


@dataclass(frozen=True, slots=True)
class LicenseInfo:
    """License status model."""

    state: str
    reason: str

    def to_dict(self) -> dict[str, str]:
        """Convert to dictionary."""
        return {"state": self.state, "reason": self.reason}


@dataclass(frozen=True, slots=True)
class AboutInfoPayload:
    """Host environment and application metadata."""

    application: str
    version: str
    build_timestamp: str
    runtime: str
    metadata_source: str
    license: LicenseInfo

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary matching homeClient.ts AboutInfo."""
        return {
            "application": self.application,
            "version": self.version,
            "build_timestamp": self.build_timestamp,
            "runtime": self.runtime,
            "metadata_source": self.metadata_source,
            "license": self.license.to_dict(),
        }


@dataclass(frozen=True, slots=True)
class ReleaseInfoPayload:
    """Release information status."""

    state: str
    reason: str
    current_version: str
    latest_version: str | None
    update_available: bool | None
    changelog: str | None
    release_url: str | None
    published_at: str | None
    checked_at: str

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary matching homeClient.ts ReleaseInfo."""
        return {
            "state": self.state,
            "reason": self.reason,
            "current_version": self.current_version,
            "latest_version": self.latest_version,
            "update_available": self.update_available,
            "changelog": self.changelog,
            "release_url": self.release_url,
            "published_at": self.published_at,
            "checked_at": self.checked_at,
        }


@dataclass(frozen=True, slots=True)
class DiagnosticsInfoPayload:
    """Host diagnostics and hardware resource metrics."""

    status: str
    database: dict[str, Any]
    hardware: dict[str, Any]
    directories: dict[str, str]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary matching homeClient.ts DiagnosticsInfo."""
        return {
            "status": self.status,
            "database": copy_json(self.database),
            "hardware": copy_json(self.hardware),
            "directories": dict(self.directories),
        }


class HomeService:
    """Coordinating service for Home workspace endpoints and project workflows."""

    def __init__(
        self,
        persistence: HostPersistence | None = None,
        *,
        project_store: ProjectStore | None = None,
        result_store: ResultStore | None = None,
        job_manager: JobManager | None = None,
        data_catalog: DataCatalog | None = None,
        settings_manager: SettingsManager | None = None,
        projects_dir: Path | str | None = None,
    ) -> None:
        """Initialize HomeService with persistence and Core capabilities."""
        if persistence is None:
            raise DomainError(
                code="PERSISTENCE_UNAVAILABLE",
                message="Inject the shared host persistence authority",
            )
        self._persistence = persistence
        self._project_store = project_store or HomeProjectRepository()
        self._result_store = result_store or ResultStore(self._persistence)
        self._job_manager = job_manager
        self._data_catalog = data_catalog or DataCatalog(self._persistence)
        self._settings_manager = settings_manager or SettingsManager(self._persistence)
        self._projects_dir = (
            Path(projects_dir).resolve()
            if projects_dir is not None
            else Path("data/projects").resolve()
        )
        self._projects_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._executor = ProjectExecutor(self._data_catalog, self._result_store)

    @property
    def result_store(self) -> ResultStore:
        """Expose the injected result capability for shared workspace projections."""
        return self._result_store

    @property
    def projects_dir(self) -> Path:
        """Return the active projects directory."""
        return self._projects_dir

    @staticmethod
    def _get_project_revision(doc: ProjectDocument) -> int:
        """Extract monotonic edit revision from project metadata."""
        raw = doc.metadata.get("revision")
        if isinstance(raw, int) and not isinstance(raw, bool):
            return raw
        if isinstance(raw, str) and raw.isdigit():
            return int(raw)
        return 1

    def get_recent_projects(self) -> list[dict[str, str]]:
        """Scan projects directory and return projects sorted by activity."""
        logger.info(
            "FR-home-landing: scanning recent projects from %s", self._projects_dir
        )
        projects: list[RecentProjectItem] = []

        if not self._projects_dir.is_dir():
            return []

        for candidate in self._projects_dir.glob("*.haru"):
            try:
                envelope = read_project_envelope(candidate)
                manifest_dict = envelope.manifest
                project_id = str(manifest_dict.get("project_id") or candidate.stem)
                name = str(manifest_dict.get("name") or candidate.stem)
                updated_at = str(
                    manifest_dict.get("updated_at")
                    or manifest_dict.get("created_at")
                    or datetime.now(UTC).isoformat()
                )
                workspace = str(
                    envelope.project.get("target_workspace") or "builder"
                ).lower()
                projects.append(
                    RecentProjectItem(
                        id=project_id,
                        name=name,
                        workspace=workspace,
                        last_activity=updated_at,
                    )
                )
            except (OSError, ValueError, KeyError) as err:
                logger.warning(
                    "FR-home-landing: skipped unreadable project container %s: %s",
                    candidate,
                    err,
                )
                continue

        projects.sort(key=lambda p: p.last_activity, reverse=True)
        return [p.to_dict() for p in projects]

    def get_about_info(self) -> dict[str, Any]:
        """Return host system metadata and license info."""
        logger.info("FR-home-system-about: generating system metadata")
        v = sys.version_info
        py_ver = f"{v.major}.{v.minor}.{v.micro}"

        app_version = "unconfigured"
        build_timestamp = "unversioned"
        license_state = "unconfigured"
        license_reason = "No license configured in host settings"
        metadata_source = "HostSettings"

        try:
            scope = self._settings_manager.get_scope("system")
            if isinstance(scope, dict):
                if "version" in scope:
                    app_version = str(scope["version"])
                if "build_timestamp" in scope:
                    build_timestamp = str(scope["build_timestamp"])
                if "license" in scope and isinstance(scope["license"], dict):
                    lic = scope["license"]
                    license_state = str(lic.get("state", "unconfigured"))
                    license_reason = str(
                        lic.get("reason", "No license configured in host settings")
                    )
        except RuntimeError, KeyError, ValueError, TypeError:
            metadata_source = "unconfigured"

        info = AboutInfoPayload(
            application="HaruQuantAI",
            version=app_version,
            build_timestamp=build_timestamp,
            runtime=f"Python {py_ver} / FastAPI",
            metadata_source=metadata_source,
            license=LicenseInfo(state=license_state, reason=license_reason),
        )
        return info.to_dict()

    def get_release_info(self) -> dict[str, Any]:
        """Return release update information, failing closed when unconfigured."""
        logger.info("FR-home-updates-check: checking release updates")
        now_iso = datetime.now(UTC).isoformat()
        info = ReleaseInfoPayload(
            state="unavailable",
            reason="No release feed configured.",
            current_version="1.0.0",
            latest_version=None,
            update_available=None,
            changelog=None,
            release_url=None,
            published_at=None,
            checked_at=now_iso,
        )
        return info.to_dict()

    def get_host_diagnostics(self) -> dict[str, Any]:
        """Inspect host database, memory headroom, and workspace directories."""
        logger.info("FR-home-host-diagnostics: collecting host diagnostics")
        db_path = getattr(self._persistence, "db_path", None)
        db_path_str = str(db_path) if db_path is not None else ":memory:"
        db_exists = Path(db_path_str).is_file() if db_path_str != ":memory:" else True

        mem = psutil.virtual_memory()
        directories = {
            "projects_dir": str(self._projects_dir),
            "data_root": str(Path("data").resolve()),
            "logs_root": str(Path("logs").resolve()),
        }

        info = DiagnosticsInfoPayload(
            status="OK",
            database={"exists": db_exists, "path": db_path_str, "error": None},
            hardware={
                "ram_total_bytes": mem.total,
                "ram_available_bytes": mem.available,
                "ram_used_pct": float(mem.percent),
            },
            directories=directories,
        )
        return info.to_dict()

    def _resolve_project_file(self, project_id: str) -> Path:
        """Find the .haru file for a given project ID with strict containment."""
        clean_id = project_id.strip()
        if not clean_id or not PROJECT_ID_PATTERN.match(clean_id):
            logger.warning(
                "FR-home-project-persistence: invalid project identifier '%s'",
                clean_id,
            )
            raise DomainError(
                code="INVALID_PROJECT_ID",
                message=f"Project identifier '{clean_id}' contains invalid characters.",
                details={"project_id": clean_id},
            )

        projects_dir_resolved = self._projects_dir.resolve()
        direct_path = (self._projects_dir / f"{clean_id}.haru").resolve()
        if not direct_path.is_relative_to(projects_dir_resolved):
            logger.warning(
                "FR-home-project-persistence: path traversal attempt '%s'", clean_id
            )
            raise DomainError(
                code="INVALID_PROJECT_ID",
                message=f"Project identifier '{clean_id}' escapes allowed directory.",
                details={"project_id": clean_id},
            )

        if direct_path.is_file():
            if not direct_path.resolve().is_relative_to(projects_dir_resolved):
                raise DomainError(
                    code="INVALID_PROJECT_ID",
                    message="Project file symlink escapes allowed directory.",
                    details={"project_id": clean_id},
                )
            return direct_path

        if projects_dir_resolved.is_dir():
            for candidate in self._projects_dir.glob("*.haru"):
                cand_resolved = candidate.resolve()
                if not cand_resolved.is_relative_to(projects_dir_resolved):
                    continue
                try:
                    env = read_project_envelope(candidate)
                    if env.manifest.get("project_id") == clean_id:
                        return candidate
                except OSError, ValueError, KeyError:
                    continue

        logger.warning(
            "FR-home-project-persistence: project %s not found in %s",
            clean_id,
            self._projects_dir,
        )
        raise DomainError(
            code="PROJECT_FILE_NOT_FOUND",
            message=f"Project '{clean_id}' was not found.",
            details={"project_id": clean_id},
        )

    def load_project(self, project_id: str) -> dict[str, Any]:
        """Load and return project document details by project ID."""
        logger.info("FR-home-project-persistence: loading project %s", project_id)
        path = self._resolve_project_file(project_id)
        doc = self._project_store.load_project(path)
        current_rev = self._get_project_revision(doc)
        return {
            "manifest": doc.manifest.to_dict(),
            "pipeline": list(doc.pipeline),
            "databanks": dict(doc.databanks),
            "metadata": dict(doc.metadata),
            "tasks": {t_id: t.to_dict() for t_id, t in doc.tasks.items()},
            "revision": current_rev,
        }

    def save_project_settings(
        self,
        project_id: str,
        task_id: str,
        settings: Mapping[str, Any],
        expected_revision: int,
    ) -> dict[str, Any]:
        """Update task settings in a project with revision conflict detection."""
        logger.info(
            "FR-home-project-persistence: saving settings for project %s, task %s",
            project_id,
            task_id,
        )
        require_revision(expected_revision)
        path = self._resolve_project_file(project_id)
        with self._lock, _project_file_lock(path):
            doc = self._project_store.load_project(path)
            current_revision = self._get_project_revision(doc)

            if current_revision != expected_revision:
                logger.warning(
                    "FR-home-project-persistence: revision conflict for project %s: "
                    "expected %d, found %d",
                    project_id,
                    expected_revision,
                    current_revision,
                )
                raise DomainError(
                    code="CONFLICT",
                    message=(
                        "Project revision mismatch; please reload current "
                        "project state."
                    ),
                    details={
                        "expected_revision": expected_revision,
                        "current_revision": current_revision,
                    },
                )

            current_task = doc.tasks.get(task_id)
            if current_task is None:
                raise DomainError(
                    code="TASK_NOT_FOUND", message="Task is not in this project"
                )

            updated_settings: dict[str, Any] = dict(current_task.settings)
            updated_settings.update(dict(settings))
            validate_settings(updated_settings)

            updated_task = TaskDocument(
                task_id=current_task.task_id,
                task_type=current_task.task_type,
                name=current_task.name,
                enabled=current_task.enabled,
                databank_target=current_task.databank_target,
                dependencies=current_task.dependencies,
                settings=updated_settings,
            )

            new_tasks = dict(doc.tasks)
            new_tasks[task_id] = updated_task
            new_metadata = dict(doc.metadata)
            new_metadata["revision"] = current_revision + 1

            new_manifest = ProjectManifest(
                project_id=doc.manifest.project_id,
                name=doc.manifest.name,
                app_name=doc.manifest.app_name,
                schema_version=doc.manifest.schema_version,
                description=doc.manifest.description,
                created_at=doc.manifest.created_at,
                updated_at=datetime.now(UTC).isoformat(),
            )

            updated_doc = ProjectDocument(
                manifest=new_manifest,
                pipeline=doc.pipeline,
                databanks=doc.databanks,
                tasks=new_tasks,
                metadata=new_metadata,
            )

            self._project_store.save_project(path, updated_doc)
            logger.info(
                "FR-home-project-persistence: saved settings revision %d",
                new_metadata["revision"],
            )
            return {
                "project_id": project_id,
                "task_id": task_id,
                "revision": new_metadata["revision"],
                "status": "saved",
            }

    def save_project_notes(
        self,
        project_id: str,
        notes: str,
        expected_revision: int,
    ) -> dict[str, Any]:
        """Save project notes with optimistic revision checking."""
        path = self._resolve_project_file(project_id)
        with self._lock:
            revision = update_project_metadata(
                self._project_store, path, expected_revision, {"notes": notes}
            )
        logger.info(
            "FR-home-notes-persistence: acknowledged saved revision %d", revision
        )
        return {
            "project_id": project_id,
            "notes": notes,
            "revision": revision,
            "status": "saved",
        }

    def save_project_analysis(
        self,
        project_id: str,
        names: list[str],
        expected_revision: int,
    ) -> dict[str, Any]:
        """Persist shared analysis tab definitions with revision conflict checks."""
        if (
            len(names) > _MAX_ANALYSIS_TABS
            or len(set(names)) != len(names)
            or any(not name.strip() or len(name) > _MAX_ANALYSIS_NAME for name in names)
        ):
            raise DomainError(
                code="INVALID_ANALYSIS",
                message="Analysis names must be unique, nonempty and bounded",
            )
        path = self._resolve_project_file(project_id)
        with self._lock:
            revision = update_project_metadata(
                self._project_store,
                path,
                expected_revision,
                {"analysis_tabs": list(names)},
            )
        logger.info(
            "FR-home-analysis-persistence: acknowledged saved analysis revision %d",
            revision,
        )
        return {
            "project_id": project_id,
            "analysis_tabs": names,
            "revision": revision,
            "status": "saved",
        }

    def apply_template(
        self,
        project_id: str,
        task_id: str,
        strategy_type: str,
        expected_revision: int,
    ) -> dict[str, Any]:
        """Apply a strategy template with validation and atomic rollback on failure."""
        logger.info(
            "FR-home-template-manager: applying template %s to project %s",
            strategy_type,
            project_id,
        )
        self._resolve_project_file(project_id)
        try:
            templates = self._settings_manager.get_scope("project_templates")
        except (KeyError, RuntimeError) as error:
            raise DomainError(
                code="TEMPLATES_UNAVAILABLE",
                message="No template documents are configured",
            ) from error
        template = templates.get(strategy_type)
        if not isinstance(template, dict) or not isinstance(
            template.get("settings"), dict
        ):
            raise DomainError(
                code="INVALID_TEMPLATE",
                message="Select a configured native template document",
            )
        template_config = template["settings"]
        validate_settings(template_config)
        require_revision(expected_revision)
        path = self._resolve_project_file(project_id)
        with self._lock, _project_file_lock(path):
            doc = self._project_store.load_project(path)
            current_revision = self._get_project_revision(doc)

            if current_revision != expected_revision:
                raise DomainError(
                    code="CONFLICT",
                    message=(
                        "Project revision mismatch; please reload current "
                        "project state."
                    ),
                    details={
                        "expected_revision": expected_revision,
                        "current_revision": current_revision,
                    },
                )

            task = doc.tasks.get(task_id)
            if task is None or template.get("task_type") != task.task_type:
                raise DomainError(
                    code="INVALID_TEMPLATE",
                    message="Template task type does not match saved task",
                )
            merged_settings = copy_json(dict(task.settings))
            if isinstance(merged_settings, dict):
                merged_settings["template"] = strategy_type
                merged_settings.update(template_config)
                validate_settings(merged_settings)

            updated_task = TaskDocument(
                task_id=task.task_id,
                task_type=task.task_type,
                name=task.name,
                enabled=task.enabled,
                databank_target=task.databank_target,
                dependencies=task.dependencies,
                settings=merged_settings if isinstance(merged_settings, dict) else {},
            )

            new_tasks = dict(doc.tasks)
            new_tasks[task_id] = updated_task
            new_metadata = dict(doc.metadata)
            new_metadata["revision"] = current_revision + 1

            new_manifest = ProjectManifest(
                project_id=doc.manifest.project_id,
                name=doc.manifest.name,
                app_name=doc.manifest.app_name,
                schema_version=doc.manifest.schema_version,
                description=doc.manifest.description,
                created_at=doc.manifest.created_at,
                updated_at=datetime.now(UTC).isoformat(),
            )

            updated_doc = ProjectDocument(
                manifest=new_manifest,
                pipeline=doc.pipeline,
                databanks=doc.databanks,
                tasks=new_tasks,
                metadata=new_metadata,
            )

            self._project_store.save_project(path, updated_doc)
            logger.info(
                "FR-home-template-manager: applied template %s successfully",
                strategy_type,
            )
            return {
                "project_id": project_id,
                "task_id": task_id,
                "template": strategy_type,
                "revision": new_metadata["revision"],
            }

    def resolve_resources(
        self,
        project_id: str,
        resolutions: Mapping[str, str],
        expected_revision: int,
    ) -> dict[str, Any]:
        """Validate and resolve resource dependencies for a project."""
        logger.info(
            "FR-home-resource-resolver: resolving resources for project %s", project_id
        )
        path = self._resolve_project_file(project_id)
        require_revision(expected_revision)
        resolved_count = 0
        with self._lock, _project_file_lock(path):
            doc = self._project_store.load_project(path)
            current_revision = self._get_project_revision(doc)

            if current_revision != expected_revision:
                raise DomainError(
                    code="CONFLICT",
                    message=(
                        "Project revision mismatch; please reload current "
                        "project state."
                    ),
                    details={
                        "expected_revision": expected_revision,
                        "current_revision": current_revision,
                    },
                )

            declared = doc.metadata.get("resources")
            if not isinstance(declared, dict) or any(
                key not in declared for key in resolutions
            ):
                raise DomainError(
                    code="RESOURCE_NOT_OWNED",
                    message="Resource is not declared by this project",
                )
            for res_key, target_sym in resolutions.items():
                ds_info = self._data_catalog.get_dataset_info(
                    DatasetRef(symbol=str(target_sym))
                )
                if ds_info is None:
                    logger.warning(
                        "FR-home-resource-resolver: symbol %s not found in DataCatalog",
                        target_sym,
                    )
                    raise DomainError(
                        code="DATASET_NOT_FOUND",
                        message=(
                            f"Dataset for symbol '{target_sym}' was not found in "
                            "DataCatalog."
                        ),
                        details={"symbol": target_sym, "resource_key": res_key},
                    )

            new_metadata = dict(doc.metadata)
            existing_res = new_metadata.get("resources")
            res_meta: dict[str, Any] = (
                dict(existing_res) if isinstance(existing_res, dict) else {}
            )
            for res_key, target_sym in resolutions.items():
                res_meta[str(res_key)] = str(target_sym)
                resolved_count += 1
            new_metadata["resources"] = res_meta
            new_metadata["revision"] = current_revision + 1

            new_manifest = ProjectManifest(
                project_id=doc.manifest.project_id,
                name=doc.manifest.name,
                app_name=doc.manifest.app_name,
                schema_version=doc.manifest.schema_version,
                description=doc.manifest.description,
                created_at=doc.manifest.created_at,
                updated_at=datetime.now(UTC).isoformat(),
            )

            updated_doc = ProjectDocument(
                manifest=new_manifest,
                pipeline=doc.pipeline,
                databanks=doc.databanks,
                tasks=doc.tasks,
                metadata=new_metadata,
            )
            self._project_store.save_project(path, updated_doc)
            logger.info(
                "FR-home-resource-resolver: resolved %d resources", resolved_count
            )
            return {
                "project_id": project_id,
                "resolved_count": resolved_count,
                "revision": new_metadata["revision"],
                "status": "resolved",
            }

    def engine_action(
        self,
        project_id: str,
        action: str,
        task_id: str | None = None,
        expected_revision: int | None = None,
        job_id: str | None = None,
    ) -> dict[str, Any]:
        """Apply a lifecycle action to the selected project/job identity."""
        path = self._resolve_project_file(project_id)
        manager = self._job_manager
        if manager is None:
            raise DomainError(
                code="JOB_MANAGER_UNAVAILABLE",
                message="JobManager service is unavailable",
            )
        owner = f"home_engine:{project_id}"
        logger.info(
            "FR-home-engine-controls: action %s for project %s", action, project_id
        )
        current: JobRecord | None
        with self._lock:
            if action == "start":
                active = [
                    j
                    for j in manager.list_jobs(limit=1000)
                    if j.owner == owner
                    and j.status in (JobState.RUNNING, JobState.PAUSED, JobState.QUEUED)
                ]
                if active:
                    raise DomainError(
                        code="ALREADY_RUNNING", message="Project has an active job"
                    )
                with _project_file_lock(path):
                    project = self._project_store.load_project(path)
                    snapshot = self._executor.prepare(
                        project, task_id, expected_revision
                    )
                    record = manager.submit_job(
                        functools.partial(self._executor.run, snapshot=snapshot),
                        kind="engine",
                        owner=owner,
                        executor_kind="thread",
                        pass_context=True,
                    )
                current = manager.get_job(record.job_id) or record
            elif action in {"pause", "resume", "stop"}:
                current = manager.get_job(job_id) if job_id else None
                if current is None or current.owner != owner:
                    raise DomainError(
                        code="JOB_NOT_FOUND",
                        message="Select a job owned by this project",
                    )
                operation = {
                    "pause": manager.pause_job,
                    "resume": manager.resume_job,
                    "stop": manager.cancel_job,
                }[action]
                if not operation(current.job_id):
                    raise DomainError(
                        code="INVALID_JOB_STATE", message="Job rejected this transition"
                    )
                current = manager.get_job(current.job_id) or current
            else:
                raise DomainError(
                    code="INVALID_ENGINE_ACTION", message="Unsupported engine action"
                )
            return {
                "project_id": project_id,
                "action": action,
                "task_id": task_id,
                "job_id": current.job_id,
                "status": current.status,
            }

    def get_engine_status(
        self,
        project_id: str,
        job_id: str | None = None,
    ) -> dict[str, Any]:
        """Return actual Core job state, including reload recovery and failures."""
        self._resolve_project_file(project_id)
        logger.info("FR-home-engine-controls: status for project %s", project_id)
        owner = f"home_engine:{project_id}"
        manager = self._job_manager
        current = None
        if manager is not None:
            if job_id:
                current = manager.get_job(job_id)
                if current is None or current.owner != owner:
                    raise DomainError(
                        code="JOB_NOT_FOUND", message="Job is outside this project"
                    )
            else:
                jobs = [j for j in manager.list_jobs(limit=1000) if j.owner == owner]
                latest = max(jobs, key=lambda j: j.submitted_at_utc, default=None)
                current = manager.get_job(latest.job_id) if latest else None
        if current is None:
            return {
                "project_id": project_id,
                "job_id": None,
                "status": "IDLE",
                "progress": 0.0,
                "message": "No engine run",
                "result": None,
            }
        return {
            "project_id": project_id,
            "job_id": current.job_id,
            "status": current.status,
            "progress": current.progress,
            "message": current.message,
            "result": current.result,
        }

    def get_dashboard_results(
        self,
        project_id: str,
        databank_id: str = "Results",
        sample_type: str = "ALL",
        metric: str = "net_profit",
        limit: int = 10,
    ) -> dict[str, Any]:
        """Rank the complete stored result collection for an owned databank."""
        project = self._project_store.load_project(
            self._resolve_project_file(project_id)
        )
        return ResultProjection(self._result_store).leaderboard(
            project, databank_id, sample_type.upper(), metric.lower(), limit
        )

    def get_result(self, project_id: str, result_id: str) -> dict[str, Any]:
        """Inspect one persisted result with project databank ownership checks."""
        project = self._project_store.load_project(
            self._resolve_project_file(project_id)
        )
        return ResultProjection(self._result_store).detail(project, result_id)
