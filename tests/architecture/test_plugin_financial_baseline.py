"""Verification tests for the plugin financial evidence baseline manifest."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

_MANIFEST_PATH = (
    Path(__file__).resolve().parent / "fixtures" / "plugin_financial_baseline.json"
)
_REPO_ROOT = Path(__file__).resolve().parents[2]
_HASH_PATTERN = re.compile(r"^[0-9a-f]{64}$")


def _load_manifest() -> dict[str, Any]:
    """Load and parse the financial baseline JSON manifest.

    Returns:
        dict[str, Any]: Parsed JSON dictionary.
    """
    return json.loads(_MANIFEST_PATH.read_text(encoding="utf-8"))


def test_financial_manifest_is_canonical() -> None:
    """Verify that the financial baseline manifest structure conforms to canonical rules."""
    assert _MANIFEST_PATH.is_file(), f"Manifest not found at {_MANIFEST_PATH}"
    manifest = _load_manifest()

    expected_top_keys = {"baseline_commit", "algorithm", "artifacts"}
    assert set(manifest.keys()) == expected_top_keys, (
        f"Manifest keys mismatch: got {set(manifest.keys())}, expected {expected_top_keys}"
    )

    baseline_commit = manifest["baseline_commit"]
    assert isinstance(baseline_commit, str), (
        f"Invalid baseline_commit type: {type(baseline_commit)}"
    )
    assert len(baseline_commit) == 40, (
        f"Invalid baseline_commit length: {len(baseline_commit)}"
    )

    assert manifest["algorithm"] == "sha256", (
        f"Invalid algorithm: {manifest['algorithm']!r}"
    )

    artifacts = manifest["artifacts"]
    assert isinstance(artifacts, list), (
        f"Expected artifacts list, got {type(artifacts)}"
    )
    assert len(artifacts) == 15, f"Expected 15 artifacts, got {len(artifacts)}"

    paths: list[str] = []
    for item in artifacts:
        assert isinstance(item, dict), f"Artifact item is not a dict: {item}"
        assert set(item.keys()) == {"path", "sha256"}, (
            f"Artifact item keys mismatch: {item}"
        )

        path_str = item["path"]
        assert isinstance(path_str, str), f"Path must be string: {path_str}"
        assert not Path(path_str).is_absolute(), f"Absolute path forbidden: {path_str}"
        assert "\\" not in path_str, f"Backslashes forbidden in path: {path_str}"
        assert _HASH_PATTERN.fullmatch(item["sha256"]), (
            f"Hash must be 64 lowercase hex chars: {item['sha256']}"
        )
        paths.append(path_str)

    assert paths == sorted(paths), "Artifact paths must be strictly sorted"
    assert len(paths) == len(set(paths)), "Duplicate artifact paths found"


def test_financial_artifacts_match_baseline() -> None:
    """Verify that all financial baseline artifacts match their expected SHA-256 byte hashes."""
    manifest = _load_manifest()
    artifacts: list[dict[str, str]] = manifest["artifacts"]

    for item in artifacts:
        relative_path = item["path"]
        expected_hash = item["sha256"]
        target_file = _REPO_ROOT / relative_path

        assert target_file.is_file(), (
            f"Financial baseline target file missing: {relative_path}"
        )

        raw_bytes = target_file.read_bytes()
        actual_hash = hashlib.sha256(raw_bytes).hexdigest()

        assert actual_hash == expected_hash, (
            f"Financial baseline hash mismatch for {relative_path}:\n"
            f"  Expected: {expected_hash}\n"
            f"  Actual:   {actual_hash}"
        )
