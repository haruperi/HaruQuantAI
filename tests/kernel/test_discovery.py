"""Unit tests for kernel manifest discovery."""

from __future__ import annotations

from pathlib import Path

from app.kernel.discovery import DiscoveredProvider, discover_manifests
from app.kernel.identifiers import ProviderId


def test_discover_manifests_nonexistent_root(tmp_path: Path) -> None:
    """Verify discover_manifests returns empty tuple when root does not exist."""
    non_existent = tmp_path / "does_not_exist"
    assert discover_manifests(non_existent) == ()


def test_discover_manifests_finds_valid_manifests(tmp_path: Path) -> None:
    """Verify discover_manifests finds and sorts provider manifests."""
    p1 = tmp_path / "provider_b"
    p1.mkdir()
    (p1 / "manifest.toml").write_text(
        """
[provider]
id = "provider.b.default"
version = "1.0.0"
entry_point = "pkg.b:create_provider"

[[provides]]
capability_id = "cap.b.v1"
""",
        encoding="utf-8",
    )

    p2 = tmp_path / "provider_a"
    p2.mkdir()
    (p2 / "manifest.toml").write_text(
        """
[provider]
id = "provider.a.default"
version = "1.0.0"
entry_point = "pkg.a:create_provider"

[[provides]]
capability_id = "cap.a.v1"
""",
        encoding="utf-8",
    )

    results = discover_manifests(tmp_path)
    assert len(results) == 2
    assert isinstance(results[0], DiscoveredProvider)
    # Sorted by provider id
    assert results[0].manifest.id == ProviderId.parse("provider.a.default")
    assert results[1].manifest.id == ProviderId.parse("provider.b.default")


def test_discover_manifests_skips_pycache_and_invalid_toml(tmp_path: Path) -> None:
    """Verify discover_manifests skips __pycache__ and invalid TOML manifests."""
    pycache_dir = tmp_path / "__pycache__"
    pycache_dir.mkdir()
    (pycache_dir / "manifest.toml").write_text("invalid", encoding="utf-8")

    invalid_dir = tmp_path / "invalid_manifest"
    invalid_dir.mkdir()
    (invalid_dir / "manifest.toml").write_text("not a valid toml = [", encoding="utf-8")

    valid_dir = tmp_path / "valid_manifest"
    valid_dir.mkdir()
    (valid_dir / "manifest.toml").write_text(
        """
[provider]
id = "provider.c.default"
version = "1.0.0"
entry_point = "pkg.c:create_provider"
""",
        encoding="utf-8",
    )

    results = discover_manifests(tmp_path)
    assert len(results) == 1
    assert results[0].manifest.id == ProviderId.parse("provider.c.default")


def test_discover_manifests_handles_duplicate_provider_ids(tmp_path: Path) -> None:
    """Verify discover_manifests handles duplicate provider IDs gracefully."""
    p1 = tmp_path / "p1"
    p1.mkdir()
    (p1 / "manifest.toml").write_text(
        """
[provider]
id = "provider.dup.default"
version = "1.0.0"
entry_point = "pkg.p1:create_provider"
""",
        encoding="utf-8",
    )

    p2 = tmp_path / "p2"
    p2.mkdir()
    (p2 / "manifest.toml").write_text(
        """
[provider]
id = "provider.dup.default"
version = "2.0.0"
entry_point = "pkg.p2:create_provider"
""",
        encoding="utf-8",
    )

    results = discover_manifests(tmp_path)
    assert len(results) == 2
    assert results[0].manifest.id == ProviderId.parse("provider.dup.default")
