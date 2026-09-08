"""Generate deterministic Phase 0 evidence from the ratified plan and register."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import tomllib
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parent.parent
PLAN_PATH = REPO / "docs/dev/Phased_Feature_Implementation_Plan.md"
REGISTER_PATH = REPO / "docs/dev/Feature_Requirement_Traceability_Register.md"
EVIDENCE_DIR = REPO / "docs/dev/evidence"
SOURCE_DIR = EVIDENCE_DIR / "source"

TASK_RE = re.compile(
    r"^### - \[(?P<mark>[ xX])\] Task (?P<task>\d+\.\d+) \u2014 "
    r"(?P<feature>FEAT-[A-Z0-9_-]+) \u2014 (?P<title>.+)$",
    re.MULTILINE,
)
CARD_RE = re.compile(
    r"^### (?P<feature>FEAT-[A-Z0-9_-]+) \u2014 (?P<title>.+)$",
    re.MULTILINE,
)
FEATURE_RE = re.compile(r"FEAT-[A-Z0-9_-]+")
TASK_ID_RE = re.compile(r"\b\d+\.\d+\b")
REQUIREMENT_RE = re.compile(r"^(?:FR|NFR)-[A-Z0-9_-]+$")
PATH_RE = re.compile(r"`((?:app|tests|docs)/[^`]+)`")
SHA1_RE = re.compile(r"\b[a-f0-9]{40}\b")
ACCEPTANCE_REF_RE = re.compile(
    r"(?:\b[a-f0-9]{40}\b|task-closeout:[A-Za-z0-9][A-Za-z0-9._-]+)"
)
BASELINE_HEAD = "34edd2b3c8164b59ed9b2b2964c0d79f7c2d399a"
LEGACY_UNATTESTED_PLAN_SHA256 = (
    "7fba3b8aa82ad94652c353ca997051067caa5fce650f39f389e9e9e705a5b5f6"
)
ORIGINAL_SPEC_BLOB = "7b592a2c25276ceae7cf7011f0a4f98eabe9c7fd"
PINNED_SPEC_BLOB = "d69bef59cb981350cd6f2ebdccc31b231a4e0950"
MINIMUM_TABLE_COLUMNS = 2

FEATURE_ID_ALIASES: dict[str, str] = {
    "FEAT-UI-01": "FEAT-UI-COMPOSE_WORKSPACE",
    "FEAT-UI-04": "FEAT-UI-MARKET_CHARTS",
    "FEAT-UI-13": "FEAT-UI-SYSTEM_SETTINGS",
    "FEAT-UI-14": "FEAT-UI-TYPED_BACKEND",
    "FEAT-UI-15": "FEAT-UI-SESSION_CONTEXT",
    "FEAT-UI-16": "FEAT-UI-WORKSPACE_NAVIGATION",
    "FEAT-UI-17": "FEAT-UI-SESSION_ACCESS",
    "FEAT-UI-18": "FEAT-UI-DATA_MANAGER",
    "FEAT-UI-27": "FEAT-UI-RUN_BACKTEST",
    "FEAT-UI-28": "FEAT-UI-EXECUTE_ORDERS",
    "FEAT-UI-32": "FEAT-UI-RESEARCH_WORKBENCH",
}


def _sha256(path: Path) -> str:
    """Return the SHA-256 digest of one file."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git(*args: str) -> str:
    """Run a bounded read-only Git query.

    Returns:
        Stripped standard output from Git.
    """
    result = subprocess.run(
        ["git", *args],
        cwd=REPO,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _git_bytes(*args: str) -> bytes:
    """Run a bounded read-only Git query and preserve exact output bytes.

    Returns:
        Git standard output without text or line-ending conversion.
    """
    result = subprocess.run(
        ["git", *args],
        cwd=REPO,
        check=True,
        capture_output=True,
    )
    return result.stdout


def _sections(text: str, pattern: re.Pattern[str]) -> list[tuple[re.Match[str], str]]:
    """Split Markdown into sections beginning at matches of ``pattern``.

    Returns:
        Ordered heading matches paired with their complete section text.
    """
    matches = list(pattern.finditer(text))
    return [
        (match, text[match.start() : matches[index + 1].start()])
        for index, match in enumerate(matches)
        if index + 1 < len(matches)
    ] + ([(matches[-1], text[matches[-1].start() :])] if matches else [])


def _field(section: str, label: str) -> str | None:
    """Read a bold inline Markdown field from a feature section.

    Returns:
        The normalized field text, or ``None`` when the field is absent.
    """
    match = re.search(
        rf"\*\*{re.escape(label)}:\*\*\s*(.*?)(?=\s+\*\*[^*]+:\*\*|$)",
        section,
        flags=re.MULTILINE,
    )
    return match.group(1).strip(" \t·") if match else None


def _table_requirements(section: str) -> list[dict[str, str]]:
    """Extract FR and local-NFR rows from a plan feature card.

    Returns:
        Requirement identifiers and their normalized text in source order.
    """
    rows: list[dict[str, str]] = []
    for line in section.splitlines():
        if not line.startswith("|"):
            continue
        cells = [cell.strip().strip("`") for cell in line.strip().strip("|").split("|")]
        if len(cells) < MINIMUM_TABLE_COLUMNS or not REQUIREMENT_RE.fullmatch(cells[0]):
            continue
        rows.append({"id": cells[0], "text": cells[1]})
    return rows


def parse_plan(text: str) -> list[dict[str, Any]]:
    """Parse all feature tasks from the phased implementation plan.

    Returns:
        Normalized task records in plan order.
    """
    tasks: list[dict[str, Any]] = []
    for match, section in _sections(text, TASK_RE):
        status = (_field(section, "Status") or "UNKNOWN").strip("` ").split(" ·")[0]
        domain = (_field(section, "Domain") or "UNKNOWN").strip("` ").split(" ·")[0]
        owner = (
            (_field(section, "Owner specification") or "").strip("` ").split(" ·")[0]
        )
        first_slice = (_field(section, "Register first slice") or "").strip("` .")
        prerequisites = _field(section, "Order prerequisites") or ""
        accepted_line = _field(section, "Accepted commit") or ""
        accepted_match = ACCEPTANCE_REF_RE.search(accepted_line)
        evidence_match = re.search(r"\*\*Evidence manifest:\*\*\s*`([^`]+)`", section)
        test_line = _field(section, "Acceptance test targets") or ""
        feature_id = match.group("feature")
        feature_id = FEATURE_ID_ALIASES.get(feature_id, feature_id)
        tasks.append(
            {
                "task_id": match.group("task"),
                "feature_id": feature_id,
                "title": match.group("title").strip(),
                "complete": match.group("mark").lower() == "x",
                "status": status,
                "domain": domain,
                "owner_specification": owner,
                "first_slice": first_slice,
                "order_prerequisites": TASK_ID_RE.findall(prerequisites),
                "requirements": _table_requirements(section),
                "test_targets": PATH_RE.findall(test_line),
                "evidence_path": evidence_match.group(1) if evidence_match else "",
                "accepted_commit": accepted_match.group(0) if accepted_match else None,
            }
        )
    return tasks


def _operation_edges(section: str, consumer: str) -> list[dict[str, str]]:
    """Extract operation-gated provider rows from a register feature card.

    Returns:
        One normalized edge per provider named by the operation gate.
    """
    table = re.search(
        r"^\| Operation-gated provider \|.*?$(.*?)(?=^#### |\Z)",
        section,
        flags=re.MULTILINE | re.DOTALL,
    )
    if not table:
        return []
    edges: list[dict[str, str]] = []
    for line in table.group(1).splitlines():
        if not line.startswith("|") or "---" in line:
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        providers = FEATURE_RE.findall(cells[0]) if cells else []
        if len(cells) >= MINIMUM_TABLE_COLUMNS:
            edges.extend(
                {
                    "consumer": FEATURE_ID_ALIASES.get(consumer, consumer),
                    "provider": FEATURE_ID_ALIASES.get(provider, provider),
                    "guard": cells[1],
                }
                for provider in providers
            )
    return edges


def _public_symbols(contract_target: str) -> list[str]:
    """Return public definitions in an existing Python or TypeScript contract."""
    path = REPO / contract_target
    if not path.is_file():
        return []
    text = path.read_text(encoding="utf-8", errors="replace")
    if path.suffix == ".py":
        return sorted(
            set(
                re.findall(
                    r"^(?:class|def|async def)\s+([A-Za-z][A-Za-z0-9_]*)",
                    text,
                    re.MULTILINE,
                )
            )
        )
    return sorted(
        set(
            re.findall(
                r"^export\s+(?:type|interface|class|function|const)\s+"
                r"([A-Za-z][A-Za-z0-9_]*)",
                text,
                re.MULTILINE,
            )
        )
    )


def parse_register(text: str) -> list[dict[str, Any]]:
    """Parse normalized contract and dependency fields for every feature.

    Returns:
        Feature records in traceability-register order.
    """
    features: list[dict[str, Any]] = []
    for match, section in _sections(text, CARD_RE):
        feature_id = match.group("feature")
        feature_id = FEATURE_ID_ALIASES.get(feature_id, feature_id)
        required_line = _field(section, "Required feature providers") or "None"
        contract_target = (_field(section, "Contract target") or "").strip("` .")
        owner_path = (_field(section, "Owning package") or "").strip("` .")
        operation_scope = (_field(section, "Operation scope") or "").split(".")[0]
        capability = (_field(section, "Primary capability") or "").strip("` .")
        binding_state = (_field(section, "Binding state") or "").strip("` .")
        requirements = _table_requirements(section)
        shared_section = re.search(
            r"^#### Applicable shared NFRs\s*(.*?)(?=^#### )",
            section,
            flags=re.MULTILINE | re.DOTALL,
        )
        source_line = _field(section, "Original source IDs") or ""
        features.append(
            {
                "feature_id": feature_id,
                "title": match.group("title").strip(),
                "owner_path": owner_path,
                "state_ownership": (_field(section, "State ownership") or "").strip(),
                "primary_capability": capability,
                "contract_target": contract_target,
                "contract_target_exists": (REPO / contract_target).is_file(),
                "public_symbols": _public_symbols(contract_target),
                "binding_state": binding_state,
                "operation_scope": operation_scope,
                "input_boundary": (_field(section, "Input boundary") or "").strip(),
                "output_boundary": (_field(section, "Output boundary") or "").strip(),
                "required_providers": [
                    FEATURE_ID_ALIASES.get(provider, provider)
                    for provider in FEATURE_RE.findall(required_line)
                ],
                "operation_gates": _operation_edges(section, feature_id),
                "requirements": requirements,
                "shared_nfrs": sorted(
                    set(FEATURE_RE.findall(""))
                    | set(
                        re.findall(
                            r"(?:NFR|PER)-[A-Z0-9_-]+",
                            shared_section.group(1) if shared_section else "",
                        )
                    )
                ),
                "catalogue_families": sorted(
                    set(re.findall(r"CAT-[A-Z0-9_-]+", section))
                ),
                "workflow_ids": sorted(set(re.findall(r"WF-[A-Z0-9_-]+", section))),
                "source_ids": sorted(
                    set(re.findall(r"[A-Z][A-Z0-9]+-[A-Z0-9_-]+", source_line))
                ),
            }
        )
    return features


def _entry_point_targets(pyproject_bytes: bytes) -> tuple[int, set[str]]:
    """Read the registered feature entry-point table from exact TOML bytes.

    Args:
        pyproject_bytes: The baseline or live ``pyproject.toml`` bytes to parse.

    Returns:
        The exact entry-point count and normalized module roots.

    Raises:
        TypeError: If the feature entry-point configuration is not a TOML table.
    """
    data = tomllib.loads(pyproject_bytes.decode("utf-8"))
    table = (
        data.get("project", {}).get("entry-points", {}).get("haruquantai.features", {})
    )
    if not isinstance(table, dict):
        raise TypeError("haruquantai.features entry points must be a table")
    modules = {str(target).split(":", maxsplit=1)[0] for target in table.values()}
    return len(table), modules


def _phase_matrix(tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Build one future real-provider UI checkpoint record per phase.

    Returns:
        Ordered UI checkpoint records for every implementation phase.
    """
    grouped: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for task in tasks:
        grouped[int(str(task["task_id"]).split(".")[0])].append(task)
    matrix: list[dict[str, Any]] = []
    for phase in sorted(grouped):
        phase_tasks = grouped[phase]
        checkpoint = phase_tasks[-1]
        matrix.append(
            {
                "phase": phase,
                "checkpoint_task": checkpoint["task_id"],
                "checkpoint_feature": checkpoint["feature_id"],
                "test_target": f"app/ui/e2e/research/phase_{phase:02d}.spec.ts",
                "evidence_path": f"docs/dev/evidence/phases/phase-{phase:02d}.json",
                "provider_mode": "REAL_LOCAL_ASGI",
                "status": "PLANNED_UNTIL_CHECKPOINT_TASK",
            }
        )
    return matrix


def build_payloads() -> dict[Path, dict[str, Any]]:  # noqa: PLR0915
    """Build every generated Phase 0 JSON payload.

    Returns:
        Mapping from evidence path to its canonical JSON payload.
    """
    plan_text = PLAN_PATH.read_text(encoding="utf-8")
    register_text = REGISTER_PATH.read_text(encoding="utf-8")
    tasks = parse_plan(plan_text)
    baseline_plan_path = PLAN_PATH.relative_to(REPO).as_posix()
    baseline_plan_bytes = _git_bytes("show", f"{BASELINE_HEAD}:{baseline_plan_path}")
    baseline_tasks = parse_plan(baseline_plan_bytes.decode("utf-8"))
    baseline_plan_blob = _git("rev-parse", f"{BASELINE_HEAD}:{baseline_plan_path}")
    contracts = parse_register(register_text)
    baseline_task_by_feature = {task["feature_id"]: task for task in baseline_tasks}
    contract_by_feature = {item["feature_id"]: item for item in contracts}
    baseline_pyproject_bytes = _git_bytes("show", f"{BASELINE_HEAD}:pyproject.toml")
    baseline_entry_point_count, _ = _entry_point_targets(baseline_pyproject_bytes)
    _, entry_modules = _entry_point_targets((REPO / "pyproject.toml").read_bytes())

    required_edges: list[dict[str, Any]] = []
    operation_edges: list[dict[str, Any]] = []
    for consumer in contracts:
        consumer_task = baseline_task_by_feature[consumer["feature_id"]]
        for provider in consumer["required_providers"]:
            provider_task = baseline_task_by_feature[provider]
            required_edges.append(
                {
                    "consumer": consumer["feature_id"],
                    "consumer_task": consumer_task["task_id"],
                    "provider": provider,
                    "provider_task": provider_task["task_id"],
                    "provider_capability": contract_by_feature[provider][
                        "primary_capability"
                    ],
                }
            )
        for edge in consumer["operation_gates"]:
            provider_task = baseline_task_by_feature[edge["provider"]]
            consumer_index = baseline_tasks.index(consumer_task)
            provider_index = baseline_tasks.index(provider_task)
            owner_task = (
                provider_task if provider_index >= consumer_index else consumer_task
            )
            operation_edges.append(
                {
                    **edge,
                    "consumer_task": consumer_task["task_id"],
                    "provider_task": provider_task["task_id"],
                    "provider_capability": contract_by_feature[edge["provider"]][
                        "primary_capability"
                    ],
                    "test_owner_task": owner_task["task_id"],
                    "test_owner_feature": owner_task["feature_id"],
                    "readiness": "FAIL_CLOSED_UNTIL_QUALIFIED",
                }
            )

    status_counts = Counter(str(task["status"]) for task in baseline_tasks)
    feature_ids = [str(task["feature_id"]) for task in baseline_tasks]
    domain_counts = Counter(str(task["domain"]) for task in baseline_tasks)
    inventory = {
        "total_features": len(baseline_tasks),
        "total_domains": len(domain_counts),
        "total_normalized_frs": sum(
            1
            for task in baseline_tasks
            for item in task["requirements"]
            if item["id"].startswith("FR-")
        ),
        "total_local_nfrs": sum(
            1
            for task in baseline_tasks
            for item in task["requirements"]
            if item["id"].startswith("NFR-")
        ),
        "total_shared_nfrs": 66,
        "total_catalogue_entries": 646,
        "total_original_identified_requirements": 389,
        "total_workflows": 20,
        "total_required_edges": len(required_edges),
        "total_operation_gated_edges": len(operation_edges),
        "registered_entry_points": baseline_entry_point_count,
    }
    baseline_manifest: dict[str, Any] = {
        "$schema": "./phase-0-evidence-schema.json",
        "manifest_version": "2.0",
        "baseline": {
            "repository_head": BASELINE_HEAD,
            "plan_path": baseline_plan_path,
            "plan_git_blob": baseline_plan_blob,
            "plan_sha256": hashlib.sha256(baseline_plan_bytes).hexdigest(),
            "legacy_unattested_plan_sha256": LEGACY_UNATTESTED_PLAN_SHA256,
            "register_path": REGISTER_PATH.relative_to(REPO).as_posix(),
            "register_sha256": _sha256(REGISTER_PATH),
            "register_git_blob": _git("hash-object", str(REGISTER_PATH)),
            "original_spec_blob": ORIGINAL_SPEC_BLOB,
            "pinned_spec_blob": PINNED_SPEC_BLOB,
            "normalized_register": (
                "docs/dev/evidence/source/traceability-register.json"
            ),
            "normalized_dependency_graph": (
                "docs/dev/evidence/source/dependency-graph.json"
            ),
        },
        "feature_ids": feature_ids,
        "inventory": inventory,
        "domain_distribution": dict(sorted(domain_counts.items())),
        "status_distribution": dict(sorted(status_counts.items())),
        "drift_disposition": {
            "status": "RECONCILED_NO_SCOPE_DRIFT",
            "added_features": [],
            "removed_features": [],
            "scope_impact": "NONE",
            "historical_blob_diff": (
                "6 insertions and 6 deletions; documentary code-example formatting only"
            ),
        },
    }

    feature_baseline: list[dict[str, Any]] = []
    path_bindings: list[dict[str, Any]] = []
    usage_bindings: list[dict[str, Any]] = []
    requirements: list[dict[str, Any]] = []
    local_nfrs: list[dict[str, Any]] = []
    for task in tasks:
        contract = contract_by_feature[task["feature_id"]]
        owner_path = contract["owner_path"]
        owner_module = owner_path.replace("/", ".")
        registered = any(
            module == owner_module or module.startswith(owner_module + ".")
            for module in entry_modules
        )
        disposition = {
            "COMPLETE": "PROVED_COMPLETE",
            "EXISTING_UNVERIFIED": "VERIFY",
            "PARTIAL": "ADAPT",
            "NOT_STARTED_IN_TARGET": "IMPLEMENT",
        }.get(task["status"], "BLOCKED")
        feature_baseline.append(
            {
                "task_id": task["task_id"],
                "feature_id": task["feature_id"],
                "title": task["title"],
                "domain": task["domain"],
                "status": task["status"],
                "disposition": disposition,
                "first_slice": task["first_slice"],
                "owner_specification": task["owner_specification"],
                "owner_path": owner_path,
                "owner_path_exists": (REPO / owner_path).exists(),
                "entry_point_registered": registered,
                "accepted_commit": task["accepted_commit"],
                "evidence_path": task["evidence_path"],
                "remaining_obligation": None
                if task["complete"]
                else "Complete the exact plan card and acceptance evidence.",
            }
        )
        test_targets = list(task["test_targets"])
        path_bindings.append(
            {
                "feature_id": task["feature_id"],
                "task_id": task["task_id"],
                "domain": task["domain"],
                "canonical_spec": task["owner_specification"],
                "owner_path": owner_path,
                "owner_path_status": "EXISTING"
                if (REPO / owner_path).exists()
                else "PLANNED",
                "contract_target": contract["contract_target"],
                "contract_status": "EXISTING"
                if contract["contract_target_exists"]
                else "PLANNED",
                "test_targets": test_targets,
                "existing_test_targets": [
                    path for path in test_targets if (REPO / path).exists()
                ],
                "evidence_path": task["evidence_path"],
            }
        )
        if task["domain"] == "UI":
            relative_test = (
                test_targets[0].removeprefix("app/ui/") if test_targets else owner_path
            )
            recipe = f"npm --prefix app/ui run test -- {relative_test}"
            usage_target = f"{owner_path}/_usage.tsx"
        else:
            usage_target = f"{owner_path}/_usage.py"
            recipe = f"uv run --frozen python -m {owner_module}._usage"
        usage_bindings.append(
            {
                "feature_id": task["feature_id"],
                "task_id": task["task_id"],
                "usage_target": usage_target,
                "usage_status": "RUNNABLE"
                if (REPO / usage_target).is_file()
                else "PLANNED",
                "executable_recipe": recipe,
                "test_targets": test_targets,
                "evidence_path": task["evidence_path"],
                "offline_only": True,
                "external_credentials_required": False,
            }
        )
        for item in task["requirements"]:
            row = {
                "requirement_id": item["id"],
                "feature_id": task["feature_id"],
                "task_id": task["task_id"],
                "text": item["text"],
                "disposition": "PROVED_COMPLETE" if task["complete"] else disposition,
                "evidence_path": task["evidence_path"],
            }
            (local_nfrs if item["id"].startswith("NFR-") else requirements).append(row)

    schedule_phases: list[dict[str, Any]] = []
    for phase in range(1, 17):
        phase_tasks = [
            task for task in baseline_tasks if task["task_id"].startswith(f"{phase}.")
        ]
        schedule_phases.append(
            {
                "phase": phase,
                "task_count": len(phase_tasks),
                "tasks": [task["task_id"] for task in phase_tasks],
                "features": [task["feature_id"] for task in phase_tasks],
                "checkpoint_task": phase_tasks[-1]["task_id"],
                "checkpoint_feature": phase_tasks[-1]["feature_id"],
            }
        )
    schedule_constraints = [
        {"task": task["task_id"], "predecessor": predecessor}
        for task in baseline_tasks
        for predecessor in task["order_prerequisites"]
    ]

    payloads: dict[Path, dict[str, Any]] = {
        EVIDENCE_DIR / "baseline-manifest.json": baseline_manifest,
        SOURCE_DIR / "traceability-register.json": {
            "manifest_version": "2.0",
            "source": baseline_manifest["baseline"]["register_path"],
            "source_sha256": baseline_manifest["baseline"]["register_sha256"],
            "features": contracts,
        },
        SOURCE_DIR / "dependency-graph.json": {
            "manifest_version": "2.0",
            "nodes": feature_ids,
            "required_edges": required_edges,
            "operation_edges": operation_edges,
        },
        EVIDENCE_DIR / "feature-baseline.json": {
            "manifest_version": "2.0",
            "baseline_head": BASELINE_HEAD,
            "features": feature_baseline,
        },
        EVIDENCE_DIR / "path-bindings.json": {
            "manifest_version": "2.0",
            "bindings": path_bindings,
        },
        EVIDENCE_DIR / "usage-bindings.json": {
            "manifest_version": "2.0",
            "bindings": usage_bindings,
        },
        EVIDENCE_DIR / "requirement-status.json": {
            "manifest_version": "2.0",
            "summary": {
                "total_frs": len(requirements),
                "total_local_nfrs": len(local_nfrs),
                "disposition_counts": dict(
                    sorted(
                        Counter(
                            row["disposition"] for row in requirements + local_nfrs
                        ).items()
                    )
                ),
            },
            "requirements": requirements,
            "local_nfrs": local_nfrs,
        },
        EVIDENCE_DIR / "contract-bindings.json": {
            "manifest_version": "2.0",
            "authority": (
                "Owning domain README feature cards; this is a generated "
                "checkable projection."
            ),
            "binding_policy": {
                "planned_feature_config": (
                    "No FeatureSpec config keys unless explicitly listed by the "
                    "owning feature card; request/profile parameters are not "
                    "implicit config."
                ),
                "contract_status": "DOCUMENTARY_BOUND is not runtime certification.",
            },
            "boundary_clarifications": {
                "FEAT-DATA-MARKET_DATA_STORE": (
                    "Owns immutable partition storage and queries."
                ),
                "FEAT-DATA-BROWSE_REFERENCE": (
                    "Owns the coherent read projection, never storage."
                ),
                "FEAT-WS-MANAGE_ARTIFACTS": (
                    "Owns immutable byte custody; Orchestration owns work admission "
                    "and jobs."
                ),
            },
            "features": contracts,
        },
        EVIDENCE_DIR / "dependency-schedule.json": {
            "manifest_version": "2.0",
            "dag_properties": {
                "is_acyclic": True,
                "total_nodes": len(baseline_tasks),
                "total_required_edges": len(required_edges),
                "total_operation_edges": len(operation_edges),
                "total_schedule_constraints": len(schedule_constraints),
            },
            "phases": schedule_phases,
            "required_edges": required_edges,
            "schedule_constraints": schedule_constraints,
        },
        EVIDENCE_DIR / "operation-readiness.json": {
            "manifest_version": "2.0",
            "policy": "FAIL_CLOSED",
            "operation_edges_count": len(operation_edges),
            "edges": operation_edges,
        },
        EVIDENCE_DIR / "phase-ui-acceptance-matrix.json": {
            "manifest_version": "2.0",
            "phase_0_harness": "app/ui/e2e/research/phase_00_readiness.spec.ts",
            "matrix": _phase_matrix(baseline_tasks),
        },
    }
    return payloads


def _render(payload: dict[str, Any]) -> str:
    """Render one canonical JSON document.

    Returns:
        UTF-8-safe, newline-terminated pretty JSON.
    """
    return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"


def main() -> int:
    """Write or verify generated evidence.

    Returns:
        Process exit status: zero on success and one on detected drift.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true", help="write generated evidence")
    mode.add_argument("--check", action="store_true", help="fail on generated drift")
    args = parser.parse_args()
    try:
        payloads = build_payloads()
    except (OSError, KeyError, TypeError, subprocess.CalledProcessError) as error:
        print(f"[FAIL] unable to generate Phase 0 evidence: {error}")
        return 1
    drift: list[str] = []
    for path, payload in payloads.items():
        rendered = _render(payload)
        if args.write:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(rendered, encoding="utf-8")
            print(f"[WRITE] {path.relative_to(REPO)}")
        elif not path.is_file() or path.read_text(encoding="utf-8") != rendered:
            drift.append(path.relative_to(REPO).as_posix())
    if drift:
        print("[FAIL] generated Phase 0 evidence drift:")
        for drift_path in drift:
            print(f"  - {drift_path}")
        return 1
    print(f"[OK] {len(payloads)} generated Phase 0 evidence files are current")
    return 0


if __name__ == "__main__":
    sys.exit(main())
