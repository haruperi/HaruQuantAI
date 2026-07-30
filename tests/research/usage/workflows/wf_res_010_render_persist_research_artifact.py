"""WF-RES-010: mask, render, and safely persist a Research artifact."""

from __future__ import annotations

import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.research import (
    create_research_value,
    mask_research_artifact,
    render_research_report,
    run_edge_lab_profile,
    write_research_artifact,
)
from app.utils import create_auth_context
from tests.research._support import make_edge_lab_config
from tests.research.usage.workflows._support import limits, live_market_dataset

WORKFLOW_ID = "WF-RES-010"
STAGES = (
    "Receive a versioned Research result, AuthContext, and approved destination.",
    "Mask sensitive and forbidden forward fields before serialization.",
    "Render the bounded report without performing I/O.",
    "Atomically persist the masked result and return ArtifactReference.",
)
type AuthContext = Any


# fmt: off
def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}")
# fmt: on


def _auth() -> AuthContext:
    """Return a dev-only Research write authority."""
    return create_auth_context(
        contract_version="v1",
        schema_id="utils.auth_context.v1",
        principal_id="research-workflow",
        principal_type="SERVICE_ACCOUNT",
        roles=("researcher",),
        permissions=("research:write",),
        scopes=("research",),
        tenant_or_environment="dev",
        request_id="req-01234567-89ab-4def-8123-456789abcdef",
        workflow_id="wf-01234567-89ab-4def-8123-456789abcdef",
        correlation_id="cor-01234567-89ab-4def-8123-456789abcdef",
        issued_at=datetime.now(UTC),
    )


def main() -> None:
    """Execute the documented artifact workflow."""
    print(f"{WORKFLOW_ID} — Render and Persist Research Artifact")
    print("INPUT BOUNDARY — ResearchReport, AuthContext v1, approved temp destination")
    with tempfile.TemporaryDirectory(prefix="wf-res-010-") as directory:
        root = Path(directory).resolve()

        # Stage 1 — Receive a versioned Research result, AuthContext, and approved destination.
        _stage(1)
        response = run_edge_lab_profile(
            live_market_dataset(),
            hypothesis="Bounded MT5 returns contain measurable structure.",
            config=make_edge_lab_config(root, selected_stages=("data", "metrics")),
        )
        assert response.status == "success"
        report = response.data

        # Stage 2 — Mask sensitive and forbidden forward fields before serialization.
        _stage(2)
        assert report is not None
        masked = mask_research_artifact(
            {
                "schema_id": report.schema_id,
                "report_id": report.report_id,
                "hypothesis": report.hypothesis,
                "evidence": dict(report.evidence),
                "advisory_only": report.advisory_only,
            }
        )

        # Stage 3 — Render the bounded report without performing I/O.
        _stage(3)
        rendered = render_research_report(report, format="markdown")
        assert isinstance(rendered, str)
        assert masked["report_id"] == report.report_id

        # Stage 4 — Atomically persist the masked result and return ArtifactReference.
        _stage(4)
        reference = write_research_artifact(
            report,
            root / "report.json",
            config=create_research_value("ArtifactWriteConfig", root, "json"),
            auth=_auth(),
            limits=limits(),
        )
        print("Rendered bytes:", len(rendered.encode("utf-8")))
        print("OUTPUT BOUNDARY — typed ArtifactReference:", reference.relative_path)


if __name__ == "__main__":
    main()
