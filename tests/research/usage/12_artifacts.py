"""Executable Research artifacts usage example.

Demonstrates safe artifact persistence and migration definition.
"""

import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.research import (
    build_research_migration_request,
    create_research_value,
    write_research_artifact,
)
from app.utils.contracts.auth import AuthContext

_HASH = "e" * 64


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


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
    return AuthContext(
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
    print("Research Example 12: Artifact Persistence")
    import tempfile

    root = Path(tempfile.mkdtemp()) / "artifacts"
    config = create_research_value("ArtifactWriteConfig", root, "json")
    destination = root / "report.json"
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


def main() -> None:
    """Run Research artifacts usage example."""
    fr_res_097()
    fr_res_098()


if __name__ == "__main__":
    main()
