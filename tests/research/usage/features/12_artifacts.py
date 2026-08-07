"""Executable Research artifacts usage example.

Demonstrates safe artifact persistence and migration definition.
"""

import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.data import (
    build_data_settings,
    data_settings_context,
    run_data_migrations,
)
from app.services.research import (
    build_research_migration_request,
    create_research_value,
    write_research_artifact,
)
from app.utils import create_auth_context, generate_id

type AuthContext = Any

_HASH = "e" * 64


def _feature_header(title: str) -> None:
    """Print the feature header banner."""
    print(f"SUCCESS: {title}")


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"SUCCESS: {title}")


def _format_result(obj: Any) -> str:
    """Dynamically format the output result type name and field/key signature."""
    cls = type(obj)
    type_name = cls.__name__
    if hasattr(cls, "model_fields"):
        keys = ", ".join(cls.model_fields.keys())
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    if isinstance(obj, dict):
        keys = ", ".join(obj.keys())
        return f"Output Result -> dict({keys}) : dict"
    if hasattr(obj, "__dict__"):
        keys = ", ".join(vars(obj).keys())
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    return f"Output Result -> {type_name} : {type_name}"


def _report() -> object:
    """Build a canonical advisory report."""
    return create_research_value(
        "ResearchReport",
        "v1",
        "research.report.v1",
        "research-report-test",
        "Test hypothesis",
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
        principal_id="researcher-001",
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


def fr_res_097() -> None:
    """FR-RES-097: Mask, validate, and atomically persist an artifact."""
    _header("FR-RES-097: Mask, validate, and atomically persist an artifact.")
    with tempfile.TemporaryDirectory(prefix="research-artifacts-") as directory:
        data_dir = Path(directory)
        settings = build_data_settings(
            database_url="sqlite:///research.db",
            data_dir=data_dir,
            sqlite_busy_timeout_seconds=1.0,
            write_lock_lease_seconds=10.0,
            approved_storage_roots=(data_dir,),
        )
        root = data_dir / "artifacts"
        config = create_research_value("ArtifactWriteConfig", root, "json")
        destination = root / "report.json"
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
    print(f"FR-RES-097 path={ref.relative_path} atomic={ref.atomic}")


def fr_res_098() -> None:
    """FR-RES-098: Return the deterministic Research-owned migration."""
    _header("FR-RES-098: Return the deterministic Research-owned migration.")
    request = build_research_migration_request(
        "req-01234567-89ab-4def-8123-456789abcdef"
    )
    print(f"FR-RES-098 domain={request.domain} steps={len(request.steps)}")


def fr_res_105() -> None:
    """FR-RES-105: Keep migration definitions in the migration package."""
    _header("FR-RES-105: Keep migration definitions in the migration package.")
    request = build_research_migration_request(
        "req-01234567-89ab-4def-8123-456789abcdef"
    )
    print(f"FR-RES-105 migration_module={request.steps[0].domain}")


def fr_res_106() -> None:
    """FR-RES-106: Demonstrate the strict traceable artifact table."""
    _header("FR-RES-106: Demonstrate the strict traceable artifact table.")
    request = build_research_migration_request(
        "req-01234567-89ab-4def-8123-456789abcdef"
    )
    statements = " ".join(request.steps[0].statements)
    print(
        "FR-RES-106 strict_traceable=",
        all(
            token in statements
            for token in ("STRICT", "request_id", "correlation_id", "audit_event_id")
        ),
    )


def main() -> None:
    """Run Research artifacts usage example."""
    _feature_header(
        "FEATURE: FEAT-RES-12 — artifacts/ — Safe Research Artifact Persistence\n\n"
        "Purpose: Govern research artifact persistence, schema migrations, and masked JSON/Markdown storage.\n\n"
        "Module flow:\n"
        "-> Stage 1: Artifact metadata envelope construction\n-> Stage 2: Masked JSON/Markdown serialization\n-> Stage 3: Database ledger migration and artifact persistence"
    )

    fr_res_097()
    fr_res_098()
    fr_res_105()
    fr_res_106()


if __name__ == "__main__":
    main()
