"""Bounded offline usage demonstration for FEAT-PLUG-DECLARE_MANIFESTS.

Exercises:
    1. Parse and validate valid extension manifest
       (FR-TRC-PLUG-DECLARE_MANIFESTS-001).
    2. Package verification and hash computation.
    3. Overbroad permission rejection (AT-PLUG-DECLARE_MANIFESTS-001).
    4. Bounded compatibility/permission/ownership preview
       (FR-TRC-PLUG-DECLARE_MANIFESTS-002, AT-PLUG-DECLARE_MANIFESTS-002).
    5. Clean scoped feature lifecycle mounting and disposal
       (NFR-TRC-PLUG-DECLARE_MANIFESTS-001).

CLI command:
    uv run --frozen python -m app.services.plugins.declare_manifests._usage
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import tempfile
import zipfile
from pathlib import Path
from typing import TYPE_CHECKING, Any

from app.contracts.plugins.capabilities import DECLARE_MANIFESTS_CAPABILITY
from app.contracts.plugins.errors import (
    PluginManifestError,
    PluginPackageValidationError,
)
from app.kernel.context import DefaultFeatureContext
from app.kernel.events import EventBus
from app.kernel.registry import ServiceRegistry
from app.kernel.scope import FeatureScope
from app.services.plugins.declare_manifests.declare_manifests import (
    DeclareManifestsService,
    fr_trc_plug_declare_manifests_001,
    fr_trc_plug_declare_manifests_002,
)
from app.services.plugins.declare_manifests.feature import DeclareManifestsFeature

if TYPE_CHECKING:
    from app.kernel.capability import CapabilityKey


def _run_usage_example() -> None:  # noqa: PLR0915
    """Execute the bounded offline usage demonstration.

    Raises:
        RuntimeError: If any demonstration invariant fails.
    """
    print("=== [1/5] Demonstrating FR-001: Valid Manifest Parsing & Validation ===")
    service = DeclareManifestsService()

    manifest_dict: dict[str, object] = {
        "id": "com.haruquantai.sample.momentum",
        "version": "1.0.0",
        "apiRange": ">=1.0.0,<2.0.0",
        "type": ["INDICATOR", "FILTER"],
        "entryPoint": "momentum_filter.py",
        "capabilities": ["indicator.momentum", "filter.trend"],
        "permissions": {
            "filesystem_read": ["data/"],
            "filesystem_write": [],
            "network_endpoints": ["https://api.example.com/feed"],
            "subprocess_allow": False,
            "secrets": ["MARKET_API_KEY"],
        },
        "resources": {
            "cpu_limit_cores": 1.5,
            "memory_limit_mb": 256,
            "timeout_seconds": 15.0,
        },
        "contributions": [
            {
                "contribution_id": "momentum_oscillator",
                "plugin_type": "INDICATOR",
                "name": "Deceptive Display Name Attempting Authority",
                "description": "Calculates normalized momentum oscillation",
            }
        ],
        "dependencies": [
            {
                "id": "com.haruquantai.core.math",
                "version_range": ">=1.0.0",
                "optional": False,
            }
        ],
        "migrations": [
            {
                "from_version": "0.9.0",
                "to_version": "1.0.0",
                "description": "Initial stable migration",
                "step": 1,
            }
        ],
    }

    manifest = fr_trc_plug_declare_manifests_001(manifest_dict)
    if not hasattr(manifest, "id") or not manifest.id:
        msg = "Manifest missing expected id attribute"
        raise RuntimeError(msg)
    print(f"   Successfully parsed manifest: {manifest.id} v{manifest.version}")
    print(f"   Declared types: {[t.value for t in manifest.types]}")
    print(f"   Declared contributions: {len(manifest.contributions)}")

    print("\n=== [2/5] Demonstrating Package Validation & Hash Computation ===")
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        zip_path = tmp_path / "sample_plugin.zip"
        main_content = b"print('Hello from momentum plugin')\n"
        main_hash = hashlib.sha256(main_content).hexdigest()

        manifest_dict["sha256ByFile"] = {"momentum_filter.py": main_hash}
        manifest_json = json.dumps(manifest_dict, indent=2).encode()

        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("plugin.json", manifest_json)
            zf.writestr("momentum_filter.py", main_content)

        validation = service.validate_package(zip_path)
        print(f"   Successfully validated package: {zip_path.name}")
        print(f"   Canonical package hash: {validation.package_hash}")
        print(f"   Verified {len(validation.files)} payload files.")

        print("\n=== [3/5] Demonstrating Overbroad & Malicious Path Rejections ===")
        # Traversal sequence
        bad_zip = tmp_path / "malicious_slip.zip"
        with zipfile.ZipFile(bad_zip, "w") as zf:
            zf.writestr("plugin.json", manifest_json)
            zf.writestr("../evil.py", b"evil code")

        try:
            service.validate_package(bad_zip)
            msg = "Expected malicious zip to fail"
            raise RuntimeError(msg)
        except PluginPackageValidationError as err:
            print(f"   Caught zip slip traversal attempt: {err}")

        # Overbroad permission rejection (AT-PLUG-DECLARE_MANIFESTS-001)
        overbroad_manifest = dict(manifest_dict)
        overbroad_manifest["permissions"] = {
            "filesystem_read": ["/etc/passwd"],  # Absolute path forbidden
            "network_endpoints": ["*"],  # Wildcard egress forbidden
        }
        try:
            service.parse_manifest(overbroad_manifest)
            msg = "Expected overbroad permissions to be rejected"
            raise RuntimeError(msg)
        except PluginManifestError as err:
            print(f"   Caught overbroad permission attempt: {err}")

    print(
        "\n=== [4/5] Demonstrating FR-002 & AT-002: Bounded Preview & "
        "Display Name Independence ==="
    )
    preview = fr_trc_plug_declare_manifests_002(manifest)
    print(f"   Plugin ID: {preview.plugin_id}")
    print(f"   Compatible: {preview.is_compatible} ({preview.compatibility_details})")
    print(f"   Owned contribution identities: {preview.owned_contribution_ids}")
    # Verify display name cannot replace contribution ID
    expected_owned = ("com.haruquantai.sample.momentum.momentum_oscillator",)
    if preview.owned_contribution_ids != expected_owned:
        msg = f"Unexpected owned IDs: {preview.owned_contribution_ids}"
        raise RuntimeError(msg)
    if "Deceptive Display Name" in preview.owned_contribution_ids[0]:
        msg = "Display name leaked into contribution identity"
        raise RuntimeError(msg)
    print("   Verified: Display name cannot replace contribution ID.")

    print("\n=== [5/5] Demonstrating Feature Lifecycle Mount & Scoped Disposal ===")

    async def _test_lifecycle() -> None:
        registry = ServiceRegistry()
        event_bus = EventBus()
        feat = DeclareManifestsFeature()
        scope = FeatureScope(owner_id=feat.spec.feature_id)

        def registrar(
            cap: CapabilityKey[Any],
            impl: object,
            sc: FeatureScope,
        ) -> None:
            registry.register(cap, impl, owner_id=feat.spec.feature_id, scope=sc)

        context = DefaultFeatureContext(
            spec=feat.spec,
            scope=scope,
            resolver=registry.resolve,
            provider_registrar=registrar,
            event_bus=event_bus,
        )
        await feat.mount(context, {})

        # Resolve capability
        cap = registry.resolve(DECLARE_MANIFESTS_CAPABILITY)
        if cap is None:
            msg = "Capability was not registered"
            raise RuntimeError(msg)
        cap_str = (
            f"{DECLARE_MANIFESTS_CAPABILITY.name}@{DECLARE_MANIFESTS_CAPABILITY.major}"
        )
        print(f"   Mounted and resolved {cap_str}")

        # Dispose scope
        await scope.close()
        if registry.is_available(DECLARE_MANIFESTS_CAPABILITY):
            msg = "Capability was not withdrawn on scope close"
            raise RuntimeError(msg)
        print("   Closed feature scope: capability withdrawn successfully.")

    asyncio.run(_test_lifecycle())

    print("\n=== Usage demonstration completed successfully ===")


if __name__ == "__main__":
    _run_usage_example()
