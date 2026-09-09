#!/usr/bin/env python3
"""Preview or create one explicit incomplete stateless backend feature shell."""

from __future__ import annotations

import argparse
import json
import re
import string
import sys
import tempfile
import tomllib
from pathlib import Path
from typing import Any, Final, cast

REPO: Final[Path] = Path(__file__).resolve().parent.parent
TEMPLATE_DIR: Final[Path] = REPO / "docs/templates/feature/stateless_backend"
ENTRY_POINT_HEADER: Final[str] = '[project.entry-points."haruquantai.features"]'


class ScaffoldError(RuntimeError):
    """Raised when a shell cannot be generated without guessing or overwriting."""


def _load_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        message = f"Invalid Task packet: {path}"
        raise ScaffoldError(message) from exc
    if not isinstance(value, dict):
        raise ScaffoldError("Task packet must be a JSON object.")
    return value


def _camel(value: str) -> str:
    words = re.findall(r"[A-Za-z0-9]+", value)
    if not words:
        raise ScaffoldError("Cannot derive a Python identifier from the feature path.")
    return "".join(word[:1].upper() + word[1:] for word in words)


def _module_path(relative: str) -> str:
    return relative.removesuffix(".py").replace("/", ".").replace("\\", ".")


def _render_template(name: str, values: dict[str, str]) -> bytes:
    template = string.Template((TEMPLATE_DIR / name).read_text(encoding="utf-8"))
    try:
        return (template.substitute(values).rstrip() + "\n").encode()
    except KeyError as exc:
        message = f"Template {name} has an unknown placeholder."
        raise ScaffoldError(message) from exc


def build_outputs(packet: dict[str, Any]) -> tuple[dict[str, bytes], dict[str, str]]:
    """Render exact shell outputs and the serialized entry-point proposal.

    Returns:
        Exact output bytes and the proposed entry-point mapping.

    Raises:
        ScaffoldError: If the packet is ineligible, malformed, or overbroad.
    """
    authoring = packet.get("authoring")
    if not isinstance(authoring, dict) or authoring.get("route") != (
        "SCAFFOLD_STATELESS_BACKEND"
    ):
        raise ScaffoldError("Task packet does not authorize the stateless scaffold.")
    raw_identity = packet.get("identity")
    raw_paths = packet.get("paths")
    raw_contract = packet.get("contract")
    raw_task = packet.get("task")
    if not all(
        isinstance(item, dict)
        for item in (raw_identity, raw_paths, raw_contract, raw_task)
    ):
        raise ScaffoldError(
            "Task packet lacks identity, paths, contract, or task data."
        )
    identity = cast("dict[str, Any]", raw_identity)
    paths = cast("dict[str, Any]", raw_paths)
    contract = cast("dict[str, Any]", raw_contract)
    task = cast("dict[str, Any]", raw_task)
    owner_path = str(paths.get("owner_path", ""))
    contract_target = str(paths.get("contract_target", ""))
    acceptance_target = str(paths.get("evidence_path", ""))
    if not owner_path.startswith("app/services/") or not contract_target.startswith(
        "app/contracts/"
    ):
        raise ScaffoldError("Scaffold paths are not approved backend boundaries.")
    feature_id = str(identity.get("feature_id", ""))
    task_id = str(identity.get("task_id", ""))
    baseline = str(identity.get("baseline_commit", ""))
    capability = str(contract.get("primary_capability", ""))
    state_ownership = str(contract.get("state_ownership", "")).strip().lower()
    capability_match = re.fullmatch(r"([a-z0-9.-]+)@(\d+)", capability)
    if not capability_match or not re.fullmatch(r"FEAT-[A-Z0-9_-]+", feature_id):
        raise ScaffoldError("Feature or capability identity is malformed.")
    if not state_ownership.startswith("none"):
        raise ScaffoldError("Contract is not explicitly stateless.")
    slug = Path(owner_path).name
    stem = _camel(slug)
    public_symbols = contract.get("public_symbols", [])
    capability_class = (
        str(public_symbols[0])
        if isinstance(public_symbols, list) and public_symbols
        else f"{stem}Capability"
    )
    capability_constant = f"{re.sub(r'[^A-Za-z0-9]+', '_', slug).upper()}_CAPABILITY"
    domain = str(paths.get("domain", "")).lower()
    title = str(task.get("task_name") or contract.get("title") or stem)
    requirement_ids = [
        str(item.get("requirement_id", item.get("id", "")))
        for item in [*packet.get("requirements", []), *packet.get("local_nfrs", [])]
        if isinstance(item, dict)
    ]
    requirements = [
        {
            "id": requirement_id,
            "status": "FAIL",
            "evidence_target": "INCOMPLETE: feature-specific assertion required",
        }
        for requirement_id in requirement_ids
    ]
    stages = {
        name: {
            "status": "FAIL",
            "evidence": "INCOMPLETE: generated structure is not acceptance evidence",
        }
        for name in (
            "contract",
            "provider",
            "composition",
            "interfaces",
            "ui",
            "end_to_end",
        )
    }
    values = {
        "title": title,
        "feature_id": feature_id,
        "task_id": task_id,
        "task_slug": str(task.get("task_slug", slug)),
        "baseline_commit": baseline,
        "owner_specification": str(paths.get("canonical_spec", "")),
        "owner_module": _module_path(owner_path),
        "contract_module": _module_path(contract_target),
        "domain": domain,
        "capability": capability,
        "capability_name": capability_match.group(1),
        "capability_major": capability_match.group(2),
        "capability_class": capability_class,
        "capability_constant": capability_constant,
        "config_class": f"{stem}Config",
        "feature_class": f"{stem}Feature",
        "requirements_json": json.dumps(requirements, indent=2),
        "stages_json": json.dumps(stages, indent=2),
    }
    outputs = {
        f"{owner_path}/__init__.py": b"",
        f"{owner_path}/README.md": _render_template("README.md.tmpl", values),
        f"{owner_path}/config.py": _render_template("config.py.tmpl", values),
        f"{owner_path}/manifest.py": _render_template("manifest.py.tmpl", values),
        f"{owner_path}/feature.py": _render_template("feature.py.tmpl", values),
        f"{owner_path}/_usage.py": _render_template("_usage.py.tmpl", values),
        contract_target: _render_template("contract.py.tmpl", values),
        acceptance_target: _render_template("acceptance.json.tmpl", values),
    }
    authority = {
        str(path).replace("\\", "/")
        for path in packet.get("authorized_write_paths", [])
    }
    unexpected = set(outputs) - authority
    if unexpected:
        message = f"Generated paths exceed Task packet authority: {sorted(unexpected)}"
        raise ScaffoldError(message)
    entry_name = f"{domain}-{slug.replace('_', '-')}"
    return outputs, {entry_name: f"{_module_path(owner_path)}.feature:feature"}


def _registration_bytes(pyproject: Path, proposal: dict[str, str]) -> bytes:
    text = pyproject.read_text(encoding="utf-8")
    if ENTRY_POINT_HEADER not in text:
        raise ScaffoldError("pyproject entry-point table is missing.")
    for name, target in proposal.items():
        if re.search(rf"(?m)^\s*{re.escape(name)}\s*=", text):
            message = f"Entry point already exists: {name}"
            raise ScaffoldError(message)
        insertion = f'{name} = "{target}"\n'
        start = text.index(ENTRY_POINT_HEADER) + len(ENTRY_POINT_HEADER)
        newline = text.index("\n", start) + 1
        text = text[:newline] + insertion + text[newline:]
    raw = text.encode()
    tomllib.loads(raw.decode())
    return raw


def apply_outputs(
    outputs: dict[str, bytes],
    *,
    root: Path,
    replace_paths: frozenset[str] = frozenset(),
) -> None:
    """Create all outputs atomically after refusing every existing target.

    Args:
        outputs: Exact repository-relative output bytes.
        root: Destination repository root.
        replace_paths: Explicit shared files the serialized integrator may replace.

    Raises:
        ScaffoldError: If any target already exists.
        OSError: If staging, creation, or rollback fails.
    """
    existing = sorted(
        relative
        for relative in outputs
        if (root / relative).exists() and relative not in replace_paths
    )
    if existing:
        message = f"Refusing to overwrite existing paths: {existing}"
        raise ScaffoldError(message)
    originals = {
        relative: (root / relative).read_bytes()
        for relative in replace_paths
        if (root / relative).is_file()
    }
    with tempfile.TemporaryDirectory(prefix="hq-scaffold-") as temp_name:
        temp = Path(temp_name)
        for relative, content in outputs.items():
            staged = temp / relative
            staged.parent.mkdir(parents=True, exist_ok=True)
            staged.write_bytes(content)
        created: list[Path] = []
        try:
            for relative in sorted(outputs):
                target = root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes((temp / relative).read_bytes())
                created.append(target)
        except OSError:
            for target in reversed(created):
                relative = target.relative_to(root).as_posix()
                if relative in originals:
                    target.write_bytes(originals[relative])
                else:
                    target.unlink(missing_ok=True)
            raise


def _add_registration(
    outputs: dict[str, bytes],
    proposal: dict[str, str],
    packet: dict[str, Any],
    *,
    output_root: Path,
) -> None:
    """Add the shared registration only under packet-scoped integrator authority.

    Raises:
        ScaffoldError: If serialized registration authority is absent.
    """
    if "pyproject.toml" not in packet.get("serialized_integration_write_paths", []):
        raise ScaffoldError("Task packet does not authorize serialized registration.")
    outputs["pyproject.toml"] = _registration_bytes(
        output_root / "pyproject.toml", proposal
    )


def main() -> int:
    """Run preview or fail-closed shell creation.

    Returns:
        Process exit status.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-packet", required=True, type=Path)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--preview", action="store_true")
    mode.add_argument("--apply", action="store_true")
    parser.add_argument("--output-root", type=Path, default=REPO)
    parser.add_argument("--apply-registration", action="store_true")
    parser.add_argument("--serialized-integrator", action="store_true")
    args = parser.parse_args()
    if args.apply_registration != args.serialized_integrator:
        print(
            "[FAIL] registration requires both --apply-registration and "
            "--serialized-integrator"
        )
        return 1
    try:
        outputs, proposal = build_outputs(_load_object(args.task_packet))
        if args.apply_registration:
            packet = _load_object(args.task_packet)
            _add_registration(
                outputs,
                proposal,
                packet,
                output_root=args.output_root,
            )
        replace_paths = (
            frozenset({"pyproject.toml"}) if args.apply_registration else frozenset()
        )
        existing = sorted(
            relative
            for relative in outputs
            if (args.output_root / relative).exists() and relative not in replace_paths
        )
        preview = {
            "status": "INCOMPLETE_SHELL",
            "outputs": sorted(outputs),
            "existing_paths": existing,
            "entry_point_proposal": proposal,
            "registration_applied": bool(args.apply_registration),
        }
        print(json.dumps(preview, indent=2))
        if args.preview:
            return 0 if not existing else 1
        apply_outputs(
            outputs,
            root=args.output_root,
            replace_paths=replace_paths,
        )
    except (OSError, ScaffoldError, tomllib.TOMLDecodeError) as exc:
        print(f"[FAIL] stateless scaffold: {exc}")
        return 1
    print(f"[OK] created {len(outputs)} incomplete shell files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
