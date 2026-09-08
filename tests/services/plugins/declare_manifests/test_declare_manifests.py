"""Unit tests for DeclareManifestsService."""

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
from app.services.plugins.declare_manifests.config import PluginManifestsConfig
from app.services.plugins.declare_manifests.declare_manifests import (
    DeclareManifestsService,
    fr_trc_plug_declare_manifests_001,
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


def test_parse_manifest_success(
    service: DeclareManifestsService,
    valid_manifest_dict: dict[str, Any],
) -> None:
    """Verify parsing and validation of a complete valid manifest."""
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
    """Verify rejection of malformed JSON string or invalid types."""
    with pytest.raises(PluginManifestError, match=r"Malformed JSON"):
        service.parse_manifest("not valid json {")

    with pytest.raises(PluginManifestError, match=r"Expected str, bytes, or dict"):
        service.parse_manifest(12345)


def test_validate_identity_failures(
    service: DeclareManifestsService,
    valid_manifest_dict: dict[str, Any],
) -> None:
    """Verify rejection of invalid reverse-DNS ID, non-SemVer, or missing api_range."""
    # Missing ID
    bad = dict(valid_manifest_dict, id="")
    with pytest.raises(PluginManifestError, match="id is required"):
        service.parse_manifest(bad)

    # Invalid reverse-DNS
    bad = dict(valid_manifest_dict, id="my_invalid_id")
    with pytest.raises(PluginManifestError, match="reverse-DNS format"):
        service.parse_manifest(bad)

    # Invalid SemVer
    bad = dict(valid_manifest_dict, version="1.0")
    with pytest.raises(PluginManifestError, match="valid SemVer"):
        service.parse_manifest(bad)

    # Missing API range
    bad = dict(valid_manifest_dict, apiRange="")
    with pytest.raises(PluginManifestError, match="api_range is required"):
        service.parse_manifest(bad)

    # Missing types
    bad = dict(valid_manifest_dict, type=[])
    with pytest.raises(PluginManifestError, match="at least one plugin type"):
        service.parse_manifest(bad)


def test_validate_entry_point_safety(
    service: DeclareManifestsService,
    valid_manifest_dict: dict[str, Any],
) -> None:
    """Verify rejection of unsafe entry points."""
    bad = dict(valid_manifest_dict, entryPoint="../escape.py")
    with pytest.raises(PluginManifestError, match="safe relative path"):
        service.parse_manifest(bad)

    bad = dict(valid_manifest_dict, entryPoint="/absolute/main.py")
    with pytest.raises(PluginManifestError, match="safe relative path"):
        service.parse_manifest(bad)


def test_validate_package_success(
    service: DeclareManifestsService,
    valid_manifest_dict: dict[str, Any],
    tmp_path: Path,
) -> None:
    """Verify complete package validation with hashes and canonical digest."""
    main_code = b"print('rsi filter')\n"
    main_hash = hashlib.sha256(main_code).hexdigest()

    manifest_data = dict(valid_manifest_dict)
    manifest_data["sha256ByFile"] = {"rsi_filter.py": main_hash}

    zip_path = tmp_path / "valid_plugin.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("plugin.json", json.dumps(manifest_data))
        zf.writestr("rsi_filter.py", main_code)

    validation = service.validate_package(zip_path)
    assert isinstance(validation, PluginPackageValidation)
    assert validation.is_valid
    assert len(validation.files) == 2
    assert len(validation.package_hash) == 64


def test_validate_package_missing_manifest(
    service: DeclareManifestsService,
    tmp_path: Path,
) -> None:
    """Verify rejection of zip missing plugin.json."""
    zip_path = tmp_path / "no_manifest.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("other.txt", b"some data")

    with pytest.raises(
        PluginPackageValidationError, match=r"missing required 'plugin\.json'"
    ):
        service.validate_package(zip_path)


def test_validate_package_zip_slip_rejection(
    service: DeclareManifestsService,
    valid_manifest_dict: dict[str, Any],
    tmp_path: Path,
) -> None:
    """Verify rejection of directory traversal zip slip attempts."""
    zip_path = tmp_path / "zip_slip.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("plugin.json", json.dumps(valid_manifest_dict))
        zf.writestr("../../etc/passwd", b"root:x:0:0")

    with pytest.raises(PluginPackageValidationError, match="directory traversal"):
        service.validate_package(zip_path)


def test_validate_package_hash_mismatch(
    service: DeclareManifestsService,
    valid_manifest_dict: dict[str, Any],
    tmp_path: Path,
) -> None:
    """Verify rejection when declared file hash mismatches payload content."""
    manifest_data = dict(valid_manifest_dict)
    manifest_data["sha256ByFile"] = {"rsi_filter.py": "a" * 64}

    zip_path = tmp_path / "hash_mismatch.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("plugin.json", json.dumps(manifest_data))
        zf.writestr("rsi_filter.py", b"actual content")

    with pytest.raises(PluginPackageValidationError, match="Hash mismatch for file"):
        service.validate_package(zip_path)


def test_strict_signatures_enforcement(
    valid_manifest_dict: dict[str, Any],
    tmp_path: Path,
) -> None:
    """Verify rejection of unsigned package when strict_signatures=True."""
    strict_service = DeclareManifestsService(
        config=PluginManifestsConfig(strict_signatures=True)
    )

    zip_path = tmp_path / "unsigned.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("plugin.json", json.dumps(valid_manifest_dict))

    with pytest.raises(
        PluginPackageValidationError, match="Package signature is required"
    ):
        strict_service.validate_package(zip_path)


def test_fr_trace_function(
    valid_manifest_dict: dict[str, Any],
    tmp_path: Path,
) -> None:
    """Verify requirement implementation trace function on dict and Path."""
    result = fr_trc_plug_declare_manifests_001(valid_manifest_dict)
    assert isinstance(result, PluginManifest)
    assert result.id == valid_manifest_dict["id"]

    zip_path = tmp_path / "trace_pkg.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("plugin.json", json.dumps(valid_manifest_dict))

    pkg_result = fr_trc_plug_declare_manifests_001(zip_path)
    assert isinstance(pkg_result, PluginPackageValidation)
    assert pkg_result.is_valid


def test_resource_limits_validation_bounds(
    service: DeclareManifestsService,
    valid_manifest_dict: dict[str, Any],
) -> None:
    """Verify numeric boundaries for CPU, memory, and timeout limits."""
    # Negative CPU
    bad = dict(valid_manifest_dict, resources={"cpu_limit_cores": -1.0})
    with pytest.raises(PluginManifestError, match="cpu_limit_cores must be positive"):
        service.parse_manifest(bad)

    # CPU > 32
    bad = dict(valid_manifest_dict, resources={"cpu_limit_cores": 64.0})
    with pytest.raises(
        PluginManifestError, match=r"cpu_limit_cores must be positive and <= 32\.0"
    ):
        service.parse_manifest(bad)

    # Negative memory
    bad = dict(valid_manifest_dict, resources={"memory_limit_mb": -100})
    with pytest.raises(PluginManifestError, match="memory_limit_mb must be positive"):
        service.parse_manifest(bad)

    # Memory > 65536
    bad = dict(valid_manifest_dict, resources={"memory_limit_mb": 100000})
    with pytest.raises(
        PluginManifestError, match="memory_limit_mb must be positive and <= 65536"
    ):
        service.parse_manifest(bad)

    # Negative timeout
    bad = dict(valid_manifest_dict, resources={"timeout_seconds": -5.0})
    with pytest.raises(PluginManifestError, match="timeout_seconds must be positive"):
        service.parse_manifest(bad)

    # Timeout > 3600
    bad = dict(valid_manifest_dict, resources={"timeout_seconds": 7200.0})
    with pytest.raises(
        PluginManifestError, match=r"timeout_seconds must be positive and <= 3600\.0"
    ):
        service.parse_manifest(bad)

    # Non-numeric
    bad = dict(valid_manifest_dict, resources={"cpu_limit_cores": "invalid_num"})
    with pytest.raises(PluginManifestError, match="Invalid numeric resource limit"):
        service.parse_manifest(bad)


def test_schema_and_structural_validation(
    service: DeclareManifestsService,
    valid_manifest_dict: dict[str, Any],
) -> None:
    """Verify rejection of malformed structural components."""
    # Schemas not a dict
    bad = dict(valid_manifest_dict, schemas="not_a_dict")
    with pytest.raises(PluginManifestError, match="Schemas field must be an object"):
        service.parse_manifest(bad)

    # Permissions not a dict
    bad = dict(valid_manifest_dict, permissions="not_a_dict")
    with pytest.raises(
        PluginManifestError, match="Permissions field must be an object"
    ):
        service.parse_manifest(bad)

    # Resources not a dict
    bad = dict(valid_manifest_dict, resources="not_a_dict")
    with pytest.raises(PluginManifestError, match="Resources field must be an object"):
        service.parse_manifest(bad)

    # Contributions not a list
    bad = dict(valid_manifest_dict, contributions="not_a_list")
    with pytest.raises(PluginManifestError, match="Contributions field must be a list"):
        service.parse_manifest(bad)

    # Contribution item not a dict
    bad = dict(valid_manifest_dict, contributions=["not_a_dict"])
    with pytest.raises(PluginManifestError, match="must be an object"):
        service.parse_manifest(bad)

    # Contribution missing ID
    bad = dict(valid_manifest_dict, contributions=[{"name": "No ID"}])
    with pytest.raises(PluginManifestError, match="missing required contribution_id"):
        service.parse_manifest(bad)

    # Contribution invalid type
    bad = dict(
        valid_manifest_dict,
        contributions=[{"contribution_id": "test_c", "type": "UNSUPPORTED_TYPE"}],
    )
    with pytest.raises(PluginManifestError, match="Invalid plugin_type"):
        service.parse_manifest(bad)

    # Dependencies not a list
    bad = dict(valid_manifest_dict, dependencies="not_a_list")
    with pytest.raises(PluginManifestError, match="Dependencies field must be a list"):
        service.parse_manifest(bad)

    # Dependency invalid reverse-DNS
    bad = dict(valid_manifest_dict, dependencies=["not_reverse_dns"])
    with pytest.raises(PluginManifestError, match="must be in reverse-DNS format"):
        service.parse_manifest(bad)

    # Migrations not a list
    bad = dict(valid_manifest_dict, migrations="not_a_list")
    with pytest.raises(PluginManifestError, match="Migrations field must be a list"):
        service.parse_manifest(bad)

    # Migration item not a dict
    bad = dict(valid_manifest_dict, migrations=["not_a_dict"])
    with pytest.raises(PluginManifestError, match="must be an object"):
        service.parse_manifest(bad)

    # Migration non-SemVer
    bad = dict(
        valid_manifest_dict, migrations=[{"from_version": "1.0", "to_version": "2.0"}]
    )
    with pytest.raises(PluginManifestError, match="must be SemVer"):
        service.parse_manifest(bad)

    # Migration circular
    bad = dict(
        valid_manifest_dict,
        migrations=[{"from_version": "1.0.0", "to_version": "1.0.0"}],
    )
    with pytest.raises(PluginManifestError, match="Circular migration declaration"):
        service.parse_manifest(bad)

    # Migration duplicate transition
    bad = dict(
        valid_manifest_dict,
        migrations=[
            {"from_version": "1.0.0", "to_version": "1.1.0"},
            {"from_version": "1.0.0", "to_version": "1.1.0"},
        ],
    )
    with pytest.raises(PluginManifestError, match="Duplicate migration transition"):
        service.parse_manifest(bad)


def test_package_safety_checks_extended(
    service: DeclareManifestsService,
    valid_manifest_dict: dict[str, Any],
    tmp_path: Path,
) -> None:
    """Verify package edge cases: missing file, non-file path, file limits, bomb limits, collisions."""
    # File does not exist
    with pytest.raises(
        PluginPackageValidationError, match="Package file does not exist"
    ):
        service.validate_package(tmp_path / "does_not_exist.zip")

    # Path is a directory
    with pytest.raises(PluginPackageValidationError, match="not a regular file"):
        service.validate_package(tmp_path)

    # Max package size exceeded
    small_service = DeclareManifestsService(
        config=PluginManifestsConfig(max_package_size_bytes=10)
    )
    oversized_zip = tmp_path / "oversized.zip"
    with zipfile.ZipFile(oversized_zip, "w") as zf:
        zf.writestr("plugin.json", json.dumps(valid_manifest_dict))
    with pytest.raises(PluginPackageValidationError, match="exceeds maximum limit"):
        small_service.validate_package(oversized_zip)

    # Max file count exceeded
    low_count_service = DeclareManifestsService(
        config=PluginManifestsConfig(max_file_count=1)
    )
    multi_file_zip = tmp_path / "multi_file.zip"
    with zipfile.ZipFile(multi_file_zip, "w") as zf:
        zf.writestr("plugin.json", json.dumps(valid_manifest_dict))
        zf.writestr("extra.txt", b"extra")
    with pytest.raises(PluginPackageValidationError, match="exceeding limit of"):
        low_count_service.validate_package(multi_file_zip)

    # Decompression bomb expansion ratio
    bomb_zip = tmp_path / "bomb.zip"
    with zipfile.ZipFile(bomb_zip, "w") as zf:
        zf.writestr("plugin.json", json.dumps(valid_manifest_dict))
        # Zero bytes compress heavily
        zf.writestr(
            "huge.dat", b"\x00" * (1024 * 1024), compress_type=zipfile.ZIP_DEFLATED
        )
    low_expand_service = DeclareManifestsService(
        config=PluginManifestsConfig(max_package_size_bytes=40_000)
    )
    with pytest.raises(
        PluginPackageValidationError, match="exceeds safe expansion limit"
    ):
        low_expand_service.validate_package(bomb_zip)

    # Case-fold collision
    collision_zip = tmp_path / "collision.zip"
    with zipfile.ZipFile(collision_zip, "w") as zf:
        zf.writestr("plugin.json", json.dumps(valid_manifest_dict))
        zf.writestr("Readme.txt", b"one")
        zf.writestr("README.TXT", b"two")
    with pytest.raises(PluginPackageValidationError, match="case-fold collision"):
        service.validate_package(collision_zip)

    # Absolute path in zip entry
    abs_zip = tmp_path / "abs_entry.zip"
    with zipfile.ZipFile(abs_zip, "w") as zf:
        zf.writestr("plugin.json", json.dumps(valid_manifest_dict))
        zf.writestr("/root/secret.py", b"secret")
    with pytest.raises(PluginPackageValidationError, match="unsafe absolute path"):
        service.validate_package(abs_zip)

    # Corrupted zip
    corrupt_zip = tmp_path / "corrupt.zip"
    corrupt_zip.write_bytes(b"PK\x03\x04corrupted_zip_bytes")
    with pytest.raises(PluginPackageValidationError, match="Invalid ZIP archive"):
        service.validate_package(corrupt_zip)


def test_usage_scenario_execution() -> None:
    """Verify that _usage._run_usage_example executes cleanly."""
    from app.services.plugins.declare_manifests._usage import _run_usage_example

    _run_usage_example()
