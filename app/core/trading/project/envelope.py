"""Native project envelope container reader and writer for HaruQuantAI (.haru)."""

from __future__ import annotations

import contextlib
import json
import re
import uuid
import zipfile
import zlib
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType
from typing import Any

from app.core.host.logging import get_logger
from app.core.lib.errors import DomainError, JSONValue, copy_json

logger = get_logger(__name__)

_TASK_MEMBER_RE = re.compile(r"^tasks/[A-Za-z0-9_-]+\.json$")
_REQUIRED_MANIFEST_FIELDS = ("app_name", "schema_version", "project_id", "name")


def _validate_member_name(name: str) -> None:
    """Validate archive member name for admission and path safety."""
    if "\\" in name or name.startswith("/") or (len(name) > 1 and name[1] == ":"):
        logger.warning("Rejected unsafe path syntax in container member: %s", name)
        raise DomainError(
            code="INVALID_PROJECT_CONTAINER",
            message="Invalid project container",
            details={"member": name},
        )

    parts = name.split("/")
    if any(part in (".", "..") for part in parts):
        logger.warning("Rejected traversal path in container member: %s", name)
        raise DomainError(
            code="INVALID_PROJECT_CONTAINER",
            message="Invalid project container",
            details={"member": name},
        )

    if name in ("manifest.json", "project.json"):
        return

    if _TASK_MEMBER_RE.fullmatch(name):
        return

    logger.warning("Rejected unauthorized container member: %s", name)
    raise DomainError(
        code="INVALID_PROJECT_CONTAINER",
        message="Invalid project container",
        details={"member": name},
    )


def _validate_task_key(key: str) -> None:
    """Validate that a task dictionary key conforms to tasks/<task_id>.json."""
    if "\\" in key or key.startswith("/") or (len(key) > 1 and key[1] == ":"):
        logger.warning("Rejected unsafe path in task key: %s", key)
        raise DomainError(
            code="INVALID_PROJECT_CONTAINER",
            message="Invalid project container",
            details={"member": key},
        )

    parts = key.split("/")
    if any(part in (".", "..") for part in parts):
        logger.warning("Rejected traversal in task key: %s", key)
        raise DomainError(
            code="INVALID_PROJECT_CONTAINER",
            message="Invalid project container",
            details={"member": key},
        )

    if not _TASK_MEMBER_RE.fullmatch(key):
        logger.warning("Rejected task key not matching pattern: %s", key)
        raise DomainError(
            code="INVALID_PROJECT_CONTAINER",
            message="Invalid project container",
            details={"member": key},
        )


def _validate_manifest(manifest: Any) -> None:
    """Validate manifest dictionary shape and required fields."""
    if not isinstance(manifest, dict):
        logger.warning("Manifest is not a dictionary")
        raise DomainError(
            code="INVALID_PROJECT_CONTAINER",
            message="Invalid project container",
            details={"member": "manifest.json"},
        )

    for req_field in _REQUIRED_MANIFEST_FIELDS:
        if req_field not in manifest:
            logger.warning("Missing required field %s in manifest", req_field)
            raise DomainError(
                code="INVALID_PROJECT_CONTAINER",
                message="Invalid project container",
                details={"member": "manifest.json"},
            )
        val = manifest[req_field]
        if req_field == "schema_version":
            if not isinstance(val, int) or isinstance(val, bool):
                logger.warning("Invalid schema_version type in manifest: %r", val)
                raise DomainError(
                    code="INVALID_PROJECT_CONTAINER",
                    message="Invalid project container",
                    details={"member": "manifest.json"},
                )
        elif not isinstance(val, str):
            logger.warning("Invalid string field %s in manifest: %r", req_field, val)
            raise DomainError(
                code="INVALID_PROJECT_CONTAINER",
                message="Invalid project container",
                details={"member": "manifest.json"},
            )


def _validate_tasks(tasks: Any) -> None:
    """Validate tasks mapping entries."""
    if not isinstance(tasks, Mapping):
        logger.warning("Tasks property is not a Mapping")
        raise DomainError(
            code="INVALID_PROJECT_CONTAINER",
            message="Invalid project container",
            details={"member": ""},
        )

    for task_name, task_data in tasks.items():
        if not isinstance(task_name, str):
            logger.warning("Task name is not a string: %r", task_name)
            raise DomainError(
                code="INVALID_PROJECT_CONTAINER",
                message="Invalid project container",
                details={"member": str(task_name)},
            )
        _validate_task_key(task_name)
        if not isinstance(task_data, dict):
            logger.warning("Task data for %s is not a dict", task_name)
            raise DomainError(
                code="INVALID_PROJECT_CONTAINER",
                message="Invalid project container",
                details={"member": task_name},
            )


def _validate_envelope(
    manifest: Any,
    project: Any,
    tasks: Any,
) -> None:
    """Validate in-memory envelope structures."""
    _validate_manifest(manifest)

    if not isinstance(project, dict):
        logger.warning("Project property is not a dictionary")
        raise DomainError(
            code="INVALID_PROJECT_CONTAINER",
            message="Invalid project container",
            details={"member": "project.json"},
        )

    _validate_tasks(tasks)


@dataclass(frozen=True, slots=True)
class ProjectEnvelope:
    """Immutable envelope representing a native .haru project container."""

    manifest: dict[str, JSONValue]
    project: dict[str, JSONValue]
    tasks: Mapping[str, dict[str, JSONValue]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Initialize envelope and enforce immutability and schema invariants."""
        _validate_envelope(self.manifest, self.project, self.tasks)
        copied_manifest = copy_json(self.manifest)
        copied_project = copy_json(self.project)
        if isinstance(copied_manifest, dict):
            object.__setattr__(self, "manifest", copied_manifest)
        if isinstance(copied_project, dict):
            object.__setattr__(self, "project", copied_project)

        detached_tasks: dict[str, dict[str, JSONValue]] = {}
        for k, v in self.tasks.items():
            copied_v = copy_json(v)
            if isinstance(copied_v, dict):
                detached_tasks[k] = copied_v
        object.__setattr__(self, "tasks", MappingProxyType(detached_tasks))


def _read_and_parse_member(
    zf: zipfile.ZipFile,
    info: zipfile.ZipInfo,
) -> dict[str, JSONValue]:
    """Read, decode, and parse a single member as UTF-8 JSON dict."""
    filename = getattr(info, "orig_filename", info.filename)
    try:
        raw = zf.read(info)
    except (zipfile.BadZipFile, zlib.error) as err:
        logger.warning(
            "Failed decompression for container member %s: %s", filename, err
        )
        raise DomainError(
            code="INVALID_PROJECT_CONTAINER",
            message="Invalid project container",
            details={"member": filename},
        ) from err

    if not raw or not raw.strip():
        logger.warning("Empty member payload in project container: %s", filename)
        raise DomainError(
            code="INVALID_PROJECT_CONTAINER",
            message="Invalid project container",
            details={"member": filename},
        )

    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as err:
        logger.warning("Non-UTF-8 payload in project container member %s", filename)
        raise DomainError(
            code="INVALID_PROJECT_CONTAINER",
            message="Invalid project container",
            details={"member": filename},
        ) from err

    try:
        data = json.loads(text)
    except json.JSONDecodeError as err:
        logger.warning(
            "Malformed JSON in project container member %s: %s", filename, err
        )
        raise DomainError(
            code="INVALID_PROJECT_CONTAINER",
            message="Invalid project container",
            details={"member": filename},
        ) from err

    if not isinstance(data, dict):
        logger.warning("Member %s JSON root is not an object", filename)
        raise DomainError(
            code="INVALID_PROJECT_CONTAINER",
            message="Invalid project container",
            details={"member": filename},
        )

    return data


def _read_archive_members(
    zf: zipfile.ZipFile,
) -> tuple[
    dict[str, JSONValue],
    dict[str, JSONValue],
    dict[str, dict[str, JSONValue]],
]:
    """Read, validate, and unpack all members from a project archive."""
    seen_names: set[str] = set()
    manifest_data: dict[str, JSONValue] | None = None
    project_data: dict[str, JSONValue] | None = None
    task_data: dict[str, dict[str, JSONValue]] = {}

    for info in zf.infolist():
        raw_name = getattr(info, "orig_filename", info.filename)
        filename = info.filename
        if info.is_dir() or filename.endswith("/"):
            logger.warning("Directory entry in container: %s", raw_name)
            raise DomainError(
                code="INVALID_PROJECT_CONTAINER",
                message="Invalid project container",
                details={"member": raw_name},
            )

        if raw_name in seen_names or filename in seen_names:
            logger.warning("Duplicate entry in container: %s", raw_name)
            raise DomainError(
                code="INVALID_PROJECT_CONTAINER",
                message="Invalid project container",
                details={"member": raw_name},
            )
        seen_names.add(raw_name)
        seen_names.add(filename)

        _validate_member_name(raw_name)
        data = _read_and_parse_member(zf, info)

        if filename == "manifest.json":
            manifest_data = data
        elif filename == "project.json":
            project_data = data
        else:
            task_data[filename] = data

    if manifest_data is None:
        logger.warning("Missing manifest.json in project container")
        raise DomainError(
            code="INVALID_PROJECT_CONTAINER",
            message="Invalid project container",
            details={"member": "manifest.json"},
        )
    if project_data is None:
        logger.warning("Missing project.json in project container")
        raise DomainError(
            code="INVALID_PROJECT_CONTAINER",
            message="Invalid project container",
            details={"member": "project.json"},
        )

    return manifest_data, project_data, task_data


def read_project_envelope(path: Path | str) -> ProjectEnvelope:
    """Read and validate a .haru project archive from disk.

    Args:
        path: Path to the .haru ZIP archive.

    Returns:
        Validated ProjectEnvelope containing parsed JSON dictionaries.

    Raises:
        DomainError(code='PROJECT_FILE_NOT_FOUND'): If the file does not exist.
        DomainError(code='INVALID_PROJECT_CONTAINER'): If archive or members are bad.
        OSError: If an unexpected operating system I/O error occurs.
    """
    path_obj = Path(path)
    if not path_obj.exists() or not path_obj.is_file():
        logger.warning("Project file not found: %s", path_obj)
        raise DomainError(
            code="PROJECT_FILE_NOT_FOUND",
            message="Project file not found",
        )

    if not zipfile.is_zipfile(path_obj):
        logger.warning("File is not a valid zip container: %s", path_obj)
        raise DomainError(
            code="INVALID_PROJECT_CONTAINER",
            message="Invalid project container",
            details={"member": ""},
        )

    try:
        with zipfile.ZipFile(path_obj, mode="r") as zf:
            manifest, project, tasks = _read_archive_members(zf)
            logger.info(
                "Successfully read project envelope from %s (project_id=%s, tasks=%d)",
                path_obj,
                manifest.get("project_id"),
                len(tasks),
            )
            return ProjectEnvelope(
                manifest=manifest,
                project=project,
                tasks=tasks,
            )

    except (zipfile.BadZipFile, zipfile.LargeZipFile) as err:
        logger.warning("Bad zip archive in %s: %s", path_obj, err)
        raise DomainError(
            code="INVALID_PROJECT_CONTAINER",
            message="Invalid project container",
            details={"member": ""},
        ) from err


def write_project_envelope(path: Path | str, envelope: ProjectEnvelope) -> None:
    """Validate and atomically write a ProjectEnvelope to a .haru ZIP archive.

    Args:
        path: Destination file path.
        envelope: ProjectEnvelope to serialize and persist.

    Raises:
        DomainError(code='INVALID_PROJECT_CONTAINER'): If envelope validation fails.
        OSError: If destination parent directory does not exist or atomic write fails.
    """
    path_obj = Path(path)
    _validate_envelope(envelope.manifest, envelope.project, envelope.tasks)

    parent_dir = path_obj.parent if str(path_obj.parent) else Path()
    if not parent_dir.is_dir():
        logger.error("Destination parent directory does not exist: %s", parent_dir)
        raise FileNotFoundError(f"Parent directory does not exist: {parent_dir}")

    temp_path = parent_dir / f"{path_obj.name}.tmp.{uuid.uuid4().hex}"
    logger.debug(
        "Preparing atomic write of project envelope %s via temporary file %s",
        path_obj,
        temp_path,
    )

    try:
        with zipfile.ZipFile(
            temp_path, mode="w", compression=zipfile.ZIP_DEFLATED
        ) as zf:
            m_bytes = json.dumps(
                envelope.manifest, indent=2, ensure_ascii=False
            ).encode("utf-8")
            zf.writestr("manifest.json", m_bytes)

            p_bytes = json.dumps(envelope.project, indent=2, ensure_ascii=False).encode(
                "utf-8"
            )
            zf.writestr("project.json", p_bytes)

            for key in sorted(envelope.tasks.keys()):
                t_bytes = json.dumps(
                    envelope.tasks[key], indent=2, ensure_ascii=False
                ).encode("utf-8")
                zf.writestr(key, t_bytes)

        temp_path.replace(path_obj)
        logger.info(
            "Successfully wrote project envelope to %s (project_id=%s, tasks=%d)",
            path_obj,
            envelope.manifest.get("project_id"),
            len(envelope.tasks),
        )
    except Exception:
        logger.exception(
            "Failed writing project envelope to %s; cleaning up temporary file %s",
            path_obj,
            temp_path,
        )
        if temp_path.exists():
            with contextlib.suppress(OSError):
                temp_path.unlink()
        raise
