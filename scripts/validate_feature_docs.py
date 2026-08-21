"""Validate feature READMEs against exact runtime FeatureSpec declarations."""

from __future__ import annotations

import importlib
import re
import sys
import tomllib
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.kernel.feature import FeatureSpec

_CAPABILITY_PATTERN = re.compile(r"[a-z][a-z0-9_.-]*@[1-9][0-9]*")


def load_feature_entry_points(pyproject_path: Path) -> dict[str, str]:
    """Load registered feature factories from pyproject.toml."""
    with pyproject_path.open("rb") as file:
        data = tomllib.load(file)
    value = (
        data.get("project", {}).get("entry-points", {}).get("haruquantai.features", {})
    )
    if not isinstance(value, dict):
        raise ValueError("Feature entry-point table is invalid")
    return {str(name): str(target) for name, target in value.items()}


def _section(content: str, title: str) -> str | None:
    match = re.search(
        rf"^##\s+{re.escape(title)}\s*$\n(.*?)(?=^##\s+|\Z)",
        content,
        flags=re.IGNORECASE | re.MULTILINE | re.DOTALL,
    )
    return match.group(1).strip() if match is not None else None


def _capability_set(section: str | None) -> set[str] | None:
    if section is None:
        return None
    if section.strip().lower().startswith("none"):
        return set()
    return set(_CAPABILITY_PATTERN.findall(section))


def _configuration_keys(section: str | None) -> set[str] | None:
    if section is None:
        return None
    if section.strip().lower().startswith("none"):
        return set()
    keys: set[str] = set()
    for line in section.splitlines():
        match = re.match(r"^\|\s*`([^`]+)`\s*\|", line)
        if match is not None:
            keys.add(match.group(1).strip())
    return keys


def validate_feature_readme(
    spec: FeatureSpec,
    readme_path: Path,
) -> list[str]:
    """Return exact manifest-versus-documentation mismatches."""
    if not readme_path.is_file():
        return [f"README.md missing at {readme_path}"]
    content = readme_path.read_text(encoding="utf-8")
    errors: list[str] = []

    if spec.feature_id not in content:
        errors.append(f"Feature ID '{spec.feature_id}' is missing")

    domain_section = _section(content, "Domain")
    documented_domain = (
        domain_section.replace("`", "").strip().lower()
        if domain_section is not None
        else None
    )
    if documented_domain != spec.domain.lower():
        errors.append(
            f"Domain mismatch: expected '{spec.domain}', got '{documented_domain}'"
        )

    comparisons = (
        ("Provides", {cap.identifier for cap in spec.provides}),
        ("Required Capabilities", {cap.identifier for cap in spec.requires}),
        ("Optional Capabilities", {cap.identifier for cap in spec.optional}),
    )
    for section_name, expected in comparisons:
        documented = _capability_set(_section(content, section_name))
        if documented is None:
            errors.append(f"Missing section '## {section_name}'")
        elif documented != expected:
            errors.append(
                f"{section_name} mismatch: expected {sorted(expected)}, "
                f"got {sorted(documented)}"
            )

    documented_config = _configuration_keys(_section(content, "Configuration"))
    if documented_config is None:
        errors.append("Missing section '## Configuration'")
    elif documented_config != set(spec.config_keys):
        errors.append(
            f"Configuration mismatch: expected {sorted(spec.config_keys)}, "
            f"got {sorted(documented_config)}"
        )

    for required_section in (
        "Purpose",
        "Runtime Effects",
        "Failure Behavior",
        "Removal Behavior",
    ):
        section_content = _section(content, required_section)
        if section_content is None or not section_content.strip():
            errors.append(f"Missing or empty section '## {required_section}'")

    state_section = _section(content, "Persistent State")
    if state_section is None:
        errors.append("Missing section '## Persistent State'")
    elif spec.state is None and not state_section.strip().lower().startswith("none"):
        errors.append("Persistent State must be 'None' when FeatureSpec.state is None")
    elif spec.state is not None and spec.state.namespace not in state_section:
        errors.append(f"Persistent state namespace '{spec.state.namespace}' is missing")
    return errors


def main() -> int:
    """Validate every registered feature README."""
    root = Path(__file__).resolve().parent.parent
    try:
        entry_points = load_feature_entry_points(root / "pyproject.toml")
    except (OSError, ValueError, tomllib.TOMLDecodeError) as error:
        print(f"[ERROR] {error}")
        return 1
    if not entry_points:
        print("[ERROR] No registered feature entry points")
        return 1

    errors_by_feature: dict[str, list[str]] = {}
    seen_feature_ids: set[str] = set()
    for entry_point_name, target in entry_points.items():
        if ":" not in target:
            errors_by_feature[entry_point_name] = [
                f"Invalid entry-point target '{target}'"
            ]
            continue
        module_name, factory_name = target.split(":", maxsplit=1)
        try:
            module = importlib.import_module(module_name)
            factory: Any = getattr(module, factory_name)
            feature = factory() if callable(factory) else factory
            spec: FeatureSpec = feature.spec
            spec.validate()
            if spec.feature_id in seen_feature_ids:
                errors_by_feature[entry_point_name] = [
                    f"Duplicate feature ID '{spec.feature_id}'"
                ]
                continue
            seen_feature_ids.add(spec.feature_id)
            module_file = Path(module.__file__).resolve()
            errors = validate_feature_readme(
                spec,
                module_file.parent / "README.md",
            )
            if errors:
                errors_by_feature[spec.feature_id] = errors
            else:
                print(f"[OK] {spec.feature_id}")
        except Exception as error:  # noqa: BLE001
            errors_by_feature[entry_point_name] = [str(error)]

    if errors_by_feature:
        print("\n[FAIL] Feature documentation drift detected:")
        for feature_id, errors in sorted(errors_by_feature.items()):
            print(f"  {feature_id}:")
            for error in errors:
                print(f"    - {error}")
        return 1
    print(f"\n[SUCCESS] {len(entry_points)} feature READMEs match runtime truth")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
