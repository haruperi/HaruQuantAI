"""Validate feature documentation against runtime FeatureSpec truth."""

import importlib
import re
import sys
import tomllib
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.kernel.feature import FeatureSpec


def load_feature_entry_points(pyproject_path: Path) -> dict[str, str]:
    """Parse feature entry points from pyproject.toml.

    Args:
        pyproject_path: Path to pyproject.toml.

    Returns:
        Dictionary mapping entry point names to target factories.
    """
    with pyproject_path.open("rb") as f:
        data = tomllib.load(f)
    return (
        data.get("project", {}).get("entry-points", {}).get("haruquantai.features", {})
    )


def validate_feature_readme(
    spec: FeatureSpec,
    readme_path: Path,
) -> list[str]:
    """Validate that README content matches FeatureSpec metadata.

    Args:
        spec: Runtime FeatureSpec instance.
        readme_path: Path to feature's README.md file.

    Returns:
        List of error messages (empty if valid).
    """
    errors: list[str] = []
    if not readme_path.exists():
        return [f"README.md missing at {readme_path}"]

    content = readme_path.read_text(encoding="utf-8")

    # Check Feature ID
    if spec.feature_id not in content:
        errors.append(f"Feature ID '{spec.feature_id}' not found in {readme_path.name}")

    # Check Domain
    domain_match = re.search(r"## Domain\s+`?([a-z_]+)`?", content, re.IGNORECASE)
    if not domain_match or domain_match.group(1).lower() != spec.domain.lower():
        found = domain_match.group(1) if domain_match else "none"
        errors.append(
            f"Domain mismatch in {readme_path.name}: "
            f"expected '{spec.domain}', found '{found}'"
        )

    # Check Provided Capabilities
    for cap in spec.provides:
        if cap.identifier not in content:
            errors.append(
                f"Provided capability '{cap.identifier}' missing "
                f"from {readme_path.name}"
            )

    # Check Required Capabilities
    for cap in spec.requires:
        if cap.identifier not in content:
            errors.append(
                f"Required capability '{cap.identifier}' missing "
                f"from {readme_path.name}"
            )

    # Check Optional Capabilities
    for cap in spec.optional:
        if cap.identifier not in content:
            errors.append(
                f"Optional capability '{cap.identifier}' missing "
                f"from {readme_path.name}"
            )

    return errors


def main() -> int:
    """Validate all registered feature READMEs against runtime FeatureSpec.

    Returns:
        Exit code (0 if all valid, 1 if drift detected).
    """
    root_dir = Path(__file__).resolve().parent.parent
    pyproject_path = root_dir / "pyproject.toml"

    entry_points = load_feature_entry_points(pyproject_path)
    if not entry_points:
        print("[ERROR] No feature entry points found in pyproject.toml")
        return 1

    all_errors: dict[str, list[str]] = {}

    for target in entry_points.values():
        module_name, func_name = target.split(":")
        mod = importlib.import_module(module_name)
        factory: Any = getattr(mod, func_name)
        feature = factory()
        spec: FeatureSpec = feature.spec

        module_file = Path(mod.__file__).resolve()
        pkg_dir = module_file.parent
        readme_path = pkg_dir / "README.md"

        errs = validate_feature_readme(spec, readme_path)
        if errs:
            all_errors[spec.feature_id] = errs
        else:
            print(f"[OK] {spec.feature_id} documentation validated.")

    if all_errors:
        print("\n[FAIL] Feature documentation drift detected:")
        for fid, errs in all_errors.items():
            print(f"\n  Feature: {fid}")
            for err in errs:
                print(f"    - {err}")
        return 1

    total = len(entry_points)
    print(f"\n[SUCCESS] All {total} feature READMEs match FeatureSpec truth!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
