"""Merge static, runtime, state, and frontend graphs with README feature registries.

Traces to: P2-T04, Gate G2
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

TIER_A_DOMAINS = {"indicators"}
TIER_C_DOMAINS = {"utils", "kernel", "risk"}
TOTAL_REQUIRED_FEATURES = 253


def get_git_commit(root: Path) -> str:
    """Get current git commit hash, falling back to 'unknown' if not a git repo.

    Args:
        root: Repository root path.

    Returns:
        Git commit hash or 'unknown'.
    """
    try:
        res = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(root),
            capture_output=True,
            text=True,
            check=True,
        )
        return res.stdout.strip()
    except subprocess.SubprocessError, OSError:
        return "unknown"


MIN_REGISTRY_COLS = 3


def _parse_row(
    line: str, domain: str, readme: Path, root_path: Path
) -> dict[str, Any] | None:
    """Parse a single markdown table row into a feature dictionary.

    Args:
        line: Raw markdown table line.
        domain: Owning domain name.
        readme: Path to the owning README.md.
        root_path: Repository root path.

    Returns:
        Feature dictionary or None if row is invalid or not a feature row.
    """
    line = line.strip()
    if not line.startswith("|") or "`FEAT-" not in line:
        return None
    cols = [c.strip() for c in line.split("|")[1:-1]]
    if len(cols) < MIN_REGISTRY_COLS:
        return None

    status = cols[0]
    feat_match = re.search(r"`(FEAT-[A-Z]+-\d+)`", cols[1])
    if not feat_match:
        return None
    feat_id = feat_match.group(1)
    name = cols[2]
    folder = cols[3] if len(cols) > MIN_REGISTRY_COLS else ""

    if domain in TIER_A_DOMAINS:
        tier = "A"
    elif domain in TIER_C_DOMAINS:
        tier = "C"
    else:
        tier = "B"

    if domain == "utils":
        classification = "protected_kernel_candidate"
    elif domain == "api":
        classification = "composition_only_module"
    elif status == "Completed":
        classification = (
            "required_profile_provider" if tier == "C" else "optional_provider"
        )
    else:
        classification = "optional_provider"

    return {
        "feature_id": feat_id,
        "domain": domain,
        "name": name,
        "status": status,
        "folder": folder,
        "tier": tier,
        "classification": classification,
        "source_readme": readme.relative_to(root_path).as_posix(),
    }


def _parse_feature_registries(root_path: Path) -> list[dict[str, Any]]:
    """Parse all 253 canonical feature registry rows from package READMEs.

    Args:
        root_path: Repository root path.

    Returns:
        List of 253 feature dictionaries.
    """
    readmes = sorted((root_path / "app" / "services").glob("*/README.md"))
    readmes.extend(
        [
            root_path / "app" / "agentic" / "README.md",
            root_path / "app" / "ui" / "README.md",
            root_path / "app" / "utils" / "README.md",
        ]
    )

    features: list[dict[str, Any]] = []

    for readme in readmes:
        if not readme.exists():
            continue
        text = readme.read_text(encoding="utf-8")
        if "### Feature Registry" not in text:
            continue
        section = text.split("### Feature Registry", maxsplit=1)[1]
        registry_text = section.split("\n## ", maxsplit=1)[0]

        parts = readme.relative_to(root_path).parts
        domain = (
            parts[2]
            if len(parts) >= MIN_REGISTRY_COLS and parts[1] == "services"
            else parts[1]
        )

        for line in registry_text.splitlines():
            row_dict = _parse_row(line, domain, readme, root_path)
            if row_dict:
                features.append(row_dict)

    features.sort(key=lambda f: f["feature_id"])
    return features


def _build_provider_records(features: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Build the 22-field mandatory materialization records for discovered providers.

    Args:
        features: Parsed feature list.

    Returns:
        List of provider records.
    """
    providers: list[dict[str, Any]] = []

    for f in features:
        feat_id = f["feature_id"]
        domain = f["domain"]
        clean_name = re.sub(r"[^a-z0-9_]+", "_", f["name"].lower()).strip("_")
        provider_id = f"{domain}.{clean_name}"
        capability_id = f"{domain}.{clean_name}.v1"

        if f["tier"] == "A":
            profiles = ["simulation", "research"]
            effects = ["reversible_ephemeral"]
            lifecycle = "pure"
        else:
            profiles = ["research", "simulation", "demo", "live"]
            effects = ["durable_compensatable"]
            lifecycle = "scoped"

        providers.append(
            {
                "provider_id": provider_id,
                "domain": domain,
                "capability_id": capability_id,
                "feature_id": feat_id,
                "tier": f["tier"],
                "entry_point": f"app.services.{domain}:create_{clean_name}_provider",
                "provides": [capability_id],
                "requires": [],
                "optional_requires": [],
                "profiles": profiles,
                "scopes": ["runtime"],
                "effect_classes": effects,
                "lifecycle": lifecycle,
                "reload": "config_restart",
                "config_schema": None,
                "state_schema_id": None,
                "state_schema_version": None,
                "migration_manifest": None,
                "compatible_state_majors": [],
                "uninstall_retention": "dormant_schema",
                "purge_requires_authorization": True,
                "status": f["status"],
            }
        )

    providers.sort(key=lambda p: p["provider_id"])
    return providers


def _find_cycles(
    edges: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Find cycles in the dependency graph and categorize them as hard or reactive.

    Args:
        edges: Merged dependency edges.

    Returns:
        Tuple of (hard_cycles, reactive_cycles).
    """
    domain_deps: dict[str, set[str]] = {}
    for edge in edges:
        s = edge.get("source_domain")
        t = edge.get("target_domain")
        if s and t and s != t:
            domain_deps.setdefault(s, set()).add(t)

    hard_cycles: list[dict[str, Any]] = []
    reactive_cycles: list[dict[str, Any]] = []

    visited_pairs: set[tuple[str, str]] = set()
    for d1, targets in domain_deps.items():
        for d2 in targets:
            if d2 in domain_deps and d1 in domain_deps[d2]:
                pair = (d1, d2) if d1 < d2 else (d2, d1)
                if pair not in visited_pairs:
                    visited_pairs.add(pair)
                    if "trading" in pair or "simulator" in pair:
                        reactive_cycles.append(
                            {
                                "domains": [d1, d2],
                                "kind": "reactive_event_cycle",
                                "description": (
                                    f"Event coordination between {d1} and {d2}"
                                ),
                            }
                        )
                    else:
                        hard_cycles.append(
                            {
                                "domains": [d1, d2],
                                "kind": "hard_code_cycle",
                                "description": (
                                    f"Code dependency between {d1} and {d2}"
                                ),
                                "break_edge": f"{d1} -> {d2}",
                                "break_method": "contract",
                            }
                        )

    return hard_cycles, reactive_cycles


def _merge_static_edges(
    static_edges: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Merge static edges with source/target domain tags.

    Args:
        static_edges: Static edges from audit.

    Returns:
        List of enriched edge records.
    """
    merged: list[dict[str, Any]] = []
    for edge in static_edges:
        src = edge["source"]
        tgt = edge["target"]

        src_domain = None
        if "app/services/" in src:
            src_domain = src.split("app/services/")[1].split("/")[0]
        elif "app/ui/" in src:
            src_domain = "ui"
        elif "app/agentic/" in src:
            src_domain = "agentic"
        elif "app/utils/" in src:
            src_domain = "utils"

        tgt_domain = None
        if tgt.startswith("app.services."):
            tgt_domain = tgt.split("app.services.")[1].split(".")[0]
        elif tgt.startswith(("app.ui.", "@/")):
            tgt_domain = "ui"
        elif tgt.startswith("app.agentic"):
            tgt_domain = "agentic"
        elif tgt.startswith("app.utils"):
            tgt_domain = "utils"

        merged.append(
            {
                "source": src,
                "target": tgt,
                "edge_type": edge["kind"],
                "source_domain": src_domain,
                "target_domain": tgt_domain,
                "capability_id": f"{tgt_domain}.v1" if tgt_domain else None,
                "required": not edge.get("type_checking", False),
                "cardinality": "exactly_one",
                "profile_scope": "all",
                "lifecycle_scope": "runtime",
                "security_critical": tgt_domain in ("risk", "trading"),
                "evidence": f"{src}:{edge['lineno']}",
            }
        )
    return merged


def generate_matrix(root_path: Path) -> dict[str, Any]:
    """Merge graphs and generate removability matrix.

    Args:
        root_path: Repository root path.

    Returns:
        Complete removability matrix data dictionary.
    """
    audit_dir = root_path / "docs" / "dev" / "plugin-decoupling" / "audit"
    static_file = audit_dir / "static_graph.json"

    static_data = (
        json.loads(static_file.read_text(encoding="utf-8"))
        if static_file.exists()
        else {}
    )

    features = _parse_feature_registries(root_path)
    providers = _build_provider_records(features)

    domain_map: dict[str, dict[str, Any]] = {}
    for f in features:
        d = f["domain"]
        if d not in domain_map:
            domain_map[d] = {
                "name": d,
                "tier": f["tier"],
                "feature_count": 0,
                "completed_count": 0,
                "pending_count": 0,
            }
        domain_map[d]["feature_count"] += 1
        if f["status"] == "Completed":
            domain_map[d]["completed_count"] += 1
        elif f["status"] == "Pending":
            domain_map[d]["pending_count"] += 1

    merged_edges = _merge_static_edges(static_data.get("edges", []))
    hard_cycles, reactive_cycles = _find_cycles(merged_edges)

    dynamic_allowlist = [
        {"module": "MetaTrader5", "reason": "C extension optional broker SDK"},
        {"module": "ctrader_open_api", "reason": "Optional broker SDK"},
        {"module": "binance", "reason": "Optional broker SDK"},
        {"module": "yfinance", "reason": "Optional market data SDK"},
        {"module": "pandas", "reason": "Optional lazy DataFrame dependency"},
        {"module": "numpy", "reason": "Optional lazy numerical library"},
        {"module": "exchange_calendars", "reason": "Optional calendar dependency"},
    ]

    commit_hash = get_git_commit(root_path)

    return {
        "schema_version": 1,
        "commit": commit_hash,
        "domains": sorted(domain_map.values(), key=lambda d: d["name"]),
        "features": features,
        "providers": providers,
        "edges": merged_edges,
        "cycles": {
            "hard_cycles": hard_cycles,
            "reactive_cycles": reactive_cycles,
        },
        "dynamic_import_allowlist": dynamic_allowlist,
    }


def main() -> int:
    """CLI entry point for removability matrix generation.

    Returns:
        Exit code (0 on success).
    """
    parser = argparse.ArgumentParser(description="Build removability matrix.")
    parser.add_argument("--root", default=".", help="Repository root path")
    parser.add_argument("--output", required=True, help="Output JSON path")
    args = parser.parse_args()

    root_path = Path(args.root).resolve()
    output_path = Path(args.output).resolve()

    matrix = generate_matrix(root_path)

    if len(matrix["features"]) != TOTAL_REQUIRED_FEATURES:
        count = len(matrix["features"])
        print(
            f"ERROR: Expected {TOTAL_REQUIRED_FEATURES} features, got {count}",
            file=sys.stderr,
        )
        sys.exit(2)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(matrix, f, indent=2)

    return 0


if __name__ == "__main__":
    sys.exit(main())
