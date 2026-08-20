"""Unit tests for filesystem provider manifest discovery.

Traces to: P4-T03, Gate G4
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from app.kernel.discovery import discover_manifests
from app.kernel.errors import ManifestValidationError

_SAMPLE_MANIFEST_A = """
[provider]
id = "indicator.rsi.default"
version = "1.0.0"
entry_point = "app.services.indicators.rsi_default.plugin:create_provider"

[[provides]]
capability_id = "indicator.rsi.v1"
contract_version = "1.0.0"
cardinality = "many"

[runtime]
profiles = ["research"]
scopes = ["process"]
effect_classes = ["reversible_ephemeral"]
lifecycle = "pure"
reload = "config_restart"
"""

_SAMPLE_MANIFEST_B = """
[provider]
id = "indicator.williams_r.default"
version = "1.0.0"
entry_point = "app.services.indicators.williams_r_default.plugin:create_provider"

[[provides]]
capability_id = "indicator.williams_r.v1"
contract_version = "1.0.0"
cardinality = "many"

[runtime]
profiles = ["research"]
scopes = ["process"]
effect_classes = ["reversible_ephemeral"]
lifecycle = "pure"
reload = "config_restart"
"""


def test_discover_empty_root_returns_empty(tmp_path: Path) -> None:
    """Verify empty directory returns empty tuple."""
    res = discover_manifests(tmp_path)
    assert res == ()


def test_discover_nonexistent_root_returns_empty(tmp_path: Path) -> None:
    """Verify non-existent directory returns empty tuple."""
    res = discover_manifests(tmp_path / "nonexistent")
    assert res == ()


def test_discover_multiple_manifests_sorted(tmp_path: Path) -> None:
    """Verify discovery finds multiple manifests and sorts by provider ID."""
    dir_b = tmp_path / "williams"
    dir_b.mkdir()
    (dir_b / "manifest.toml").write_text(_SAMPLE_MANIFEST_B.strip(), encoding="utf-8")

    dir_a = tmp_path / "rsi"
    dir_a.mkdir()
    (dir_a / "manifest.toml").write_text(_SAMPLE_MANIFEST_A.strip(), encoding="utf-8")

    res = discover_manifests(tmp_path)
    assert len(res) == 2
    assert str(res[0].manifest.provider_id) == "indicator.rsi.default"
    assert str(res[1].manifest.provider_id) == "indicator.williams_r.default"


def test_discover_skips_hidden_and_pycache(tmp_path: Path) -> None:
    """Verify discovery ignores hidden folders and __pycache__."""
    hidden = tmp_path / ".hidden"
    hidden.mkdir()
    (hidden / "manifest.toml").write_text(_SAMPLE_MANIFEST_A.strip(), encoding="utf-8")

    pycache = tmp_path / "__pycache__"
    pycache.mkdir()
    (pycache / "manifest.toml").write_text(_SAMPLE_MANIFEST_A.strip(), encoding="utf-8")

    res = discover_manifests(tmp_path)
    assert res == ()


def test_discover_rejects_duplicate_provider_id(tmp_path: Path) -> None:
    """Verify discovery fails closed when duplicate provider ID is discovered."""
    dir1 = tmp_path / "p1"
    dir1.mkdir()
    (dir1 / "manifest.toml").write_text(_SAMPLE_MANIFEST_A.strip(), encoding="utf-8")

    dir2 = tmp_path / "p2"
    dir2.mkdir()
    (dir2 / "manifest.toml").write_text(_SAMPLE_MANIFEST_A.strip(), encoding="utf-8")

    with pytest.raises(
        ManifestValidationError,
        match=r"duplicate provider id indicator\.rsi\.default",
    ):
        discover_manifests(tmp_path)


def test_discovery_does_not_import_provider_modules(tmp_path: Path) -> None:
    """Verify filesystem discovery imports zero Python provider modules."""
    sentinel_mod = "app.test_discovery_sentinel_mod_abc"
    content = f"""
[provider]
id = "indicator.rsi.default"
version = "1.0.0"
entry_point = "{sentinel_mod}:create_provider"

[[provides]]
capability_id = "indicator.rsi.v1"
contract_version = "1.0.0"
cardinality = "many"

[runtime]
profiles = ["research"]
scopes = ["process"]
effect_classes = ["reversible_ephemeral"]
lifecycle = "pure"
reload = "config_restart"
"""
    p_dir = tmp_path / "rsi"
    p_dir.mkdir()
    (p_dir / "manifest.toml").write_text(content.strip(), encoding="utf-8")

    res = discover_manifests(tmp_path)
    assert len(res) == 1
    assert sentinel_mod not in sys.modules
