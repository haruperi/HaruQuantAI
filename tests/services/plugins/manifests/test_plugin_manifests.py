"""Unit tests for FEAT-PLUG-DECLARE_MANIFESTS (Plugin Manifests)."""

from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path
from typing import Any

import pytest

from app.contracts.plugins.errors import (
    PluginManifestError,
    PluginPackageValidationError,
)
from app.contracts.plugins.models import (
    PluginManifest,
    PluginPackageValidation,
    PluginType,
)
from app.services.plugins.manifests.config import PluginManifestsConfig
from app.services.plugins.manifests.plugin_manifests import (
    DeclareManifestsService,
    fr_plug_declare_plugin_manifests,
)


@pytest.fixture
def service() -> DeclareManifestsService:
    """Fixture providing a DeclareManifestsService instance."""
    return DeclareManifestsService()


@pytest.fixture
def valid_manifest_dict() -> dict[str, Any]:
    """Fixture providing a valid plugin manifest dictionary."""
    return {
        "id": "com.haruquantai.example.rsi_filter",
        "version": "1.2.3",
        "apiRange": ">=1.0.0,<2.0.0",
        "type": ["INDICATOR", "FILTER"],
        "entryPoint": "rsi_filter.py",
        "schemas": {"config": {"type": "object"}},
        "capabilities": ["indicator.rsi", "filter.momentum"],
        "permissions": {
            "filesystem_read": ["data/"],
            "network_endpoints": ["https://api.example.com"],
            "subprocess_allow": False,
            "secrets": ["API_KEY"],
        },
        "resources": {
            "cpu_limit_cores": 2.0,
            "memory_limit_mb": 1024,
            "timeout_seconds": 60.0,
        },
    }


def test_plug_declare_plugin_manifests(
    service: DeclareManifestsService,
    valid_manifest_dict: dict[str, Any],
) -> None:
    """Test FR-PLUG-DECLARE_PLUGIN_MANIFESTS: Parse and validate complete valid manifest."""
    manifest = service.parse_manifest(valid_manifest_dict)
    assert isinstance(manifest, PluginManifest)
    assert manifest.id == "com.haruquantai.example.rsi_filter"
    assert manifest.version == "1.2.3"
    assert manifest.api_range == ">=1.0.0,<2.0.0"
    assert manifest.types == (PluginType.INDICATOR, PluginType.FILTER)
    assert manifest.entry_point == "rsi_filter.py"
    assert manifest.capabilities == ("indicator.rsi", "filter.momentum")
    assert manifest.permissions.filesystem_read == ("data/",)
    assert manifest.permissions.network_endpoints == ("https://api.example.com",)
    assert manifest.permissions.secrets == ("API_KEY",)
    assert manifest.resources.cpu_limit_cores == 2.0
    assert manifest.resources.memory_limit_mb == 1024
    assert manifest.resources.timeout_seconds == 60.0


def test_parse_manifest_string_and_bytes(
    service: DeclareManifestsService,
    valid_manifest_dict: dict[str, Any],
) -> None:
    """Verify parsing from JSON string and UTF-8 bytes."""
    json_str = json.dumps(valid_manifest_dict)
    manifest_str = service.parse_manifest(json_str)
    assert manifest_str.id == valid_manifest_dict["id"]

    json_bytes = json_str.encode()
    manifest_bytes = service.parse_manifest(json_bytes)
    assert manifest_bytes.id == valid_manifest_dict["id"]


def test_parse_manifest_malformed_json(service: DeclareManifestsService) -> None:
    """Verify rejection of malformed JSON string or invalid type."""
    with pytest.raises(PluginManifestError, match=r"Malformed JSON"):
        service.parse_manifest("not valid json {")

    with pytest.raises(PluginManifestError, match=r"Expected str, bytes, or dict"):
        service.parse_manifest(12345)


def test_manifest_validation_reverse_dns(
    service: DeclareManifestsService,
    valid_manifest_dict: dict[str, Any],
) -> None:
    """Verify reverse-DNS ID enforcement."""
    invalid_ids = ["", "singleword", "com.", ".com", "com.my-plugin!", "com..plugin"]
    for bad_id in invalid_ids:
        bad_data = dict(valid_manifest_dict, id=bad_id)
        with pytest.raises(PluginManifestError):
            service.parse_manifest(bad_data)


def test_manifest_validation_semver(
    service: DeclareManifestsService,
    valid_manifest_dict: dict[str, Any],
) -> None:
    """Verify SemVer version string enforcement."""
    invalid_versions = ["", "1", "1.0", "v1.0.0", "1.0.0.0", "1.0.0-"]
    for bad_ver in invalid_versions:
        bad_data = dict(valid_manifest_dict, version=bad_ver)
        with pytest.raises(PluginManifestError):
            service.parse_manifest(bad_data)

    valid_versions = ["0.1.0", "1.0.0-alpha.1", "2.0.0+20130313144700"]
    for good_ver in valid_versions:
        good_data = dict(valid_manifest_dict, version=good_ver)
        manifest = service.parse_manifest(good_data)
        assert manifest.version == good_ver


def test_manifest_validation_plugin_types(
    service: DeclareManifestsService,
    valid_manifest_dict: dict[str, Any],
) -> None:
    """Verify plugin types validation against supported PluginType enum."""
    bad_data = dict(valid_manifest_dict, type=["UNKNOWN_TYPE"])
    with pytest.raises(PluginManifestError, match=r"Unsupported plugin type"):
        service.parse_manifest(bad_data)

    empty_data = dict(valid_manifest_dict, type=[])
    with pytest.raises(PluginManifestError, match=r"declare at least one plugin type"):
        service.parse_manifest(empty_data)

    # Test single string type form
    single_data = dict(valid_manifest_dict, type="METRIC")
    manifest = service.parse_manifest(single_data)
    assert manifest.types == (PluginType.METRIC,)


def test_manifest_validation_entry_point(
    service: DeclareManifestsService,
    valid_manifest_dict: dict[str, Any],
) -> None:
    """Verify entry point safety constraints."""
    bad_entries = [
        "",
        "/abs/path.py",
        "\\abs\\path.py",
        "../escape.py",
        "sub/../../escape.py",
    ]
    for bad in bad_entries:
        bad_data = dict(valid_manifest_dict, entryPoint=bad)
        with pytest.raises(PluginManifestError):
            service.parse_manifest(bad_data)


def test_manifest_validation_resource_limits(
    service: DeclareManifestsService,
    valid_manifest_dict: dict[str, Any],
) -> None:
    """Verify resource limits validation."""
    bad_resources = [
        {"cpu_limit_cores": -1.0, "memory_limit_mb": 512, "timeout_seconds": 10.0},
        {"cpu_limit_cores": 1.0, "memory_limit_mb": 0, "timeout_seconds": 10.0},
        {"cpu_limit_cores": 1.0, "memory_limit_mb": 512, "timeout_seconds": -5.0},
    ]
    for bad_res in bad_resources:
        bad_data = dict(valid_manifest_dict, resources=bad_res)
        with pytest.raises(PluginManifestError):
            service.parse_manifest(bad_data)


def test_package_validation_valid_archive(
    tmp_path: Path,
    service: DeclareManifestsService,
    valid_manifest_dict: dict[str, Any],
) -> None:
    """Verify successful validation and canonical hash computation for valid ZIP archive."""
    pkg_path = tmp_path / "good_plugin.zip"
    code = b"def calculate(): return 42\n"
    code_hash = hashlib.sha256(code).hexdigest()

    manifest_dict = dict(valid_manifest_dict)
    manifest_dict["sha256ByFile"] = {"rsi_filter.py": code_hash}
    manifest_bytes = json.dumps(manifest_dict).encode()

    with zipfile.ZipFile(pkg_path, "w") as zf:
        zf.writestr("plugin.json", manifest_bytes)
        zf.writestr("rsi_filter.py", code)

    validation = service.validate_package(pkg_path)
    assert validation.is_valid is True
    assert validation.manifest.id == valid_manifest_dict["id"]
    assert len(validation.files) == 2
    assert len(validation.package_hash) == 64  # SHA-256 hex length


def test_package_validation_missing_file_or_wrong_path(
    tmp_path: Path,
    service: DeclareManifestsService,
) -> None:
    """Verify error on non-existent package path."""
    with pytest.raises(PluginPackageValidationError, match=r"does not exist"):
        service.validate_package(tmp_path / "non_existent.zip")


def test_package_validation_missing_manifest(
    tmp_path: Path,
    service: DeclareManifestsService,
) -> None:
    """Verify rejection of ZIP missing plugin.json."""
    pkg_path = tmp_path / "no_manifest.zip"
    with zipfile.ZipFile(pkg_path, "w") as zf:
        zf.writestr("code.py", b"print(1)")

    with pytest.raises(
        PluginPackageValidationError, match=r"missing required 'plugin\.json'"
    ):
        service.validate_package(pkg_path)


def test_package_validation_hash_mismatch(
    tmp_path: Path,
    service: DeclareManifestsService,
    valid_manifest_dict: dict[str, Any],
) -> None:
    """Verify rejection when declared file SHA-256 does not match actual payload."""
    pkg_path = tmp_path / "tampered.zip"
    manifest_dict = dict(valid_manifest_dict)
    manifest_dict["sha256ByFile"] = {"rsi_filter.py": "0" * 64}  # fake hash
    manifest_bytes = json.dumps(manifest_dict).encode()

    with zipfile.ZipFile(pkg_path, "w") as zf:
        zf.writestr("plugin.json", manifest_bytes)
        zf.writestr("rsi_filter.py", b"real code")

    with pytest.raises(PluginPackageValidationError, match=r"Hash mismatch"):
        service.validate_package(pkg_path)


def test_package_validation_declared_file_missing(
    tmp_path: Path,
    service: DeclareManifestsService,
    valid_manifest_dict: dict[str, Any],
) -> None:
    """Verify rejection when manifest declares a file hash for a file not in the zip."""
    pkg_path = tmp_path / "missing_file.zip"
    manifest_dict = dict(valid_manifest_dict)
    manifest_dict["sha256ByFile"] = {"absent.py": "a" * 64}
    manifest_bytes = json.dumps(manifest_dict).encode()

    with zipfile.ZipFile(pkg_path, "w") as zf:
        zf.writestr("plugin.json", manifest_bytes)

    with pytest.raises(PluginPackageValidationError, match=r"missing from package"):
        service.validate_package(pkg_path)


def test_package_validation_zip_slip_traversal(
    tmp_path: Path,
    service: DeclareManifestsService,
    valid_manifest_dict: dict[str, Any],
) -> None:
    """Verify rejection of zip-slip directory traversal paths."""
    pkg_path = tmp_path / "zip_slip.zip"
    manifest_bytes = json.dumps(valid_manifest_dict).encode()

    with zipfile.ZipFile(pkg_path, "w") as zf:
        zf.writestr("plugin.json", manifest_bytes)
        zf.writestr("../escape.py", b"evil")

    with pytest.raises(
        PluginPackageValidationError, match=r"directory traversal sequence"
    ):
        service.validate_package(pkg_path)


def test_package_validation_absolute_path(
    tmp_path: Path,
    service: DeclareManifestsService,
    valid_manifest_dict: dict[str, Any],
) -> None:
    """Verify rejection of absolute paths or drive letters in zip entries."""
    pkg_path = tmp_path / "abs_path.zip"
    manifest_bytes = json.dumps(valid_manifest_dict).encode()

    with zipfile.ZipFile(pkg_path, "w") as zf:
        zf.writestr("plugin.json", manifest_bytes)
        zf.writestr("/root/target.py", b"evil")

    with pytest.raises(
        PluginPackageValidationError, match=r"unsafe absolute path or drive letter"
    ):
        service.validate_package(pkg_path)


def test_package_validation_case_fold_collision(
    tmp_path: Path,
    service: DeclareManifestsService,
    valid_manifest_dict: dict[str, Any],
) -> None:
    """Verify rejection of duplicate or case-folding collision filenames."""
    pkg_path = tmp_path / "case_fold.zip"
    manifest_bytes = json.dumps(valid_manifest_dict).encode()

    with zipfile.ZipFile(pkg_path, "w") as zf:
        zf.writestr("plugin.json", manifest_bytes)
        zf.writestr("file.py", b"content 1")
        zf.writestr("FILE.PY", b"content 2")

    with pytest.raises(PluginPackageValidationError, match=r"case-fold collision"):
        service.validate_package(pkg_path)


def test_package_validation_limits(
    tmp_path: Path,
    valid_manifest_dict: dict[str, Any],
) -> None:
    """Verify enforcement of max file count and max package size limits."""
    # 1. Test file count limit
    config_files = PluginManifestsConfig(
        max_package_size_bytes=100000, max_file_count=2
    )
    service_files = DeclareManifestsService(config=config_files)

    pkg_path = tmp_path / "too_many_files.zip"
    manifest_bytes = json.dumps(valid_manifest_dict).encode()
    with zipfile.ZipFile(pkg_path, "w") as zf:
        zf.writestr("plugin.json", manifest_bytes)
        zf.writestr("f1.txt", b"1")
        zf.writestr("f2.txt", b"2")

    with pytest.raises(PluginPackageValidationError, match=r"exceeding limit of 2"):
        service_files.validate_package(pkg_path)

    # 2. Test package size limit
    config_size = PluginManifestsConfig(max_package_size_bytes=50, max_file_count=10)
    service_size = DeclareManifestsService(config=config_size)

    with pytest.raises(PluginPackageValidationError, match=r"exceeds maximum limit"):
        service_size.validate_package(pkg_path)


def test_fr_trace_function(
    tmp_path: Path,
    valid_manifest_dict: dict[str, Any],
) -> None:
    """Verify fr_plug_declare_plugin_manifests requirement trace helper."""
    # Dict input
    res_manifest = fr_plug_declare_plugin_manifests(valid_manifest_dict)
    assert isinstance(res_manifest, PluginManifest)
    assert res_manifest.id == valid_manifest_dict["id"]

    # Path input
    pkg_path = tmp_path / "pkg.zip"
    manifest_bytes = json.dumps(valid_manifest_dict).encode()
    with zipfile.ZipFile(pkg_path, "w") as zf:
        zf.writestr("plugin.json", manifest_bytes)

    res_pkg = fr_plug_declare_plugin_manifests(pkg_path)
    assert isinstance(res_pkg, PluginPackageValidation)
    assert res_pkg.manifest.id == valid_manifest_dict["id"]
