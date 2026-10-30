"""Task Manager REST routes and action endpoints.

Description:
    Provides FastAPI router exposing endpoints for Task Manager operations:
    project lifecycle, task graph manipulation, symbol modification, pipeline
    execution, and progress statistics.

Purpose:
    FEAT-TM-ROUTES: REST API for Task Manager workspace.

Key Capabilities:
    FR-TM-ROUTE-PROJECTS: Project CRUD and validation routes.
    FR-TM-ROUTE-TASKS: Task graph CRUD and catalogue endpoints.
    FR-TM-ROUTE-SYMBOLS: Symbol discovery and batch replacement.
    FR-TM-ROUTE-PIPELINE: Start, stop, pause, and execution status monitoring.

Python API Usage:
    ```python
    from app.workspace.task_manager.routes import task_manager_router
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(task_manager_router)
    ```

CLI Usage:
    ```bash
    uv run python -m pytest tests/workspace/task_manager/test_routes.py -q
    ```
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field

from app.workspace.task_manager.app_task_manager import AppTaskManager
from app.workspace.task_manager.task_manager_projects import (
    TaskManagerProjects,
)
from app.workspace.task_manager.task_manager_projects_models import (
    ModifySymbolItem,
)
from app.workspace.task_manager.task_manager_tasks import TaskManagerTasks

logger = logging.getLogger("haruquant.task_manager.routes")

task_manager_router = APIRouter(prefix="/taskmanager", tags=["taskmanager"])

# Global singletons for Task Manager engine
_projects_engine = TaskManagerProjects()
_tasks_engine = TaskManagerTasks(_projects_engine)
_app_tm = AppTaskManager(_projects_engine)


def get_projects_engine() -> TaskManagerProjects:
    """Access singleton projects engine."""
    return _projects_engine


def get_tasks_engine() -> TaskManagerTasks:
    """Access singleton tasks engine."""
    return _tasks_engine


def get_app_tm() -> AppTaskManager:
    """Access singleton app pipeline engine."""
    return _app_tm


# Request schemas with Pydantic aliases for donor JSON compatibility
class BasePayload(BaseModel):
    """Base payload enabling population by field name or alias."""

    model_config = ConfigDict(populate_by_name=True)


class CreateProjectPayload(BasePayload):
    """Payload to create project."""

    project_name: str = Field(..., alias="projectName", description="Project name")


class OpenProjectPayload(BasePayload):
    """Payload to open project from file."""

    file: str = Field(..., description="Path to file")
    project_name: str | None = Field(default=None, alias="projectName")
    load_as_is: bool = Field(default=False, alias="loadAsIs")


class ValidateProjectPayload(BasePayload):
    """Payload to validate project file."""

    file_path: str = Field(..., alias="filePath", description="Path to project file")
    deep: bool = Field(default=True)
    settings: bool = Field(default=True)


class SaveProjectPayload(BasePayload):
    """Payload to save project."""

    project_name: str = Field(..., alias="projectName", description="Project name")
    file: str = Field(..., description="Target file path")


class ProjectNamePayload(BasePayload):
    """Payload referencing single project name."""

    project_name: str = Field(..., alias="projectName", description="Project name")


class RenameProjectPayload(BasePayload):
    """Payload to rename project."""

    old_name: str = Field(..., alias="oldName", description="Current name")
    new_name: str = Field(..., alias="newName", description="Target new name")


class AddTaskPayload(BasePayload):
    """Payload to add task to project."""

    project_name: str = Field(..., alias="projectName")
    task_name: str = Field(..., alias="taskName")
    task_type: str = Field(..., alias="taskType")
    task_title: str | None = Field(default=None, alias="taskTitle")
    index: int = Field(default=-1)
    config: dict[str, Any] | None = Field(default=None)


class RemoveTaskPayload(BasePayload):
    """Payload to remove task from project."""

    project_name: str = Field(..., alias="projectName")
    task_name: str = Field(..., alias="taskName")


class MoveTaskPayload(BasePayload):
    """Payload to reorder task."""

    project_name: str = Field(..., alias="projectName")
    task_name: str = Field(..., alias="taskName")
    to_index: int = Field(..., alias="toIndex")


class RenameTaskPayload(BasePayload):
    """Payload to rename task title."""

    project_name: str = Field(..., alias="projectName")
    task_name: str = Field(..., alias="taskName")
    task_title: str = Field(..., alias="taskTitle")


class CloneTaskPayload(BasePayload):
    """Payload to clone task."""

    project_name: str = Field(..., alias="projectName")
    task_name: str = Field(..., alias="taskName")
    position: str = Field(default="end")


class ActivateTaskPayload(BasePayload):
    """Payload to set task activation."""

    project_name: str = Field(..., alias="projectName")
    task_name: str = Field(..., alias="taskName")
    active: bool = Field(...)


class ModifySymbolsPayload(BasePayload):
    """Payload to replace symbols."""

    project_name: str = Field(..., alias="projectName")
    symbols: list[dict[str, str]] = Field(...)


# Endpoints
@task_manager_router.get("/listProjects")
@task_manager_router.post("/listProjects")
def list_projects() -> dict[str, Any]:
    """List all projects in the engine."""
    projects = _projects_engine.list_projects()
    return {
        "projects": [p.to_dict() for p in projects],
        "success": "Projects listed.",
    }


@task_manager_router.post("/createProject")
def create_project(payload: CreateProjectPayload) -> dict[str, Any]:
    """Create a new project."""
    try:
        project = _projects_engine.create_project(payload.project_name)
        return {
            "projectName": project.name,
            "success": f"Project created {project.name}.",
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@task_manager_router.post("/openProject")
def open_project(payload: OpenProjectPayload) -> dict[str, Any]:
    """Open project from JSON configuration file."""
    try:
        project = _projects_engine.open_project(
            payload.file,
            project_name=payload.project_name,
            load_as_is=payload.load_as_is,
        )
        return {
            "projectName": project.name,
            "success": f"Project loaded '{project.name}'.",
        }
    except (FileNotFoundError, ValueError, TypeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@task_manager_router.post("/validateProject")
def validate_project(payload: ValidateProjectPayload) -> dict[str, Any]:
    """Validate project file."""
    res = _projects_engine.validate_project(
        payload.file_path, deep=payload.deep, settings=payload.settings
    )
    return res.to_dict()


@task_manager_router.post("/saveProject")
def save_project(payload: SaveProjectPayload) -> dict[str, Any]:
    """Save project to file."""
    try:
        _projects_engine.save_project(payload.project_name, payload.file)
        return {"success": "Project saved."}
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@task_manager_router.post("/removeProject")
def remove_project(payload: ProjectNamePayload) -> dict[str, Any]:
    """Remove project."""
    try:
        _projects_engine.remove_project(payload.project_name)
        return {"success": "Project removed."}
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@task_manager_router.post("/cloneProject")
def clone_project(payload: ProjectNamePayload) -> dict[str, Any]:
    """Clone project."""
    try:
        cloned = _projects_engine.clone_project(payload.project_name)
        return {
            "projectName": cloned.name,
            "success": "Project cloned.",
        }
    except KeyError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@task_manager_router.post("/renameProject")
def rename_project(payload: RenameProjectPayload) -> dict[str, Any]:
    """Rename project."""
    try:
        _projects_engine.rename_project(payload.old_name, payload.new_name)
        return {"success": "Project renamed."}
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@task_manager_router.get("/getAvailableTasks")
@task_manager_router.post("/getAvailableTasks")
def get_available_tasks() -> dict[str, Any]:
    """List available task plugins."""
    tasks = _tasks_engine.get_available_tasks()
    return {
        "tasks": [t.to_dict() for t in tasks],
        "success": "Available tasks listed.",
    }


@task_manager_router.post("/addTask")
def add_task(payload: AddTaskPayload) -> dict[str, Any]:
    """Add task to project."""
    try:
        task = _tasks_engine.add_task(
            payload.project_name,
            payload.task_name,
            payload.task_type,
            task_title=payload.task_title,
            index=payload.index,
            config=payload.config,
        )
        return {
            "task": task.to_dict(),
            "success": "Task added.",
        }
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@task_manager_router.post("/removeTask")
def remove_task(payload: RemoveTaskPayload) -> dict[str, Any]:
    """Remove task from project."""
    try:
        task = _tasks_engine.remove_task(payload.project_name, payload.task_name)
        return {
            "task": task.to_dict(),
            "success": "Task removed.",
        }
    except KeyError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@task_manager_router.post("/moveTask")
def move_task(payload: MoveTaskPayload) -> dict[str, Any]:
    """Move task position."""
    try:
        _tasks_engine.move_task(
            payload.project_name, payload.task_name, payload.to_index
        )
        return {"success": "Task moved."}
    except KeyError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@task_manager_router.post("/renameTask")
def rename_task(payload: RenameTaskPayload) -> dict[str, Any]:
    """Rename task title."""
    try:
        _tasks_engine.rename_task(
            payload.project_name, payload.task_name, payload.task_title
        )
        return {"success": "Task renamed."}
    except KeyError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@task_manager_router.post("/cloneTask")
def clone_task(payload: CloneTaskPayload) -> dict[str, Any]:
    """Clone task."""
    try:
        cloned = _tasks_engine.clone_task(
            payload.project_name, payload.task_name, position=payload.position
        )
        return {
            "task": cloned.to_dict(),
            "success": "Task cloned.",
        }
    except KeyError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@task_manager_router.post("/activateTask")
def activate_task(payload: ActivateTaskPayload) -> dict[str, Any]:
    """Set task active status."""
    try:
        _tasks_engine.activate_task(
            payload.project_name, payload.task_name, payload.active
        )
        return {"success": "Task status changed."}
    except KeyError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@task_manager_router.post("/modifySymbolsList")
def modify_symbols_list(payload: ProjectNamePayload) -> dict[str, Any]:
    """List all symbols across project tasks."""
    try:
        symbols = _projects_engine.modify_symbols_list(payload.project_name)
        return {"symbols": symbols, "success": "Symbols listed."}
    except KeyError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@task_manager_router.post("/modifySymbols")
def modify_symbols(payload: ModifySymbolsPayload) -> dict[str, Any]:
    """Batch replace symbols in project."""
    try:
        items = [
            ModifySymbolItem(
                symbol_from=item.get("symbolFrom", ""),
                symbol_to=item.get("symbolTo", ""),
            )
            for item in payload.symbols
        ]
        _projects_engine.modify_symbols(payload.project_name, items)
        return {"success": "Symbols changed."}
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@task_manager_router.post("/startProject")
def start_project(payload: ProjectNamePayload) -> dict[str, Any]:
    """Start project pipeline execution."""
    try:
        _app_tm.start_project(payload.project_name)
        return {"success": "Project started."}
    except KeyError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@task_manager_router.post("/stopProject")
def stop_project(payload: ProjectNamePayload) -> dict[str, Any]:
    """Stop project pipeline execution."""
    try:
        _app_tm.stop_project(payload.project_name)
        return {"success": "Project stopped."}
    except KeyError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@task_manager_router.post("/pauseProject")
def pause_project(payload: ProjectNamePayload) -> dict[str, Any]:
    """Pause project pipeline execution."""
    try:
        _app_tm.pause_project(payload.project_name)
        return {"success": "Project paused."}
    except KeyError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@task_manager_router.get("/projectStatus")
def get_project_status(
    project_name: str = Query(..., alias="projectName", description="Project name"),
) -> dict[str, Any]:
    """Get runtime execution status of project."""
    try:
        state = _app_tm.get_project_status(project_name)
        return state.to_dict()
    except KeyError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@task_manager_router.get("/customProjectStats")
def get_custom_project_stats() -> dict[str, Any]:
    """Get progress publisher stats for all custom projects."""
    return {"stats": _app_tm.get_custom_project_stats()}
