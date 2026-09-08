"""Traceability acceptance tests for FEAT-PLUG-DECLARE_MANIFESTS.

Tests:
    AT-PLUG-DECLARE_MANIFESTS-001:
        Unknown/overbroad permissions or incompatible majors fail before activation;
        manifest inspection executes no package code.
    AT-PLUG-DECLARE_MANIFESTS-002:
        A display name cannot grant authority or replace another contribution identity.
"""

from __future__ import annotations

import json
import zipfile
from pathlib import Path
from typing import Any

import pytest
from app.contracts.plugins.errors import PluginManifestError
from app.contracts.plugins.models import (
    PluginManifest,
    PluginManifestPreview,
)
from app.services.plugins.declare_manifests.declare_manifests import (
    DeclareManifestsService,
    fr_trc_plug_declare_manifests_001,
    fr_trc_plug_declare_manifests_002,
)


@pytest.fixture
def service() -> DeclareManifestsService:
    """Fixture providing a DeclareManifestsService instance."""
    return DeclareManifestsService()


@pytest.fixture
def base_manifest_dict() -> dict[str, Any]:
    """Fixture providing a baseline valid manifest dictionary."""
    return {
        "id": "com.haruquantai.test.traceability",
        "version": "1.0.0",
        "apiRange": ">=1.0.0,<2.0.0",
        "type": ["INDICATOR"],
        "entryPoint": "indicator.py",
        "permissions": {
            "filesystem_read": ["data/"],
            "filesystem_write": [],
            "network_endpoints": ["https://market.example.com"],
            "subprocess_allow": False,
            "secrets": ["VALID_SECRET_KEY"],
        },
        "resources": {
            "cpu_limit_cores": 1.0,
            "memory_limit_mb": 512,
            "timeout_seconds": 30.0,
        },
        "contributions": [
            {
                "contribution_id": "trend_indicator",
                "plugin_type": "INDICATOR",
                "name": "Super Admin Master Authority",
                "description": "Calculates trend line",
            }
        ],
    }


def test_trc_declare_manifests_001_unknown_and_overbroad_permissions(
    service: DeclareManifestsService,
    base_manifest_dict: dict[str, Any],
) -> None:
    """AT-PLUG-DECLARE_MANIFESTS-001: Unknown or overbroad permissions fail before activation."""
    # 1. Unknown permission key
    bad_unknown_key = dict(base_manifest_dict)
    bad_unknown_key["permissions"] = dict(
        base_manifest_dict["permissions"],
        unadmitted_super_power=True,
    )
    with pytest.raises(
        PluginManifestError, match="Unknown or unadmitted permission keys"
    ):
        service.parse_manifest(bad_unknown_key)

    # 2. Overbroad absolute path in filesystem_read
    bad_abs_read = dict(base_manifest_dict)
    bad_abs_read["permissions"] = dict(
        base_manifest_dict["permissions"],
        filesystem_read=["/etc/shadow"],
    )
    with pytest.raises(PluginManifestError, match="Overbroad or absolute path"):
        service.parse_manifest(bad_abs_read)

    # 3. Directory traversal in filesystem_write
    bad_trav_write = dict(base_manifest_dict)
    bad_trav_write["permissions"] = dict(
        base_manifest_dict["permissions"],
        filesystem_write=["../../system32"],
    )
    with pytest.raises(PluginManifestError, match="Directory traversal sequence"):
        service.parse_manifest(bad_trav_write)

    # 4. Wildcard network endpoint (overbroad egress)
    bad_wildcard_egress = dict(base_manifest_dict)
    bad_wildcard_egress["permissions"] = dict(
        base_manifest_dict["permissions"],
        network_endpoints=["*"],
    )
    with pytest.raises(
        PluginManifestError, match="Wildcard network endpoints are overbroad"
    ):
        service.parse_manifest(bad_wildcard_egress)

    # 5. Insecure non-HTTPS endpoint
    bad_http_egress = dict(base_manifest_dict)
    bad_http_egress["permissions"] = dict(
        base_manifest_dict["permissions"],
        network_endpoints=["http://insecure.example.com"],
    )
    with pytest.raises(PluginManifestError, match="must use secure HTTPS"):
        service.parse_manifest(bad_http_egress)

    # 6. Malformed or wildcard secret name
    bad_secret = dict(base_manifest_dict)
    bad_secret["permissions"] = dict(
        base_manifest_dict["permissions"],
        secrets=["SECRET_*"],
    )
    with pytest.raises(PluginManifestError, match="Invalid or overbroad secret name"):
        service.parse_manifest(bad_secret)


def test_trc_declare_manifests_001_incompatible_major_version(
    service: DeclareManifestsService,
    base_manifest_dict: dict[str, Any],
) -> None:
    """AT-PLUG-DECLARE_MANIFESTS-001: Incompatible major versions fail before activation."""
    # Requiring major version 2+ on host major 1 fails before activation
    bad_major = dict(base_manifest_dict, apiRange=">=2.0.0")
    with pytest.raises(PluginManifestError, match="Incompatible major version"):
        service.parse_manifest(bad_major)


def test_trc_declare_manifests_001_executes_no_package_code(
    service: DeclareManifestsService,
    base_manifest_dict: dict[str, Any],
    tmp_path: Path,
) -> None:
    """AT-PLUG-DECLARE_MANIFESTS-001: Manifest inspection executes no package code."""
    # Package contains code that would explode if executed or imported
    poison_code = b"""
import sys
raise SystemExit("CODE EXECUTION DETECTED DURING INSPECTION - SECURITY BREACH")
"""
    zip_path = tmp_path / "poisoned_extension.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("plugin.json", json.dumps(base_manifest_dict))
        zf.writestr("indicator.py", poison_code)

    # Validation must parse static headers and verify bytes without executing poison_code
    validation = service.validate_package(zip_path)
    assert validation.is_valid
    assert validation.manifest.id == "com.haruquantai.test.traceability"
    assert len(validation.files) == 2


def test_trc_declare_manifests_002_display_name_cannot_grant_authority(
    service: DeclareManifestsService,
    base_manifest_dict: dict[str, Any],
) -> None:
    """AT-PLUG-DECLARE_MANIFESTS-002: A display name cannot grant authority or replace identity."""
    # The contribution has contribution_id="trend_indicator" but deceptive display name "Super Admin Master Authority"
    manifest = fr_trc_plug_declare_manifests_001(base_manifest_dict)
    assert isinstance(manifest, PluginManifest)

    preview = fr_trc_plug_declare_manifests_002(manifest)
    assert isinstance(preview, PluginManifestPreview)
    assert preview.plugin_id == "com.haruquantai.test.traceability"
    assert preview.version == "1.0.0"
    assert preview.is_compatible is True

    # The owned contribution identity must strictly bind to the reverse-DNS plugin ID and contribution ID
    expected_owned_id = "com.haruquantai.test.traceability.trend_indicator"
    assert preview.owned_contribution_ids == (expected_owned_id,)

    # Display name cannot replace contribution ID or appear in owned authority identifiers
    assert "Super Admin Master Authority" not in preview.owned_contribution_ids
    assert "Super Admin" not in preview.owned_contribution_ids[0]


def test_trc_declare_manifests_002_duplicate_contribution_ids_rejected(
    service: DeclareManifestsService,
    base_manifest_dict: dict[str, Any],
) -> None:
    """AT-PLUG-DECLARE_MANIFESTS-002: Duplicate contribution IDs are rejected."""
    bad_duplicates = dict(base_manifest_dict)
    bad_duplicates["contributions"] = [
        {
            "contribution_id": "trend_indicator",
            "plugin_type": "INDICATOR",
            "name": "First Name",
        },
        {
            "contribution_id": "trend_indicator",
            "plugin_type": "INDICATOR",
            "name": "Second Name Attempting Replacement",
        },
    ]
    with pytest.raises(PluginManifestError, match="Duplicate contribution ID declared"):
        service.parse_manifest(bad_duplicates)
