"""Local landing content and safe project-summary projections.

Description:
    Reads the shared bundled text catalog and projects host-owned entity rows
    into public summaries without exposing arbitrary saved payloads.
Purpose:
    FEAT-HOME-DASHBOARD: Original onboarding and persisted project metadata.
Key Capabilities:
    - FR-HOME-INDEX: Load local content through Home.index() (INFO at boundary).
    - FR-HOME-RECENT: Validate summaries through Home.get_recent_projects();
      WARNING records malformed rows without their contents.
Python API Usage:
    from app.workspace.home import Home
    # Use Home.index() with explicitly injected host services.
CLI Usage:
    uv run python -m app.cli home --json
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.host.logging import get_logger
from pydantic import BaseModel, ConfigDict, Field, ValidationError

logger = get_logger(__name__)
_WORKSPACES = frozenset(
    {
        "datamanager",
        "algowizard",
        "builder",
        "projects",
        "retester",
        "optimizer",
        "composer",
        "portfolio",
        "codeeditor",
        "neuralnet",
        "mtanalyzer",
    }
)


class _Action(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    id: str
    label: str


class _Guide(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    id: str
    title: str
    body: str
    summary: str = ""
    workspace: str | None = None


class _Catalog(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    title: str
    description: str
    actions: list[_Action]
    tutorials: list[_Guide]
    help: list[_Guide]


class _Project(BaseModel):
    model_config = ConfigDict(extra="ignore", strict=True)
    name: str = Field(min_length=1, max_length=200)
    workspace: str


def _load_content() -> dict[str, Any]:
    """Load the single catalog shared with the browser application."""
    path = (
        Path(__file__).resolve().parents[3] / "ui/app/workspace/Home/homeContent.json"
    )
    return _Catalog.model_validate_json(path.read_bytes()).model_dump()


def _project_summary(row: dict[str, Any]) -> dict[str, Any] | None:
    """Validate a saved summary and omit unsupported or malformed metadata."""
    try:
        project = _Project.model_validate_json(row["payload"])
        identity, timestamp = row["entity_id"], row["updated_at_utc"]
        date = datetime.fromisoformat(timestamp)
        valid = (
            isinstance(identity, str)
            and bool(identity.strip())
            and date.tzinfo is not None
            and date.utcoffset() == UTC.utcoffset(date)
            and project.workspace in _WORKSPACES
            and bool(project.name.strip())
        )
        if not valid:
            _invalid_project()
            return None
        return {
            "id": identity,
            "name": project.name,
            "workspace": project.workspace,
            "last_activity": timestamp,
        }
    except KeyError, TypeError, ValueError, ValidationError:
        _invalid_project()
        return None


def _invalid_project() -> None:
    logger.warning("Ignored invalid project summary", extra={"fr_id": "FR-HOME-RECENT"})
