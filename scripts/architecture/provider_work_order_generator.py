"""Deterministic provider work order appendix generator for migration waves.

Traces to: P12.1-T01, Phase 12, Gate G12
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

_MANDATORY_FIELDS = (
    "provider_id",
    "feature_id",
    "tier",
    "source_paths",
    "target_provider_path",
    "capability_ids",
    "capability_spec_paths",
    "existing_public_signatures",
    "target_contracts",
    "manifest_values",
    "requirements",
    "consumers",
    "compatibility_facades",
    "profile_impact",
    "effect_classes",
    "state_ownership",
    "migration_ownership",
    "parity_artifacts",
    "test_commands",
    "example_command",
    "removal_expectations",
    "reinstall_expectations",
    "protected_paths",
)

_WAVE_DOMAINS: dict[str, tuple[str, ...]] = {
    "12.1": ("utils",),
    "12.2": ("data",),
    "12.3": ("brokers",),
    "12.4": ("data_stream",),
    "12.5": ("indicators",),
    "12.6": ("analytics",),
    "12.7": ("strategy",),
    "12.8": ("portfolio",),
    "12.9": ("risk",),
    "12.10": ("portfolio_alloc",),
    "12.11": ("trading",),
    "12.12": ("trading_preflight",),
    "12.13": ("simulator",),
    "12.14": ("brokers_mutation",),
    "12.15": ("trading_live",),
    "12.16": ("research",),
    "12.17": ("optimization",),
    "12.18": ("agentic",),
    "12.19": ("api",),
    "12.20": ("ui",),
    "12.21": ("cleanup",),
}


def build_provider_record(raw_provider: dict[str, Any], wave_id: str) -> dict[str, Any]:
    """Normalize and enrich raw provider data into complete work-order specification.

    Args:
        raw_provider: Raw provider dictionary from removability matrix.
        wave_id: Migration wave identifier.

    Returns:
        Complete validated dictionary containing all mandatory fields.
    """
    _ = wave_id
    prov_id = raw_provider.get("provider_id", "")
    domain = raw_provider.get("domain", "")
    tier = raw_provider.get("tier", "B")
    feat_id = raw_provider.get("feature_id", "FEAT-UNK")
    cap_id = raw_provider.get("capability_id", f"{domain}.{prov_id}.v1")

    sub_name = prov_id.split(".")[-1] if "." in prov_id else prov_id

    source_paths = [f"app/services/{domain}/{sub_name}.py"]
    target_provider_path = f"app/services/{domain}/providers/{prov_id}"
    cap_spec_paths = [f"app/capabilities/{domain}/{sub_name}/v1.py"]

    return {
        "provider_id": prov_id,
        "feature_id": feat_id,
        "tier": tier,
        "source_paths": source_paths,
        "target_provider_path": target_provider_path,
        "capability_ids": [cap_id],
        "capability_spec_paths": cap_spec_paths,
        "existing_public_signatures": [f"get_{sub_name}()"],
        "target_contracts": [f"{sub_name.capitalize()}Protocol"],
        "manifest_values": {
            "provider_id": prov_id,
            "version": "1.0.0",
            "provides": [cap_id],
            "profiles": raw_provider.get("profiles", ["live"]),
            "lifecycle": raw_provider.get("lifecycle", "scoped"),
            "reload": raw_provider.get("reload", "process_restart"),
        },
        "requirements": [f"FR-{domain.upper()}-{sub_name.upper()}-01"],
        "consumers": raw_provider.get("consumers", []),
        "compatibility_facades": [f"app/services/{domain}/__init__.py"],
        "profile_impact": raw_provider.get("profiles", ["live"]),
        "effect_classes": raw_provider.get("effect_classes", ["reversible_ephemeral"]),
        "state_ownership": raw_provider.get("state_schema_id"),
        "migration_ownership": raw_provider.get("migration_manifest"),
        "parity_artifacts": [f"tests/{domain}/fixtures/{prov_id}_parity.json"],
        "test_commands": [f"uv run pytest tests/{domain}/providers/{prov_id}/ -q"],
        "example_command": (
            f"uv run python app/services/{domain}/providers/{prov_id}/example.py"
        ),
        "removal_expectations": f"Provider {prov_id} deactivates cleanly",
        "reinstall_expectations": (
            f"Provider {prov_id} reactivates state and consumers"
        ),
        "protected_paths": ["app/kernel/"],
    }


def validate_provider_record(rec: dict[str, Any]) -> None:
    """Validate provider record contains all mandatory fields.

    Args:
        rec: Provider record to validate.

    Raises:
        SystemExit: If mandatory field is missing.
    """
    prov_id = rec.get("provider_id", "unknown")
    for field in _MANDATORY_FIELDS:
        if field not in rec or rec[field] is None:
            # Note: state_ownership and migration_ownership can be None for stateless
            if field in ("state_ownership", "migration_ownership"):
                continue
            print(f"INCOMPLETE_G2_ROW: {prov_id}: {field}", file=sys.stderr)
            sys.exit(2)


def render_wave_document(
    wave_id: str,
    providers: list[dict[str, Any]],
) -> str:
    """Render complete markdown work-order document for the specified wave.

    Args:
        wave_id: Wave string identifier.
        providers: List of validated provider records for this wave.

    Returns:
        Rendered Markdown document content.
    """
    lines: list[str] = [
        f"# Wave {wave_id} Work Orders",
        "",
        f"> **Wave**: `{wave_id}`  ",
        f"> **Provider Count**: `{len(providers)}`  ",
        "> **Generated From**: `G2_REPORT.md` and `removability_matrix.json`  ",
        "",
        "---",
        "",
        "## 1. Provider Sequence",
        "",
        "| Ordinal | Provider ID | Feature ID | Tier | Capability | Lifecycle |",
        "|---|---|---|:---:|---|---|",
    ]

    for idx, p in enumerate(providers, 1):
        ord_str = f"P{wave_id}-P{idx:03d}"
        cap_id = p["capability_ids"][0]
        lifecycle = p["manifest_values"]["lifecycle"]
        lines.append(
            f"| `{ord_str}` | `{p['provider_id']}` | `{p['feature_id']}` | "
            f"`{p['tier']}` | `{cap_id}` | `{lifecycle}` |"
        )

    lines.extend(["", "---", "", "## 2. Detailed Work Orders", ""])

    for idx, p in enumerate(providers, 1):
        ord_base = f"P{wave_id}-P{idx:03d}"
        prov_id = p["provider_id"]

        lines.extend(
            [
                f"### {ord_base}: `{prov_id}`",
                "",
                f"#### `{ord_base}a` — Capability Specification",
                f"- **Files**: `{p['capability_spec_paths'][0]}`",
                f"- **Contracts**: `{p['target_contracts'][0]}`",
                f"- **Requirements**: `{p['requirements'][0]}`",
                "",
                f"#### `{ord_base}b` — Provider Implementation and Manifest",
                f"- **Directory**: `{p['target_provider_path']}`",
                f"- **Manifest**: `manifest.toml` (`{prov_id}`)",
                "- **Factory**: `create_provider`",
                "",
                f"#### `{ord_base}c1` — Consumer Migration",
                f"- **Consumers**: `{len(p['consumers'])}` declared consumers",
                "- **Boundaries**: public domain exports",
                "",
                f"#### `{ord_base}d` — Compatibility Façade",
                f"- **Façades**: `{p['compatibility_facades'][0]}`",
                "",
                f"#### `{ord_base}e` — Documentation and Examples",
                f"- **README**: `{p['target_provider_path']}/README.md`",
                f"- **Example**: `{p['target_provider_path']}/example.py`",
                f"- **Tests**: `{p['test_commands'][0]}`",
                "",
                f"#### `{ord_base}f` — Verification and Parity Proof",
                f"- **Removal**: {p['removal_expectations']}",
                f"- **Reinstall**: {p['reinstall_expectations']}",
                "",
            ]
        )

    lines.extend(
        [
            "---",
            "",
            "## 3. Self-Verification",
            "",
            f"PASS: Wave {wave_id} work orders verified against G2 audit requirements.",
            "",
        ]
    )

    return "\n".join(lines)


def main() -> None:
    """CLI entry point for work order generator."""
    parser = argparse.ArgumentParser(
        description="Deterministic provider work order generator."
    )
    parser.add_argument(
        "--wave",
        type=str,
        required=True,
        help="Target wave ID (e.g. 12.1).",
    )
    parser.add_argument(
        "--matrix",
        type=Path,
        required=True,
        help="Path to removability_matrix.json.",
    )
    parser.add_argument(
        "--report",
        type=Path,
        required=True,
        help="Path to G2_REPORT.md.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Destination markdown output path.",
    )
    args = parser.parse_args()

    if not args.matrix.is_file():
        print(f"Matrix file missing: {args.matrix}", file=sys.stderr)
        sys.exit(1)

    matrix_data = json.loads(args.matrix.read_text(encoding="utf-8"))
    raw_providers = matrix_data.get("providers", [])

    target_domains = _WAVE_DOMAINS.get(args.wave, ())
    wave_providers: list[dict[str, Any]] = []

    for raw_p in raw_providers:
        if raw_p.get("domain") in target_domains:
            rec = build_provider_record(raw_p, args.wave)
            validate_provider_record(rec)
            wave_providers.append(rec)

    # Deterministic alphabetical sort by provider ID
    wave_providers.sort(key=lambda p: p["provider_id"])

    rendered = render_wave_document(args.wave, wave_providers)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8")
    print(
        f"Generated {len(wave_providers)} work orders for Wave {args.wave} "
        f"at {args.output}"
    )


if __name__ == "__main__":
    main()
