"""Unit tests for the AppMarketplace backend service and domain models.

Description:
    Tests the MarketplacePluginDescriptor, MarketplaceStore isolated persistence,
    MarketplaceFileMap shareable tree filtering, MarketplaceService zip packaging,
    safe archive extraction, checksum verification, and uninstallation workflows.

Purpose:
    FEAT-MARKETPLACE-TESTS: High-assurance coverage for marketplace logic.

Key Capabilities:
    - FR-TEST-DESCRIPTOR: Verifies default descriptor properties.
    - FR-TEST-STORE: Verifies isolated store load, save, record, list, and delete.
    - FR-TEST-FILEMAP: Verifies tree building, excluded directories, and filtering.
    - FR-TEST-BUILD-ZIP: Verifies zip construction, manifest generation, and cleanup.
    - FR-TEST-INSTALL-UNINSTALL: Verifies checksum check, zip slip guard, builtin skip,
      restart detection, file extraction, uninstallation, and directory pruning.

Python API Usage:
    ```python
    uv run python -m pytest tests/workspace/marketplace/test_app_marketplace.py -v
    ```

CLI Usage:
    ```bash
    uv run python -m pytest tests/workspace/marketplace/test_app_marketplace.py --cov=app/workspace/marketplace --cov-branch
    ```
"""

from __future__ import annotations

import hashlib
import io
import json
import zipfile
from pathlib import Path

import pytest
from app.workspace.marketplace.app_marketplace import (
    EXCLUDED_TOP_DIRS,
    MarketplaceFileMap,
    MarketplaceService,
    MarketplaceStore,
)
from app.workspace.marketplace.app_marketplace_models import (
    InstalledProductModel,
    MarketplacePluginDescriptor,
    ShareManifestCategory,
    ShareManifestModel,
)


def test_marketplace_descriptor_defaults() -> None:
    """Verify plugin descriptor matches StrategyQuant Marketplace conventions."""
    descriptor = MarketplacePluginDescriptor()
    assert descriptor.name == "MARKETPLACE"
    assert descriptor.product == "SQUANT"
    assert descriptor.preferred_position == 1000
    assert descriptor.context_path == "/marketplace"
    assert descriptor.app_code == "MARKETPLACE"
    assert descriptor.url == "../MARKETPLACE/index.html"
    assert descriptor.icon_class == "fa-shopping-bag"
    assert descriptor.section == 1
    assert descriptor.iframe_id == "marketplace-frame"
    assert descriptor.link_id == "marketplace-link"


def test_marketplace_models_and_manifest() -> None:
    """Verify models validation and manifest serialization."""
    cat = ShareManifestCategory(id="indicators", label="Indicators")
    manifest = ShareManifestModel(
        title="Sample Pack",
        description="A test pack",
        version="1.0.0",
        author="Tester",
        category=cat,
        files=["indicators/Test.java"],
        generated_at="2026-10-30T00:00:00Z",
    )
    dump = manifest.model_dump(by_alias=True)
    assert dump["schema"] == "sqx-marketplace/1"
    assert dump["title"] == "Sample Pack"
    assert dump["category"]["id"] == "indicators"

    entry = InstalledProductModel(
        slug="pack-1",
        title="Pack One",
        version="1.0.1",
        files=["file1.txt"],
    )
    assert entry.slug == "pack-1"
    assert entry.files == ["file1.txt"]


def test_marketplace_store_operations(tmp_path: Path) -> None:
    """Verify isolated MarketplaceStore file operations."""
    store_file = tmp_path / "installed.json"
    store = MarketplaceStore(file_path=store_file)

    # Initial state
    assert store.list_installed() == []
    assert store.get_installed_files("unknown") == []
    assert store.get_installed_record("unknown") is None

    # Record install
    store.record_install(
        slug="alpha",
        title="Alpha Plugin",
        version="1.2.0",
        file_name="alpha.zip",
        sha256="abc123sha",
        installed_files=["alpha/plugin.py"],
    )
    store.record_install(
        slug="beta",
        title="Beta Plugin",
        version="",
        file_name="beta.zip",
        sha256="def456sha",
    )

    installed = store.list_installed()
    assert len(installed) == 2
    assert installed[0].slug == "alpha"
    assert installed[0].version == "1.2.0"
    assert installed[1].slug == "beta"
    assert installed[1].version is None

    record = store.get_installed_record("alpha")
    assert record is not None
    assert record.title == "Alpha Plugin"
    assert record.files == ["alpha/plugin.py"]
    assert store.get_installed_files("alpha") == ["alpha/plugin.py"]

    # Delete install
    store.delete_install("alpha")
    assert len(store.list_installed()) == 1
    assert store.get_installed_record("alpha") is None

    # Re-open store from file
    store2 = MarketplaceStore(file_path=store_file)
    assert len(store2.list_installed()) == 1
    assert store2.list_installed()[0].slug == "beta"

    # Corrupt store file handling
    store_file.write_text("invalid json", encoding="utf-8")
    store3 = MarketplaceStore(file_path=store_file)
    assert store3.list_installed() == []


def test_marketplace_file_map_exclusions(tmp_path: Path) -> None:
    """Verify excluded system roots and file map detection."""
    user_root = tmp_path / "user"
    user_root.mkdir()

    for name in EXCLUDED_TOP_DIRS:
        (user_root / name).mkdir()
        (user_root / name / "file.txt").write_text("secret", encoding="utf-8")

    valid_dir = user_root / "snippets"
    valid_dir.mkdir()
    valid_file = valid_dir / "Indicator.java"
    valid_file.write_text("code", encoding="utf-8")

    assert "settings" in MarketplaceFileMap.excluded_top_dirs()
    assert MarketplaceFileMap.is_excluded_from_share(
        user_root / "settings" / "file.txt", user_root
    )
    assert MarketplaceFileMap.is_excluded_from_share(
        user_root / "cache" / "temp.dat", user_root
    )
    assert not MarketplaceFileMap.is_excluded_from_share(valid_file, user_root)
    assert not MarketplaceFileMap.is_excluded_from_share(user_root, user_root)

    # Outside root is excluded
    outside_file = tmp_path / "other" / "file.txt"
    assert MarketplaceFileMap.is_excluded_from_share(outside_file, user_root)


def test_marketplace_file_map_generate_tree(tmp_path: Path) -> None:
    """Verify tree building with nesting and search filtering."""
    user_root = tmp_path / "user"
    snippets = user_root / "snippets"
    indicators = snippets / "indicators"
    indicators.mkdir(parents=True)

    f1 = indicators / "RSI.java"
    f1.write_text("class RSI {}", encoding="utf-8")
    f2 = indicators / "MACD.java"
    f2.write_text("class MACD {}", encoding="utf-8")
    f3 = snippets / "Notes.txt"
    f3.write_text("notes", encoding="utf-8")

    # Excluded folder should not appear
    (user_root / "log").mkdir()
    (user_root / "log" / "app.log").write_text("log", encoding="utf-8")

    source_dirs = {str(user_root.resolve()): "user"}

    # Full tree
    tree = MarketplaceFileMap.generate_tree(source_dirs=source_dirs, filter_str="")
    assert len(tree) == 1
    assert tree[0]["text"] == "user"
    sub_items = tree[0]["item"]
    assert len(sub_items) == 1  # snippets only (log is excluded)
    assert sub_items[0]["text"] == "snippets"

    # Filtered tree matching 'rsi'
    filtered_rsi = MarketplaceFileMap.generate_tree(
        source_dirs=source_dirs, filter_str="rsi"
    )
    assert len(filtered_rsi) == 1
    assert filtered_rsi[0]["item"][0]["text"] == "snippets"
    nested_rsi = filtered_rsi[0]["item"][0]["item"][0]
    assert nested_rsi["text"] == "indicators"
    assert len(nested_rsi["item"]) == 1
    assert nested_rsi["item"][0]["text"] == "RSI.java"

    # Filtered tree matching non-existent
    filtered_none = MarketplaceFileMap.generate_tree(
        source_dirs=source_dirs, filter_str="nonexistent"
    )
    assert len(filtered_none) == 1
    assert filtered_none[0]["item"] == []

    # Non-existent source dir returns empty
    empty_tree = MarketplaceFileMap.generate_tree(
        source_dirs={str(tmp_path / "missing"): "missing"}
    )
    assert empty_tree == []


def test_marketplace_service_record_and_list_shareable(tmp_path: Path) -> None:
    """Verify record_share and list_shareable service endpoints."""
    store = MarketplaceStore(file_path=tmp_path / "installed.json")
    service = MarketplaceService(store=store, data_dir=tmp_path)

    assert service.get_descriptor().app_code == "MARKETPLACE"

    # record_share
    with pytest.raises(ValueError, match="Missing product slug"):
        service.record_share("   ")

    slug = service.record_share(
        slug="my-pack",
        title="My Package",
        version="2.0.0",
        file_name="my-pack.zip",
        sha256="abc",
    )
    assert slug == "my-pack"
    assert len(service.list_installed()) == 1

    # list_shareable with user dir
    (service.user_dir / "strategies").mkdir(parents=True)
    (service.user_dir / "strategies" / "Strat1.java").write_text(
        "code", encoding="utf-8"
    )
    (service.user_dir / "settings").mkdir(parents=True)

    result = service.list_shareable(filter_str="", license_owner="Tester")
    assert result["success"] == "Sources listed."
    assert result["licenseOwner"] == "Tester"
    assert "settings" in result["excluded"]
    assert len(result["item"]) == 1


def test_marketplace_service_build_zip_and_cleanup(tmp_path: Path) -> None:
    """Verify zip creation, manifest generation, and cleanup."""
    store = MarketplaceStore(file_path=tmp_path / "installed.json")
    service = MarketplaceService(store=store, data_dir=tmp_path)

    user_dir = service.user_dir
    user_dir.mkdir(parents=True)
    file1 = user_dir / "Rule1.java"
    file1.write_text("class Rule1 {}", encoding="utf-8")
    sub_dir = user_dir / "blocks"
    sub_dir.mkdir()
    file2 = sub_dir / "Block1.java"
    file2.write_text("class Block1 {}", encoding="utf-8")

    # Error cases for build_zip
    with pytest.raises(ValueError, match=r"File name must end with \.zip"):
        service.build_zip([file1], "invalid_name.tar")
    with pytest.raises(ValueError, match=r"File name must end with \.zip"):
        service.build_zip([file1], "../traversal.zip")
    with pytest.raises(ValueError, match="There are no files to share"):
        service.build_zip([], "test.zip")

    # File outside user folder
    outside = tmp_path / "outside.txt"
    outside.write_text("outside", encoding="utf-8")
    with pytest.raises(ValueError, match="not inside the user folder"):
        service.build_zip([outside], "outside.zip")

    # Excluded file
    excluded_dir = user_dir / "data"
    excluded_dir.mkdir()
    exc_file = excluded_dir / "test.csv"
    exc_file.write_text("1,2,3", encoding="utf-8")
    with pytest.raises(ValueError, match="folder that cannot be shared"):
        service.build_zip([exc_file], "excluded.zip")

    # Non-existent file
    with pytest.raises(ValueError, match="does not exist"):
        service.build_zip([user_dir / "missing.txt"], "missing.zip")

    # Successful build_zip with directory and file
    meta = {
        "title": "Custom Rules",
        "description": "Rules description",
        "version": "1.0.0",
        "author": "Alice",
        "categoryId": "rules",
        "categoryLabel": "Trading Rules",
    }
    built = service.build_zip(
        files=[file1, sub_dir],
        file_name="rules_package.zip",
        meta=meta,
    )
    assert built.file_name == "rules_package.zip"
    assert built.size > 0
    assert built.build == "HaruQuantAI"

    # Inspect zip contents
    zip_path = service.tmp_root / built.zip_id / built.file_name
    assert zip_path.exists()
    with zipfile.ZipFile(zip_path, "r") as zf:
        namelist = zf.namelist()
        assert "manifest.json" in namelist
        assert "Rule1.java" in namelist
        assert "blocks/Block1.java" in namelist

        manifest_data = json.loads(zf.read("manifest.json").decode("utf-8"))
        assert manifest_data["schema"] == "sqx-marketplace/1"
        assert manifest_data["title"] == "Custom Rules"
        assert manifest_data["category"]["id"] == "rules"

    # Cleanup zip
    with pytest.raises(ValueError, match="Invalid package id"):
        service.cleanup_zip("invalid-uuid")

    service.cleanup_zip(built.zip_id)
    assert not (service.tmp_root / built.zip_id).exists()


def test_marketplace_service_install_and_uninstall(tmp_path: Path) -> None:
    """Verify package installation with safety checks and uninstallation."""
    store = MarketplaceStore(file_path=tmp_path / "installed.json")
    service = MarketplaceService(store=store, data_dir=tmp_path)

    service.user_dir.mkdir(parents=True)
    service.custom_indicators_dir.mkdir(parents=True)
    service.builtin_dir.mkdir(parents=True)

    # Pre-populate a builtin file to test conflict skip
    builtin_conflict = service.builtin_dir / "indicators" / "SMA.java"
    builtin_conflict.parent.mkdir(parents=True)
    builtin_conflict.write_text("builtin code", encoding="utf-8")

    # Create a test zip archive in-memory
    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, "w") as zf:
        zf.writestr("manifest.json", '{"schema": "sqx-marketplace/1"}')
        zf.writestr("user/indicators/EMA.java", "class EMA {}")
        zf.writestr("user/indicators/SMA.java", "conflict with builtin")
        zf.writestr("custom_indicators/FastRSI.java", "class FastRSI {}")
        zf.writestr("extend/Plugins/MyPlugin.jar", "binary plugin")

    zip_bytes = zip_buf.getvalue()
    valid_sha = hashlib.sha256(zip_bytes).hexdigest()

    # Checksum mismatch
    with pytest.raises(ValueError, match="Checksum mismatch"):
        service.install_package(
            slug="pack1",
            title="Pack 1",
            version="1.0.0",
            zip_bytes_or_path=zip_bytes,
            expected_sha256="wrongsha",
        )

    # Path traversal attack detection
    bad_zip_buf = io.BytesIO()
    with zipfile.ZipFile(bad_zip_buf, "w") as zf:
        zf.writestr("../../../evil.txt", "attack")
    bad_bytes = bad_zip_buf.getvalue()
    bad_sha = hashlib.sha256(bad_bytes).hexdigest()
    with pytest.raises(ValueError, match="points outside the user folder"):
        service.install_package(
            slug="bad-pack",
            title="Bad",
            version="1.0.0",
            zip_bytes_or_path=bad_bytes,
            expected_sha256=bad_sha,
        )

    # Successful install (testing Path input as well)
    zip_file_on_disk = tmp_path / "pack1.zip"
    zip_file_on_disk.write_bytes(zip_bytes)

    res = service.install_package(
        slug="pack1",
        title="Pack 1",
        version="1.0.0",
        zip_bytes_or_path=zip_file_on_disk,
        expected_sha256=valid_sha,
        file_name="pack1.zip",
    )
    assert res.slug == "pack1"
    assert res.restart_required is True  # due to extend/Plugins/MyPlugin.jar
    assert "indicators/EMA.java" in res.installed_files
    assert "custom_indicators/FastRSI.java" in res.installed_files
    assert "extend/Plugins/MyPlugin.jar" in res.installed_files

    # Builtin conflict skipped
    assert len(res.skipped_files) == 1
    assert res.skipped_files[0].name == "indicators/SMA.java"
    assert res.skipped_files[0].reason == "already exists in Builtin"

    # Verify extracted physical files
    assert (service.user_dir / "indicators" / "EMA.java").exists()
    assert (service.custom_indicators_dir / "FastRSI.java").exists()
    assert (service.user_dir / "extend" / "Plugins" / "MyPlugin.jar").exists()

    # Verify store recorded install
    assert len(service.list_installed()) == 1

    # Uninstallation
    with pytest.raises(ValueError, match="Missing product id"):
        service.uninstall_package("   ")

    unres = service.uninstall_package("pack1")
    assert unres.slug == "pack1"
    assert unres.restart_required is True
    assert "indicators/EMA.java" in unres.removed_files
    assert "custom_indicators/FastRSI.java" in unres.removed_files
    assert "extend/Plugins/MyPlugin.jar" in unres.removed_files

    # Verify physical deletion and empty directory pruning
    assert not (service.user_dir / "indicators" / "EMA.java").exists()
    assert not (service.user_dir / "indicators").exists()  # pruned empty dir
    assert not (service.custom_indicators_dir / "FastRSI.java").exists()
    assert not (service.user_dir / "extend" / "Plugins" / "MyPlugin.jar").exists()

    # Verify store cleaned up
    assert len(service.list_installed()) == 0
