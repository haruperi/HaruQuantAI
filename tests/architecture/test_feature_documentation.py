"""Architectural test ensuring feature documentation matches FeatureSpec truth."""

from pathlib import Path

from scripts.validate_feature_docs import (
    load_feature_entry_points,
    validate_feature_readme,
)


def test_all_feature_readmes_match_spec() -> None:
    """Verify that every entry point feature has a synchronized README.md."""
    root_dir = Path(__file__).resolve().parent.parent.parent
    pyproject_path = root_dir / "pyproject.toml"

    entry_points = load_feature_entry_points(pyproject_path)
    assert len(entry_points) > 0, "Expected registered feature entry points"

    for name, target in entry_points.items():
        module_name, func_name = target.split(":")
        mod = __import__(module_name, fromlist=[func_name])
        factory = getattr(mod, func_name)
        feature = factory()
        spec = feature.spec

        module_file = Path(mod.__file__).resolve()
        pkg_dir = module_file.parent
        readme_path = pkg_dir / "README.md"

        errors = validate_feature_readme(spec, readme_path)
        assert not errors, (
            f"Feature documentation drift in {name} ({spec.feature_id}): {errors}"
        )
