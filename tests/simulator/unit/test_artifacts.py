"""Unit tests for safe Simulation artifact manifests."""

from datetime import UTC, datetime
from pathlib import Path

import pytest
from app.services.simulator.errors import SimulationError, unwrap_simulation_response
from app.services.simulator.reporting import build_artifact_manifest


def test_manifest_rejects_path_escape(tmp_path: Path) -> None:
    """Reject one artifact outside the approved root."""
    root = tmp_path / "root"
    root.mkdir()
    outside = tmp_path / "journal.jsonl"
    outside.write_text("{}\n", encoding="utf-8")
    for name in ("result.json", "report.md"):
        (root / name).write_text("evidence", encoding="utf-8")
    with pytest.raises(SimulationError) as captured:
        unwrap_simulation_response(
            build_artifact_manifest(
                root,
                (outside, root / "result.json", root / "report.md"),
                created_at=datetime(2025, 1, 1, tzinfo=UTC),
            ),
            operation="test.artifacts.build_artifact_manifest",
        )
    assert captured.value.code == "SIM_PERSISTENCE_FAILED"


def test_manifest_hashes_three_canonical_entries(tmp_path: Path) -> None:
    """Hash every non-manifest canonical artifact in stable order."""
    paths = []
    for name in ("journal.jsonl", "result.json", "report.md"):
        path = tmp_path / name
        path.write_text(name, encoding="utf-8")
        paths.append(path)
    manifest = unwrap_simulation_response(
        build_artifact_manifest(
            tmp_path,
            paths,
            created_at=datetime(2025, 1, 1, tzinfo=UTC),
        ),
        operation="test.artifacts.build_artifact_manifest",
    )
    assert tuple(entry.relative_path for entry in manifest.artifacts) == (
        "journal.jsonl",
        "result.json",
        "report.md",
    )


def _completed_run(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Prepare one completed run directory under the default artifact root.

    Args:
        tmp_path: Isolated test directory used as the process working root.
        monkeypatch: pytest patcher redirecting the default artifact root.

    Returns:
        The run's artifact directory containing the canonical result.
    """
    monkeypatch.chdir(tmp_path)
    run_root = tmp_path / "artifacts" / "simulation" / "run-attach"
    run_root.mkdir(parents=True)
    (run_root / "result.json").write_text('{"run_id": "run-attach"}', encoding="utf-8")
    return run_root


def test_attach_rejects_an_absent_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An unknown run fails closed with the not-found code."""
    from app.services.simulator import attach_analytics_report_artifact

    monkeypatch.chdir(tmp_path)
    with pytest.raises(SimulationError) as captured:
        unwrap_simulation_response(
            attach_analytics_report_artifact(
                "run-missing", '{"report": true}', request_id="req-1"
            ),
            operation="test.artifacts.attach",
        )
    assert captured.value.code == "SIMULATION_RESULT_NOT_FOUND"


def test_attach_rejects_invalid_json(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A non-JSON payload is refused before touching the artifact root."""
    from app.services.simulator import attach_analytics_report_artifact

    _completed_run(tmp_path, monkeypatch)
    with pytest.raises(SimulationError) as captured:
        unwrap_simulation_response(
            attach_analytics_report_artifact(
                "run-attach", "{not json", request_id="req-2"
            ),
            operation="test.artifacts.attach",
        )
    assert captured.value.code == "ANALYTICS_REPORT_INVALID"


def test_attach_writes_the_immutable_artifact_once(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The first attachment writes the artifact beside the canonical three."""
    from hashlib import sha256

    from app.services.simulator import attach_analytics_report_artifact

    run_root = _completed_run(tmp_path, monkeypatch)
    payload = '{"sections": [], "non_binding": true}'
    attached = unwrap_simulation_response(
        attach_analytics_report_artifact("run-attach", payload, request_id="req-3"),
        operation="test.artifacts.attach",
    )
    assert attached["status"] == "attached"
    assert attached["artifact_ref"] == "run-attach/analytics-report.json"
    assert attached["sha256"] == sha256(payload.encode("utf-8")).hexdigest()
    written = run_root / "analytics-report.json"
    assert written.read_text(encoding="utf-8") == payload
    # The completed canonical result artifact remains untouched.
    assert (run_root / "result.json").read_text(encoding="utf-8") == (
        '{"run_id": "run-attach"}'
    )


def test_identical_bytes_are_idempotent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Re-attaching identical bytes reports the existing artifact."""
    from app.services.simulator import attach_analytics_report_artifact

    _completed_run(tmp_path, monkeypatch)
    payload = '{"sections": [], "non_binding": true}'
    first = unwrap_simulation_response(
        attach_analytics_report_artifact("run-attach", payload, request_id="req-4"),
        operation="test.artifacts.attach",
    )
    second = unwrap_simulation_response(
        attach_analytics_report_artifact("run-attach", payload, request_id="req-5"),
        operation="test.artifacts.attach",
    )
    assert first["sha256"] == second["sha256"]
    assert second["status"] == "already_attached"


def test_different_bytes_conflict(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Attaching a different report to the same run fails closed."""
    from app.services.simulator import attach_analytics_report_artifact

    _completed_run(tmp_path, monkeypatch)
    unwrap_simulation_response(
        attach_analytics_report_artifact("run-attach", '{"v": 1}', request_id="req-6"),
        operation="test.artifacts.attach",
    )
    with pytest.raises(SimulationError) as captured:
        unwrap_simulation_response(
            attach_analytics_report_artifact(
                "run-attach", '{"v": 2}', request_id="req-7"
            ),
            operation="test.artifacts.attach",
        )
    assert captured.value.code == "ANALYTICS_REPORT_CONFLICT"
