"""SYS-WF-004 Data-to-Research-to-approved-Strategy integration."""

from contextlib import AbstractContextManager
from pathlib import Path

from app.services.api import build_research_run_request
from app.services.api.identity import require_auth_context
from app.services.api.workstation.research.routes import router as research_router
from app.services.api.workstation.strategies.routes import router as strategies_router
from app.services.data import build_data_settings, data_settings_context
from app.services.strategy import register_strategy_version
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
        build_data_settings(
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
    return app


def test_sys_wf_004_research_to_reviewed_strategy_candidate(tmp_path: Path) -> None:
    """Verify reviewed Research evidence enters Strategy through its owner API."""
    research_request = build_research_run_request(
        hypothesis="Returns persist over one research bar.",
        dataset=make_dataset(),
        config=make_edge_lab_config(tmp_path),
    )
    app = _api()

    report_status, report = post_json(
        app,
        "/api/v1/research/run",
        research_request.model_dump(mode="json"),
    )
    assert report_status == 200
    assert set(report) == {"status", "message", "data", "error", "metadata"}
    assert report["status"] == "success"
    assert report["error"] is None
    research_report = report["data"]
    assert research_report["schema_id"] == "research.report.v1"
    assert research_report["advisory_only"] is True

    registration = make_registration()
    manifest = registration.manifest.model_copy(
        update={"provenance_refs": (research_report["report_id"],)}
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
        mutation_response = register_strategy_version(
            registration,
            make_auth(),
            make_policy(),
        )

    assert "/api/v1/strategies/registrations" not in {
        route.path for route in strategies_router.routes
    }
    assert mutation_response.data is not None
    assert mutation_response.data.status == "ACCEPTED"
    assert mutation_response.data.validated_ref is not None
    assert mutation_response.data.validated_ref.manifest.provenance_refs == (
        research_report["report_id"],
    )
