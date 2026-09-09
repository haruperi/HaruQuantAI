#!/usr/bin/env python3
"""Generate and validate compact, source-pinned Task packets."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any, Final

PACKET_SCHEMA_VERSION: Final[int] = 1
CURRENT_PROJECTION_PATHS: Final[tuple[str, ...]] = (
    "docs/dev/Phased_Feature_Implementation_Plan.md",
    "docs/dev/evidence/feature-baseline.json",
    "docs/dev/evidence/path-bindings.json",
    "docs/dev/evidence/usage-bindings.json",
    "docs/dev/evidence/requirement-status.json",
    "docs/dev/evidence/contract-bindings.json",
)
EVIDENCE_SOURCES: Final[tuple[str, ...]] = (
    "docs/dev/evidence/feature-baseline.json",
    "docs/dev/evidence/contract-bindings.json",
    "docs/dev/evidence/path-bindings.json",
    "docs/dev/evidence/requirement-status.json",
    "docs/dev/evidence/usage-bindings.json",
    "docs/dev/evidence/dependency-schedule.json",
    "docs/dev/evidence/source/traceability-register.json",
)
CRITICAL_TERMS: Final[tuple[str, ...]] = (
    "authorization",
    "session",
    "cross-account",
    "cross-workspace",
    "trading",
    "risk",
    "numerical",
    "persistence",
    "recovery",
    "resource",
    "concurrency",
    "provider",
    "network",
    "destructive",
    "approval policy",
    "validation policy",
    "broker",
    "credential",
    "idempotency",
)
ROUTINE_TERMS: Final[tuple[str, ...]] = (
    "nonsemantic",
    "documentation-only",
    "prose-only",
    "typo",
)


class RiskTier(StrEnum):
    """Conservative Task workflow tiers."""

    ROUTINE = "ROUTINE"
    STANDARD = "STANDARD"
    CRITICAL = "CRITICAL"


@dataclass(frozen=True, slots=True)
class RiskClassification:
    """Deterministic risk result and its auditable reasons."""

    tier: RiskTier
    reasons: tuple[str, ...]


class TaskPacketError(RuntimeError):
    """Raised when authoritative packet inputs are invalid or stale."""


def _sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise TaskPacketError(f"Cannot read packet authority: {path}") from exc
    if not isinstance(payload, dict):
        raise TaskPacketError(f"Packet authority must be an object: {path}")
    return payload


def _one(items: list[dict[str, Any]], key: str, value: str) -> dict[str, Any] | None:
    matches = [item for item in items if str(item.get(key, "")) == value]
    if len(matches) > 1:
        raise TaskPacketError(f"Authority contains duplicate {key}={value!r}.")
    return matches[0] if matches else None


def classify_risk(
    task: dict[str, Any], records: list[dict[str, Any]]
) -> RiskClassification:
    """Classify Task risk conservatively from behavior-bearing text.

    Args:
        task: Task specification.
        records: Structured feature records included in the packet.

    Returns:
        Deterministic risk tier and matching reasons.
    """

    def text_values(value: Any) -> list[str]:
        if isinstance(value, dict):
            return [text for item in value.values() for text in text_values(item)]
        if isinstance(value, list | tuple | set):
            return [text for item in value for text in text_values(item)]
        return [value] if isinstance(value, str) else []

    semantic_record_values: list[str] = []
    for record in records:
        semantic_record_values.extend(
            text_values(
                {
                    "title": record.get("title"),
                    "domain": record.get("domain"),
                    "state_ownership": record.get("state_ownership"),
                    "operation_scope": record.get("operation_scope"),
                    "requirements": record.get("requirements", []),
                    "operation_gates": record.get("operation_gates", []),
                }
            )
        )
    corpus = " ".join(text_values(task) + semantic_record_values).lower()
    critical = tuple(term for term in CRITICAL_TERMS if term in corpus)
    if critical:
        return RiskClassification(
            RiskTier.CRITICAL,
            tuple(f"critical behavior term: {term}" for term in critical),
        )
    if str(task.get("task_kind", "feature")).lower() != "feature":
        routine = tuple(term for term in ROUTINE_TERMS if term in corpus)
        if routine:
            return RiskClassification(
                RiskTier.ROUTINE,
                tuple(f"routine-only term: {term}" for term in routine),
            )
    return RiskClassification(
        RiskTier.STANDARD,
        ("bounded behavior with no critical marker",),
    )


def _existing_owner_files(repo: Path, owner_path: str) -> list[str]:
    root = repo / owner_path
    if not root.is_dir():
        return []
    return sorted(
        path.relative_to(repo).as_posix() for path in root.rglob("*") if path.is_file()
    )


def _authoring_route(
    *,
    repo: Path,
    task: dict[str, Any],
    owner_path: str,
    contract_target: str,
    contract: dict[str, Any] | None,
    classification: RiskClassification,
) -> dict[str, Any]:
    """Choose a conservative implementation-authoring route.

    Args:
        repo: Repository root.
        task: Frozen Task specification.
        owner_path: Canonical feature owner path.
        contract_target: Canonical public-contract target.
        contract: Feature contract binding, when present.
        classification: Conservative workflow risk classification.

    Returns:
        Auditable route and optional scaffolding command.
    """
    if owner_path and (repo / owner_path).is_dir():
        route = "REUSE_EXISTING_FIRST"
        reason = "The canonical V3 owner path already exists."
    elif str(task.get("task_kind", "feature")).lower() != "feature":
        route = "NO_AUTOMATIC_SCAFFOLD"
        reason = "Only registered backend features are scaffold candidates."
    elif classification.tier is RiskTier.CRITICAL:
        route = "NO_AUTOMATIC_SCAFFOLD"
        reason = "Critical behavior requires explicit design and implementation."
    elif not owner_path.startswith("app/services/"):
        route = "NO_AUTOMATIC_SCAFFOLD"
        reason = "The first scaffold shape is backend-service-only."
    elif not contract_target or (repo / contract_target).exists():
        route = "IMPLEMENT_MISSING"
        reason = (
            "An absent dedicated contract target is required for this first "
            "deterministic scaffold shape."
        )
    elif not contract or not contract.get("primary_capability"):
        route = "IMPLEMENT_MISSING"
        reason = "Contract authority is incomplete for deterministic scaffolding."
    elif (
        not str(contract.get("state_ownership", "")).strip().lower().startswith("none")
    ):
        route = "NO_AUTOMATIC_SCAFFOLD"
        reason = "The declared state ownership is not explicitly stateless."
    else:
        route = "SCAFFOLD_STATELESS_BACKEND"
        reason = "Missing Standard backend owner matches the proven stateless shape."
    command = None
    if route == "SCAFFOLD_STATELESS_BACKEND":
        command = (
            "uv run python scripts/scaffold_stateless_feature.py "
            "--task-packet <task-packet.json> --preview"
        )
    return {
        "route": route,
        "reason": reason,
        "scaffold_command": command,
        "template_reference": (
            "FEAT-PLUG-DECLARE_MANIFESTS"
            if route == "SCAFFOLD_STATELESS_BACKEND"
            else None
        ),
    }


def _source_record(repo: Path, relative: str, selector: str) -> dict[str, str]:
    path = repo / relative
    if not path.is_file():
        raise TaskPacketError(f"Required packet source is missing: {relative}")
    return {
        "path": relative,
        "selector": selector,
        "sha256": _sha_bytes(path.read_bytes()),
    }


def _commit_message(repo: Path, task: dict[str, Any]) -> str:
    """Extract the exact declared commit message for a tracker entry."""
    tracker = str(task.get("implementation_file", ""))
    entry = str(task.get("implementation_entry", ""))
    if tracker and entry:
        path = repo / tracker
        if path.is_file():
            text = path.read_text(encoding="utf-8", errors="replace")
            header = re.search(
                rf"(?m)^###\s+-\s+\[[ xX]?\]\s+Task\s+{re.escape(entry)}\b",
                text,
            )
            if header:
                next_header = re.search(r"(?m)^###\s+-\s+\[", text[header.end() :])
                end = header.end() + next_header.start() if next_header else len(text)
                match = re.search(
                    r"(?m)^\*\*Commit message:\*\*\s+`([^`]+)`",
                    text[header.start() : end],
                )
                if match:
                    return match.group(1)
    explicit = str(task.get("commit_message", "")).strip()
    if explicit:
        return explicit
    return f"task: complete {task['task_id']}"


def build_task_packet(
    repo: Path,
    task: dict[str, Any],
    *,
    baseline: str,
) -> dict[str, Any]:
    """Build one complete packet from current structured repository authority.

    Args:
        repo: Repository root at the clean activation baseline.
        task: Frozen Task specification.
        baseline: Exact accepted-main commit.

    Returns:
        JSON-compatible packet. Incomplete packets explicitly require Planner.
    """
    sources = {relative: _load_json(repo / relative) for relative in EVIDENCE_SOURCES}
    feature_id = str(task.get("task_id", ""))
    task_id = str(task.get("implementation_entry", ""))
    blockers: list[str] = []

    feature_baseline = _one(
        list(sources[EVIDENCE_SOURCES[0]].get("features", [])),
        "feature_id",
        feature_id,
    )
    contract = _one(
        list(sources[EVIDENCE_SOURCES[1]].get("features", [])),
        "feature_id",
        feature_id,
    )
    path_binding = _one(
        list(sources[EVIDENCE_SOURCES[2]].get("bindings", [])),
        "feature_id",
        feature_id,
    )
    usage = _one(
        list(sources[EVIDENCE_SOURCES[4]].get("bindings", [])),
        "feature_id",
        feature_id,
    )
    trace = _one(
        list(sources[EVIDENCE_SOURCES[6]].get("features", [])),
        "feature_id",
        feature_id,
    )
    feature_records = [
        record
        for record in (feature_baseline, contract, path_binding, usage, trace)
        if record is not None
    ]
    if str(task.get("task_kind", "feature")).lower() == "feature":
        for label, record in (
            ("feature baseline", feature_baseline),
            ("contract binding", contract),
            ("path binding", path_binding),
            ("usage binding", usage),
            ("traceability record", trace),
        ):
            if record is None:
                blockers.append(f"missing {label} for {feature_id}")

    requirement_source = sources[EVIDENCE_SOURCES[3]]
    requirements = [
        item
        for item in requirement_source.get("requirements", [])
        if str(item.get("feature_id", "")) == feature_id
    ]
    local_nfrs = [
        item
        for item in requirement_source.get("local_nfrs", [])
        if str(item.get("feature_id", "")) == feature_id
    ]
    if contract is not None:
        contract_ids = {
            str(item.get("id")) for item in contract.get("requirements", [])
        }
        packet_ids = {
            str(item.get("requirement_id", item.get("id")))
            for item in [*requirements, *local_nfrs]
        }
        missing_ids = sorted(contract_ids - packet_ids)
        if missing_ids:
            blockers.append(f"requirement records missing: {', '.join(missing_ids)}")

    dependency_source = sources[EVIDENCE_SOURCES[5]]
    required_edges = [
        edge
        for edge in dependency_source.get("required_edges", [])
        if str(edge.get("consumer", "")) == feature_id
    ]
    constraints = [
        edge
        for edge in dependency_source.get("schedule_constraints", [])
        if str(edge.get("task", "")) == task_id
    ]
    baseline_features = {
        str(item.get("feature_id")): item
        for item in sources[EVIDENCE_SOURCES[0]].get("features", [])
    }
    predecessor_evidence: list[dict[str, Any]] = []
    for edge in required_edges:
        provider = str(edge.get("provider", ""))
        provider_record = baseline_features.get(provider)
        accepted = bool(
            provider_record
            and provider_record.get("status")
            in {"ACCEPTED", "COMPLETE", "PROVED_COMPLETE"}
            and provider_record.get("accepted_commit")
        )
        predecessor_evidence.append(
            {**edge, "accepted": accepted, "record": provider_record}
        )
        if not accepted:
            blockers.append(f"required provider is not accepted: {provider}")

    source_locations = [
        _source_record(repo, relative, f"feature_id={feature_id}")
        for relative in EVIDENCE_SOURCES
    ]
    owner_spec = str(
        (feature_baseline or {}).get("owner_specification")
        or (path_binding or {}).get("canonical_spec")
        or ""
    )
    if owner_spec:
        source_locations.append(
            _source_record(repo, owner_spec, f"owning specification for {feature_id}")
        )
    else:
        blockers.append("owning specification is not bound")
    implementation_file = str(task.get("implementation_file", ""))
    if implementation_file:
        source_locations.append(
            _source_record(repo, implementation_file, f"Task {task_id}")
        )
    shared_nfr_context: list[str] = []
    if contract and contract.get("shared_nfrs"):
        project_path = "docs/PROJECT.md"
        source_locations.append(
            _source_record(repo, project_path, "shared NFR families")
        )
        families = {
            "-".join(str(item).split("-")[:2])
            for item in contract.get("shared_nfrs", [])
        }
        shared_nfr_context = [
            line
            for line in (repo / project_path).read_text(encoding="utf-8").splitlines()
            if any(family in line for family in families)
        ]

    owner_path = str((path_binding or {}).get("owner_path", ""))
    write_paths = set(_existing_owner_files(repo, owner_path))
    for value in (
        (path_binding or {}).get("contract_target"),
        *((path_binding or {}).get("test_targets", [])),
        (usage or {}).get("usage_target"),
        (path_binding or {}).get("evidence_path"),
        owner_spec,
        task.get("implementation_file"),
    ):
        if value:
            write_paths.add(str(value).replace("\\", "/"))
    if not write_paths:
        blockers.append("no exact write-path authority could be derived")

    classification = classify_risk(task, feature_records)
    authoring = _authoring_route(
        repo=repo,
        task=task,
        owner_path=owner_path,
        contract_target=str((path_binding or {}).get("contract_target", "")),
        contract=contract,
        classification=classification,
    )
    if authoring["route"] == "SCAFFOLD_STATELESS_BACKEND":
        write_paths.update(
            f"{owner_path}/{name}"
            for name in (
                "__init__.py",
                "README.md",
                "config.py",
                "manifest.py",
                "feature.py",
                "_usage.py",
            )
        )
    compatible_example = _compatible_example(
        feature_id, feature_baseline, sources[EVIDENCE_SOURCES[0]]
    )
    if authoring["route"] == "SCAFFOLD_STATELESS_BACKEND":
        reference = _one(
            list(sources[EVIDENCE_SOURCES[0]].get("features", [])),
            "feature_id",
            "FEAT-PLUG-DECLARE_MANIFESTS",
        )
        if reference is None or reference.get("status") not in {
            "COMPLETE",
            "ACCEPTED",
            "PROVED_COMPLETE",
        }:
            blockers.append("stateless scaffold reference is not accepted")
        else:
            compatible_example = {
                "feature_id": reference["feature_id"],
                "owner_path": reference["owner_path"],
                "accepted_commit": reference["accepted_commit"],
            }
    planner_required = classification.tier is RiskTier.CRITICAL or bool(blockers)
    status = (
        "BLOCKED"
        if blockers
        else ("READY_FOR_PLANNING" if planner_required else "EXECUTOR_READY")
    )
    packet = {
        "schema_version": PACKET_SCHEMA_VERSION,
        "packet_kind": "haruquant-task-packet",
        "task": task,
        "commit_message": _commit_message(repo, task),
        "identity": {
            "task_id": task_id,
            "feature_id": feature_id,
            "baseline_commit": baseline,
        },
        "source_locations": source_locations,
        "requirements": requirements,
        "local_nfrs": local_nfrs,
        "shared_nfrs": list((contract or {}).get("shared_nfrs", [])),
        "shared_nfr_context": shared_nfr_context,
        "catalogue_obligations": list((contract or {}).get("catalogue_families", [])),
        "contract": contract,
        "paths": path_binding,
        "usage": usage,
        "traceability": trace,
        "dependencies": {
            "required_edges": required_edges,
            "schedule_constraints": constraints,
            "accepted_predecessors": predecessor_evidence,
        },
        "expected_behavior": {
            "input_boundary": (contract or {}).get("input_boundary"),
            "output_boundary": (contract or {}).get("output_boundary"),
            "operation_gates": list((contract or {}).get("operation_gates", [])),
            "lifecycle_obligations": [
                item
                for item in (contract or {}).get("requirements", [])
                if "remov" in str(item.get("text", "")).lower()
                or "lifecycle" in str(item.get("text", "")).lower()
            ],
            "numerical_examples": [],
            "qualification_boundary": {
                "usage_status": (usage or {}).get("usage_status"),
                "offline_only": (usage or {}).get("offline_only"),
                "external_credentials_required": (usage or {}).get(
                    "external_credentials_required"
                ),
            },
        },
        "compatible_example": compatible_example,
        "reuse_decision": "REFERENCE_ONLY",
        "authorized_write_paths": sorted(write_paths),
        "controller_projection_paths": sorted(
            {
                *CURRENT_PROJECTION_PATHS,
                str((path_binding or {}).get("evidence_path", "")),
            }
            - {""}
        ),
        "serialized_integration_write_paths": (
            ["pyproject.toml"]
            if authoring["route"] == "SCAFFOLD_STATELESS_BACKEND"
            else []
        ),
        "authoring": authoring,
        "validation": {
            "test_targets": list((path_binding or {}).get("test_targets", [])),
            "usage_recipe": (usage or {}).get("executable_recipe"),
            "coverage_in_inner_loop": False,
        },
        "risk": {
            "tier": classification.tier.value,
            "reasons": list(classification.reasons),
        },
        "unresolved_decisions": blockers,
        "planner_required": planner_required,
        "status": status,
    }
    return packet


def _compatible_example(
    feature_id: str,
    feature: dict[str, Any] | None,
    baseline: dict[str, Any],
) -> dict[str, Any] | None:
    domain = str((feature or {}).get("domain", ""))
    candidates = sorted(
        (
            item
            for item in baseline.get("features", [])
            if item.get("feature_id") != feature_id
            and item.get("domain") == domain
            and item.get("status") == "COMPLETE"
            and item.get("owner_path_exists")
        ),
        key=lambda item: str(item.get("task_id", "")),
    )
    if not candidates:
        return None
    candidate = candidates[0]
    return {
        "feature_id": candidate.get("feature_id"),
        "owner_path": candidate.get("owner_path"),
        "accepted_commit": candidate.get("accepted_commit"),
    }


def write_task_packet(path: Path, packet: dict[str, Any]) -> str:
    """Write canonical packet bytes and return their SHA-256."""
    raw = json.dumps(packet, indent=2, sort_keys=True) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(raw, encoding="utf-8", newline="\n")
    return _sha_bytes(raw.encode("utf-8"))


def validate_task_packet(path: Path, repo: Path, *, baseline: str) -> dict[str, Any]:
    """Validate packet structure, baseline and source fingerprints."""
    packet = _load_json(path)
    if packet.get("schema_version") != PACKET_SCHEMA_VERSION:
        raise TaskPacketError("Unsupported Task packet schema.")
    identity = packet.get("identity")
    if not isinstance(identity, dict) or identity.get("baseline_commit") != baseline:
        raise TaskPacketError("Task packet baseline is stale.")
    locations = packet.get("source_locations")
    if not isinstance(locations, list) or not locations:
        raise TaskPacketError("Task packet has no source manifest.")
    for item in locations:
        if not isinstance(item, dict):
            raise TaskPacketError("Task packet source entry is malformed.")
        relative = str(item.get("path", ""))
        path_value = repo / relative
        if not path_value.is_file() or _sha_bytes(path_value.read_bytes()) != item.get(
            "sha256"
        ):
            raise TaskPacketError(f"Task packet source changed: {relative}")
    return packet
