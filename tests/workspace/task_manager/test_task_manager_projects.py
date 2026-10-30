"""Tests for TaskManagerProjects and project models."""

from __future__ import annotations

from pathlib import Path

import pytest
from app.workspace.task_manager.task_manager_projects import (
    TaskManagerProjects,
    normalize_project_name,
    validate_project_name,
)
from app.workspace.task_manager.task_manager_projects_models import (
    ModifySymbolItem,
    ProjectInfo,
    ProjectSummary,
    ProjectValidationResult,
)


class TestProjectModels:
    """Test suite for Project domain models."""

    def test_project_models_serialization(self) -> None:
        """Verify to_dict outputs for ProjectSummary and ProjectInfo."""
        summary = ProjectSummary(project_name="Alpha", tasks_count=3, active=True)
        assert summary.to_dict() == {
            "projectName": "Alpha",
            "tasksCount": 3,
            "active": True,
            "isAppProject": False,
        }
        assert summary.project_name == "Alpha"
        assert summary.tasks_count == 3
        assert not summary.is_app_project

        item = ModifySymbolItem(symbol_from="EURUSD/H1", symbol_to="AUDUSD/H1")
        assert item.to_dict() == {
            "symbolFrom": "EURUSD/H1",
            "symbolTo": "AUDUSD/H1",
        }

        info = ProjectInfo(name="Alpha", tasks=[{"name": "T1"}], settings={"opt": 1})
        info_dict = info.to_dict()
        assert info_dict["name"] == "Alpha"
        assert len(info_dict["tasks"]) == 1
        assert info_dict["settings"]["opt"] == 1

        val_err = ProjectValidationResult(
            valid=False, stage="resolve", error="File not found"
        )
        assert val_err.to_dict() == {
            "valid": False,
            "stage": "resolve",
            "error": "File not found",
            "success": "ok",
        }

        val_ok = ProjectValidationResult(valid=True, stage="complete")
        assert val_ok.to_dict() == {
            "valid": True,
            "stage": "complete",
            "success": "ok",
        }


class TestValidateProjectName:
    """Test suite for project name validation."""

    def test_normalize_name(self) -> None:
        """Verify trimming and None behavior."""
        assert normalize_project_name("  Trend  ") == "Trend"
        assert normalize_project_name(None) is None

    @pytest.mark.parametrize("empty_name", ["", "   ", None])
    def test_empty_name(self, empty_name: str | None) -> None:
        """Reject empty or whitespace-only names."""
        with pytest.raises(ValueError, match=r"Project name cannot be empty\."):
            validate_project_name(empty_name)

    def test_leading_dot(self) -> None:
        """Reject names starting with dot."""
        with pytest.raises(ValueError, match=r"Project name cannot start with dot\."):
            validate_project_name(".hidden_project")

    @pytest.mark.parametrize("char", ["\\", "/", ":", "*", "?", '"', "<", ">", "|"])
    def test_forbidden_chars(self, char: str) -> None:
        """Reject forbidden file system characters."""
        with pytest.raises(
            ValueError, match=r"Project name contains forbidden characters"
        ):
            validate_project_name(f"My{char}Project")

    @pytest.mark.parametrize(
        "reserved", ["CON", "prn", "aux", "nul", "COM1", "com9", "lpt5"]
    )
    def test_reserved_system_names(self, reserved: str) -> None:
        """Reject reserved DOS / Windows device names."""
        with pytest.raises(
            ValueError, match=r"Project name uses a reserved system name\."
        ):
            validate_project_name(reserved)
        with pytest.raises(
            ValueError, match=r"Project name uses a reserved system name\."
        ):
            validate_project_name(f"{reserved}.json")

    @pytest.mark.parametrize(
        "bad_whitespace", ["Project\tName", "Project\nName", "Project\rName"]
    )
    def test_tabs_and_newlines(self, bad_whitespace: str) -> None:
        """Reject tabs and newlines in project names."""
        with pytest.raises(
            ValueError, match=r"Project name cannot contain tabs or new lines\."
        ):
            validate_project_name(bad_whitespace)

    def test_valid_names(self) -> None:
        """Accept valid names with spaces and alphanumerics."""
        validate_project_name("Trend Hunter 2026")
        validate_project_name("EURUSD-Strategy_v1.0")


class TestTaskManagerProjectsEngine:
    """Test suite for TaskManagerProjects CRUD and file persistence."""

    def test_create_and_list_projects(self) -> None:
        """Verify project creation and sorted listing."""
        engine = TaskManagerProjects()
        assert engine.list_projects() == []

        p_beta = engine.create_project("BetaProject")
        p_alpha = engine.create_project("AlphaProject")
        assert p_beta.name == "BetaProject"
        assert p_alpha.name == "AlphaProject"

        summaries = engine.list_projects()
        assert len(summaries) == 2
        assert summaries[0].project_name == "AlphaProject"
        assert summaries[1].project_name == "BetaProject"

    def test_create_duplicate_rejected(self) -> None:
        """Reject duplicate project creation."""
        engine = TaskManagerProjects()
        engine.create_project("Unique")
        with pytest.raises(
            ValueError, match=r"Project with the same name already exists\."
        ):
            engine.create_project("Unique")

    def test_create_with_invalid_name(self) -> None:
        """Reject project creation when name is empty or invalid."""
        engine = TaskManagerProjects()
        with pytest.raises(ValueError, match=r"Project name cannot be empty\."):
            engine.create_project("   ")

    def test_get_nonexistent_project(self) -> None:
        """Raise KeyError on non-existent project lookup."""
        engine = TaskManagerProjects()
        with pytest.raises(KeyError, match=r"Project 'Ghost' does not exist\."):
            engine.get_project("Ghost")

    def test_rename_project(self) -> None:
        """Verify project rename and conflict checks."""
        engine = TaskManagerProjects()
        engine.create_project("OldName")
        engine.create_project("Existing")

        # No-op rename to self
        engine.rename_project("OldName", "OldName")
        assert engine.project_exists("OldName")

        # Conflict with existing
        with pytest.raises(
            ValueError, match=r"Project with the same name already exists\."
        ):
            engine.rename_project("OldName", "Existing")

        # Rename non-empty invalid
        with pytest.raises(ValueError, match=r"Project name cannot be empty\."):
            engine.rename_project("OldName", "   ")

        # Successful rename
        engine.rename_project("OldName", "NewName")
        assert not engine.project_exists("OldName")
        assert engine.project_exists("NewName")
        assert engine.get_project("NewName").name == "NewName"

    def test_remove_project(self) -> None:
        """Verify project removal and predefined project protection."""
        engine = TaskManagerProjects()
        engine.create_project("Normal")
        engine.remove_project("Normal")
        assert not engine.project_exists("Normal")

        # App project protection
        app_p = engine.create_project("AppBuilder")
        app_p.is_app_project = True
        with pytest.raises(
            ValueError, match=r"Predefined project AppBuilder cannot be removed\."
        ):
            engine.remove_project("AppBuilder")

    def test_clone_project(self) -> None:
        """Verify deep cloning of project and unique naming."""
        engine = TaskManagerProjects()
        orig = engine.create_project("Alpha")
        orig.tasks.append({"name": "Task 1", "config": {"Data": {"symbol": "EURUSD"}}})
        orig.settings["max_retries"] = 5

        clone1 = engine.clone_project("Alpha")
        assert clone1.name == "Alpha(2)"
        assert len(clone1.tasks) == 1
        assert clone1.settings["max_retries"] == 5

        # Mutating clone does not mutate original
        clone1.tasks.append({"name": "Task 2"})
        assert len(orig.tasks) == 1

        clone2 = engine.clone_project("Alpha")
        assert clone2.name == "Alpha(3)"

    def test_save_and_open_project(self, tmp_path: Path) -> None:
        """Verify file persistence and loading."""
        engine = TaskManagerProjects()
        p = engine.create_project("SavedProj")
        p.tasks.append({"name": "Build 1"})
        p_file = tmp_path / "sub" / "saved_proj.json"

        engine.save_project("SavedProj", p_file)
        assert p_file.is_file()

        # Open in fresh engine
        fresh_engine = TaskManagerProjects()
        loaded = fresh_engine.open_project(p_file)
        assert loaded.name == "SavedProj"
        assert len(loaded.tasks) == 1

        # Open again in same engine generates unique name
        second_load = fresh_engine.open_project(p_file)
        assert second_load.name == "SavedProj(2)"

        # Load as is preserves name
        as_is_load = fresh_engine.open_project(p_file, load_as_is=True)
        assert as_is_load.name == "SavedProj"

    def test_open_project_errors(self, tmp_path: Path) -> None:
        """Verify open_project error handling for missing and invalid files."""
        engine = TaskManagerProjects()
        with pytest.raises(FileNotFoundError, match="No such file"):
            engine.open_project(tmp_path / "nonexistent.json")

        corrupt_file = tmp_path / "corrupt.json"
        corrupt_file.write_text("{invalid json", encoding="utf-8")
        with pytest.raises(ValueError, match="corrupted"):
            engine.open_project(corrupt_file)

        non_dict_file = tmp_path / "non_dict.json"
        non_dict_file.write_text('["list", "not", "dict"]', encoding="utf-8")
        with pytest.raises(TypeError, match="Root must be a dictionary"):
            engine.open_project(non_dict_file)

        no_name_file = tmp_path / "no_name.json"
        no_name_file.write_text('{"active": true}', encoding="utf-8")
        with pytest.raises(ValueError, match="Missing project name"):
            engine.open_project(no_name_file)

    def test_validate_project(self, tmp_path: Path) -> None:
        """Verify project file validation verdicts."""
        engine = TaskManagerProjects()

        # Missing file
        res = engine.validate_project(tmp_path / "missing.json")
        assert not res.valid
        assert res.stage == "resolve"

        # Corrupted JSON
        corrupt = tmp_path / "bad.json"
        corrupt.write_text("bad data", encoding="utf-8")
        res = engine.validate_project(corrupt)
        assert not res.valid
        assert res.stage == "parse"

        # Non-dict JSON
        non_dict = tmp_path / "arr.json"
        non_dict.write_text("[1, 2, 3]", encoding="utf-8")
        res = engine.validate_project(non_dict)
        assert not res.valid
        assert res.stage == "schema"

        # Missing name
        no_name = tmp_path / "no_name.json"
        no_name.write_text('{"tasks": []}', encoding="utf-8")
        res = engine.validate_project(no_name)
        assert not res.valid
        assert res.stage == "schema"

        # Valid project file
        good = tmp_path / "good.json"
        good.write_text('{"name": "GoodProject", "tasks": []}', encoding="utf-8")
        res = engine.validate_project(good)
        assert res.valid
        assert res.stage == "complete"

    def test_modify_symbols(self) -> None:
        """Verify listing and replacing symbols across project tasks."""
        engine = TaskManagerProjects()
        p = engine.create_project("SymbolsTest")
        p.tasks = [
            {
                "name": "Task 1",
                "config": {
                    "Data": {
                        "symbol": "EURUSD",
                        "timeframe": "M1",
                        "symbols": ["GBPUSD/H1"],
                    },
                    "CrossChecks": {
                        "RetestOnAdditionalMarkets": {
                            "symbols": ["USDJPY/M15"],
                        }
                    },
                },
            },
            {
                "name": "Task 2",
                "config": {
                    "Data": {
                        "symbol": "EURUSD",
                        "timeframe": "M1",
                    }
                },
            },
            {"name": "Task 3 without config"},
        ]

        # Extract symbols
        symbols = engine.modify_symbols_list("SymbolsTest")
        assert symbols == ["EURUSD/M1", "GBPUSD/H1", "USDJPY/M15"]

        # Reject empty items
        with pytest.raises(ValueError, match=r"No symbols to change\."):
            engine.modify_symbols("SymbolsTest", [])

        # Reject bad format
        with pytest.raises(ValueError, match=r"Symbols must be in format SYMBOL/TF\."):
            engine.modify_symbols(
                "SymbolsTest",
                [ModifySymbolItem(symbol_from="EURUSD", symbol_to="AUDUSD/H1")],
            )

        # Replace EURUSD/M1 -> AUDUSD/H4
        engine.modify_symbols(
            "SymbolsTest",
            [ModifySymbolItem(symbol_from="EURUSD/M1", symbol_to="AUDUSD/H4")],
        )
        assert p.tasks[0]["config"]["Data"]["symbol"] == "AUDUSD"
        assert p.tasks[0]["config"]["Data"]["timeframe"] == "H4"
        assert p.tasks[1]["config"]["Data"]["symbol"] == "AUDUSD"
        assert p.tasks[1]["config"]["Data"]["timeframe"] == "H4"

        # Wildcard replacement
        engine.modify_symbols(
            "SymbolsTest",
            [ModifySymbolItem(symbol_from="AUDUSD/*", symbol_to="NZDUSD/*")],
        )
        assert p.tasks[0]["config"]["Data"]["symbol"] == "NZDUSD"
        assert p.tasks[0]["config"]["Data"]["timeframe"] == "H4"
