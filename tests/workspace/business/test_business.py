"""Unit tests for the SQXBusiness domain service and models.

Description:
    Tests the SQXBusinessPluginDescriptor, SQXBusinessService project CRUD,
    settings persistence, EA parameter extraction, and build job lifecycle.

Purpose:
    FEAT-APP-BUSINESS: High-assurance coverage for SQX Business workflows.

Key Capabilities:
    - FR-TEST-BUSINESS-DESCRIPTOR: Verifies default descriptor properties.
    - FR-TEST-SETTINGS: Verifies saving and loading MetaTrader compiler paths.
    - FR-TEST-PROJECTS: Verifies project creation, renaming, updating, and deletion.
    - FR-TEST-EA-PARAMS: Verifies parsing MQL parameters and standard options.
    - FR-TEST-BUILD-LIFECYCLE: Verifies starting, pausing, resuming, stopping jobs.

Python API Usage:
    ```python
    uv run python -m pytest tests/workspace/business/test_business.py -v
    ```

CLI Usage:
    ```bash
    uv run python -m pytest tests/workspace/business/test_business.py --cov=app/workspace/business --cov-branch
    ```
"""

from __future__ import annotations

from pathlib import Path

import pytest
from app.workspace.business.business import SQXBusinessService
from app.workspace.business.business_models import (
    EAParameterModel,
    MQLMarketProjectModel,
    SQXBusinessMainSettingsModel,
    SQXBusinessPluginDescriptor,
)


def test_business_descriptor_defaults() -> None:
    """Verify plugin descriptor matches StrategyQuant SQX Business conventions."""
    descriptor = SQXBusinessPluginDescriptor()
    assert descriptor.name == "SQX Business"
    assert descriptor.product == "SQUANT"
    assert descriptor.preferred_position == 10
    assert descriptor.context_path == "/sqxbusiness"
    assert descriptor.app_code == "SQXBUSINESS"
    assert descriptor.url == "../SQXBUSINESS/dist/index.html"
    assert descriptor.icon_class == "fa-briefcase"
    assert descriptor.section == 1
    assert descriptor.iframe_id == "sqxbusiness-frame"
    assert descriptor.link_id == "sqxbusiness-frame-link"
    assert descriptor.hidden is True


def test_business_models_validation() -> None:
    """Verify Pydantic models serialization and validation."""
    settings = SQXBusinessMainSettingsModel(
        mt5_path="C:/MetaTrader5/metaeditor64.exe",
    )
    assert settings.mt5_path == "C:/MetaTrader5/metaeditor64.exe"

    param = EAParameterModel(
        name="TrailingStop",
        value="25",
        param_type="int",
        comment="Trailing stop in pips",
    )
    assert param.name == "TrailingStop"
    assert param.comment == "Trailing stop in pips"

    project = MQLMarketProjectModel(
        name="TrendHunter",
        config_xml="<Project/>",
        sample=False,
    )
    assert project.name == "TrendHunter"


def test_business_settings_save_and_load(tmp_path: Path) -> None:
    """Verify saving and reading compiler settings in XML."""
    service = SQXBusinessService(projects_dir=tmp_path)
    initial_settings = service.load_main_settings()
    assert initial_settings.mt5_path == ""

    service.save_main_settings(
        mt5_path="C:/MT5/metaeditor64.exe",
    )

    settings = service.load_main_settings()
    assert settings.mt5_path == "C:/MT5/metaeditor64.exe"

    # Reload fresh service instance from disk
    service2 = SQXBusinessService(projects_dir=tmp_path)
    reloaded = service2.load_main_settings()
    assert reloaded.mt5_path == "C:/MT5/metaeditor64.exe"


def test_business_project_crud(tmp_path: Path) -> None:
    """Verify project addition, listing, updating, renaming, and removal."""
    service = SQXBusinessService(projects_dir=tmp_path)
    assert service.list_projects() == []

    # Validation errors on add
    with pytest.raises(ValueError, match="Project name cannot be empty"):
        service.add_project("   ")

    # Add projects
    proj_a = service.add_project("AlphaBot", "<Project><Name>AlphaBot</Name></Project>")
    assert proj_a.name == "AlphaBot"
    assert proj_a.sample is False

    proj_sample = service.add_project("SampleScalper")
    assert proj_sample.sample is True

    # Duplicate name rejection
    with pytest.raises(ValueError, match="already exists"):
        service.add_project("AlphaBot")

    projects = service.list_projects()
    assert len(projects) == 2
    assert projects[0].name == "AlphaBot"
    assert projects[1].name == "SampleScalper"

    # Update project XML
    updated = service.update_project(
        name="AlphaBot",
        config_xml="<Project version='2'/>",
    )
    assert updated.config_xml == "<Project version='2'/>"

    # Rename project
    with pytest.raises(ValueError, match="doesn't exist"):
        service.update_project("NewName", old_name="NonExistent")

    with pytest.raises(ValueError, match="already exists"):
        service.update_project("SampleScalper", old_name="AlphaBot")

    with pytest.raises(ValueError, match="Project name cannot be empty"):
        service.update_project("  ")

    renamed = service.update_project(
        name="AlphaBotV2",
        config_xml="<Project version='2.1'/>",
        old_name="AlphaBot",
    )
    assert renamed.name == "AlphaBotV2"
    assert not (tmp_path / "AlphaBot").exists()
    assert (tmp_path / "AlphaBotV2").exists()

    # Update non-existent without old_name
    with pytest.raises(ValueError, match="does not exist"):
        service.update_project("GhostProject")

    # Remove project
    service.remove_project("SampleScalper")
    assert len(service.list_projects()) == 1
    assert not (tmp_path / "SampleScalper").exists()


def test_business_scan_existing_projects(tmp_path: Path) -> None:
    """Verify scanning pre-existing project directories on startup."""
    proj_dir = tmp_path / "PreExisting"
    proj_dir.mkdir()
    (proj_dir / "config.xml").write_text("<Config data='1'/>", encoding="utf-8")

    service = SQXBusinessService(projects_dir=tmp_path)
    projects = service.list_projects()
    assert len(projects) == 1
    assert projects[0].name == "PreExisting"
    assert "<Config data='1'/>" in projects[0].config_xml


def test_business_parse_parameters_and_options() -> None:
    """Verify MQL strategy parameter extraction and standard EA options."""
    mql_code = """
    // Strategy Header
    input int Magic = 999111; // Strategy Magic Number
    input double Lots = 0.10;
    extern bool UseTrailing = true; // Enable trailing stop
    input string CommentNote = "TestEA"; // Note for broker
    int internalVar = 42;
    """
    params = SQXBusinessService.parse_parameters(mql_code)
    assert len(params) == 4

    assert params[0].name == "Magic"
    assert params[0].value == "999111"
    assert params[0].param_type == "int"
    assert params[0].comment == "Strategy Magic Number"

    assert params[1].name == "Lots"
    assert params[1].value == "0.10"
    assert params[1].comment == ""

    assert params[2].name == "UseTrailing"
    assert params[2].value == "true"
    assert params[2].param_type == "bool"

    options = SQXBusinessService.load_ea_options()
    assert len(options) >= 3
    names = [opt.name for opt in options]
    assert "MagicNumber" in names
    assert "OrderComment" in names
    assert "LotSizingMode" in names


def test_business_build_lifecycle(tmp_path: Path) -> None:
    """Verify build job state transitions: start, pause, resume, stop, clear."""
    service = SQXBusinessService(projects_dir=tmp_path)
    assert service.get_descriptor().app_code == "SQXBUSINESS"
    assert service.get_build_job("Alpha") is None

    # Start build
    job = service.start_build("Alpha")
    assert job.status == "building"
    assert job.progress == 10
    assert len(job.log) == 1

    # Pause build
    paused = service.pause_build("Alpha")
    assert paused.status == "paused"
    assert "Build paused" in paused.log[-1]

    # Resume build
    resumed = service.resume_build("Alpha")
    assert resumed.status == "building"
    assert "Build resumed" in resumed.log[-1]

    # Stop build
    stopped = service.stop_build("Alpha")
    assert stopped.status == "stopped"
    assert "Build stopped by user" in stopped.log[-1]

    # Clear log
    service.clear_log("Alpha")
    cleared = service.get_build_job("Alpha")
    assert cleared is not None
    assert cleared.log == []

    # Non-existent job pause / resume / stop handling
    job_unknown = service.pause_build("Beta")
    assert job_unknown.status == "paused"
    job_unknown_res = service.resume_build("Beta")
    assert job_unknown_res.status == "building"
    job_unknown_stop = service.stop_build("Beta")
    assert job_unknown_stop.status == "stopped"
