"""Test identity between legacy bridge paths and canonical core trading block contracts."""

from __future__ import annotations

import app.core.trading.blocks.base as new_base
import app.core.trading.blocks.metadata as new_meta
import app.include.blocks.base as old_base
import app.include.blocks.metadata as old_meta


def test_old_and_new_contracts_are_identical() -> None:
    """Verify that importing old and new contract paths returns identical objects."""
    assert old_base.BaseBlock is new_base.BaseBlock
    assert old_base.block is new_base.block
    assert old_meta.BlockSpec is new_meta.BlockSpec
    assert old_meta.ExecutionKind is new_meta.ExecutionKind
    assert old_meta.PortType is new_meta.PortType
    assert old_meta._freeze_mapping is new_meta._freeze_mapping
