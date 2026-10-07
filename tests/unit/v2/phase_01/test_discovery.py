"""Unit tests for workspace and plugin discovery, manifest verification, and lifecycle.

Validates FEAT-HOST-DISCOVERY and functional requirements:
- FR-HOST-DISC-MANIFEST-SCHEMA
- FR-HOST-DISC-CONTAINMENT-SECURITY
- FR-HOST-DISC-SLOT-REGISTRATION
- FR-HOST-DISC-DEPENDENCY-RESOLUTION
- FR-HOST-DISC-CAPABILITY-INJECTION
- FR-HOST-DISC-LIFECYCLE-MANAGEMENT
- FR-HOST-DISC-BROWSER-PROJECTION
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from app.host.discovery import (
    MAX_MANIFEST_BYTES,
    ManifestValidationError,
    PluginDependency,
    PluginDiscoveryEngine,
    PluginHostContext,
    PluginLifecycleManager,
    PluginManifest,
    PluginRecord,
    PluginState,
    SecurityViolationError,
    SlotDefinition,
    SlotRegistry,
    _is_version_compatible,
    _parse_semver,
    create_discovery_router,
    main,
)
from fastapi import APIRouter, FastAPI
from fastapi.testclient import TestClient


@pytest.fixture
def slot_registry() -> SlotRegistry:
    """Fixture providing clean slot registry."""
    return SlotRegistry()


@pytest.fixture
def discovery_engine(slot_registry: SlotRegistry) -> PluginDiscoveryEngine:
    """Fixture providing discovery engine."""
    return PluginDiscoveryEngine(slot_registry=slot_registry)


@pytest.fixture
def lifecycle_manager(
    discovery_engine: PluginDiscoveryEngine, tmp_path: Path
) -> PluginLifecycleManager:
    """Fixture providing lifecycle manager with isolated data directory."""
    data_dir = tmp_path / "data" / "plugins"
    return PluginLifecycleManager(
        discovery_engine=discovery_engine,
        data_base_dir=data_dir,
    )


def _create_plugin_dir(
    parent: Path,
    dirname: str,
    manifest_dict: dict[str, Any],
    *,
    manifest_name: str = "plugin.json",
    python_code: str | None = None,
    py_filename: str = "plugin.py",
) -> Path:
    """Helper to create a plugin directory with manifest and optional python script."""
    pkg_dir = parent / dirname
    pkg_dir.mkdir(parents=True, exist_ok=True)
    manifest_file = pkg_dir / manifest_name
    manifest_file.write_text(json.dumps(manifest_dict, indent=2), encoding="utf-8")
    if python_code is not None:
        (pkg_dir / py_filename).write_text(python_code, encoding="utf-8")
    return pkg_dir


# -----------------------------------------------------------------------------
# Manifest Validation & Schema Tests
# -----------------------------------------------------------------------------


def test_parse_semver_and_compatibility() -> None:
    """Verify semver parsing and range checks."""
    assert _parse_semver("1.2.3") == (1, 2, 3)
    assert _parse_semver("v2.0.1-beta") == (2, 0, 1)
    assert _parse_semver("3") == (3, 0, 0)
    assert _parse_semver("invalid.abc") == (0, 0, 0)

    assert _is_version_compatible("1.5.0", min_ver="1.0.0", max_ver="2.0.0")
    assert not _is_version_compatible("0.9.0", min_ver="1.0.0", max_ver="2.0.0")
    assert not _is_version_compatible("2.1.0", min_ver="1.0.0", max_ver="2.0.0")
    assert _is_version_compatible("1.5.0", min_ver=None, max_ver=None)


def test_manifest_validation_valid(
    tmp_path: Path, discovery_engine: PluginDiscoveryEngine
) -> None:
    """Test parsing a fully specified valid manifest."""
    manifest_dict = {
        "manifest_version": 1,
        "id": "test.valid_plugin",
        "name": "Test Valid Plugin",
        "version": "1.0.0",
        "description": "A valid test plugin",
        "author": "HaruQuantAI Team",
        "slot": "workspace.panel",
        "entrypoint": "plugin.py:create_plugin",
        "dependencies": [{"plugin_id": "core.dep", "min_version": "1.0.0"}],
        "capabilities": ["host:settings", "host:logging"],
        "enabled": True,
        "metadata": {"custom_flag": True},
    }
    pkg_dir = _create_plugin_dir(tmp_path, "valid_plugin", manifest_dict)
    manifest = discovery_engine.parse_manifest_file(pkg_dir / "plugin.json", tmp_path)

    assert manifest.id == "test.valid_plugin"
    assert manifest.name == "Test Valid Plugin"
    assert manifest.slot == "workspace.panel"
    assert manifest.entrypoint == "plugin.py:create_plugin"
    assert len(manifest.dependencies) == 1
    assert manifest.dependencies[0].plugin_id == "core.dep"


def test_manifest_validation_rejects_invalid_id() -> None:
    """Verify manifest validation rejects invalid plugin identifiers."""
    with pytest.raises(ValueError, match="Plugin identifier"):
        PluginManifest(
            id="bad/plugin/id",
            name="Bad ID",
            version="1.0.0",
            slot="workspace.panel",
            entrypoint="mod:factory",
        )


def test_manifest_validation_rejects_malformed_entrypoint() -> None:
    """Verify entrypoint syntax and traversal detection."""
    with pytest.raises(ValueError, match="must be in format"):
        PluginManifest(
            id="test-id",
            name="Bad Entrypoint",
            version="1.0.0",
            slot="workspace.panel",
            entrypoint="no_colon_entrypoint",
        )

    with pytest.raises(ValueError, match="escaped path"):
        PluginManifest(
            id="test-id",
            name="Escape Entrypoint",
            version="1.0.0",
            slot="workspace.panel",
            entrypoint="../outside:factory",
        )


def test_manifest_validation_rejects_oversized_file(
    tmp_path: Path, discovery_engine: PluginDiscoveryEngine
) -> None:
    """Verify rejection of manifests exceeding 1 MiB."""
    pkg_dir = tmp_path / "big_plugin"
    pkg_dir.mkdir(parents=True)
    manifest_file = pkg_dir / "plugin.json"
    manifest_file.write_bytes(b" " * (MAX_MANIFEST_BYTES + 10))

    with pytest.raises(ManifestValidationError, match="exceeds size limit"):
        discovery_engine.parse_manifest_file(manifest_file, tmp_path)


def test_manifest_validation_rejects_non_finite_json(
    tmp_path: Path, discovery_engine: PluginDiscoveryEngine
) -> None:
    """Verify rejection of non-finite numbers (NaN, Infinity)."""
    pkg_dir = tmp_path / "nan_plugin"
    pkg_dir.mkdir(parents=True)
    manifest_file = pkg_dir / "plugin.json"
    manifest_file.write_text(
        '{"id": "test-nan", "name": "NaN Plugin", "version": "1.0.0", '
        '"slot": "workspace.panel", "entrypoint": "mod:func", "score": NaN}',
        encoding="utf-8",
    )

    with pytest.raises(ManifestValidationError, match="malformed JSON"):
        discovery_engine.parse_manifest_file(manifest_file, tmp_path)


def test_manifest_validation_rejects_non_dict_root(
    tmp_path: Path, discovery_engine: PluginDiscoveryEngine
) -> None:
    """Verify rejection of manifest root JSON arrays or primitives."""
    pkg_dir = tmp_path / "list_plugin"
    pkg_dir.mkdir(parents=True)
    manifest_file = pkg_dir / "plugin.json"
    manifest_file.write_text('[{"id": "list"}]', encoding="utf-8")

    with pytest.raises(ManifestValidationError, match="must be a JSON object"):
        discovery_engine.parse_manifest_file(manifest_file, tmp_path)


# -----------------------------------------------------------------------------
# Containment & Security Tests
# -----------------------------------------------------------------------------


def test_verify_containment_rejects_directory_escape(
    tmp_path: Path, discovery_engine: PluginDiscoveryEngine
) -> None:
    """Verify security rejection when package directory escapes search root."""
    root_a = tmp_path / "root_a"
    root_b = tmp_path / "root_b"
    root_a.mkdir()
    root_b.mkdir()

    with pytest.raises(SecurityViolationError, match="escapes authorized root"):
        discovery_engine.verify_containment(root_b, root_a)


# -----------------------------------------------------------------------------
# Slot Registry Tests
# -----------------------------------------------------------------------------


def test_slot_registry_core_and_custom(slot_registry: SlotRegistry) -> None:
    """Verify registration and lookup of extension slots."""
    assert slot_registry.has_slot("workspace.root")
    assert slot_registry.has_slot("workspace.panel")
    assert slot_registry.has_slot("data.provider")
    assert slot_registry.has_slot("engine.evaluator")
    assert slot_registry.has_slot("export.formatter")
    assert slot_registry.has_slot("diagnostic.probe")

    custom_slot = SlotDefinition(
        slot_id="custom.slot",
        description="Custom extension slot",
        multi_instance=False,
    )
    slot_registry.register_slot(custom_slot)
    assert slot_registry.has_slot("custom.slot")
    retrieved = slot_registry.get_slot("custom.slot")
    assert retrieved is not None
    assert retrieved.multi_instance is False


# -----------------------------------------------------------------------------
# Discovery Engine Tests
# -----------------------------------------------------------------------------


def test_zero_plugin_resilience(
    discovery_engine: PluginDiscoveryEngine, tmp_path: Path
) -> None:
    """Verify that zero-plugin directory discovers cleanly and returns empty collection."""
    empty_dir = tmp_path / "empty_plugins"
    empty_dir.mkdir()
    discovered = discovery_engine.discover([empty_dir])
    assert discovered == {}
    order = discovery_engine.resolve_dependencies(discovered)
    assert order == []


def test_discovery_manifest_json_alias(
    tmp_path: Path, discovery_engine: PluginDiscoveryEngine
) -> None:
    """Verify discovery recognizes both plugin.json and manifest.json."""
    manifest_dict = {
        "id": "alias-manifest-plugin",
        "name": "Alias Plugin",
        "version": "1.0.0",
        "slot": "data.provider",
        "entrypoint": "mod:func",
    }
    _create_plugin_dir(
        tmp_path, "alias_pkg", manifest_dict, manifest_name="manifest.json"
    )
    discovered = discovery_engine.discover([tmp_path])
    assert "alias-manifest-plugin" in discovered
    assert discovered["alias-manifest-plugin"].state == PluginState.DISCOVERED


def test_discovery_rejects_duplicate_plugin_id(
    tmp_path: Path, discovery_engine: PluginDiscoveryEngine
) -> None:
    """Verify duplicate plugin IDs are flagged as INCOMPATIBLE."""
    manifest_a = {
        "id": "duplicate.id",
        "name": "Plugin A",
        "version": "1.0.0",
        "slot": "workspace.panel",
        "entrypoint": "mod:func",
    }
    manifest_b = {
        "id": "duplicate.id",
        "name": "Plugin B",
        "version": "1.0.0",
        "slot": "workspace.panel",
        "entrypoint": "mod:func",
    }
    _create_plugin_dir(tmp_path, "dir_a", manifest_a)
    _create_plugin_dir(tmp_path, "dir_b", manifest_b)

    discovered = discovery_engine.discover([tmp_path])
    assert "duplicate.id" in discovered
    assert discovered["duplicate.id"].state == PluginState.INCOMPATIBLE
    assert "Duplicate plugin ID" in (discovered["duplicate.id"].error_message or "")


def test_discovery_unregistered_slot_marks_incompatible(
    tmp_path: Path, discovery_engine: PluginDiscoveryEngine
) -> None:
    """Verify plugins declaring unrecognized extension slots are marked INCOMPATIBLE."""
    manifest = {
        "id": "unregistered-slot-plugin",
        "name": "Bad Slot Plugin",
        "version": "1.0.0",
        "slot": "unregistered.bogus.slot",
        "entrypoint": "mod:func",
    }
    _create_plugin_dir(tmp_path, "bad_slot", manifest)
    discovered = discovery_engine.discover([tmp_path])
    assert discovered["unregistered-slot-plugin"].state == PluginState.INCOMPATIBLE
    assert "not registered" in (
        discovered["unregistered-slot-plugin"].error_message or ""
    )


# -----------------------------------------------------------------------------
# Dependency Resolution Tests
# -----------------------------------------------------------------------------


def test_dependency_resolution_topological_order(
    discovery_engine: PluginDiscoveryEngine,
) -> None:
    """Verify topological sort yields correct dependency ordering."""
    p1 = PluginRecord(
        manifest=PluginManifest(
            id="p1",
            name="P1 Base",
            version="1.0.0",
            slot="workspace.root",
            entrypoint="m:f",
        ),
        state=PluginState.DISCOVERED,
        package_dir="/dummy/p1",
        discovered_at="2026-10-07T00:00:00Z",
    )
    p2 = PluginRecord(
        manifest=PluginManifest(
            id="p2",
            name="P2 Dependent on P1",
            version="1.0.0",
            slot="workspace.panel",
            entrypoint="m:f",
            dependencies=[PluginDependency(plugin_id="p1")],
        ),
        state=PluginState.DISCOVERED,
        package_dir="/dummy/p2",
        discovered_at="2026-10-07T00:00:00Z",
    )
    p3 = PluginRecord(
        manifest=PluginManifest(
            id="p3",
            name="P3 Dependent on P2",
            version="1.0.0",
            slot="data.provider",
            entrypoint="m:f",
            dependencies=[PluginDependency(plugin_id="p2")],
        ),
        state=PluginState.DISCOVERED,
        package_dir="/dummy/p3",
        discovered_at="2026-10-07T00:00:00Z",
    )

    plugins = {"p3": p3, "p1": p1, "p2": p2}
    order = discovery_engine.resolve_dependencies(plugins)
    assert order == ["p1", "p2", "p3"]


def test_dependency_resolution_missing_dependency(
    discovery_engine: PluginDiscoveryEngine,
) -> None:
    """Verify missing required dependency flags dependent plugin as INCOMPATIBLE."""
    p_dep = PluginRecord(
        manifest=PluginManifest(
            id="p_needs_missing",
            name="Missing Dep Plugin",
            version="1.0.0",
            slot="workspace.panel",
            entrypoint="m:f",
            dependencies=[PluginDependency(plugin_id="nonexistent")],
        ),
        state=PluginState.DISCOVERED,
        package_dir="/dummy",
        discovered_at="2026-10-07T00:00:00Z",
    )
    plugins = {"p_needs_missing": p_dep}
    order = discovery_engine.resolve_dependencies(plugins)
    assert order == []
    assert plugins["p_needs_missing"].state == PluginState.INCOMPATIBLE
    assert "Missing required dependency" in (
        plugins["p_needs_missing"].error_message or ""
    )


def test_dependency_resolution_optional_dependency(
    discovery_engine: PluginDiscoveryEngine,
) -> None:
    """Verify missing optional dependency is ignored and does not block attachment."""
    p_opt = PluginRecord(
        manifest=PluginManifest(
            id="p_opt",
            name="Optional Dep Plugin",
            version="1.0.0",
            slot="workspace.panel",
            entrypoint="m:f",
            dependencies=[PluginDependency(plugin_id="nonexistent", optional=True)],
        ),
        state=PluginState.DISCOVERED,
        package_dir="/dummy",
        discovered_at="2026-10-07T00:00:00Z",
    )
    plugins = {"p_opt": p_opt}
    order = discovery_engine.resolve_dependencies(plugins)
    assert order == ["p_opt"]
    assert plugins["p_opt"].state == PluginState.DISCOVERED


def test_dependency_resolution_circular_dependency(
    discovery_engine: PluginDiscoveryEngine,
) -> None:
    """Verify circular dependencies are detected and flagged as INCOMPATIBLE."""
    p_a = PluginRecord(
        manifest=PluginManifest(
            id="p_a",
            name="Plugin A",
            version="1.0.0",
            slot="workspace.panel",
            entrypoint="m:f",
            dependencies=[PluginDependency(plugin_id="p_b")],
        ),
        state=PluginState.DISCOVERED,
        package_dir="/dummy/a",
        discovered_at="2026-10-07T00:00:00Z",
    )
    p_b = PluginRecord(
        manifest=PluginManifest(
            id="p_b",
            name="Plugin B",
            version="1.0.0",
            slot="workspace.panel",
            entrypoint="m:f",
            dependencies=[PluginDependency(plugin_id="p_a")],
        ),
        state=PluginState.DISCOVERED,
        package_dir="/dummy/b",
        discovered_at="2026-10-07T00:00:00Z",
    )

    plugins = {"p_a": p_a, "p_b": p_b}
    order = discovery_engine.resolve_dependencies(plugins)
    assert order == []
    assert plugins["p_a"].state == PluginState.INCOMPATIBLE
    assert plugins["p_b"].state == PluginState.INCOMPATIBLE
    assert "Circular dependency" in (plugins["p_a"].error_message or "")


# -----------------------------------------------------------------------------
# Capability Injection & Context Tests
# -----------------------------------------------------------------------------


def test_plugin_host_context_capabilities(tmp_path: Path) -> None:
    """Verify PluginHostContext manages routes, events, jobs, and teardown."""
    pkg_dir = tmp_path / "pkg"
    data_dir = tmp_path / "data"
    pkg_dir.mkdir()

    ctx = PluginHostContext(
        plugin_id="test_ctx_plugin",
        package_dir=pkg_dir,
        data_dir=data_dir,
        settings={"theme": "dark"},
    )
    assert ctx.data_dir.is_dir()
    assert ctx.settings == {"theme": "dark"}

    # Route registration
    sub_router = APIRouter()
    ctx.register_route(sub_router)
    assert len(ctx._mounted_routers) == 1

    # Event listener registration
    def dummy_handler(ev: Any) -> None:
        pass

    ctx.register_event_listener("quote_tick", dummy_handler)
    assert len(ctx._event_listeners) == 1

    # Job tracking & cancellation
    job_cancelled = False

    def cancel_job() -> None:
        nonlocal job_cancelled
        job_cancelled = True

    ctx.register_job("job-101", cancel_job)

    # Teardown hook
    teardown_executed = False

    def on_teardown() -> None:
        nonlocal teardown_executed
        teardown_executed = True

    ctx.register_teardown(on_teardown)

    # Execute teardown
    ctx.execute_teardown()
    assert job_cancelled is True
    assert teardown_executed is True
    assert len(ctx._mounted_routers) == 0
    assert len(ctx._event_listeners) == 0
    assert len(ctx._tracked_jobs) == 0


# -----------------------------------------------------------------------------
# Plugin Lifecycle Manager Tests
# -----------------------------------------------------------------------------


def test_lifecycle_attach_and_disable(
    tmp_path: Path,
    discovery_engine: PluginDiscoveryEngine,
    lifecycle_manager: PluginLifecycleManager,
) -> None:
    """Verify attaching, disabling, enabling, and reloading an executable plugin."""
    py_code = """
class MyPlugin:
    def __init__(self, ctx):
        self.ctx = ctx
        self.active = True
        ctx.register_teardown(self.cleanup)

    def cleanup(self):
        self.active = False

def create_instance(ctx):
    return MyPlugin(ctx)
"""
    manifest_dict = {
        "id": "my_executable_plugin",
        "name": "My Executable Plugin",
        "version": "1.0.0",
        "slot": "workspace.panel",
        "entrypoint": "plugin.py:create_instance",
    }
    _create_plugin_dir(tmp_path, "my_exec", manifest_dict, python_code=py_code)

    records = discovery_engine.discover([tmp_path])
    lifecycle_manager.set_records(records)

    # 1. Attach
    attached = lifecycle_manager.attach("my_executable_plugin")
    assert attached is True
    rec = lifecycle_manager.get_record("my_executable_plugin")
    assert rec is not None
    assert rec.state == PluginState.ATTACHED
    assert rec.attached_at is not None

    # Verify context
    ctx = lifecycle_manager.get_context("my_executable_plugin")
    assert ctx is not None

    # 2. Disable
    disabled = lifecycle_manager.disable("my_executable_plugin")
    assert disabled is True
    rec_disabled = lifecycle_manager.get_record("my_executable_plugin")
    assert rec_disabled is not None
    assert rec_disabled.state == PluginState.DISABLED

    # 3. Enable
    enabled = lifecycle_manager.enable("my_executable_plugin")
    assert enabled is True
    rec_enabled = lifecycle_manager.get_record("my_executable_plugin")
    assert rec_enabled is not None
    assert rec_enabled.state == PluginState.ATTACHED

    # 4. Reload
    reloaded = lifecycle_manager.reload("my_executable_plugin")
    assert reloaded is True
    rec_reloaded = lifecycle_manager.get_record("my_executable_plugin")
    assert rec_reloaded is not None
    assert rec_reloaded.state == PluginState.ATTACHED

    # 5. Uninstall
    uninstalled = lifecycle_manager.uninstall("my_executable_plugin")
    assert uninstalled is True
    assert lifecycle_manager.get_record("my_executable_plugin") is None


def test_lifecycle_attach_factory_failure_handling(
    tmp_path: Path,
    discovery_engine: PluginDiscoveryEngine,
    lifecycle_manager: PluginLifecycleManager,
) -> None:
    """Verify plugin factory exceptions are safely trapped without crashing host."""
    py_code = """
def faulty_factory(ctx):
    raise RuntimeError("Intentional factory crash for testing")
"""
    manifest_dict = {
        "id": "faulty_plugin",
        "name": "Faulty Plugin",
        "version": "1.0.0",
        "slot": "workspace.panel",
        "entrypoint": "plugin.py:faulty_factory",
    }
    _create_plugin_dir(tmp_path, "faulty_pkg", manifest_dict, python_code=py_code)

    records = discovery_engine.discover([tmp_path])
    lifecycle_manager.set_records(records)

    attached = lifecycle_manager.attach("faulty_plugin")
    assert attached is False
    rec = lifecycle_manager.get_record("faulty_plugin")
    assert rec is not None
    assert rec.state == PluginState.UNAVAILABLE
    assert "Intentional factory crash" in (rec.error_message or "")


def test_lifecycle_cascade_disable(
    discovery_engine: PluginDiscoveryEngine,
    lifecycle_manager: PluginLifecycleManager,
) -> None:
    """Verify disabling a plugin cascades to dependent attached plugins."""
    rec_parent = PluginRecord(
        manifest=PluginManifest(
            id="parent_plugin",
            name="Parent Plugin",
            version="1.0.0",
            slot="workspace.root",
            entrypoint="app.host.discovery:main",
        ),
        state=PluginState.ATTACHED,
        package_dir="/dummy/parent",
        discovered_at="2026-10-07T00:00:00Z",
    )
    rec_child = PluginRecord(
        manifest=PluginManifest(
            id="child_plugin",
            name="Child Plugin",
            version="1.0.0",
            slot="workspace.panel",
            entrypoint="app.host.discovery:main",
            dependencies=[PluginDependency(plugin_id="parent_plugin")],
        ),
        state=PluginState.ATTACHED,
        package_dir="/dummy/child",
        discovered_at="2026-10-07T00:00:00Z",
    )
    lifecycle_manager.set_records(
        {"parent_plugin": rec_parent, "child_plugin": rec_child}
    )

    lifecycle_manager.disable("parent_plugin")
    rec_p = lifecycle_manager.get_record("parent_plugin")
    assert rec_p is not None
    assert rec_p.state == PluginState.DISABLED

    rec_c = lifecycle_manager.get_record("child_plugin")
    assert rec_c is not None
    assert rec_c.state == PluginState.DISABLED


# -----------------------------------------------------------------------------
# FastAPI REST Projection Tests
# -----------------------------------------------------------------------------


def test_discovery_router_projections(
    lifecycle_manager: PluginLifecycleManager,
) -> None:
    """Verify REST endpoints for plugin listing, filtering, detail, enable/disable, and slots."""
    app = FastAPI()
    app.include_router(create_discovery_router(lifecycle_manager))
    client = TestClient(app)

    # Seed mock records
    rec1 = PluginRecord(
        manifest=PluginManifest(
            id="rest_plugin_1",
            name="REST Plugin 1",
            version="1.0.0",
            slot="workspace.panel",
            entrypoint="app.host.discovery:main",
        ),
        state=PluginState.ATTACHED,
        package_dir="/dummy/1",
        discovered_at="2026-10-07T00:00:00Z",
        attached_at="2026-10-07T00:01:00Z",
    )
    rec2 = PluginRecord(
        manifest=PluginManifest(
            id="rest_plugin_2",
            name="REST Plugin 2",
            version="2.0.0",
            slot="data.provider",
            entrypoint="app.host.discovery:main",
            enabled=False,
        ),
        state=PluginState.DISABLED,
        package_dir="/dummy/2",
        discovered_at="2026-10-07T00:00:00Z",
    )
    lifecycle_manager.set_records({"rest_plugin_1": rec1, "rest_plugin_2": rec2})

    # 1. GET /discovery/plugins
    resp = client.get("/discovery/plugins")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    assert "attached" in data["states_count"]

    # 2. Filter by slot
    resp_slot = client.get("/discovery/plugins?slot=workspace.panel")
    assert resp_slot.status_code == 200
    assert resp_slot.json()["total"] == 1
    assert resp_slot.json()["plugins"][0]["id"] == "rest_plugin_1"

    # 3. GET /discovery/plugins/{plugin_id}
    resp_detail = client.get("/discovery/plugins/rest_plugin_1")
    assert resp_detail.status_code == 200
    assert resp_detail.json()["manifest"]["id"] == "rest_plugin_1"

    # 4. 404 for unknown plugin
    resp_404 = client.get("/discovery/plugins/nonexistent")
    assert resp_404.status_code == 404

    # 5. POST /discovery/plugins/{plugin_id}/disable
    resp_dis = client.post("/discovery/plugins/rest_plugin_1/disable")
    assert resp_dis.status_code == 200
    assert resp_dis.json()["state"] == "disabled"

    # 6. GET /discovery/slots
    resp_slots = client.get("/discovery/slots")
    assert resp_slots.status_code == 200
    slots_data = resp_slots.json()
    assert isinstance(slots_data, list)
    assert any(s["slot_id"] == "workspace.panel" for s in slots_data)


# -----------------------------------------------------------------------------
# CLI Entrypoint Tests
# -----------------------------------------------------------------------------


def test_cli_slots_listing(capsys: pytest.CaptureFixture[str]) -> None:
    """Verify CLI --slots command."""
    code = main(["--slots"])
    assert code == 0
    captured = capsys.readouterr()
    assert "Registered Host Extension Slots" in captured.out
    assert "workspace.root" in captured.out


def test_cli_scan_listing(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Verify CLI --scan and --list command."""
    code = main(["--scan", str(tmp_path), "--list"])
    assert code == 0
    captured = capsys.readouterr()
    assert "Discovered 0 plugin packages" in captured.out


def test_entrypoint_validation_empty_parts() -> None:
    """Verify rejection of empty target or attribute in entrypoint."""
    with pytest.raises(ValueError, match="empty target or attr"):
        PluginManifest(
            id="test-empty",
            name="Empty Part",
            version="1.0.0",
            slot="workspace.panel",
            entrypoint=":create",
        )
    with pytest.raises(ValueError, match="empty target or attr"):
        PluginManifest(
            id="test-empty2",
            name="Empty Part 2",
            version="1.0.0",
            slot="workspace.panel",
            entrypoint="mod:",
        )


def test_context_teardown_and_job_errors(tmp_path: Path) -> None:
    """Verify exceptions in teardown hooks and job cancel handlers are logged cleanly."""
    ctx = PluginHostContext(
        plugin_id="error_ctx_plugin",
        package_dir=tmp_path / "pkg",
        data_dir=tmp_path / "data",
    )

    def faulty_teardown() -> None:
        raise ValueError("Teardown failed")

    def faulty_job_cancel() -> None:
        raise RuntimeError("Job cancel failed")

    ctx.register_teardown(faulty_teardown)
    ctx.register_job("job-faulty", faulty_job_cancel)
    ctx.execute_teardown()


def test_lifecycle_attach_edge_cases(
    discovery_engine: PluginDiscoveryEngine,
    lifecycle_manager: PluginLifecycleManager,
) -> None:
    """Verify attaching unknown, disabled, or incompatible plugins returns False."""
    assert lifecycle_manager.attach("completely_unknown") is False
    assert lifecycle_manager.enable("completely_unknown") is False
    assert lifecycle_manager.reload("completely_unknown") is False
    assert lifecycle_manager.uninstall("completely_unknown") is False

    # Disabled record
    rec_disabled = PluginRecord(
        manifest=PluginManifest(
            id="disabled_rec",
            name="Disabled Rec",
            version="1.0.0",
            slot="workspace.panel",
            entrypoint="mod:func",
            enabled=False,
        ),
        state=PluginState.DISABLED,
        package_dir="/dummy",
        discovered_at="2026-10-07T00:00:00Z",
    )
    # Incompatible record
    rec_incompat = PluginRecord(
        manifest=PluginManifest(
            id="incompat_rec",
            name="Incompat Rec",
            version="1.0.0",
            slot="workspace.panel",
            entrypoint="mod:func",
        ),
        state=PluginState.INCOMPATIBLE,
        package_dir="/dummy",
        error_message="Slot error",
        discovered_at="2026-10-07T00:00:00Z",
    )
    lifecycle_manager.set_records(
        {"disabled_rec": rec_disabled, "incompat_rec": rec_incompat}
    )

    assert lifecycle_manager.attach("disabled_rec") is False
    assert lifecycle_manager.attach("incompat_rec") is False


def test_lifecycle_reload_missing_manifest(
    tmp_path: Path,
    discovery_engine: PluginDiscoveryEngine,
    lifecycle_manager: PluginLifecycleManager,
) -> None:
    """Verify reload fails gracefully when manifest file is deleted."""
    manifest_dict = {
        "id": "transient_plugin",
        "name": "Transient Plugin",
        "version": "1.0.0",
        "slot": "workspace.panel",
        "entrypoint": "plugin.py:factory",
    }
    py_code = "def factory(ctx): return {'ok': True}"
    pkg_dir = _create_plugin_dir(
        tmp_path, "transient_pkg", manifest_dict, python_code=py_code
    )
    records = discovery_engine.discover([tmp_path])
    lifecycle_manager.set_records(records)
    lifecycle_manager.attach("transient_plugin")

    # Delete manifest
    (pkg_dir / "plugin.json").unlink()
    reloaded = lifecycle_manager.reload("transient_plugin")
    assert reloaded is False


def dummy_module_factory(ctx: Any) -> dict[str, str]:
    """Helper module-level factory function for module entrypoint tests."""
    return {"module_plugin": "active"}


def test_entrypoint_module_import_and_attribute_errors(
    tmp_path: Path,
    discovery_engine: PluginDiscoveryEngine,
    lifecycle_manager: PluginLifecycleManager,
) -> None:
    """Verify module:attribute entrypoint loading and missing attribute handling."""
    # 1. Valid module import
    manifest_module = {
        "id": "module_plugin",
        "name": "Module Plugin",
        "version": "1.0.0",
        "slot": "workspace.panel",
        "entrypoint": "tests.unit.v2.phase_01.test_discovery:dummy_module_factory",
    }
    _create_plugin_dir(tmp_path, "mod_pkg", manifest_module)
    records = discovery_engine.discover([tmp_path])
    lifecycle_manager.set_records(records)
    assert lifecycle_manager.attach("module_plugin") is True

    # 2. Missing attribute in module
    manifest_bad_attr = {
        "id": "bad_attr_plugin",
        "name": "Bad Attr Plugin",
        "version": "1.0.0",
        "slot": "workspace.panel",
        "entrypoint": "tests.unit.v2.phase_01.test_discovery:nonexistent_attr_function",
    }
    _create_plugin_dir(tmp_path, "bad_attr_pkg", manifest_bad_attr)
    records2 = discovery_engine.discover([tmp_path])
    lifecycle_manager.set_records(records2)
    assert lifecycle_manager.attach("bad_attr_plugin") is False

    # 3. Missing file in package
    manifest_missing_file = {
        "id": "missing_file_plugin",
        "name": "Missing File Plugin",
        "version": "1.0.0",
        "slot": "workspace.panel",
        "entrypoint": "absent_file.py:factory",
    }
    _create_plugin_dir(tmp_path, "missing_file_pkg", manifest_missing_file)
    records3 = discovery_engine.discover([tmp_path])
    lifecycle_manager.set_records(records3)
    assert lifecycle_manager.attach("missing_file_plugin") is False


def test_discovery_router_enable_reload_and_state_filter(
    tmp_path: Path,
    discovery_engine: PluginDiscoveryEngine,
    lifecycle_manager: PluginLifecycleManager,
) -> None:
    """Verify REST endpoints for enabling, reloading, and state filtering."""
    manifest_dict = {
        "id": "rest_operable_plugin",
        "name": "Rest Operable Plugin",
        "version": "1.0.0",
        "slot": "workspace.panel",
        "entrypoint": "plugin.py:factory",
    }
    py_code = "def factory(ctx): return {'ready': True}"
    _create_plugin_dir(tmp_path, "operable_pkg", manifest_dict, python_code=py_code)
    records = discovery_engine.discover([tmp_path])
    lifecycle_manager.set_records(records)
    lifecycle_manager.attach("rest_operable_plugin")

    app = FastAPI()
    app.include_router(create_discovery_router(lifecycle_manager))
    client = TestClient(app)

    # Filter by state
    resp_state = client.get("/discovery/plugins?state=attached")
    assert resp_state.status_code == 200
    assert resp_state.json()["total"] == 1

    # Disable
    client.post("/discovery/plugins/rest_operable_plugin/disable")
    rec_disabled = lifecycle_manager.get_record("rest_operable_plugin")
    assert rec_disabled is not None
    assert rec_disabled.state == PluginState.DISABLED

    # Enable via REST
    resp_enable = client.post("/discovery/plugins/rest_operable_plugin/enable")
    assert resp_enable.status_code == 200
    assert resp_enable.json()["state"] == "attached"

    # Reload via REST
    resp_reload = client.post("/discovery/plugins/rest_operable_plugin/reload")
    assert resp_reload.status_code == 200
    assert resp_reload.json()["state"] == "attached"


def test_cli_scan_with_discovered_plugins(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Verify CLI scan output when plugins are present."""
    manifest_dict = {
        "id": "cli_sample_plugin",
        "name": "CLI Sample Plugin",
        "version": "2.5.0",
        "slot": "workspace.root",
        "entrypoint": "mod:func",
    }
    _create_plugin_dir(tmp_path, "sample_pkg", manifest_dict)
    code = main(["--scan", str(tmp_path), "--list"])
    assert code == 0
    captured = capsys.readouterr()
    assert "Discovered 1 plugin packages" in captured.out
    assert "CLI Sample Plugin" in captured.out
