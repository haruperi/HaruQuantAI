"""WF-SIM-011: verify reports and the artifact manifest from a completed run."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.simulator import (
    build_artifact_manifest,
    build_json_report,
    build_markdown_report,
    dump_simulation_value,
    get_simulation_value_field,
    run_backtest,
    unwrap_simulation_response,
)
from tests.simulator.usage.workflows._support import (
    authority,
    backtest_request,
    dependencies,
    live_tick_dataset,
)

WORKFLOW_ID = "WF-SIM-011"
STAGES = (
    "Execute one bounded canonical run from genuine MT5 evidence.",
    "Read the completed run artifacts from the isolated artifact root.",
    "Verify the manifest and render deterministic JSON and Markdown.",
    "Display the completed result, manifest, and bounded report excerpts.",
)


def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(
        f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}"
    )


def main() -> None:
    """Build and print bounded canonical reporting evidence from an actual run."""
    print("INPUT BOUNDARY — genuine MT5 ticks and a canonical run request")
    # Stage 1 — Execute one bounded canonical run from genuine MT5 evidence.
    _stage(1)
    dataset = live_tick_dataset()
    request = backtest_request(dataset)
    with tempfile.TemporaryDirectory(prefix="wf-sim-011-") as directory:
        root = Path(directory)
        deps = dependencies(root, dataset)
        result = unwrap_simulation_response(
            run_backtest(request, authority(request), deps),
            operation="simulation.workflow.wf_sim_011.run_backtest",
        )
        # Stage 2 — Read the completed run artifacts from the isolated artifact root.
        _stage(2)
        run_id = str(get_simulation_value_field(result, "run_id"))
        artifact_root = deps.artifact_root / run_id
        paths = tuple(
            artifact_root / name
            for name in ("journal.jsonl", "result.json", "report.md")
        )
        # Stage 3 — Verify the manifest and render deterministic JSON and Markdown.
        _stage(3)
        manifest = unwrap_simulation_response(
            build_artifact_manifest(artifact_root, paths, created_at=dataset.end),
            operation="simulation.workflow.wf_sim_011.build_artifact_manifest",
        )
        json_report = unwrap_simulation_response(
            build_json_report(result),
            operation="simulation.workflow.wf_sim_011.build_json_report",
        )
        markdown = unwrap_simulation_response(
            build_markdown_report(result),
            operation="simulation.workflow.wf_sim_011.build_markdown_report",
        )
        # Stage 4 — Display the completed result, manifest, and bounded report excerpts.
        _stage(4)
        print(f"{WORKFLOW_ID} — Reports and Artifact Manifest")
        print("Completed result evidence:", dump_simulation_value(result))
        print("Verified artifact manifest:", dump_simulation_value(manifest))
        print("JSON report excerpt:", json_report[:500])
        print("Markdown report excerpt:", "\n".join(markdown.splitlines()[:12]))
        print("OUTPUT BOUNDARY — verified result, manifest, JSON, and Markdown")


if __name__ == "__main__":
    main()
