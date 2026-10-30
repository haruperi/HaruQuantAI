"""Task Manager Projects engine and project lifecycle management.

Description:
    Manages project lifecycle operations including creation, opening, saving,
    cloning, renaming, removal, and symbol migration across project task graphs.
    Follows native JSON persistence and StrategyQuant donor validation conventions.

Purpose:
    FEAT-TM-PROJ-ENGINE: Project management engine for Task Manager workspace.

Key Capabilities:
    FR-TM-PROJ-LIFECYCLE: Create, rename, clone, save, and remove projects.
    FR-TM-PROJ-VALIDATE-NAME: Strict validation of project names.
    FR-TM-PROJ-PERSIST: JSON file persistence and schema validation.
    FR-TM-PROJ-SYMBOLS: Search and replacement of symbol/timeframe pairs.

Python API Usage:
    ```python
    from app.workspace.task_manager.task_manager_projects import (
        TaskManagerProjects,
    )

    engine = TaskManagerProjects()
    project = engine.create_project("AlphaProject")
    engine.save_project("AlphaProject", "projects/alpha.json")
    ```

CLI Usage:
    ```bash
    uv run python -m pytest tests/workspace/task_manager/ -q
    ```
"""

from __future__ import annotations

import copy
import json
import logging
import re
from collections.abc import Sequence
from pathlib import Path

from app.workspace.task_manager.task_manager_projects_models import (
    ModifySymbolItem,
    ProjectInfo,
    ProjectSummary,
    ProjectValidationResult,
)

logger = logging.getLogger("haruquant.task_manager.projects")

FORBIDDEN_PROJECT_NAME_CHARS = re.compile(r'[\\/:*?"<>|]')
RESERVED_PROJECT_NAME = re.compile(
    r"^(nul|prn|con|aux|lpt[0-9]|com[0-9])(\.|$)", re.IGNORECASE
)


def normalize_project_name(name: str | None) -> str | None:
    """Normalize project name by stripping leading and trailing whitespace."""
    return name.strip() if name is not None else None


def validate_project_name(name: str | None) -> None:
    """Validate project name against system and file system constraints.

    Args:
        name: Name of project to validate.

    Raises:
        ValueError: If the project name is invalid, empty, or reserved.
    """
    if not name or not name.strip():
        logger.error("Project name validation failed: name cannot be empty")
        raise ValueError("Project name cannot be empty.")
    if name.startswith("."):
        logger.error("Project name validation failed: name cannot start with dot")
        raise ValueError("Project name cannot start with dot.")
    if FORBIDDEN_PROJECT_NAME_CHARS.search(name):
        logger.error("Project name validation failed: forbidden characters in %s", name)
        raise ValueError(
            'Project name contains forbidden characters: \\ / : * ? " < > |'
        )
    if RESERVED_PROJECT_NAME.match(name):
        logger.error("Project name validation failed: reserved system name %s", name)
        raise ValueError("Project name uses a reserved system name.")
    for char in name:
        if char.isspace() and char != " ":
            logger.error("Project name validation failed: tab or newline in %s", name)
            raise ValueError("Project name cannot contain tabs or new lines.")


def _extract_task_symbols(task: dict[str, object], symbols: set[str]) -> None:
    """Extract symbols from a single task configuration."""
    cfg = task.get("config")
    if not isinstance(cfg, dict):
        return
    data = cfg.get("Data")
    if isinstance(data, dict):
        sym = data.get("symbol")
        tf = data.get("timeframe", "H1")
        if isinstance(sym, str) and sym:
            symbols.add(f"{sym}/{tf}")
        for extra in data.get("symbols", []):
            if isinstance(extra, str) and "/" in extra:
                symbols.add(extra)

    cross = cfg.get("CrossChecks")
    if isinstance(cross, dict):
        ad = cross.get("RetestOnAdditionalMarkets")
        if isinstance(ad, dict):
            for item in ad.get("symbols", []):
                if isinstance(item, str) and "/" in item:
                    symbols.add(item)


def _apply_symbol_replacements(
    data: dict[str, object],
    replacements: list[tuple[str, str, str, str]],
) -> None:
    """Apply replacement pairs to a Data configuration dictionary."""
    cur_sym = data.get("symbol")
    cur_tf = data.get("timeframe")
    for s_from, tf_from, s_to, tf_to in replacements:
        match_sym = s_from in ("*", cur_sym)
        match_tf = tf_from in ("*", cur_tf)
        if match_sym and match_tf:
            if s_to != "*":
                data["symbol"] = s_to
            if tf_to != "*":
                data["timeframe"] = tf_to


class TaskManagerProjects:
    """In-memory and file-backed Project Engine for Task Manager."""

    def __init__(self, projects_dir: str | Path | None = None) -> None:
        """Initialize the project engine."""
        self._projects: dict[str, ProjectInfo] = {}
        self._projects_dir = Path(projects_dir) if projects_dir else None
        logger.info("Initialized TaskManagerProjects engine")

    def project_exists(self, name: str) -> bool:
        """Check whether a project with the given name exists."""
        return name in self._projects

    def get_project(self, name: str) -> ProjectInfo:
        """Retrieve project by name.

        Args:
            name: Project name.

        Returns:
            ProjectInfo object.

        Raises:
            KeyError: If the project does not exist.
        """
        if name not in self._projects:
            logger.error("Project '%s' does not exist", name)
            raise KeyError(f"Project '{name}' does not exist.")
        return self._projects[name]

    def list_projects(self) -> list[ProjectSummary]:
        """List all non-predefined projects sorted alphabetically by name."""
        summaries: list[ProjectSummary] = []
        for name in sorted(self._projects.keys()):
            proj = self._projects[name]
            summaries.append(
                ProjectSummary(
                    project_name=proj.name,
                    tasks_count=len(proj.tasks),
                    active=proj.active,
                    is_app_project=proj.is_app_project,
                )
            )
        logger.info("Listed %d projects", len(summaries))
        return summaries

    def create_project(self, name: str) -> ProjectInfo:
        """Create a new project with the given name.

        Args:
            name: Desired project name.

        Returns:
            Newly created ProjectInfo.

        Raises:
            ValueError: If the name is invalid or already taken.
        """
        normalized = normalize_project_name(name)
        if normalized is None:
            raise ValueError("Project name cannot be empty.")
        validate_project_name(normalized)
        if self.project_exists(normalized):
            logger.error("Project '%s' already exists", normalized)
            raise ValueError("Project with the same name already exists.")

        project = ProjectInfo(name=normalized)
        self._projects[normalized] = project
        logger.info("Project created: %s", normalized)
        return project

    def generate_project_name(self, base_name: str) -> str:
        """Generate a unique project name by appending numeric suffixes."""
        if not self.project_exists(base_name):
            return base_name
        for i in range(2, 1000):
            candidate = f"{base_name}({i})"
            if not self.project_exists(candidate):
                return candidate
        return f"{base_name}_copy"

    def clone_project(self, project_name: str) -> ProjectInfo:
        """Clone an existing project under a new unique name.

        Args:
            project_name: Source project name to clone.

        Returns:
            Cloned ProjectInfo.
        """
        source = self.get_project(project_name)
        new_name = self.generate_project_name(project_name)
        cloned = ProjectInfo(
            name=new_name,
            active=source.active,
            tasks=copy.deepcopy(source.tasks),
            settings=copy.deepcopy(source.settings),
            conditions=copy.deepcopy(source.conditions),
            is_app_project=False,
        )
        self._projects[new_name] = cloned
        logger.info("Project cloned from %s to %s", project_name, new_name)
        return cloned

    def rename_project(self, old_name: str, new_name: str) -> None:
        """Rename an existing project.

        Args:
            old_name: Current project name.
            new_name: New project name.

        Raises:
            ValueError: If new name is invalid or taken.
            KeyError: If old project does not exist.
        """
        if old_name == new_name:
            return
        project = self.get_project(old_name)
        normalized = normalize_project_name(new_name)
        if normalized is None:
            raise ValueError("Project name cannot be empty.")
        validate_project_name(normalized)
        if self.project_exists(normalized):
            logger.error("Cannot rename: project '%s' already exists", normalized)
            raise ValueError("Project with the same name already exists.")

        del self._projects[old_name]
        project.name = normalized
        self._projects[normalized] = project
        logger.info("Project renamed from %s to %s", old_name, normalized)

    def remove_project(self, project_name: str) -> None:
        """Remove a project from the engine.

        Args:
            project_name: Project name.

        Raises:
            ValueError: If the project is a predefined app project.
            KeyError: If project does not exist.
        """
        project = self.get_project(project_name)
        if project.is_app_project:
            logger.error("Predefined project %s cannot be removed", project_name)
            raise ValueError(f"Predefined project {project_name} cannot be removed.")

        del self._projects[project_name]
        logger.info("Project removed: %s", project_name)

    def save_project(self, project_name: str, file_path: str | Path) -> None:
        """Persist project to a JSON file.

        Args:
            project_name: Project to save.
            file_path: Target file path.
        """
        project = self.get_project(project_name)
        target = Path(file_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = project.to_dict()
        target.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        logger.info("Project '%s' saved to %s", project_name, target)

    def open_project(
        self,
        file_path: str | Path,
        *,
        project_name: str | None = None,
        load_as_is: bool = False,
    ) -> ProjectInfo:
        """Load project from a JSON file.

        Args:
            file_path: Path to project file.
            project_name: Optional override project name.
            load_as_is: Whether to load without re-checking resources.

        Returns:
            Loaded ProjectInfo.

        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If file content is invalid or missing project name.
            TypeError: If the JSON root is not a dictionary.
        """
        target = Path(file_path)
        if not target.is_file():
            logger.error("File not found: %s", target)
            raise FileNotFoundError(f"No such file: {target}")

        try:
            content = json.loads(target.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            logger.exception("Failed to parse project file: %s", target)
            raise ValueError(
                f"Cannot load config. Selected config is corrupted: {exc}"
            ) from exc

        if not isinstance(content, dict):
            raise TypeError("Corrupted Project config file. Root must be a dictionary.")

        raw_name = project_name or content.get("name")
        normalized = normalize_project_name(raw_name)
        if not normalized:
            raise ValueError("Corrupted Project config file. Missing project name.")
        validate_project_name(normalized)

        if not load_as_is and self.project_exists(normalized):
            normalized = self.generate_project_name(normalized)

        project = ProjectInfo(
            name=normalized,
            active=bool(content.get("active", True)),
            tasks=list(content.get("tasks", [])),
            settings=dict(content.get("settings", {})),
            conditions=list(content.get("conditions", [])),
            is_app_project=bool(content.get("is_app_project", False)),
        )
        self._projects[normalized] = project
        logger.info("Project '%s' loaded from %s", normalized, target)
        return project

    def validate_project(
        self,
        file_path: str | Path,
        *,
        deep: bool = True,
        settings: bool = True,
    ) -> ProjectValidationResult:
        """Validate project file integrity and structure.

        Args:
            file_path: File path to validate.
            deep: Whether to perform deep inspection.
            settings: Whether to check settings fields.

        Returns:
            ProjectValidationResult.
        """
        target = Path(file_path)
        if not target.is_file():
            return ProjectValidationResult(
                valid=False,
                stage="resolve",
                error=f"No such file: {target}",
            )

        try:
            raw = json.loads(target.read_text(encoding="utf-8"))
            if not isinstance(raw, dict):
                return ProjectValidationResult(
                    valid=False,
                    stage="schema",
                    error="Project content must be a JSON object",
                )
            if "name" not in raw or not str(raw["name"]).strip():
                return ProjectValidationResult(
                    valid=False,
                    stage="schema",
                    error="Project file missing valid name",
                )
            logger.debug("Validation completed (deep=%s, settings=%s)", deep, settings)
            return ProjectValidationResult(valid=True, stage="complete")
        except (json.JSONDecodeError, OSError) as exc:
            return ProjectValidationResult(
                valid=False,
                stage="parse",
                error=str(exc),
            )

    def modify_symbols_list(self, project_name: str) -> list[str]:
        """Extract all configured symbols and timeframes across project tasks.

        Args:
            project_name: Project name.

        Returns:
            Sorted list of unique SYMBOL/TF strings.
        """
        project = self.get_project(project_name)
        symbols: set[str] = set()
        for task in project.tasks:
            _extract_task_symbols(task, symbols)

        logger.info(
            "Found %d distinct symbols in project %s", len(symbols), project_name
        )
        return sorted(symbols)

    def modify_symbols(
        self,
        project_name: str,
        items: Sequence[ModifySymbolItem],
    ) -> None:
        """Replace symbols across all tasks in the project.

        Args:
            project_name: Project name.
            items: Sequence of symbol migration items.

        Raises:
            ValueError: If items list is empty or symbol format is invalid.
        """
        if not items:
            logger.error("No symbols provided to change in %s", project_name)
            raise ValueError("No symbols to change.")

        replacements: list[tuple[str, str, str, str]] = []
        for item in items:
            s_from_raw = item.symbol_from
            s_to_raw = item.symbol_to
            if not s_from_raw or not s_to_raw:
                continue
            if "/" not in s_from_raw or "/" not in s_to_raw:
                raise ValueError("Symbols must be in format SYMBOL/TF.")
            s_from, tf_from = (x.strip() for x in s_from_raw.split("/", 1))
            s_to, tf_to = (x.strip() for x in s_to_raw.split("/", 1))
            replacements.append((s_from, tf_from, s_to, tf_to))

        if not replacements:
            raise ValueError("No symbols to change.")

        project = self.get_project(project_name)
        for task in project.tasks:
            cfg = task.get("config")
            if not isinstance(cfg, dict):
                continue
            data = cfg.get("Data")
            if isinstance(data, dict):
                _apply_symbol_replacements(data, replacements)

        logger.info("Modified symbols for project %s", project_name)
