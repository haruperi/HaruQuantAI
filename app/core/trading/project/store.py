"""High-level persistence service for native .haru project containers."""

from __future__ import annotations

from pathlib import Path

from app.core.host.logging import get_logger
from app.core.lib.errors import JSONValue, copy_json
from app.core.trading.project.contracts import (
    ProjectDocument,
    ProjectManifest,
    TaskDocument,
)
from app.core.trading.project.envelope import (
    ProjectEnvelope,
    read_project_envelope,
    write_project_envelope,
)

logger = get_logger(__name__)


class ProjectStore:
    """Service for loading and persisting strategy project workspaces."""

    def load_project(self, path: Path | str) -> ProjectDocument:
        """Load and parse a project document from a .haru container archive.

        Args:
            path: Path to the .haru file.

        Returns:
            ProjectDocument with parsed manifest, pipeline, and tasks.

        Raises:
            DomainError(code='PROJECT_FILE_NOT_FOUND'): If project file is missing.
            DomainError(code='INVALID_PROJECT_CONTAINER'): If container is malformed.
        """
        envelope = read_project_envelope(path)
        manifest = ProjectManifest.from_dict(envelope.manifest)

        pipeline_raw = envelope.project.get("pipeline", [])
        pipeline = (
            tuple(str(item) for item in pipeline_raw)
            if isinstance(pipeline_raw, list)
            else ()
        )

        databanks_raw = envelope.project.get("databanks", {})
        databanks = (
            {str(k): str(v) for k, v in databanks_raw.items()}
            if isinstance(databanks_raw, dict)
            else {}
        )

        metadata_raw = envelope.project.get("metadata", {})
        metadata = copy_json(metadata_raw) if isinstance(metadata_raw, dict) else {}

        tasks: dict[str, TaskDocument] = {}
        for member_name, task_dict in envelope.tasks.items():
            task_id = member_name.removeprefix("tasks/").removesuffix(".json")
            tasks[task_id] = TaskDocument.from_dict(task_id, task_dict)

        logger.info(
            "ProjectStore loaded project %s (project_id=%s, tasks=%d) from %s",
            manifest.name,
            manifest.project_id,
            len(tasks),
            path,
        )

        return ProjectDocument(
            manifest=manifest,
            pipeline=pipeline,
            databanks=databanks,
            tasks=tasks,
            metadata=metadata if isinstance(metadata, dict) else {},
        )

    def save_project(self, path: Path | str, project: ProjectDocument) -> None:
        """Serialize and atomically save a project document to a .haru container.

        Args:
            path: Destination file path.
            project: ProjectDocument instance to serialize.

        Raises:
            DomainError(code='INVALID_PROJECT_CONTAINER'): If envelope validation fails.
            OSError: If destination directory does not exist or replacement fails.
        """
        manifest_dict = project.manifest.to_dict()

        pipeline_list: list[JSONValue] = [str(item) for item in project.pipeline]
        databanks_dict: dict[str, JSONValue] = {
            str(k): str(v) for k, v in project.databanks.items()
        }
        metadata_dict = copy_json(dict(project.metadata))

        project_dict: dict[str, JSONValue] = {
            "pipeline": pipeline_list,
            "databanks": databanks_dict,
            "metadata": metadata_dict,
        }

        tasks_dict = {
            f"tasks/{t_id}.json": t_doc.to_dict()
            for t_id, t_doc in sorted(project.tasks.items())
        }

        envelope = ProjectEnvelope(
            manifest=manifest_dict,
            project=project_dict,
            tasks=tasks_dict,
        )

        write_project_envelope(path, envelope)
        logger.info(
            "ProjectStore saved project %s (project_id=%s, tasks=%d) to %s",
            project.manifest.name,
            project.manifest.project_id,
            len(project.tasks),
            path,
        )
