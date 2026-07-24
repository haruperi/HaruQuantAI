"""SYS-WF-004 Data-to-Research-to-approved-Strategy integration."""

from contextlib import AbstractContextManager
from pathlib import Path

from app.services.api import ResearchRunRequest
from app.services.api.identity import require_auth_context
from app.services.api.routes import strategies
from app.services.api.routes.research import router as research_router
from app.services.api.routes.strategies import router as strategies_router
from app.services.data import DataSettings, data_settings_context
from fastapi import FastAPI

from tests.api._support import post_json
from tests.research._support import make_dataset, make_edge_lab_config
from tests.strategy.unit.test_catalog import make_registration
from tests.strategy.unit.test_models import make_auth, make_policy


def _storage(root: Path) -> AbstractContextManager[None]:
    """Build isolated SYS-WF-004 persistence settings.

    Args:
        root: Temporary data root.

    Returns:
        Data settings context.
    """
    return data_settings_context(
        DataSettings(
            database_url="sqlite:///sys-wf-004.sqlite3",
            data_dir=root,
            sqlite_busy_timeout_seconds=1.5,
            write_lock_lease_seconds=30,
        )
    )


def _api() -> FastAPI:
    """Build authenticated Research and Strategy HTTP composition.

    Returns:
        Configured FastAPI application.
    """
    app = FastAPI()
    app.include_router(research_router)
    app.include_router(strategies_router)
    auth = make_auth().model_copy(
        update={
            "permissions": (
                "research:run",
                "strategy:register",
                "strategy:update",
            )
        }
    )
    app.dependency_overrides[require_auth_context] = lambda: auth
    app.dependency_overrides[strategies._strategy_validation_policy] = make_policy
    return app


def test_sys_wf_004_research_to_reviewed_strategy_candidate(tmp_path: Path) -> None:
    """Verify advisory evidence requires explicit API approval to register."""
    research_request = ResearchRunRequest(
        hypothesis="Returns persist over one research bar.",
        dataset=make_dataset(),
        config=make_edge_lab_config(tmp_path),
    )
    app = _api()

    report_status, report = post_json(
        app,
        "/api/research/run",
        research_request.model_dump(mode="json"),
    )
    assert report_status == 200
    assert report["schema_id"] == "research.report.v1"
    assert report["advisory_only"] is True

    registration = make_registration()
    manifest = registration.manifest.model_copy(
        update={"provenance_refs": (report["report_id"],)}
    )
    registration = registration.model_copy(
        update={
            "manifest": manifest,
            "provenance_refs": manifest.provenance_refs,
            "reason": "human reviewed advisory Research evidence",
            "authorization_ref": "approval-sys-wf-004",
        }
    )

    with _storage(tmp_path):
        mutation_status, mutation = post_json(
            app,
            "/api/strategies/registrations",
            registration.model_dump(mode="json"),
        )

    assert mutation_status == 200
    assert mutation["status"] == "ACCEPTED"
    assert mutation["validated_ref"]["manifest"]["provenance_refs"] == [
        report["report_id"]
    ]
