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
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Annotated, Any, Protocol

import psutil
from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.host.logging import get_logger
from app.host.persistence import HostPersistence
from app.host.response import ResponseMetadata, StandardResponse
from app.host.settings import SettingsManager

from ._content import _load_content, _project_summary
from ._releases import ReleaseSource

__all__ = ["About", "Home", "HomeCLI", "create_home_router"]
logger = get_logger(__name__)
_MAX_RECENT = 100
_BEARER_PARTS = 2


def _info(fr: str, **fields: Any) -> None:
    logger.info("%s: completed", fr, extra={"fr_id": fr, **fields})


def _default_constants() -> dict[str, Any]:
    return {
        "application": "HaruQuantAI",
        "version": "2.1.0",
        "build_timestamp": "2026-10-23T00:00:00Z",
        "runtime": f"Python {sys.version.split()[0]} on {sys.platform}",
    }


def _resolve_constants(provider: Any) -> dict[str, Any]:
    if provider is None:
        return _default_constants()
    if hasattr(provider, "get_constants"):
        return dict(provider.get_constants())
    if isinstance(provider, Mapping):
        return dict(provider)
    return _default_constants()


def _extract_bearer_token(header: str | None) -> str | None:
    if not header:
        return None
    parts = header.strip().split()
    if len(parts) == _BEARER_PARTS and parts[0].lower() == "bearer":
        return parts[1]
    return None


class SessionManagerProtocol(Protocol):
    """Optional session manager authorization boundary protocol."""

    def verify_session(self, token: str) -> Any: ...
    def authorize(self, session: Any, scope: str) -> bool: ...


class Home:
    """Welcome and project entry points using explicitly injected providers."""

    def __init__(
        self,
        releases: ReleaseSource,
        *,
        persistence: HostPersistence | None = None,
        constants: Any = None,
    ) -> None:
        self._releases = releases
        self._persistence = (
            persistence if persistence is not None else HostPersistence()
        )
        self._constants = constants

    def _get_constants(self) -> dict[str, Any]:
        return _resolve_constants(self._constants)

    def index(self) -> dict[str, Any]:
        """Return local onboarding and actual host project summaries."""
        data = {**_load_content(), "recent_projects": self.get_recent_projects()}
        _info("FR-HOME-INDEX")
        return data

    @staticmethod
    def _raise_read_failure(response: dict[str, Any]) -> None:
        raise RuntimeError(response.get("message", "Project summary read failed"))

    def get_recent_projects(self, limit: int = 10) -> list[dict[str, Any]]:
        """Return bounded summaries by last activity; never seed empty stores."""
        if type(limit) is not int or not 1 <= limit <= _MAX_RECENT:
            logger.warning("Invalid recent limit", extra={"fr_id": "FR-HOME-RECENT"})
            raise ValueError("Project limit must be an integer between 1 and 100")
        try:
            response = self._persistence.read_records(
                "host_entities",
                filters={"entity_type": "project", "scope": "workspace"},
                limit=limit,
                order_by=("updated_at_utc", "entity_id"),
                descending=True,
            )
            if not response.get("success", False):
                self._raise_read_failure(response)
            rows: list[dict[str, Any]] = response.get("data", {}).get("records", [])
        except Exception:
            logger.error(  # noqa: TRY400 - avoid saved payloads in exception logs
                "Project summary read failed", extra={"fr_id": "FR-HOME-RECENT"}
            )
            raise
        projects = [item for row in rows if (item := _project_summary(row)) is not None]
        _info("FR-HOME-RECENT", count=len(projects))
        return projects

    def check_updates(self) -> dict[str, Any]:
        """Inspect release metadata without installing or downloading updates."""
        current = str(self._get_constants()["version"])
        result = self._releases.check(current)
        _info("FR-HOME-UPDATES", state=result["state"])
        return result


class About:
    """Read-only host metadata and explicitly requested resource diagnostics."""

    def __init__(
        self,
        settings: SettingsManager,
        root: Path | None = None,
        *,
        constants: Any = None,
        resources: Any = None,
        persistence: HostPersistence | None = None,
    ) -> None:
        self._settings, self._root = settings, root
        self._constants = constants
        self._resources = resources
        self._persistence = (
            persistence if persistence is not None else HostPersistence()
        )

    def _get_constants(self) -> dict[str, Any]:
        return _resolve_constants(self._constants)

    def about(self) -> dict[str, Any]:
        """Return host-reported metadata and explicit license unavailability."""
        raw = self._get_constants()
        data = {
            key: raw.get(key, "")
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
        if self._resources is not None and hasattr(
            self._resources, "inspect_resources"
        ):
            res = self._resources.inspect_resources(
                root_path=self._root, settings=self._settings
            )
            result = res.to_dict() if hasattr(res, "to_dict") else dict(res)
        else:
            db_path = self._persistence.database_path
            db_exists = db_path.is_file()
            mem = psutil.virtual_memory()
            result = {
                "status": "OK" if db_exists else "DEGRADED",
                "database": {
                    "exists": db_exists,
                    "path": str(db_path),
                    "error": None if db_exists else "Database file not found",
                },
                "hardware": {
                    "ram_total_bytes": mem.total,
                    "ram_available_bytes": mem.available,
                    "ram_used_pct": mem.percent,
                },
            }
        result["directories"] = self._settings.as_dict().get("workspace_paths", {})
        _info("FR-HOME-DIAGNOSTICS", state=result.get("status", "OK"))
        return result


class HomeCLI:
    """Present Home results without configuring logging or writing output."""

    @staticmethod
    def format_output(data: Mapping[str, Any]) -> str:
        """Serialize headless results for the existing CLI presentation layer."""
        _info("FR-HOME-CLI")
        return json.dumps(dict(data), indent=2, ensure_ascii=False)


def _authorize_request(
    request: Request,
    session_mgr: SessionManagerProtocol | Any,
    require_auth: bool,
) -> None:
    if not require_auth:
        return
    if session_mgr is None:
        raise HTTPException(401, "Active authorized session required.")
    token = _extract_bearer_token(request.headers.get("authorization"))
    session = session_mgr.verify_session(token) if token is not None else None
    scope = (
        "diagnostics:read"
        if request.url.path.endswith("/diagnostics")
        else "settings:read"
    )
    if session is None or not session_mgr.authorize(session, scope):
        status = 401 if session is None else 403
        raise HTTPException(status, "Active authorized session required.")


def create_home_router(
    home: Home,
    about: About,
    *,
    session_mgr: SessionManagerProtocol | Any = None,
    require_auth: bool = False,
) -> APIRouter:
    """Build the authorized Home boundary around host-owned service instances."""

    def _auth_dependency(request: Request) -> None:
        _authorize_request(request, session_mgr, require_auth)

    router = APIRouter(
        prefix="/home", tags=["home"], dependencies=[Depends(_auth_dependency)]
    )

    def _response(data: Any, request: Request) -> dict[str, Any]:
        return StandardResponse.success(
            message="Operation completed",
            metadata=ResponseMetadata(
                operation="home",
                duration_ms=0.0,
                extensions={"request_id": request.headers.get("x-request-id")},
            ),
            data=data,
        )

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
