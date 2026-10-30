"""SQX Business workspace domain service and project management.

Description:
    Provides the core business service implementation for AppSQXBusiness,
    including plugin descriptor provision, MT4/MT5 compiler configuration,
    commercial MQL Market project persistence, EA parameter extraction, and
    build job lifecycle execution.

Purpose:
    FEAT-APP-BUSINESS: Business workspace service and project pipelines.

Key Capabilities:
    - FR-BUSINESS-DESCRIPTOR: Navigation and host registration metadata.
    - FR-BUSINESS-SETTINGS: Persistent configuration of MetaTrader paths.
    - FR-BUSINESS-PROJECTS: Project workspace directory and XML configuration CRUD.
    - FR-BUSINESS-PARAMS: Parsing of strategy input parameters and EA options.
    - FR-BUSINESS-BUILD: Build execution, status tracking, and logging pipeline.

Python API Usage:
    ```python
    from app.workspace.business.business import SQXBusinessService

    service = SQXBusinessService()
    descriptor = service.get_descriptor()
    projects = service.list_projects()
    ```

CLI Usage:
    ```bash
    uv run python -m pytest tests/workspace/business/test_business.py -q
    ```
"""

from __future__ import annotations

import re
import threading
from pathlib import Path

from app.core.host.logging import get_logger
from app.workspace.business.business_models import (
    EAOptionsModel,
    EAParameterModel,
    MQLMarketBuildJobModel,
    MQLMarketProjectModel,
    SQXBusinessMainSettingsModel,
    SQXBusinessPluginDescriptor,
)

logger = get_logger(__name__)

# Regular expression matching MQL input/extern parameter definitions
# e.g.: input int StopLoss = 50; // Stop loss in pips
_MQL_PARAM_REGEX = re.compile(
    r"^\s*(?:input|extern)\s+([a-zA-Z0-9_]+)\s+([a-zA-Z0-9_]+)\s*=\s*([^;/]+?)\s*;"
    r"(?:\s*//\s*(.*))?$",
    re.MULTILINE,
)


class SQXBusinessService:
    """Core domain service for SQX Business strategy commercialization."""

    def __init__(self, projects_dir: Path | None = None) -> None:
        """Initialize the SQX Business service.

        Args:
            projects_dir: Root directory for storing business projects and config.
        """
        if projects_dir is None:
            repo_root = Path(__file__).resolve().parents[3]
            self.projects_dir = repo_root / "data" / "business" / "projects"
        else:
            self.projects_dir = projects_dir

        self._lock = threading.Lock()
        self._settings_file = self.projects_dir / "config.xml"
        self._mt4_path: str = ""
        self._mt5_path: str = ""
        self._projects: dict[str, MQLMarketProjectModel] = {}
        self._build_jobs: dict[str, MQLMarketBuildJobModel] = {}
        self._init_service()

    def _init_service(self) -> None:
        """Initialize project directory and load pre-existing projects."""
        with self._lock:
            self.projects_dir.mkdir(parents=True, exist_ok=True)
            self._load_settings_unlocked()
            self._load_projects_unlocked()

    def _load_settings_unlocked(self) -> None:
        """Load compiler settings from config file if available."""
        if not self._settings_file.exists():
            return
        try:
            text = self._settings_file.read_text(encoding="utf-8")
            m_mt4 = re.search(r'<MetaTrader4\s+path="([^"]*)"', text)
            if m_mt4:
                self._mt4_path = m_mt4.group(1)
            m_mt5 = re.search(r'<MetaTrader5\s+path="([^"]*)"', text)
            if m_mt5:
                self._mt5_path = m_mt5.group(1)
            logger.info("FR-BUSINESS-SETTINGS: Loaded compiler settings")
        except OSError:
            logger.exception("FR-BUSINESS-SETTINGS: Failed reading settings file")

    def _load_projects_unlocked(self) -> None:
        """Scan projects directory for existing project subdirectories."""
        self._projects.clear()
        try:
            for item in sorted(
                self.projects_dir.iterdir(), key=lambda p: p.name.lower()
            ):
                if item.is_dir():
                    cfg_file = item / "config.xml"
                    cfg_text = (
                        cfg_file.read_text(encoding="utf-8")
                        if cfg_file.exists()
                        else ""
                    )
                    is_sample = item.name.lower().startswith("sample")
                    self._projects[item.name] = MQLMarketProjectModel(
                        name=item.name,
                        config_xml=cfg_text,
                        sample=is_sample,
                    )
            logger.info("FR-BUSINESS-PROJECTS: Loaded %d projects", len(self._projects))
        except OSError:
            logger.exception("FR-BUSINESS-PROJECTS: Failed scanning projects directory")

    def get_descriptor(self) -> SQXBusinessPluginDescriptor:
        """Return plugin descriptor for host registration.

        Returns:
            SQXBusinessPluginDescriptor instance.
        """
        return SQXBusinessPluginDescriptor()

    def load_main_settings(self) -> SQXBusinessMainSettingsModel:
        """Return current MetaTrader compiler paths.

        Returns:
            SQXBusinessMainSettingsModel instance.
        """
        with self._lock:
            return SQXBusinessMainSettingsModel(
                mt4_path=self._mt4_path,
                mt5_path=self._mt5_path,
            )

    def save_main_settings(self, mt4_path: str, mt5_path: str) -> None:
        """Save MetaTrader compiler paths to persistent XML.

        Args:
            mt4_path: Path to MetaTrader 4 terminal/metaeditor executable.
            mt5_path: Path to MetaTrader 5 terminal/metaeditor executable.
        """
        with self._lock:
            self._mt4_path = mt4_path
            self._mt5_path = mt5_path
            xml_content = (
                f"<Settings>\n"
                f'  <MetaTrader4 path="{mt4_path}"/>\n'
                f'  <MetaTrader5 path="{mt5_path}"/>\n'
                f"</Settings>\n"
            )
            self._settings_file.write_text(xml_content, encoding="utf-8")
            logger.info("FR-BUSINESS-SETTINGS: Saved compiler settings")

    def list_projects(self) -> list[MQLMarketProjectModel]:
        """Return list of all registered business projects.

        Returns:
            List of MQLMarketProjectModel objects sorted alphabetically.
        """
        with self._lock:
            return [
                self._projects[k]
                for k in sorted(self._projects.keys(), key=lambda x: x.lower())
            ]

    def add_project(
        self,
        name: str,
        config_xml: str = "",
    ) -> MQLMarketProjectModel:
        """Create a new commercial packaging project.

        Args:
            name: Project name.
            config_xml: Initial XML configuration string.

        Returns:
            Created MQLMarketProjectModel.

        Raises:
            ValueError: If name is invalid or project folder already exists.
        """
        trimmed = name.strip()
        if not trimmed:
            raise ValueError("Project name cannot be empty.")

        with self._lock:
            project_dir = self.projects_dir / trimmed
            if project_dir.exists() or trimmed in self._projects:
                raise ValueError(
                    f"Cannot create project with name '{trimmed}' "
                    "- Folder already exists"
                )

            project_dir.mkdir(parents=True, exist_ok=True)
            cfg_file = project_dir / "config.xml"
            cfg_content = config_xml or f'<Project name="{trimmed}"/>'
            cfg_file.write_text(cfg_content, encoding="utf-8")

            model = MQLMarketProjectModel(
                name=trimmed,
                config_xml=cfg_content,
                sample=trimmed.lower().startswith("sample"),
            )
            self._projects[trimmed] = model
            logger.info("FR-BUSINESS-PROJECTS: Added project '%s'", trimmed)
            return model

    def update_project(
        self,
        name: str,
        config_xml: str = "",
        old_name: str | None = None,
    ) -> MQLMarketProjectModel:
        """Update or rename an existing commercial project.

        Args:
            name: New or current project name.
            config_xml: Updated XML configuration string.
            old_name: Previous name if renaming.

        Returns:
            Updated MQLMarketProjectModel.

        Raises:
            ValueError: If project does not exist or rename target conflicts.
        """
        trimmed = name.strip()
        if not trimmed:
            raise ValueError("Project name cannot be empty.")

        with self._lock:
            target_dir = self.projects_dir / trimmed

            if old_name is not None and old_name != trimmed:
                old_dir = self.projects_dir / old_name
                if not old_dir.exists():
                    raise ValueError(
                        f"Cannot rename project - Folder '{old_name}' doesn't exist"
                    )
                if target_dir.exists():
                    raise ValueError(
                        f"Cannot rename project - Folder '{trimmed}' already exists"
                    )
                old_dir.rename(target_dir)
                if old_name in self._projects:
                    del self._projects[old_name]

            if not target_dir.exists():
                raise ValueError(f"Project '{trimmed}' does not exist.")

            cfg_file = target_dir / "config.xml"
            cfg_content = config_xml or f'<Project name="{trimmed}"/>'
            cfg_file.write_text(cfg_content, encoding="utf-8")

            model = MQLMarketProjectModel(
                name=trimmed,
                config_xml=cfg_content,
                sample=trimmed.lower().startswith("sample"),
            )
            self._projects[trimmed] = model
            logger.info("FR-BUSINESS-PROJECTS: Updated project '%s'", trimmed)
            return model

    def remove_project(self, name: str) -> None:
        """Delete an existing commercial project and its directory.

        Args:
            name: Project name to delete.
        """
        with self._lock:
            project_dir = self.projects_dir / name
            if project_dir.exists():
                for child in project_dir.rglob("*"):
                    if child.is_file():
                        child.unlink()
                for child in sorted(project_dir.rglob("*"), reverse=True):
                    if child.is_dir():
                        child.rmdir()
                project_dir.rmdir()

            if name in self._projects:
                del self._projects[name]
            if name in self._build_jobs:
                del self._build_jobs[name]
            logger.info("FR-BUSINESS-PROJECTS: Removed project '%s'", name)

    @staticmethod
    def parse_parameters(source_code: str) -> list[EAParameterModel]:
        """Parse input and extern parameters from MQL strategy code.

        Args:
            source_code: Raw MQL4 or MQL5 source code.

        Returns:
            List of parsed EAParameterModel objects.
        """
        params: list[EAParameterModel] = []
        for match in _MQL_PARAM_REGEX.finditer(source_code):
            param_type, name, val, comment = match.groups()
            params.append(
                EAParameterModel(
                    name=name.strip(),
                    value=val.strip(),
                    param_type=param_type.strip(),
                    comment=(comment or "").strip(),
                )
            )
        return params

    @staticmethod
    def load_ea_options() -> list[EAOptionsModel]:
        """Return standard Expert Advisor build options and parameters.

        Returns:
            List of standard EAOptionsModel items.
        """
        return [
            EAOptionsModel(
                name="MagicNumber",
                description="Unique identifier for EA orders",
                default_value="123456",
            ),
            EAOptionsModel(
                name="OrderComment",
                description="Custom comment attached to trades",
                default_value="SQX Expert",
            ),
            EAOptionsModel(
                name="MaxSlippagePips",
                description="Maximum tolerated slippage in pips",
                default_value="3",
            ),
            EAOptionsModel(
                name="LotSizingMode",
                description="Lot calculation mode",
                default_value="Fixed",
                options=["Fixed", "PercentRisk", "EquityBased"],
            ),
        ]

    def start_build(self, project_name: str) -> MQLMarketBuildJobModel:
        """Start a strategy build job for a commercial project.

        Args:
            project_name: Target project name.

        Returns:
            Updated MQLMarketBuildJobModel.
        """
        with self._lock:
            job = MQLMarketBuildJobModel(
                project_name=project_name,
                status="building",
                progress=10,
                log=[f"Starting build for {project_name}"],
            )
            self._build_jobs[project_name] = job
            logger.info("FR-BUSINESS-BUILD: Started build for '%s'", project_name)
            return job

    def pause_build(self, project_name: str) -> MQLMarketBuildJobModel:
        """Pause an active build job.

        Args:
            project_name: Target project name.

        Returns:
            Updated MQLMarketBuildJobModel.
        """
        with self._lock:
            job = self._build_jobs.get(
                project_name,
                MQLMarketBuildJobModel(project_name=project_name),
            )
            updated = MQLMarketBuildJobModel(
                project_name=project_name,
                status="paused",
                progress=job.progress,
                log=[*job.log, "Build paused"],
            )
            self._build_jobs[project_name] = updated
            logger.info("FR-BUSINESS-BUILD: Paused build for '%s'", project_name)
            return updated

    def resume_build(self, project_name: str) -> MQLMarketBuildJobModel:
        """Resume a paused build job.

        Args:
            project_name: Target project name.

        Returns:
            Updated MQLMarketBuildJobModel.
        """
        with self._lock:
            job = self._build_jobs.get(
                project_name,
                MQLMarketBuildJobModel(project_name=project_name),
            )
            updated = MQLMarketBuildJobModel(
                project_name=project_name,
                status="building",
                progress=job.progress,
                log=[*job.log, "Build resumed"],
            )
            self._build_jobs[project_name] = updated
            logger.info("FR-BUSINESS-BUILD: Resumed build for '%s'", project_name)
            return updated

    def stop_build(self, project_name: str) -> MQLMarketBuildJobModel:
        """Stop an active or paused build job.

        Args:
            project_name: Target project name.

        Returns:
            Updated MQLMarketBuildJobModel.
        """
        with self._lock:
            job = self._build_jobs.get(
                project_name,
                MQLMarketBuildJobModel(project_name=project_name),
            )
            updated = MQLMarketBuildJobModel(
                project_name=project_name,
                status="stopped",
                progress=job.progress,
                log=[*job.log, "Build stopped by user"],
            )
            self._build_jobs[project_name] = updated
            logger.info("FR-BUSINESS-BUILD: Stopped build for '%s'", project_name)
            return updated

    def get_build_job(self, project_name: str) -> MQLMarketBuildJobModel | None:
        """Return status for an active or completed build job.

        Args:
            project_name: Target project name.

        Returns:
            MQLMarketBuildJobModel or None.
        """
        with self._lock:
            return self._build_jobs.get(project_name)

    def clear_log(self, project_name: str) -> None:
        """Clear build execution log messages for a project.

        Args:
            project_name: Target project name.
        """
        with self._lock:
            job = self._build_jobs.get(project_name)
            if job:
                self._build_jobs[project_name] = MQLMarketBuildJobModel(
                    project_name=project_name,
                    status=job.status,
                    progress=job.progress,
                    log=[],
                )
                logger.info("FR-BUSINESS-BUILD: Cleared log for '%s'", project_name)
