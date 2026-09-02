"""Tests for conformance reports and compatibility policy behavior."""

import hashlib
import uuid
from pathlib import Path
from typing import Literal

import pytest
from app.contracts.plugins.errors import PluginFailure
from app.contracts.plugins.models import (
    MaintainCompatibilityRequest,
    MaintainCompatibilitySuccess,
    PluginCompatibility,
    PluginContributionDescriptor,
    PluginType,
    PluginValidationReport,
)
from app.services.plugins.contributions.plugin_contributions import (
    RegisterContributionsService,
)
from app.services.plugins.development_compatibility.config import (
    DevelopmentCompatibilityConfig,
)
from app.services.plugins.development_compatibility.plugin_development_compatibility import (
    DevelopmentCompatibilityService,
    _run_usage_example,
    _write_reproducible_package,
    fr_plug_declare_plugin_compatibility,
    fr_plug_validate_plugin_packages,
)
from app.services.plugins.manifests.plugin_manifests import DeclareManifestsService
from scripts.architecture_check import check_directory


def _service() -> DevelopmentCompatibilityService:
    return DevelopmentCompatibilityService(
        DevelopmentCompatibilityConfig(),
        DeclareManifestsService(),
        RegisterContributionsService(),
    )


def _request(
    operation: Literal["PUBLISH", "CHECK"],
    compatibility: PluginCompatibility | None = None,
    plugin_id: str | None = None,
    version: str | None = None,
) -> MaintainCompatibilityRequest:
    return MaintainCompatibilityRequest(
        request_id=str(uuid.uuid7()),
        capability_snapshot_id=str(uuid.uuid7()),
        operation=operation,
        compatibility=compatibility,
        plugin_id=plugin_id,
        version=version,
    )


def _policy(range_value: str, deprecated: bool = False) -> PluginCompatibility:
    return PluginCompatibility(
        plugin_api_version="2.0.0",
        supported_range=range_value,
        is_deprecated=deprecated,
        conformance_suite="plugins-v1",
    )


def _write_package(path: Path) -> None:
    _write_reproducible_package(
        path,
        {
            "apiRange": ">=1.0.0 <2.0.0",
            "entryPoint": "plugin.py",
            "id": "com.haruquantai.reference",
            "permissions": {"secrets": ["secret-reference-id"]},
            "resources": {},
            "type": ["METRIC"],
            "version": "1.0.0",
        },
        {"plugin.py": b"def compute(): return 1\n"},
    )


@pytest.mark.asyncio
async def test_publish_check_replacement_and_deprecation() -> None:
    service = _service()
    published = await service.maintain_compatibility(
        _request("PUBLISH", compatibility=_policy(">=1.0.0 <2.0.0"))
    )
    assert isinstance(published, MaintainCompatibilitySuccess)
    supported = await service.maintain_compatibility(
        _request("CHECK", plugin_id="com.haruquantai.reference", version="1.5.0+ci")
    )
    assert isinstance(supported, MaintainCompatibilitySuccess)
    assert supported.verdict == "SUPPORTED"
    await service.maintain_compatibility(
        _request("PUBLISH", compatibility=_policy(">=1.4.0 <1.6.0", True))
    )
    deprecated = await service.maintain_compatibility(
        _request("CHECK", plugin_id="com.haruquantai.reference", version="1.5.0")
    )
    assert isinstance(deprecated, MaintainCompatibilitySuccess)
    assert deprecated.verdict == "DEPRECATED"


@pytest.mark.asyncio
async def test_missing_unsupported_and_prerelease_checks_return_precise_failures() -> (
    None
):
    service = _service()
    missing = await service.maintain_compatibility(
        _request("CHECK", plugin_id="com.haruquantai.reference", version="1.0.0")
    )
    assert isinstance(missing, PluginFailure)
    assert missing.code == "PLUGIN_INCOMPATIBLE"
    await service.maintain_compatibility(
        _request("PUBLISH", compatibility=_policy(">=1.0.0 <2.0.0"))
    )
    prerelease = await service.maintain_compatibility(
        _request("CHECK", plugin_id="com.haruquantai.reference", version="1.5.0-beta")
    )
    assert isinstance(prerelease, PluginFailure)
    unsupported = await service.maintain_compatibility(
        _request("CHECK", plugin_id="com.haruquantai.reference", version="2.0.0")
    )
    assert isinstance(unsupported, PluginFailure)
    assert "outside the published supported range" in unsupported.problem.detail


@pytest.mark.asyncio
async def test_invalid_range_is_rejected() -> None:
    result = await _service().maintain_compatibility(
        _request("PUBLISH", compatibility=_policy("^1.0.0"))
    )
    assert isinstance(result, PluginFailure)
    assert result.code == "PLUGIN_VALIDATION_FAILED"


def test_plug_validate_plugin_packages(tmp_path: Path) -> None:
    package_path = tmp_path / "reference.zip"
    duplicate_path = tmp_path / "reference-copy.zip"
    _write_package(package_path)
    _write_package(duplicate_path)
    assert package_path.read_bytes() == duplicate_path.read_bytes()
    assert (
        hashlib.sha256(package_path.read_bytes()).hexdigest()
        == hashlib.sha256(duplicate_path.read_bytes()).hexdigest()
    )
    fixture = PluginContributionDescriptor(
        plugin_id="com.haruquantai.reference",
        plugin_type=PluginType.METRIC,
        contribution_id="com.haruquantai.reference.metric",
        name="Reference metric",
    )
    report = fr_plug_validate_plugin_packages(
        package_path,
        DeclareManifestsService(),
        RegisterContributionsService(),
        (fixture,),
    )
    assert isinstance(report, PluginValidationReport)
    assert report.is_valid is True
    assert report.permission_simulation_findings[-1] == "secret_references=1"
    safe_report = " ".join(
        (*report.permission_simulation_findings, *report.captured_log_counts)
    )
    assert "secret-reference-id" not in safe_report
    assert report.captured_log_counts == {"info": 2}


def test_trace_and_usage_harness() -> None:
    service = _service()
    response = fr_plug_declare_plugin_compatibility(
        _request("PUBLISH", compatibility=_policy("=1.0.0")), service
    )
    assert isinstance(response, MaintainCompatibilitySuccess)
    _run_usage_example()


def test_primary_module_has_no_cross_feature_implementation_imports() -> None:
    feature_path = (
        Path(__file__).parents[4] / "app/services/plugins/development_compatibility"
    )
    violations = check_directory(feature_path)
    assert not [
        violation
        for violation in violations
        if violation.rule == "ARCH-006-FEATURE-INDEPENDENCE"
    ]


def test_semver_and_range_edge_cases() -> None:
    from app.services.plugins.development_compatibility.plugin_development_compatibility import (
        _compare_versions,
        _parse_range,
        _parse_semver,
        _write_reproducible_package,
    )

    # Invalid SemVer strings
    with pytest.raises(ValueError, match="Invalid SemVer 2 version"):
        _parse_semver("1.0")
    with pytest.raises(ValueError, match="Invalid numeric prerelease identifier"):
        _parse_semver("1.0.0-01")

    # SemVer comparison
    v1 = _parse_semver("1.0.0-alpha.1")
    v2 = _parse_semver("1.0.0-alpha.beta")
    v3 = _parse_semver("1.0.0-beta")
    v4 = _parse_semver("1.0.0")
    assert _compare_versions(v1, v2) < 0
    assert _compare_versions(v2, v3) < 0
    assert _compare_versions(v3, v4) < 0
    assert _compare_versions(v4, v3) > 0
    assert _compare_versions(v1, v1) == 0

    # Range parsing forbidden tokens
    with pytest.raises(ValueError, match="Unsupported compatibility range grammar"):
        _parse_range(">=1.0.0 || >=2.0.0")
    with pytest.raises(ValueError, match="Unsupported compatibility range grammar"):
        _parse_range("   ")

    # Invalid comparator
    with pytest.raises(ValueError, match="Invalid compatibility comparator"):
        _parse_range("abc")

    # Package writing errors
    with pytest.raises(ValueError, match=r"Payloads must not replace plugin\.json"):
        _write_reproducible_package(Path("dummy.zip"), {}, {"plugin.json": b""})
    with pytest.raises(
        ValueError, match="Reference package payload paths must be safe"
    ):
        _write_reproducible_package(Path("dummy.zip"), {}, {"/etc/passwd": b""})
    with pytest.raises(
        ValueError, match="Reference package payload paths must be safe"
    ):
        _write_reproducible_package(Path("dummy.zip"), {}, {"../escape": b""})


@pytest.mark.asyncio
async def test_service_clear_and_validation_error_handling(tmp_path: Path) -> None:
    service = _service()
    service.clear()

    # Invalid range in compatibility declaration
    res = await service.maintain_compatibility(
        _request("PUBLISH", compatibility=_policy("abc"))
    )
    assert isinstance(res, PluginFailure)
    assert res.code == "PLUGIN_VALIDATION_FAILED"

    # Invalid semver version on check
    await service.maintain_compatibility(
        _request("PUBLISH", compatibility=_policy(">=1.0.0 <2.0.0"))
    )
    res_bad_ver = await service.maintain_compatibility(
        MaintainCompatibilityRequest(
            request_id=str(uuid.uuid7()),
            capability_snapshot_id=str(uuid.uuid7()),
            operation="CHECK",
            plugin_id="com.test",
            version="1.0.0-01",
        )
    )
    assert isinstance(res_bad_ver, PluginFailure)

    # validate_package failure when invalid zip
    bad_zip = tmp_path / "corrupt.zip"
    bad_zip.write_bytes(b"corrupt")
    rep = service.validate_package(bad_zip)
    assert isinstance(rep, PluginFailure)
    assert rep.code == "PLUGIN_VALIDATION_FAILED"
