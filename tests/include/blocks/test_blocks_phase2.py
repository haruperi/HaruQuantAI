"""Phase 2 unit tests: canonical package migration and consumer updates.

Verifies:
1. Canonical path normalization (Windows/POSIX consistent).
2. Traversal and symlink escape rejection.
3. Transactional file registration with retained last-valid reload behavior.
4. Recursive directory discovery of canonical blocks.
5. Exclusion of internal infrastructure files from block catalogs.
6. Clean migration across the board: removal of obsolete implementations,
   direct canonical consumer imports, and no compatibility aliases or shims.
"""

from __future__ import annotations

import importlib
import inspect
from pathlib import Path

import pytest
from app.include.blocks.registry import (
    BlockRegistry,
    BlockRegistryError,
    _normalize_source_path,
)
from app.workspace.code_editor.registry import registry as snippet_registry


def test_source_path_normalization_is_consistent_across_os() -> None:
    """Verify paths with Windows backslashes or POSIX slashes normalize identically."""
    p_win = "app\\include\\blocks\\indicators\\trend\\sma.py"
    p_posix = "app/include/blocks/indicators/trend/sma.py"
    assert _normalize_source_path(p_win) == p_posix
    assert _normalize_source_path(p_posix) == p_posix
    assert _normalize_source_path(None) == "<in-memory>"


def test_block_registry_discover_finds_vertical_slice() -> None:
    """Verify recursive directory discovery registers all canonical slice blocks."""
    registry = BlockRegistry()
    blocks_dir = Path("app/include/blocks")
    discovered = registry.discover(blocks_dir, authorized_root="app/include")

    discovered_ids = {desc.spec.id for desc in discovered}
    assert "indicator.trend.sma" in discovered_ids
    assert "function.plus" in discovered_ids
    assert "condition.is_greater" in discovered_ids
    assert "action.log_to_file" in discovered_ids

    # Verify snapshot contains all 4
    snapshot = registry.snapshot()
    assert "indicator.trend.sma" in snapshot
    assert "function.plus" in snapshot
    assert "condition.is_greater" in snapshot
    assert "action.log_to_file" in snapshot


def test_block_registry_rejects_path_traversal(tmp_path: Path) -> None:
    """Verify register_file and discover reject paths outside authorized root."""
    registry = BlockRegistry()
    outside_file = tmp_path / "outside.py"
    outside_file.write_text(
        "from app.include.blocks.base import BaseBlock\n"
        "from app.include.blocks.metadata import BlockSpec\n"
        "class OutsideBlock(BaseBlock):\n"
        "    spec = BlockSpec(id='test.outside')\n",
        encoding="utf-8",
    )

    authorized_root = Path("app/include").resolve()

    # Traversal file registration must be rejected
    with pytest.raises(BlockRegistryError) as exc_info:
        registry.register_file(outside_file, authorized_root=authorized_root)
    assert "escapes authorized root" in str(exc_info.value)

    # Traversal directory discovery must be rejected
    with pytest.raises(BlockRegistryError) as exc_dir:
        registry.discover(tmp_path, authorized_root=authorized_root)
    assert "escapes authorized root" in str(exc_dir.value)


def test_retained_last_valid_reload_on_failure(tmp_path: Path) -> None:
    """Verify transactional staging retains last valid registration if reload fails."""
    registry = BlockRegistry()

    # 1. Register valid block
    valid_file = tmp_path / "custom_block.py"
    valid_file.write_text(
        "from app.include.blocks.base import BaseBlock\n"
        "from app.include.blocks.metadata import BlockSpec\n"
        "class MyBlock(BaseBlock):\n"
        "    spec = BlockSpec(id='custom.my_block', name='MyBlock')\n",
        encoding="utf-8",
    )
    descs = registry.register_file(valid_file, authorized_root=tmp_path)
    assert len(descs) == 1
    assert registry.get("custom.my_block") is not None
    initial_rev = registry.revision

    # 2. Overwrite file with broken syntax and attempt reload
    valid_file.write_text("class BrokenBlock(syntax error", encoding="utf-8")
    with pytest.raises(BlockRegistryError):
        registry.register_file(valid_file, authorized_root=tmp_path)

    # 3. Last valid registration is preserved and registry is not corrupted
    assert registry.get("custom.my_block") is not None
    assert registry.require("custom.my_block").spec.name == "MyBlock"
    assert registry.revision == initial_rev


def test_internal_infrastructure_modules_are_excluded_from_catalogs() -> None:
    """Verify metadata.py, registry.py, series.py, base.py are ignored during discovery."""
    registry = BlockRegistry()
    internal_files = [
        Path("app/include/blocks/base.py"),
        Path("app/include/blocks/metadata.py"),
        Path("app/include/blocks/registry.py"),
        Path("app/include/blocks/series.py"),
    ]
    for internal in internal_files:
        descs = registry.register_file(internal, authorized_root="app/include")
        assert descs == []

    # Also verify SnippetRegistry excludes them from registering block classes
    for internal in internal_files:
        mod = importlib.import_module(f"app.include.blocks.{internal.stem}")
        classes = snippet_registry.register(internal, mod)
        assert classes == []


def test_discovery_failure_isolation_and_diagnostics(tmp_path: Path) -> None:
    """Verify broken files do not halt discovery of valid blocks and record diagnostics."""
    registry = BlockRegistry()
    blocks_dir = tmp_path / "blocks"
    blocks_dir.mkdir()

    # a_broken.py contains syntax error
    (blocks_dir / "a_broken.py").write_text(
        "class BrokenBlock(syntax error", encoding="utf-8"
    )

    # z_good.py contains valid BaseBlock
    (blocks_dir / "z_good.py").write_text(
        "from app.include.blocks.base import BaseBlock\n"
        "from app.include.blocks.metadata import BlockSpec\n"
        "class GoodBlock(BaseBlock):\n"
        "    spec = BlockSpec(id='custom.z_good', name='ZGood')\n",
        encoding="utf-8",
    )

    discovered = registry.discover(blocks_dir, authorized_root=tmp_path)
    discovered_ids = {desc.spec.id for desc in discovered}

    # Good block is discovered despite earlier broken file
    assert "custom.z_good" in discovered_ids
    assert registry.get("custom.z_good") is not None

    # Diagnostics recorded the failure for a_broken.py
    assert len(registry.diagnostics) == 1
    diag = registry.diagnostics[0]
    assert diag["file"].endswith("a_broken.py")
    assert "Failed to register block file" in diag["error"]

    # Diagnostics can be cleared
    registry.clear_diagnostics()
    assert len(registry.diagnostics) == 0


def test_imported_blocks_do_not_acquire_incorrect_ownership(tmp_path: Path) -> None:
    """Verify importing a block does not register it or steal its source ownership."""
    registry = BlockRegistry()

    # Importer file only imports plus from canonical location
    importer_file = tmp_path / "importer.py"
    importer_file.write_text(
        "from app.include.blocks.functions.plus import plus\n",
        encoding="utf-8",
    )

    # Registering importer file should not register imported plus
    registered = registry.register_file(importer_file, authorized_root=tmp_path)
    assert registered == []
    assert registry.get("function.plus") is None


def test_source_ownership_conflict_rejected(tmp_path: Path) -> None:
    """Verify attempting to register an existing block under a different source is rejected."""
    registry = BlockRegistry()

    file1 = tmp_path / "block1.py"
    file1.write_text(
        "from app.include.blocks.base import BaseBlock\n"
        "from app.include.blocks.metadata import BlockSpec\n"
        "class OwnedBlock(BaseBlock):\n"
        "    spec = BlockSpec(id='test.owned_block', name='OwnedBlock')\n",
        encoding="utf-8",
    )
    registry.register_file(file1, authorized_root=tmp_path)
    assert registry.get("test.owned_block") is not None

    # Attempt to re-register the same block ID with a different source_file
    from app.include.blocks.base import BaseBlock
    from app.include.blocks.metadata import BlockSpec

    class StolenBlock(BaseBlock):
        spec = BlockSpec(id="test.owned_block", name="OwnedBlock")

    with pytest.raises(BlockRegistryError) as exc_info:
        registry.register_block(StolenBlock, source_file=tmp_path / "block2.py")
    assert "already owned by source" in str(exc_info.value)


def test_nested_staging_transactions_preserve_state(tmp_path: Path) -> None:
    """Verify nested staging does not overwrite or discard active transaction state."""
    from app.include.blocks.functions.plus import plus

    registry = BlockRegistry()

    # 1. Start outer staging and register an in-memory block
    registry.begin_staging()
    assert bool(registry.is_staging) is True
    assert registry.staging_depth == 1
    registry.register_block(plus)
    assert registry.get("function.plus") is not None

    # 2. Call register_file while outer staging is active (pushes nested savepoint)
    valid_file = tmp_path / "nested_valid.py"
    valid_file.write_text(
        "from app.include.blocks.base import BaseBlock\n"
        "from app.include.blocks.metadata import BlockSpec\n"
        "class NestedBlock(BaseBlock):\n"
        "    spec = BlockSpec(id='custom.nested_block', name='NestedBlock')\n",
        encoding="utf-8",
    )
    reg_nested = registry.register_file(valid_file, authorized_root=tmp_path)
    assert len(reg_nested) == 1

    # Outer staging must still be active and contain BOTH blocks
    assert bool(registry.is_staging) is True
    assert registry.staging_depth == 1
    assert registry.get("function.plus") is not None
    assert registry.get("custom.nested_block") is not None

    # 3. Call register_file with a broken file to verify nested rollback preserves outer state
    broken_file = tmp_path / "nested_broken.py"
    broken_file.write_text("class BrokenBlock(syntax error", encoding="utf-8")

    with pytest.raises(BlockRegistryError):
        registry.register_file(broken_file, authorized_root=tmp_path)

    # Outer staging must still be active and its pending state preserved
    assert bool(registry.is_staging) is True
    assert registry.staging_depth == 1
    assert registry.get("function.plus") is not None
    assert registry.get("custom.nested_block") is not None

    # 4. Commit outer transaction
    registry.commit_staging()
    assert registry.staging_depth == 0

    assert bool(registry.is_staging) is False

    snapshot = registry.snapshot()
    assert "function.plus" in snapshot
    assert "custom.nested_block" in snapshot


def test_clean_migration_obsolete_implementations_removed() -> None:
    """Verify obsolete implementations in legacy files are cleanly eliminated."""
    # 1. comparisons.py legacy monolith is cleanly removed
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("app.include.comparisons")

    # 1b. bar_time.py legacy monolith is cleanly removed
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("app.include.bar_time")

    # 2. functions.py legacy monolith is cleanly removed
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("app.include.functions")

    # 2b. price.py legacy monolith is cleanly removed
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("app.include.price")

    from app.include.blocks.functions import Functions

    assert not hasattr(Functions, "plus")

    # 3. actions/logging.py has no LogToFileAction or log_to_file
    import app.include.actions.logging as act_log

    assert not hasattr(act_log, "LogToFileAction")
    assert not hasattr(act_log, "log_to_file")
    assert "LogToFileAction" not in act_log.__all__
    assert "log_to_file" not in act_log.__all__

    # 4. actions facade has no log_file method
    import app.include.actions.facade as act_facade

    assert not hasattr(act_facade.Actions, "log_file")


def test_clean_migration_direct_consumer_imports() -> None:
    """Verify all consumers import directly from canonical blocks package."""
    # 1. app.include package root exposes canonical blocks
    from app.include.blocks.comparisons.is_greater import is_greater
    from app.include.blocks.functions.plus import plus

    import app.include as root_inc

    assert root_inc.is_greater is is_greater
    assert root_inc.plus is plus

    # 2. actions package exposes canonical log_to_file
    import app.include.actions as root_act
    from app.include.blocks.actions.log_to_file import LogToFileAction, log_to_file

    assert root_act.LogToFileAction is LogToFileAction
    assert root_act.log_to_file is log_to_file

    # Direct canonical block call
    record = log_to_file(filename="test.log", message="hello")
    assert record.action_type == "log_to_file"
    assert record.params["filename"] == "test.log"

    # 3. Indicators import is_greater directly from canonical block
    from app.include.blocks.indicators.momentum.rsi import RSI
    from app.include.blocks.indicators.price_action.candlestick_patterns import (
        CandlestickPatterns,
    )
    from app.include.blocks.indicators.trend.kama import KAMA

    assert inspect.isclass(CandlestickPatterns)
    assert inspect.isclass(KAMA)
    assert inspect.isclass(RSI)
