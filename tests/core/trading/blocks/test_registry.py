"""Unit tests for BlockRegistry, transactional staging, snapshots, and block contracts."""

from __future__ import annotations

from pathlib import Path

import pytest
from app.core.lib.errors import DomainError
from app.core.trading.blocks.base import BaseBlock, block
from app.core.trading.blocks.metadata import (
    BlockSpec,
    ExecutionKind,
    OutputPort,
    PortType,
)
from app.core.trading.blocks.registry import (
    BlockDescriptor,
    BlockRegistry,
    BlockRegistryError,
    CatalogSnapshot,
)


class SampleIndicator(BaseBlock):
    """Sample block for testing."""

    spec = BlockSpec(
        id="indicator.test.sample",
        name="SampleIndicator",
        category="indicators",
        execution_kind=ExecutionKind.EXPRESSION,
        outputs=(OutputPort("value", PortType.NUMBER),),
    )


class AnotherBlock(BaseBlock):
    """Another sample block for testing."""

    spec = BlockSpec(
        id="indicator.test.another",
        name="AnotherBlock",
        category="indicators",
        execution_kind=ExecutionKind.EXPRESSION,
        outputs=(OutputPort("value", PortType.NUMBER),),
    )


@block(
    BlockSpec(
        id="function.test.add_five",
        name="AddFive",
        category="math",
        execution_kind=ExecutionKind.EXPRESSION,
        outputs=(OutputPort("result", PortType.NUMBER),),
    )
)
def add_five(x: float, amount: float = 5.0) -> float:
    return x + amount


# ---------------------------------------------------------------------------
# 1. Identity & Backward Compatibility Bridges
# ---------------------------------------------------------------------------


def test_block_registry_error_is_domain_error() -> None:
    """Verify BlockRegistryError satisfies DomainError contract."""
    err = BlockRegistryError(
        "Registration failed",
        code="REG_FAILED",
        details={"key": "val"},
    )
    assert isinstance(err, DomainError)
    assert err.code == "REG_FAILED"
    assert err.message == "Registration failed"
    assert err.details == {"key": "val"}


# ---------------------------------------------------------------------------
# 2. Registration & Duplicate ID Enforcements
# ---------------------------------------------------------------------------


def test_register_block_class_and_callable() -> None:
    registry = BlockRegistry()
    desc_class = registry.register_block(SampleIndicator)
    assert isinstance(desc_class, BlockDescriptor)
    assert desc_class.spec.id == "indicator.test.sample"
    assert desc_class.is_class is True

    desc_fn = registry.register_block(add_five)
    assert isinstance(desc_fn, BlockDescriptor)
    assert desc_fn.spec.id == "function.test.add_five"
    assert desc_fn.is_class is False


def test_register_duplicate_block_id_raises_duplicate_block_id() -> None:
    registry = BlockRegistry()
    registry.register_block(SampleIndicator)

    class DuplicateBlock(BaseBlock):
        spec = BlockSpec(
            id="indicator.test.sample",
            name="ConflictingSample",
        )

    # 1. Registering duplicate without overwrite raises DUPLICATE_BLOCK_ID
    with pytest.raises(DomainError) as exc_info:
        registry.register_block(DuplicateBlock, overwrite=False)
    assert exc_info.value.code == "DUPLICATE_BLOCK_ID"
    assert "already registered" in exc_info.value.message
    assert "Duplicate block ID" in str(exc_info.value)

    # 2. Passing descriptor keyword argument directly also enforces duplicate rejection
    desc = registry.require("indicator.test.sample")
    with pytest.raises(DomainError) as exc_info2:
        registry.register_block(descriptor=desc, overwrite=False)
    assert exc_info2.value.code == "DUPLICATE_BLOCK_ID"


def test_register_duplicate_block_id_with_overwrite_succeeds() -> None:
    registry = BlockRegistry()
    registry.register_block(SampleIndicator)

    class UpdatedSample(BaseBlock):
        spec = BlockSpec(
            id="indicator.test.sample",
            name="UpdatedSample",
        )

    # Overwrite replaces target
    desc = registry.register_block(UpdatedSample, overwrite=True)
    assert desc.spec.name == "UpdatedSample"
    assert registry.require("indicator.test.sample").spec.name == "UpdatedSample"


def test_register_block_missing_argument_raises_invalid_argument() -> None:
    registry = BlockRegistry()
    with pytest.raises(DomainError) as exc_info:
        registry.register_block()
    assert exc_info.value.code == "INVALID_ARGUMENT"


# ---------------------------------------------------------------------------
# 3. Transactional Staging Lifecycle (Begin, Commit, Rollback)
# ---------------------------------------------------------------------------


def test_staging_lifecycle_commit() -> None:
    registry = BlockRegistry()
    registry.register_block(SampleIndicator)
    initial_snapshot = registry.snapshot()
    assert len(initial_snapshot) == 1
    assert "indicator.test.sample" in initial_snapshot

    # Begin staging
    registry.begin_staging()
    assert registry.is_staging is True
    assert registry.staging_depth == 1

    # Registration during active staging modifies detached buffer
    registry.register_block(AnotherBlock)
    assert registry.get("indicator.test.another") is not None

    # Crucial: Prior snapshot and registry.snapshot() remain unchanged during active staging
    mid_snapshot = registry.snapshot()
    assert len(mid_snapshot) == 1
    assert "indicator.test.another" not in mid_snapshot

    # Commit staging returns new immutable snapshot
    committed_snapshot = registry.commit_staging()
    assert isinstance(committed_snapshot, CatalogSnapshot)
    assert len(committed_snapshot) == 2
    assert "indicator.test.sample" in committed_snapshot
    assert "indicator.test.another" in committed_snapshot
    assert registry.is_staging is False
    assert registry.staging_depth == 0


def test_staging_lifecycle_rollback() -> None:
    registry = BlockRegistry()
    registry.register_block(SampleIndicator)
    initial_snapshot = registry.snapshot()

    # Begin staging
    registry.begin_staging()
    registry.register_block(AnotherBlock)
    assert registry.get("indicator.test.another") is not None

    # Rollback staging discards detached buffer
    registry.rollback_staging()
    assert registry.is_staging is False
    assert registry.get("indicator.test.another") is None

    # Prior snapshot remains unchanged
    after_rollback = registry.snapshot()
    assert len(after_rollback) == 1
    assert "indicator.test.another" not in after_rollback
    assert after_rollback.revision == initial_snapshot.revision


def test_nested_staging_savepoints() -> None:
    registry = BlockRegistry()
    registry.register_block(SampleIndicator)

    # Outer staging
    registry.begin_staging()
    assert registry.staging_depth == 1
    registry.register_block(AnotherBlock)

    # Inner staging (savepoint)
    registry.begin_staging()
    assert registry.staging_depth == 2

    class ThirdBlock(BaseBlock):
        spec = BlockSpec(id="test.third", name="ThirdBlock")

    registry.register_block(ThirdBlock)
    assert registry.get("test.third") is not None

    # Rollback inner savepoint: discards ThirdBlock, keeps AnotherBlock in outer staging
    registry.rollback_staging()
    assert registry.staging_depth == 1
    assert registry.get("test.third") is None
    assert registry.get("indicator.test.another") is not None

    # Commit outer transaction
    final_snapshot = registry.commit_staging()
    assert registry.staging_depth == 0
    assert "indicator.test.another" in final_snapshot
    assert "test.third" not in final_snapshot


def test_commit_staging_without_active_transaction_raises() -> None:
    registry = BlockRegistry()
    with pytest.raises(DomainError) as exc_info:
        registry.commit_staging()
    assert exc_info.value.code == "NO_ACTIVE_TRANSACTION"


# ---------------------------------------------------------------------------
# 4. CatalogSnapshot Immutability & Queries
# ---------------------------------------------------------------------------


def test_catalog_snapshot_immutability() -> None:
    registry = BlockRegistry()
    registry.register_block(SampleIndicator)
    snapshot = registry.snapshot()

    # Dictionary is wrapped in MappingProxyType
    with pytest.raises(TypeError):
        snapshot.blocks["injected"] = registry.require("indicator.test.sample")  # type: ignore[index]

    # Iteration and len work
    assert len(snapshot) == 1
    assert [d.spec.id for d in snapshot] == ["indicator.test.sample"]

    # Require non-existent raises BlockRegistryError
    with pytest.raises(DomainError) as exc_info:
        snapshot.require("non_existent")
    assert exc_info.value.code == "BLOCK_NOT_FOUND"


# ---------------------------------------------------------------------------
# 5. File Registration & Atomic Discovery
# ---------------------------------------------------------------------------


def test_register_file_and_atomic_discovery(tmp_path: Path) -> None:
    block_file_1 = tmp_path / "custom_block_1.py"
    block_file_1.write_text(
        "from app.core.trading.blocks.base import BaseBlock\n"
        "from app.core.trading.blocks.metadata import BlockSpec\n\n"
        "class DiscoveredOne(BaseBlock):\n"
        "    spec = BlockSpec(id='disc.one', name='DiscoveredOne')\n",
        encoding="utf-8",
    )

    block_file_2 = tmp_path / "custom_block_2.py"
    block_file_2.write_text(
        "from app.core.trading.blocks.base import BaseBlock\n"
        "from app.core.trading.blocks.metadata import BlockSpec\n\n"
        "class DiscoveredTwo(BaseBlock):\n"
        "    spec = BlockSpec(id='disc.two', name='DiscoveredTwo')\n",
        encoding="utf-8",
    )

    registry = BlockRegistry()
    count = registry.discover(tmp_path, authorized_root=tmp_path)
    assert count == 2

    snap = registry.snapshot()
    assert "disc.one" in snap
    assert "disc.two" in snap
    assert registry.is_staging is False


def test_discovery_path_traversal_check(tmp_path: Path) -> None:
    sub_dir = tmp_path / "sub"
    sub_dir.mkdir()
    registry = BlockRegistry()

    # Path escaping authorized root raises
    with pytest.raises(DomainError) as exc_info:
        registry.discover(tmp_path, authorized_root=sub_dir)
    assert exc_info.value.code == "PATH_TRAVERSAL_DETECTED"
