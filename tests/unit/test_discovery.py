"""Unit tests for Stage 1E Dynamic Plugin Discovery Engine (app/host/discovery.py)."""

from __future__ import annotations

import json
import shutil
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import pytest
from app.host.discovery import (
    MAX_MANIFEST_BYTES,
    PluginDependency,
    PluginDiscovery,
    PluginLifecycleManager,
    PluginManifest,
    PluginState,
    SlotDefinition,
    SlotRegistry,
    _parse_semver_tuple,
    _strict_json_loads,
    create_discovery_router,
    main,
    verify_containment,
)
from fastapi import APIRouter, FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError


def _write_plugin_package(
    parent_dir: Path,
    dir_name: str,
    manifest_data: dict[str, Any],
    *,
    code: str = (
        "class Adapter:\n"
        "    def __init__(self, ctx):\n"
        "        self.plugin_id = ctx.plugin_id\n"
    ),
    module_filename: str = "adapter.py",
    manifest_filename: str = "plugin.json",
) -> Path:
    """Create a synthetic plugin directory with manifest and module code."""
    pkg_dir = parent_dir / dir_name
    pkg_dir.mkdir(parents=True, exist_ok=True)
    (pkg_dir / manifest_filename).write_text(
        json.dumps(manifest_data), encoding="utf-8"
    )
    (pkg_dir / module_filename).write_text(code, encoding="utf-8")
    return pkg_dir


# ============================================================================
# 1. Slot Registry & Manifest Schema Validation
# ============================================================================


def test_slot_registry_core_and_custom_slots() -> None:
    """Verify core slots are pre-registered and custom slots can be added."""
    registry = SlotRegistry()
    core_ids = {s.slot_id for s in registry.list_slots()}
    assert "data.provider" in core_ids
    assert "workspace.root" in core_ids
    assert "broker" in core_ids
    assert "export.platform" in core_ids

    custom = SlotDefinition(
        slot_id="custom.singleton",
        description="Single-instance custom slot",
        allow_multiple=False,
        required_capabilities=("custom.cap",),
    )
    registry.register_slot(custom)
    fetched = registry.get_slot("custom.singleton")
    assert fetched == custom
    assert registry.get_slot("nonexistent.slot") is None


def test_plugin_manifest_entry_point_and_entrypoint_aliases() -> None:
    """Verify PluginManifest supports both entry_point and entrypoint fields."""
    m1 = PluginManifest.model_validate(
        {
            "id": "data.dukascopy",
            "name": "Dukascopy Tick Feed",
            "version": "1.2.0",
            "slot": "data.provider",
            "entry_point": "adapter:DukascopyDataProvider",
            "capabilities": ["data.fetch"],
        }
    )
    assert m1.entry_point == "adapter:DukascopyDataProvider"
    assert m1.entrypoint == "adapter:DukascopyDataProvider"

    m2 = PluginManifest.model_validate(
        {
            "id": "data.yahoo",
            "name": "Yahoo Finance",
            "version": "1.0.0",
            "slot": "data.provider",
            "entrypoint": "adapter:create_adapter",
            "capabilities": ["data.fetch"],
        }
    )
    assert m2.entry_point == "adapter:create_adapter"
    assert m2.entrypoint == "adapter:create_adapter"


def test_plugin_manifest_validation_rejections() -> None:
    """Verify schema rejections for invalid id, semver, entry_point, and ui_bundle."""
    with pytest.raises(ValidationError):
        PluginManifest.model_validate(
            {
                "id": "INVALID_UPPERCASE",
                "name": "Bad ID",
                "version": "1.0.0",
                "slot": "data.provider",
                "entry_point": "adapter:Adapter",
            }
        )

    with pytest.raises(ValidationError):
        PluginManifest.model_validate(
            {
                "id": "valid.id",
                "name": "Bad Version",
                "version": "not-a-semver",
                "slot": "data.provider",
                "entry_point": "adapter:Adapter",
            }
        )

    with pytest.raises(ValidationError):
        PluginManifest.model_validate(
            {
                "id": "valid.id",
                "name": "Bad Entrypoint",
                "version": "1.0.0",
                "slot": "data.provider",
                "entry_point": "no_colon_target",
            }
        )

    with pytest.raises(ValidationError):
        PluginManifest.model_validate(
            {
                "id": "valid.id",
                "name": "Bad UI Bundle",
                "version": "1.0.0",
                "slot": "data.provider",
                "entry_point": "adapter:Adapter",
                "ui_bundle": "../escape.js",
            }
        )

    with pytest.raises(ValidationError):
        PluginDependency(plugin_id="BAD_ID")

    with pytest.raises(ValidationError):
        PluginDependency(plugin_id="good.id", min_version="bad.ver")

    with pytest.raises(ValueError, match="Invalid semantic version"):
        _parse_semver_tuple("invalid")


def test_strict_json_loads_rejects_duplicates_and_nan() -> None:
    """Verify _strict_json_loads rejects duplicate keys and NaN/Infinity."""
    with pytest.raises(ValueError, match="Duplicate JSON key"):
        _strict_json_loads('{"id": "a.b.c", "id": "d.e.f"}')

    with pytest.raises(ValueError, match="Non-finite JSON constant"):
        _strict_json_loads('{"value": NaN}')


# ============================================================================
# 2. Containment Verification
# ============================================================================


def test_verify_containment_guards_boundaries(tmp_path: Path) -> None:
    """Verify verify_containment accepts child paths and rejects outside paths."""
    allowed_root = tmp_path / "plugins"
    allowed_root.mkdir()
    inside_file = allowed_root / "pkg" / "plugin.json"
    inside_file.parent.mkdir()
    inside_file.write_text("{}", encoding="utf-8")

    resolved = verify_containment(inside_file, allowed_root)
    assert resolved == inside_file.resolve()

    outside_file = tmp_path / "outside.json"
    outside_file.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="Containment violation"):
        verify_containment(outside_file, allowed_root)

    with pytest.raises(ValueError, match="does not exist"):
        verify_containment(allowed_root / "missing.json", allowed_root)


# ============================================================================
# 3. Filesystem Discovery (1-Level, 2-Level Slot-Family, Single-File AST)
# ============================================================================


def test_discover_1_level_2_level_and_single_file_plugins(
    tmp_path: Path,
) -> None:
    """Verify discovery across 1-level, 2-level slot-family, and single-file AST."""
    plugins_root = tmp_path / "plugins"
    plugins_root.mkdir()

    # 1-level plugin using manifest.json
    _write_plugin_package(
        plugins_root,
        "flat_probe",
        {
            "id": "diag.flat",
            "name": "Flat Diagnostic Probe",
            "version": "1.0.0",
            "slot": "diagnostic.probe",
            "entry_point": "adapter:Adapter",
            "capabilities": [],
        },
        manifest_filename="manifest.json",
    )

    # 2-level slot-family plugin: data_source/dukascopy/plugin.json
    _write_plugin_package(
        plugins_root / "data_source",
        "dukascopy",
        {
            "id": "data.dukascopy",
            "name": "Dukascopy Provider",
            "version": "2.1.0",
            "slot": "data.provider",
            "entry_point": "adapter:Adapter",
            "capabilities": ["data.fetch"],
        },
    )

    # Single-file AST plugin
    single_file = plugins_root / "quick_formatter.py"
    single_file.write_text(
        "PLUGIN_MANIFEST = {\n"
        '    "id": "export.quick",\n'
        '    "name": "Quick Formatter",\n'
        '    "version": "1.0.0",\n'
        '    "slot": "export.formatter",\n'
        '    "entry_point": "quick_formatter:create_formatter",\n'
        "}\n"
        "def create_formatter():\n"
        '    return {"formatter": "quick"}\n',
        encoding="utf-8",
    )

    # Ignored files (__init__.py, hidden, __pycache__)
    (plugins_root / "__init__.py").write_text("", encoding="utf-8")
    (plugins_root / ".hidden").mkdir()
    (plugins_root / "__pycache__").mkdir()

    engine = PluginDiscovery(search_dirs=[plugins_root])
    records = engine.discover_plugins()
    order = engine.resolve_dependencies()

    assert set(records.keys()) == {
        "diag.flat",
        "data.dukascopy",
        "export.quick",
    }
    assert set(order) == {"diag.flat", "data.dukascopy", "export.quick"}

    lifecycle = PluginLifecycleManager(
        discovery_engine=engine,
        data_root=tmp_path / "data",
    )
    inst_duka = lifecycle.get_instance("data.dukascopy")
    assert inst_duka is not None
    assert inst_duka.plugin_id == "data.dukascopy"

    inst_quick = lifecycle.get_instance("export.quick")
    assert inst_quick == {"formatter": "quick"}


def test_discover_malformed_and_edge_case_diagnostics(tmp_path: Path) -> None:
    """Verify diagnostics for missing manifests, duplicate IDs, and bad files."""
    plugins_root = tmp_path / "plugins"
    plugins_root.mkdir()

    # Non-existent search dir and file-as-search-dir
    not_a_dir = tmp_path / "file_root.txt"
    not_a_dir.write_text("hello", encoding="utf-8")

    # 1. Missing manifest in 1-level dir (no subdirs)
    (plugins_root / "empty_plugin_dir").mkdir()

    # 2. Missing manifest in 2-level dir
    (plugins_root / "broker" / "broken_broker").mkdir(parents=True)

    # 3. Malformed JSON manifest
    bad_json_dir = plugins_root / "bad_json"
    bad_json_dir.mkdir()
    (bad_json_dir / "plugin.json").write_text("{bad json", encoding="utf-8")

    # 4. Non-object JSON root
    list_json_dir = plugins_root / "list_json"
    list_json_dir.mkdir()
    (list_json_dir / "plugin.json").write_text("[1, 2, 3]", encoding="utf-8")

    # 5. Oversized manifest
    huge_dir = plugins_root / "huge_manifest"
    huge_dir.mkdir()
    (huge_dir / "plugin.json").write_bytes(b" " * (MAX_MANIFEST_BYTES + 10))

    # 6. Duplicate plugin IDs
    _write_plugin_package(
        plugins_root,
        "dup_one",
        {
            "id": "dup.plugin",
            "name": "Dup 1",
            "version": "1.0.0",
            "slot": "diagnostic.probe",
            "entry_point": "adapter:Adapter",
        },
    )
    _write_plugin_package(
        plugins_root,
        "dup_two",
        {
            "id": "dup.plugin",
            "name": "Dup 2",
            "version": "1.0.0",
            "slot": "diagnostic.probe",
            "entry_point": "adapter:Adapter",
        },
    )

    # 7. Missing entrypoint module file
    missing_mod_dir = plugins_root / "missing_mod"
    missing_mod_dir.mkdir()
    (missing_mod_dir / "plugin.json").write_text(
        json.dumps(
            {
                "id": "missing.mod",
                "name": "Missing Mod",
                "version": "1.0.0",
                "slot": "diagnostic.probe",
                "entry_point": "nonexistent:Adapter",
            }
        ),
        encoding="utf-8",
    )

    # 8. Missing ui_bundle file
    missing_ui_dir = _write_plugin_package(
        plugins_root,
        "missing_ui",
        {
            "id": "missing.ui",
            "name": "Missing UI",
            "version": "1.0.0",
            "slot": "diagnostic.probe",
            "entry_point": "adapter:Adapter",
            "ui_bundle": "dist/bundle.js",
        },
    )
    assert missing_ui_dir.exists()

    # 9. Single-file AST errors (syntax error, non-literal, stem mismatch)
    (plugins_root / "syntax_err.py").write_text("def broken(:\n", encoding="utf-8")
    (plugins_root / "non_literal.py").write_text(
        "PLUGIN_MANIFEST = dict(a=1)\n", encoding="utf-8"
    )
    (plugins_root / "stem_mismatch.py").write_text(
        "PLUGIN_MANIFEST = {\n"
        '    "id": "stem.mismatch",\n'
        '    "name": "Stem Mismatch",\n'
        '    "version": "1.0.0",\n'
        '    "slot": "diagnostic.probe",\n'
        '    "entry_point": "wrong_module:fn",\n'
        "}\n",
        encoding="utf-8",
    )
    (plugins_root / "no_manifest_var.py").write_text("X = 42\n", encoding="utf-8")

    engine = PluginDiscovery(
        search_dirs=[tmp_path / "does_not_exist", not_a_dir, plugins_root]
    )
    engine.discover_plugins()

    codes = {d.code for d in engine.diagnostics}
    assert "SEARCH_PATH_NOT_DIR" in codes
    assert "MISSING_MANIFEST" in codes
    assert "MALFORMED_MANIFEST_JSON" in codes
    assert "INVALID_MANIFEST_ROOT" in codes
    assert "MANIFEST_TOO_LARGE" in codes
    assert "DUPLICATE_PLUGIN_ID" in codes
    assert "ENTRYPOINT_MODULE_MISSING" in codes
    assert "UI_BUNDLE_MISSING" in codes
    assert "AST_PARSE_ERROR" in codes
    assert "INVALID_AST_MANIFEST" in codes
    assert "SINGLE_FILE_ENTRYPOINT_MISMATCH" in codes


# ============================================================================
# 4. Dependency Resolution, Version Bounds, Slot Cardinality & Cycles
# ============================================================================


def test_dependency_resolution_dag_and_quarantines(tmp_path: Path) -> None:
    """Verify topological sort, version bounds, slot cardinality, and cycles."""
    plugins_root = tmp_path / "plugins"
    plugins_root.mkdir()

    slots = SlotRegistry()
    slots.register_slot(
        SlotDefinition(
            slot_id="singleton.slot",
            description="Only one plugin allowed",
            allow_multiple=False,
            required_capabilities=("cap.single",),
        )
    )

    # Base plugin A (v1.2.0)
    _write_plugin_package(
        plugins_root,
        "plugin_a",
        {
            "id": "core.alpha",
            "name": "Alpha",
            "version": "1.2.0",
            "slot": "singleton.slot",
            "entry_point": "adapter:Adapter",
            "capabilities": ["cap.single"],
        },
    )

    # Dependent plugin B -> requires core.alpha >=1.0.0 <=2.0.0 + optional missing
    _write_plugin_package(
        plugins_root,
        "plugin_b",
        {
            "id": "core.beta",
            "name": "Beta",
            "version": "1.0.0",
            "slot": "diagnostic.probe",
            "entry_point": "adapter:Adapter",
            "dependencies": [
                {
                    "plugin_id": "core.alpha",
                    "min_version": "1.0.0",
                    "max_version": "2.0.0",
                },
                {
                    "plugin_id": "optional.ghost",
                    "optional": True,
                },
            ],
        },
    )

    # Singleton conflict plugin
    _write_plugin_package(
        plugins_root,
        "plugin_singleton_conflict",
        {
            "id": "core.alpha.dup",
            "name": "Alpha Conflict",
            "version": "1.0.0",
            "slot": "singleton.slot",
            "entry_point": "adapter:Adapter",
            "capabilities": ["cap.single"],
        },
    )

    # Unknown slot plugin
    _write_plugin_package(
        plugins_root,
        "plugin_unknown_slot",
        {
            "id": "bad.slot",
            "name": "Bad Slot",
            "version": "1.0.0",
            "slot": "nonexistent.slot",
            "entry_point": "adapter:Adapter",
        },
    )

    # Missing required capability plugin
    _write_plugin_package(
        plugins_root,
        "plugin_missing_cap",
        {
            "id": "bad.cap",
            "name": "Missing Cap",
            "version": "1.0.0",
            "slot": "data.provider",
            "entry_point": "adapter:Adapter",
            "capabilities": [],
        },
    )

    # Incompatible required dependency version
    _write_plugin_package(
        plugins_root,
        "plugin_bad_ver",
        {
            "id": "bad.ver",
            "name": "Bad Version Dep",
            "version": "1.0.0",
            "slot": "diagnostic.probe",
            "entry_point": "adapter:Adapter",
            "dependencies": [{"plugin_id": "core.alpha", "min_version": "3.0.0"}],
        },
    )

    # Self-dependency plugin
    _write_plugin_package(
        plugins_root,
        "plugin_self_dep",
        {
            "id": "self.dep",
            "name": "Self Dep",
            "version": "1.0.0",
            "slot": "diagnostic.probe",
            "entry_point": "adapter:Adapter",
            "dependencies": [{"plugin_id": "self.dep"}],
        },
    )

    # Circular dependency pair: cycle.one <-> cycle.two
    _write_plugin_package(
        plugins_root,
        "cycle_one",
        {
            "id": "cycle.one",
            "name": "Cycle 1",
            "version": "1.0.0",
            "slot": "diagnostic.probe",
            "entry_point": "adapter:Adapter",
            "dependencies": [{"plugin_id": "cycle.two"}],
        },
    )
    _write_plugin_package(
        plugins_root,
        "cycle_two",
        {
            "id": "cycle.two",
            "name": "Cycle 2",
            "version": "1.0.0",
            "slot": "diagnostic.probe",
            "entry_point": "adapter:Adapter",
            "dependencies": [{"plugin_id": "cycle.one"}],
        },
    )

    engine = PluginDiscovery(search_dirs=[plugins_root], slot_registry=slots)
    engine.discover_plugins()
    order = engine.resolve_dependencies()

    assert order == ["core.alpha", "core.beta"]
    assert engine.registry["core.alpha"].state == PluginState.VALIDATED
    assert engine.registry["core.beta"].state == PluginState.VALIDATED
    assert engine.registry["core.alpha.dup"].state == PluginState.QUARANTINED
    assert engine.registry["bad.slot"].state == PluginState.QUARANTINED
    assert engine.registry["bad.cap"].state == PluginState.QUARANTINED
    assert engine.registry["bad.ver"].state == PluginState.QUARANTINED
    assert engine.registry["self.dep"].state == PluginState.QUARANTINED
    assert engine.registry["cycle.one"].state == PluginState.QUARANTINED
    assert engine.registry["cycle.two"].state == PluginState.QUARANTINED


# ============================================================================
# 5. Thread-Safe Lazy Instantiation, SC-02 Orthogonality & Lifecycle
# ============================================================================


def test_lazy_thread_safe_get_instance_and_slot_queries(tmp_path: Path) -> None:
    """Verify RLock-guarded lazy instantiation and caching across threads."""
    plugins_root = tmp_path / "plugins"
    plugins_root.mkdir()

    # Zero-arg class entrypoint
    _write_plugin_package(
        plugins_root / "data_source",
        "dukascopy",
        {
            "id": "data.dukascopy",
            "name": "Dukascopy",
            "version": "1.0.0",
            "slot": "data.provider",
            "entry_point": "adapter:DukascopyDataProvider",
            "capabilities": ["data.fetch"],
        },
        code=(
            "INSTANTIATION_COUNT = 0\n"
            "class DukascopyDataProvider:\n"
            "    def __init__(self):\n"
            "        global INSTANTIATION_COUNT\n"
            "        INSTANTIATION_COUNT += 1\n"
            "        self.provider = 'dukascopy'\n"
            "        self.count = INSTANTIATION_COUNT\n"
        ),
    )

    # Context-accepting factory entrypoint with package __init__.py
    yahoo_dir = _write_plugin_package(
        plugins_root / "data_source",
        "yahoo",
        {
            "id": "data.yahoo",
            "name": "Yahoo",
            "version": "1.0.0",
            "slot": "data.provider",
            "entry_point": "adapter:create_yahoo",
            "capabilities": ["data.fetch"],
            "dependencies": [{"plugin_id": "data.dukascopy"}],
        },
        code=(
            "def create_yahoo(ctx):\n"
            "    ctx.ensure_data_dir()\n"
            "    return {'provider': 'yahoo', 'id': ctx.plugin_id}\n"
        ),
    )
    (yahoo_dir / "__init__.py").write_text("# package init\n", encoding="utf-8")

    engine = PluginDiscovery(search_dirs=[plugins_root])
    engine.discover_plugins()
    # Notice we do NOT call load_and_attach_all() upfront; we test lazy loading!

    def _fetch_duka(_: int) -> Any:
        return engine.get_instance("data.dukascopy")

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(_fetch_duka, range(16)))

    first_instance = results[0]
    assert first_instance is not None
    assert first_instance.provider == "dukascopy"
    assert first_instance.count == 1
    assert all(r is first_instance for r in results)

    # Querying slot lazily instantiates data.yahoo as well
    providers = engine.get_instances_for_slot("data.provider")
    assert len(providers) == 2
    assert engine.get_instance("nonexistent.plugin") is None


def test_sc02_plugin_orthogonality_zero_host_edits(tmp_path: Path) -> None:
    """Verify SC-02: adding/removing plugin folders dynamically updates registry."""
    plugins_root = tmp_path / "plugins"
    plugins_root.mkdir()

    _write_plugin_package(
        plugins_root,
        "p_one",
        {
            "id": "probe.one",
            "name": "Probe One",
            "version": "1.0.0",
            "slot": "diagnostic.probe",
            "entry_point": "adapter:Adapter",
        },
    )

    engine = PluginDiscovery(search_dirs=[plugins_root])
    engine.discover_plugins()
    assert [p.plugin_id for p in engine.get_instances_for_slot("diagnostic.probe")] == [
        "probe.one"
    ]

    # Dynamically add a second plugin folder on disk
    _write_plugin_package(
        plugins_root,
        "p_two",
        {
            "id": "probe.two",
            "name": "Probe Two",
            "version": "1.0.0",
            "slot": "diagnostic.probe",
            "entry_point": "adapter:Adapter",
        },
    )
    engine.discover_plugins()
    assert [p.plugin_id for p in engine.get_instances_for_slot("diagnostic.probe")] == [
        "probe.one",
        "probe.two",
    ]

    # Remove p_one from disk and re-discover
    shutil.rmtree(plugins_root / "p_one")

    engine.discover_plugins()
    assert [p.plugin_id for p in engine.get_instances_for_slot("diagnostic.probe")] == [
        "probe.two"
    ]


def test_lifecycle_enable_disable_cascade_reload_and_uninstall(
    tmp_path: Path,
) -> None:
    """Verify enable, cascade disable, teardown hooks, reload, and uninstall."""
    plugins_root = tmp_path / "plugins"
    plugins_root.mkdir()

    _write_plugin_package(
        plugins_root,
        "base_pkg",
        {
            "id": "base.pkg",
            "name": "Base Package",
            "version": "1.0.0",
            "slot": "diagnostic.probe",
            "entry_point": "adapter:create_base",
        },
        code=(
            "TEARDOWN_CALLS = []\n"
            "def create_base(ctx):\n"
            "    from fastapi import APIRouter\n"
            "    ctx.register_router(APIRouter())\n"
            "    ctx.subscribe_event('tick', lambda x: x)\n"
            "    ctx.register_job_handler('sync', lambda: None)\n"
            "    ctx.register_teardown(lambda: TEARDOWN_CALLS.append('ok'))\n"
            "    def bad_teardown():\n"
            "        raise RuntimeError('teardown boom')\n"
            "    ctx.register_teardown(bad_teardown)\n"
            "    return {'v': 1}\n"
        ),
    )

    _write_plugin_package(
        plugins_root,
        "child_pkg",
        {
            "id": "child.pkg",
            "name": "Child Package",
            "version": "1.0.0",
            "slot": "diagnostic.probe",
            "entry_point": "adapter:Adapter",
            "dependencies": [{"plugin_id": "base.pkg"}],
        },
    )

    _write_plugin_package(
        plugins_root,
        "disabled_pkg",
        {
            "id": "disabled.pkg",
            "name": "Disabled By Default",
            "version": "1.0.0",
            "slot": "diagnostic.probe",
            "entry_point": "adapter:Adapter",
            "enabled_by_default": False,
        },
    )

    _write_plugin_package(
        plugins_root,
        "failing_pkg",
        {
            "id": "failing.pkg",
            "name": "Failing Runtime",
            "version": "1.0.0",
            "slot": "diagnostic.probe",
            "entry_point": "adapter:boom",
        },
        code="def boom():\n    raise RuntimeError('init failure')\n",
    )

    engine = PluginDiscovery(search_dirs=[plugins_root])
    engine.discover_plugins()
    engine.resolve_dependencies()

    lifecycle = PluginLifecycleManager(
        discovery_engine=engine,
        data_root=tmp_path / "data",
    )
    report = lifecycle.load_and_attach_all()
    assert report.enabled_count == 2
    assert report.failed_count == 1
    assert engine.registry["disabled.pkg"].state == PluginState.DISABLED

    ctx = lifecycle.contexts["base.pkg"]
    assert len(ctx.routers) == 1
    assert "tick" in ctx.event_handlers
    assert "sync" in ctx.job_handlers

    # Disabling base.pkg cascades to child.pkg
    assert lifecycle.disable_plugin("base.pkg", cascade=True) is True
    assert engine.registry["base.pkg"].state.value == "DISABLED"
    assert engine.registry["child.pkg"].state.value == "DISABLED"

    # Re-enable base.pkg and reload it
    assert lifecycle.enable_plugin("base.pkg") is True
    assert engine.registry["base.pkg"].state.value == "ENABLED"
    assert lifecycle.reload_plugin("base.pkg") is True
    assert engine.registry["base.pkg"].state.value == "ENABLED"

    # Uninstall child.pkg
    assert lifecycle.uninstall_plugin("child.pkg") is True
    assert "child.pkg" not in engine.registry
    assert lifecycle.uninstall_plugin("nonexistent") is False


# ============================================================================
# 6. FastAPI Discovery Router & CLI Entrypoint
# ============================================================================


def test_discovery_fastapi_router_endpoints(tmp_path: Path) -> None:
    """Verify FastAPI discovery inspection and lifecycle control endpoints."""
    plugins_root = tmp_path / "plugins"
    plugins_root.mkdir()

    _write_plugin_package(
        plugins_root,
        "demo_probe",
        {
            "id": "demo.probe",
            "name": "Demo Probe",
            "version": "1.0.0",
            "slot": "diagnostic.probe",
            "entry_point": "adapter:Adapter",
        },
    )

    engine = PluginDiscovery(search_dirs=[plugins_root])
    engine.discover_plugins()
    engine.resolve_dependencies()
    lifecycle = PluginLifecycleManager(
        discovery_engine=engine, data_root=tmp_path / "data"
    )
    lifecycle.load_and_attach_all()

    app = FastAPI()
    router: APIRouter = create_discovery_router(lifecycle)
    app.include_router(router)
    client = TestClient(app)

    res_list = client.get("/discovery/plugins")
    assert res_list.status_code == 200
    assert res_list.json()["report"]["enabled_count"] == 1

    res_detail = client.get("/discovery/plugins/demo.probe")
    assert res_detail.status_code == 200
    assert res_detail.json()["id"] == "demo.probe"

    res_404 = client.get("/discovery/plugins/missing.plugin")
    assert res_404.status_code == 404

    res_disable = client.post("/discovery/plugins/demo.probe/disable")
    assert res_disable.status_code == 200
    assert res_disable.json()["state"] == "DISABLED"

    res_enable = client.post("/discovery/plugins/demo.probe/enable")
    assert res_enable.status_code == 200
    assert res_enable.json()["state"] == "ENABLED"

    res_reload = client.post("/discovery/plugins/demo.probe/reload")
    assert res_reload.status_code == 200
    assert res_reload.json()["state"] == "ENABLED"

    res_slots = client.get("/discovery/slots")
    assert res_slots.status_code == 200
    probe_slot = next(
        s for s in res_slots.json()["slots"] if s["slot_id"] == "diagnostic.probe"
    )
    assert "demo.probe" in probe_slot["bound_plugins"]


def test_discovery_cli_main(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Verify standalone CLI main() execution and exit code."""
    plugins_root = tmp_path / "plugins"
    plugins_root.mkdir()
    _write_plugin_package(
        plugins_root,
        "cli_probe",
        {
            "id": "cli.probe",
            "name": "CLI Probe",
            "version": "1.0.0",
            "slot": "diagnostic.probe",
            "entry_point": "adapter:Adapter",
        },
    )

    exit_code = main(["--scan-dir", str(plugins_root)])
    assert exit_code == 0
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert payload["total_discovered"] == 1
    assert payload["quarantined_count"] == 0
