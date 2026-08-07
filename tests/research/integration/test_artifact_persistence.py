"""Integration evidence for WF-RES-010: artifact persistence."""

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.services.data import (
    build_data_settings,
    build_statement_plan,
    build_transaction_request,
    data_settings_context,
    execute_transaction,
    run_data_migrations,
)
from app.services.research import (
    create_research_value,
    is_research_value,
    write_research_artifact,
)
from app.utils import create_auth_context, generate_id, get_logger

logger = get_logger(__name__)

type AuthContext = Any

_HASH = "e" * 64


def _report() -> object:
    """Build a canonical advisory report."""
    return create_research_value(
        "ResearchReport",
        "v1",
        "research.report.v1",
        "research-report-int",
        "Integration test",
        {"data": {"rows": 1}},
        {"statistics": 7},
        _HASH,
        _HASH,
        ("fixture",),
        (),
        datetime.now(UTC),
        {"research": "v1"},
        1.0,
        True,
    )


def _auth() -> AuthContext:
    """Build a valid AuthContext."""
    return create_auth_context(
        contract_version="v1",
        schema_id="utils.auth_context.v1",
        principal_id="researcher-int",
        principal_type="USER",
        roles=("researcher",),
        permissions=("research:write",),
        scopes=("research",),
        tenant_or_environment="dev",
        request_id="req-01234567-89ab-4def-8123-456789abcdef",
        workflow_id="wf-01234567-89ab-4def-8123-456789abcdef",
        correlation_id="cor-01234567-89ab-4def-8123-456789abcdef",
        issued_at=datetime.now(UTC),
    )


def test_persist_masked_artifact_atomically(tmp_path: Path) -> None:
    """WF-RES-010: masked artifact is atomically persisted and audited."""
    logger.debug("Testing Research artifact persistence integration")
    root = tmp_path / "artifacts"
    config = create_research_value("ArtifactWriteConfig", root, "json")
    destination = root / "integration_report.json"
    settings = build_data_settings(
        database_url="sqlite:///research.db",
        data_dir=tmp_path,
        sqlite_busy_timeout_seconds=1.0,
        write_lock_lease_seconds=10.0,
        approved_storage_roots=(tmp_path,),
    )
    with data_settings_context(settings):
        run_data_migrations(generate_id("req"))
        ref = write_research_artifact(
            _report(),
            destination,
            config=config,
            auth=_auth(),
            limits=create_research_value(
                "ResearchResourceLimits", 500_000, 600.0, 52_428_800
            ),
        )
        overwrite_ref = write_research_artifact(
            _report(),
            destination,
            config=create_research_value("ArtifactWriteConfig", root, "json", True),
            auth=_auth(),
            limits=create_research_value(
                "ResearchResourceLimits", 500_000, 600.0, 52_428_800
            ),
        )
        stored = execute_transaction(
            build_transaction_request(
                plan=build_statement_plan(
                    statements=(
                        "SELECT sha256, audit_event_id FROM research_artifacts "
                        "WHERE relative_path = ?",
                    ),
                    parameter_sets=((ref.relative_path.as_posix(),),),
                    max_rows=1,
                ),
                request_id=generate_id("req"),
            )
        )
    assert is_research_value(ref, "ArtifactReference")
    assert destination.exists()
    assert ref.sha256
    assert overwrite_ref.sha256 == ref.sha256
    assert ref.audit_event_id.startswith("evt-")
    assert stored.status == "success"
    assert stored.data is not None
    assert stored.data.rows[0]["sha256"] == ref.sha256
    assert stored.data.rows[0]["audit_event_id"] == overwrite_ref.audit_event_id
