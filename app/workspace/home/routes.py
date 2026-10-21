"""Host-backed welcome workspace, About projection and HTTP entry points.

Description:
    Combines original local onboarding with persisted project summaries and
    injected host metadata/resources. Authorized routes preserve host envelopes.
Purpose:
    FEAT-HOME-DASHBOARD: Welcome, release inspection and system information.
Key Capabilities:
    - FR-HOME-INDEX: Home.index() returns local onboarding (INFO).
    - FR-HOME-RECENT: Home.get_recent_projects() reads host summaries (INFO).
    - FR-HOME-UPDATES: Home.check_updates() delegates bounded checks (INFO).
    - FR-HOME-ABOUT: About.about() projects host metadata (INFO).
    - FR-HOME-DIAGNOSTICS: About.diagnostics() delegates resource probes (INFO).
    - FR-HOME-CLI: HomeCLI.format_output() presents headless results (INFO).
    Tests verify structured fr_id logs, failures and authorization boundaries.
Python API Usage:
    from app.workspace.home import Home, About
    # Inject host constants, resources, settings and release capabilities.
CLI Usage:
    uv run python -m app.cli home --json
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Annotated, Any

from app.host.logging import get_logger
from app.host.persistence import HostPersistence
from app.host.resources import ResourceMonitor
from app.host.response import StandardResponse
from app.host.session import SessionManager
from app.host.settings import SettingsManager
from app.host.transport import ServletConstants, extract_bearer_token
from fastapi import APIRouter, Depends, HTTPException, Query, Request

from ._content import _load_content, _project_summary
from ._releases import ReleaseSource

__all__ = ["About", "Home", "HomeCLI", "create_home_router"]
logger = get_logger(__name__)
_MAX_RECENT = 100


def _info(fr: str, **fields: Any) -> None:
    logger.info("%s: completed", fr, extra={"fr_id": fr, **fields})


class Home:
    """Welcome and project entry points using explicitly injected providers."""

    def __init__(self, constants: ServletConstants, releases: ReleaseSource) -> None:
        self._constants, self._releases = constants, releases

    def index(self) -> dict[str, Any]:
        """Return local onboarding and actual host project summaries."""
        data = {**_load_content(), "recent_projects": self.get_recent_projects()}
        _info("FR-HOME-INDEX")
        return data

    def get_recent_projects(self, limit: int = 10) -> list[dict[str, Any]]:
        """Return bounded summaries by last activity; never seed empty stores."""
        if type(limit) is not int or not 1 <= limit <= _MAX_RECENT:
            logger.warning("Invalid recent limit", extra={"fr_id": "FR-HOME-RECENT"})
            raise ValueError("Project limit must be an integer between 1 and 100")
        try:
            rows = HostPersistence.read_records(
                "host_entities",
                {"entity_type": "project", "scope": "workspace"},
                limit=limit,
                order_by="updated_at_utc DESC, entity_id ASC",
            )
        except HostPersistence.Error:
            logger.error(  # noqa: TRY400 - avoid saved payloads in exception logs
                "Project summary read failed", extra={"fr_id": "FR-HOME-RECENT"}
            )
            raise
        projects = [item for row in rows if (item := _project_summary(row)) is not None]
        _info("FR-HOME-RECENT", count=len(projects))
        return projects

    def check_updates(self) -> dict[str, Any]:
        """Inspect release metadata without installing or downloading updates."""
        current = str(self._constants.get_constants()["version"])
        result = self._releases.check(current)
        _info("FR-HOME-UPDATES", state=result["state"])
        return result


class About:
    """Read-only host metadata and explicitly requested resource diagnostics."""

    def __init__(
        self,
        constants: ServletConstants,
        resources: ResourceMonitor,
        settings: SettingsManager,
        root: Path | None = None,
    ) -> None:
        self._constants, self._resources = constants, resources
        self._settings, self._root = settings, root

    def about(self) -> dict[str, Any]:
        """Return host-reported metadata and explicit license unavailability."""
        raw = self._constants.get_constants()
        data = {
            key: raw[key]
            for key in ("application", "version", "build_timestamp", "runtime")
        }
        data.update(
            metadata_source="host-reported",
            license={
                "state": "unavailable",
                "reason": "No license provider registered.",
            },
        )
        _info("FR-HOME-ABOUT")
        return data

    def diagnostics(self) -> dict[str, Any]:
        """Delegate system/database probes and expose configured directory paths."""
        result = self._resources.inspect_resources(
            root_path=self._root, settings=self._settings
        ).to_dict()
        result["directories"] = self._settings.as_dict().get("workspace_paths", {})
        _info("FR-HOME-DIAGNOSTICS", state=result["status"])
        return result


class HomeCLI:
    """Present Home results without configuring logging or writing output."""

    @staticmethod
    def format_output(data: Mapping[str, Any]) -> str:
        """Serialize headless results for the existing CLI presentation layer."""
        _info("FR-HOME-CLI")
        return json.dumps(dict(data), indent=2, ensure_ascii=False)


def create_home_router(
    home: Home, about: About, *, session_mgr: SessionManager, require_auth: bool = False
) -> APIRouter:
    """Build the authorized Home boundary around host-owned service instances."""

    def _authorize(request: Request) -> None:
        if not require_auth:
            return
        token = extract_bearer_token(request.headers.get("authorization"))
        session = session_mgr.verify_session(token) if token is not None else None
        scope = (
            "diagnostics:read"
            if request.url.path.endswith("/diagnostics")
            else "settings:read"
        )
        if session is None or not session_mgr.authorize(session, scope):
            raise HTTPException(
                401 if session is None else 403, "Active authorized session required."
            )

    router = APIRouter(
        prefix="/home", tags=["home"], dependencies=[Depends(_authorize)]
    )

    def _response(data: Any, request: Request) -> dict[str, Any]:
        return StandardResponse.success(
            data=data, request_id=request.headers.get("x-request-id")
        ).to_dict()

    @router.get("")
    def _index(request: Request) -> dict[str, Any]:
        return _response(home.index(), request)

    @router.get("/recent-projects")
    def _recent(
        request: Request, limit: Annotated[int, Query(ge=1, le=100)] = 10
    ) -> dict[str, Any]:
        return _response(home.get_recent_projects(limit), request)

    @router.get("/updates")
    def _updates(request: Request) -> dict[str, Any]:
        return _response(home.check_updates(), request)

    @router.get("/about")
    def _about(request: Request) -> dict[str, Any]:
        return _response(about.about(), request)

    @router.get("/diagnostics")
    def _diagnostics(request: Request) -> dict[str, Any]:
        return _response(about.diagnostics(), request)

    return router
