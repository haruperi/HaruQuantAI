"""Validate Phase 0 contracts, generated evidence, fixtures, and readiness gates."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq

from scripts import (
    generate_phase0_evidence,
)

REPO = Path(__file__).resolve().parent.parent
EVIDENCE = REPO / "docs/dev/evidence"
PLAN = REPO / "docs/dev/Phased_Feature_Implementation_Plan.md"
FEATURE_EVIDENCE_REQUIRED = {
    "feature_id",
    "task_id",
    "status",
    "owner_specification",
    "baseline_commit",
    "acceptance_commit",
    "requirements",
    "catalogue_entries",
    "stages",
    "commands",
    "review",
}
STAGES = {"contract", "provider", "composition", "interfaces", "ui", "end_to_end"}
EXPECTED_FEATURES = 205
EXPECTED_PREPARATIONS = 8
EXPECTED_REQUIRED_EDGES = 477
EXPECTED_OPERATION_EDGES = 233
EXPECTED_REQUIREMENTS = 575
EXPECTED_LOCAL_NFRS = 276
EXPECTED_READMES = 18
EXPECTED_FIXTURES = 3
EXPECTED_EXTERNAL_ITEMS = 8
EXPECTED_PERFORMANCE_SAMPLES = 7
EXPECTED_PHASES = 16
ACCEPTANCE_REF_RE = re.compile(
    r"(?:[a-f0-9]{40}|task-closeout:[A-Za-z0-9][A-Za-z0-9._-]+)"
)


def _load(path: Path) -> dict[str, Any]:
    """Load one JSON object.

    Returns:
        Parsed JSON object.

    Raises:
        TypeError: If the document root is not a JSON object.
    """
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        message = f"{path.relative_to(REPO)} must contain a JSON object"
        raise TypeError(message)
    return value


def _sha256(path: Path) -> str:
    """Return the SHA-256 digest of one file."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _sha256_bytes(value: bytes) -> str:
    """Return the SHA-256 digest of an immutable byte sequence."""
    return hashlib.sha256(value).hexdigest()


def _git_file_bytes(object_id: str, path: str) -> bytes:
    """Read one repository file exactly as stored at a Git object.

    Args:
        object_id: Commit or tree object containing the file.
        path: Repository-relative POSIX path.

    Returns:
        Exact blob bytes from the recorded Git object.

    Raises:
        ValueError: If the object/path pair cannot be read.
    """
    result = subprocess.run(
        ["git", "show", f"{object_id}:{path}"],
        cwd=REPO,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        message = f"cannot read frozen baseline file {object_id}:{path}"
        raise ValueError(message)
    return result.stdout


def _git_path_object(object_id: str, path: str) -> str:
    """Resolve the exact Git object stored at a repository path.

    Args:
        object_id: Commit or tree containing the path.
        path: Repository-relative POSIX path.

    Returns:
        The resolved object ID.

    Raises:
        ValueError: If the object/path pair cannot be resolved.
    """
    result = subprocess.run(
        ["git", "rev-parse", f"{object_id}:{path}"],
        cwd=REPO,
        capture_output=True,
        check=False,
        text=True,
    )
    resolved = result.stdout.strip()
    if result.returncode != 0 or not re.fullmatch(r"[a-f0-9]{40}", resolved):
        message = f"cannot resolve frozen baseline object {object_id}:{path}"
        raise ValueError(message)
    return resolved


def _valid_acceptance_reference(value: object) -> bool:
    """Return whether a value identifies a commit or Task close-out receipt."""
    return isinstance(value, str) and ACCEPTANCE_REF_RE.fullmatch(value) is not None


def _git_is_ancestor(ancestor: str, descendant: str) -> bool:
    """Return whether one commit is an ancestor of another commit."""
    result = subprocess.run(
        ["git", "merge-base", "--is-ancestor", ancestor, descendant],
        cwd=REPO,
        capture_output=True,
        check=False,
    )
    return result.returncode == 0


def _accepted_provider_precedes_consumer(
    provider_task: dict[str, Any],
    consumer_task: dict[str, Any],
) -> bool:
    """Prove an accepted provider was delivered before a consumer baseline.

    Args:
        provider_task: Parsed provider task from the phased plan.
        consumer_task: Parsed consumer task from the phased plan.

    Returns:
        Whether exact terminal manifests and Git ancestry prove delivery order.
    """
    try:
        provider = _load(REPO / str(provider_task["evidence_path"]))
        consumer = _load(REPO / str(consumer_task["evidence_path"]))
    except KeyError, OSError, TypeError, ValueError, json.JSONDecodeError:
        return False

    for payload, task in ((provider, provider_task), (consumer, consumer_task)):
        if (
            payload.get("feature_id") != task.get("feature_id")
            or payload.get("task_id") != task.get("task_id")
            or payload.get("status") != "ACCEPTED"
        ):
            return False

    provider_commit = provider.get("acceptance_commit")
    consumer_baseline = consumer.get("baseline_commit")
    if not (
        isinstance(provider_commit, str)
        and re.fullmatch(r"[a-f0-9]{40}", provider_commit)
        and isinstance(consumer_baseline, str)
        and re.fullmatch(r"[a-f0-9]{40}", consumer_baseline)
    ):
        return False
    return _git_is_ancestor(provider_commit, consumer_baseline)


def _validate_task_progress(
    live_tasks: list[dict[str, Any]],
    baseline_tasks: list[dict[str, Any]],
) -> list[str]:
    """Validate live tracker identity and monotonic completion against baseline.

    Args:
        live_tasks: Parsed tasks from the current execution tracker.
        baseline_tasks: Parsed tasks from the frozen Phase 0 plan blob.

    Returns:
        Every identity/order or completion-regression error.
    """
    errors: list[str] = []
    live_identity = [
        (str(task["task_id"]), str(task["feature_id"])) for task in live_tasks
    ]
    baseline_identity = [
        (str(task["task_id"]), str(task["feature_id"])) for task in baseline_tasks
    ]
    if live_identity != baseline_identity:
        errors.append("live task identity/order differs from the Phase 0 baseline")

    live_complete = {
        str(task["task_id"]) for task in live_tasks if bool(task["complete"])
    }
    baseline_complete = {
        str(task["task_id"]) for task in baseline_tasks if bool(task["complete"])
    }
    regressed = sorted(baseline_complete - live_complete)
    if regressed:
        errors.append(
            "live tracker regressed completed Phase 0 tasks: " + ", ".join(regressed)
        )
    return errors


def _git_object_exists(object_id: str) -> bool:
    """Return whether an object ID exists in the local Git object store."""
    result = subprocess.run(
        ["git", "cat-file", "-e", object_id],
        cwd=REPO,
        capture_output=True,
        check=False,
    )
    return result.returncode == 0


def _git_path_is_ignored(path: Path) -> bool:
    """Return whether Git ignore rules exclude a required evidence path."""
    result = subprocess.run(
        ["git", "check-ignore", "--quiet", "--", str(path.relative_to(REPO))],
        cwd=REPO,
        check=False,
    )
    return result.returncode == 0


def _readme_paths() -> list[Path]:
    """Return all authoritative domain README paths."""
    return [
        *sorted((REPO / "app/services").glob("*/README.md")),
        REPO / "app/ui/README.md",
    ]


def validate() -> list[str]:  # noqa: C901, PLR0912, PLR0915
    """Return every Phase 0 validation error without failing at the first one."""
    errors: list[str] = []
    plan_text = PLAN.read_text(encoding="utf-8")
    tasks = generate_phase0_evidence.parse_plan(plan_text)
    task_ids = [str(task["task_id"]) for task in tasks]
    feature_ids = [str(task["feature_id"]) for task in tasks]
    feature_set = set(feature_ids)
    if len(tasks) != EXPECTED_FEATURES or len(feature_set) != EXPECTED_FEATURES:
        errors.append("phased plan must contain 205 unique feature tasks")
    if len(set(task_ids)) != EXPECTED_FEATURES:
        errors.append("phased plan task IDs must be unique")
    preparations = re.findall(
        r"^### - \[(?P<mark>[ xX])\] Preparation (?P<task>0\.0[1-8])",
        plan_text,
        flags=re.MULTILINE,
    )
    if len(preparations) != EXPECTED_PREPARATIONS or any(
        mark.lower() != "x" for mark, _ in preparations
    ):
        errors.append("all eight Phase 0 preparation headings must be checked")

    manifest = _load(EVIDENCE / "baseline-manifest.json")
    baseline = manifest.get("baseline", {})
    if manifest.get("$schema") != "./phase-0-evidence-schema.json":
        errors.append("baseline manifest references the wrong schema")
    baseline_head = str(baseline.get("repository_head", ""))
    baseline_plan_path = str(baseline.get("plan_path", ""))
    try:
        baseline_plan_bytes = _git_file_bytes(baseline_head, baseline_plan_path)
        baseline_plan_blob = _git_path_object(baseline_head, baseline_plan_path)
        baseline_tasks = generate_phase0_evidence.parse_plan(
            baseline_plan_bytes.decode("utf-8")
        )
    except (UnicodeDecodeError, ValueError) as error:
        errors.append(str(error))
        baseline_tasks = []
        baseline_plan_bytes = b""
        baseline_plan_blob = ""
    if baseline.get("plan_git_blob") != baseline_plan_blob:
        errors.append("frozen baseline plan Git blob is stale")
    if baseline.get("plan_sha256") != _sha256_bytes(baseline_plan_bytes):
        errors.append("frozen baseline plan SHA-256 is stale")
    legacy_plan_sha = baseline.get("legacy_unattested_plan_sha256")
    if (
        legacy_plan_sha != generate_phase0_evidence.LEGACY_UNATTESTED_PLAN_SHA256
        or legacy_plan_sha == baseline.get("plan_sha256")
    ):
        errors.append("legacy unattested plan SHA-256 provenance is invalid")
    if baseline_tasks:
        errors.extend(_validate_task_progress(tasks, baseline_tasks))
    if feature_ids != manifest.get("feature_ids"):
        errors.append("live feature identity/order differs from baseline manifest")
    register = REPO / str(baseline.get("register_path", ""))
    if not register.is_file() or baseline.get("register_sha256") != _sha256(register):
        errors.append("baseline register path or SHA-256 is stale")
    for key in ("repository_head", "original_spec_blob", "pinned_spec_blob"):
        object_id = str(baseline.get(key, ""))
        if not re.fullmatch(r"[a-f0-9]{40}", object_id) or not _git_object_exists(
            object_id
        ):
            errors.append(f"baseline {key} is not an available Git object")

    graph = _load(EVIDENCE / "source/dependency-graph.json")
    required_edges = graph.get("required_edges", [])
    operation_edges = graph.get("operation_edges", [])
    if (
        len(graph.get("nodes", [])) != EXPECTED_FEATURES
        or set(graph.get("nodes", [])) != feature_set
    ):
        errors.append("dependency graph node set differs from the plan")
    if len(required_edges) != EXPECTED_REQUIRED_EDGES:
        errors.append(
            f"dependency graph must enumerate {EXPECTED_REQUIRED_EDGES} required edges"
        )
    if len(operation_edges) != EXPECTED_OPERATION_EDGES:
        errors.append("dependency graph must enumerate 233 operation edges")
    order = {feature: index for index, feature in enumerate(feature_ids)}
    tasks_by_feature = {str(task["feature_id"]): task for task in tasks}
    for edge in required_edges:
        if (
            edge.get("provider") not in feature_set
            or edge.get("consumer") not in feature_set
        ):
            errors.append(f"required edge has unknown endpoint: {edge}")
        elif order[str(edge["provider"])] >= order[str(edge["consumer"])] and not (
            _accepted_provider_precedes_consumer(
                tasks_by_feature[str(edge["provider"])],
                tasks_by_feature[str(edge["consumer"])],
            )
        ):
            errors.append(f"required provider is not earlier: {edge}")
    for edge in operation_edges:
        missing = {
            "provider",
            "consumer",
            "guard",
            "test_owner_task",
            "test_owner_feature",
            "readiness",
        } - set(edge)
        if missing:
            errors.append(f"operation edge is missing {sorted(missing)}: {edge}")
        if (
            edge.get("provider") not in feature_set
            or edge.get("consumer") not in feature_set
        ):
            errors.append(f"operation edge has unknown endpoint: {edge}")

    baseline_features = _load(EVIDENCE / "feature-baseline.json").get("features", [])
    path_bindings = _load(EVIDENCE / "path-bindings.json").get("bindings", [])
    usage_bindings = _load(EVIDENCE / "usage-bindings.json").get("bindings", [])
    for label, rows in (
        ("feature baseline", baseline_features),
        ("path bindings", path_bindings),
        ("usage bindings", usage_bindings),
    ):
        ids = [row.get("feature_id") for row in rows]
        if len(ids) != EXPECTED_FEATURES or set(ids) != feature_set:
            errors.append(f"{label} must cover the exact 205-feature set")
    requirement_status = _load(EVIDENCE / "requirement-status.json")
    if len(requirement_status.get("requirements", [])) != EXPECTED_REQUIREMENTS:
        errors.append("requirement status must enumerate 575 FRs")
    if len(requirement_status.get("local_nfrs", [])) != EXPECTED_LOCAL_NFRS:
        errors.append("requirement status must enumerate 276 local NFRs")

    readmes = _readme_paths()
    if len(readmes) != EXPECTED_READMES:
        errors.append(f"expected 18 authoritative domain READMEs, found {len(readmes)}")
    documented_features: list[str] = []
    forbidden = (
        "literal binding remains open",
        "BINDING_PENDING",
        "HaruQuantAI_Phased_Feature_Implementation_Plan.md",
        "HaruQuantAI_Feature_Requirement_Traceability_Register.md",
        "SQX/HaruQuantAI_Unified_Specification.md",
    )
    for readme in readmes:
        content = readme.read_text(encoding="utf-8")
        documented_features.extend(
            re.findall(
                r"^> \*\*Feature ID:\*\* `(FEAT-[A-Z0-9_-]+)`", content, re.MULTILINE
            )
        )
        for marker in forbidden:
            if marker in content:
                errors.append(f"{readme.relative_to(REPO)} retains {marker!r}")
        if re.search(r"^\| NOT_REVALIDATED \| `[^`]+@\d+`", content, re.MULTILINE):
            errors.append(
                f"{readme.relative_to(REPO)} retains an open contract table row"
            )
    if (
        len(documented_features) != EXPECTED_FEATURES
        or set(documented_features) != feature_set
    ):
        errors.append("domain README cards must cover the exact 205-feature set once")

    fixture_manifest = _load(EVIDENCE / "fixture-manifest.json")
    fixtures = fixture_manifest.get("fixtures", [])
    if len(fixtures) != EXPECTED_FIXTURES:
        errors.append("fixture manifest must enumerate three checked-in fixtures")
    for fixture in fixtures:
        path = REPO / str(fixture.get("path", ""))
        if not path.is_file():
            errors.append(f"fixture is missing: {path.relative_to(REPO)}")
            continue
        if _git_path_is_ignored(path):
            errors.append(
                f"fixture is excluded by Git ignore: {path.relative_to(REPO)}"
            )
        if fixture.get("sha256") != _sha256(path):
            errors.append(f"fixture hash mismatch: {path.relative_to(REPO)}")
        parquet_metadata = (
            pq.read_metadata(path)  # type: ignore[no-untyped-call]
            if path.suffix == ".parquet"
            else None
        )
        if parquet_metadata is not None and parquet_metadata.num_rows != fixture.get(
            "records"
        ):
            errors.append(f"fixture record mismatch: {path.relative_to(REPO)}")

    external = _load(EVIDENCE / "external-evidence-calendar.json")
    evidence_items = external.get("evidence_items", [])
    if len(evidence_items) != EXPECTED_EXTERNAL_ITEMS:
        errors.append("external evidence calendar must contain eight EVD items")
    for item in evidence_items:
        if item.get("owner") not in feature_set:
            errors.append(f"external evidence has unknown owner: {item.get('item_id')}")
        if not item.get("due_before") or not item.get("blocked_claim"):
            errors.append(
                f"external evidence lacks due gate/block scope: {item.get('item_id')}"
            )
        if (
            item.get("status") == "OPEN_EXTERNAL"
            and item.get("evidence_path") is not None
        ):
            item_id = item.get("item_id")
            errors.append(
                f"open external evidence cannot cite fabricated proof: {item_id}"
            )
    ticks: dict[str, Any] = next(
        (item for item in evidence_items if item.get("item_id") == "EVD-TICKS-01"), {}
    )
    if ticks.get("status") != "CLOSED_OFFLINE_FIXTURE":
        errors.append("EVD-TICKS-01 must be closed by the pinned offline fixture")

    hardware = _load(EVIDENCE / "reference-hardware.json")
    performance = _load(EVIDENCE / "performance-baseline.json")
    if hardware.get("hardware_id") != performance.get("reference_hardware_id"):
        errors.append("performance results do not reference the named hardware")
    for name, workload in performance.get("workloads", {}).items():
        if (
            len(workload.get("samples", [])) != EXPECTED_PERFORMANCE_SAMPLES
            or workload.get("budget_result") != "PASS"
        ):
            errors.append(f"performance workload is incomplete or over budget: {name}")

    matrix = _load(EVIDENCE / "phase-ui-acceptance-matrix.json")
    phase0_harness = REPO / str(matrix.get("phase_0_harness", ""))
    if not phase0_harness.is_file():
        errors.append("Phase 0 Playwright readiness spec is missing")
    if len(matrix.get("matrix", [])) != EXPECTED_PHASES:
        errors.append("phase/UI matrix must contain 16 future checkpoints")
    if not (REPO / "tests/harness/phase0_asgi.py").is_file():
        errors.append("real local ASGI browser harness is missing")

    for task in (task for task in tasks if task["complete"]):
        evidence_path = REPO / str(task["evidence_path"])
        if not evidence_path.is_file():
            errors.append(
                f"completed task lacks acceptance evidence: {task['feature_id']}"
            )
            continue
        payload = _load(evidence_path)
        missing = FEATURE_EVIDENCE_REQUIRED - set(payload)
        if missing:
            errors.append(f"{task['feature_id']} evidence missing {sorted(missing)}")
        if (
            payload.get("status") != "ACCEPTED"
            or payload.get("acceptance_commit") != task["accepted_commit"]
            or not _valid_acceptance_reference(payload.get("acceptance_commit"))
        ):
            errors.append(
                f"{task['feature_id']} acceptance status/commit differs from plan"
            )
        if set(payload.get("stages", {})) != STAGES:
            errors.append(
                f"{task['feature_id']} must account for all six evidence stages"
            )

    exit_review = (EVIDENCE / "phase-0-exit.md").read_text(encoding="utf-8")
    if "tracker.md" in exit_review:
        errors.append("Phase 0 exit review still cites obsolete root tracker.md")
    if "RATIFIED_READY_FOR_PHASE_1" not in exit_review:
        errors.append("Phase 0 exit review is not ratified")
    return errors


def main() -> int:
    """Print a complete readiness verdict.

    Returns:
        Process exit status: zero when every Phase 0 readiness gate passes.
    """
    try:
        errors = validate()
    except (OSError, TypeError, ValueError, json.JSONDecodeError) as error:
        print(f"[FAIL] Phase 0 validation could not complete: {error}")
        return 1
    if errors:
        print(f"[FAIL] Phase 0 has {len(errors)} readiness error(s):")
        for validation_error in errors:
            print(f"  - {validation_error}")
        return 1
    print(
        "[OK] Phase 0 is fully ratified: 205 tasks, 8 preparations, "
        f"{EXPECTED_REQUIRED_EDGES} required edges, 233 operation gates"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
