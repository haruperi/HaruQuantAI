"""Unit tests for SettingsBlocks service and models."""

from __future__ import annotations

import pytest
from app.core.lib.errors import DomainError
from app.workspace.builder.settings_blocks import (
    BlocksSelectionSettings,
    BuildingBlockSelection,
    SettingsBlocksService,
)


def test_xml_roundtrip_golden_fixture() -> None:
    """Verify save_to_xml and load_from_xml round-trip identically."""
    service = SettingsBlocksService()
    initial_selections = (
        BuildingBlockSelection(
            block_id="indicator.rsi", category="INDICATORS", enabled=True, weight=3
        ),
        BuildingBlockSelection(
            block_id="signal.crosses_above", category="SIGNALS", enabled=False, weight=1
        ),
        BuildingBlockSelection(
            block_id="exit.trailing_stop", category="EXIT_TYPES", enabled=True, weight=2
        ),
    )
    settings = BlocksSelectionSettings(selections=initial_selections)

    xml_text = service.save_to_xml(settings)
    loaded = service.load_from_xml(xml_text)

    assert len(loaded.selections) == 3
    assert loaded.selections[0].block_id == "indicator.rsi"
    assert loaded.selections[0].weight == 3
    assert loaded.selections[0].enabled is True
    assert loaded.selections[1].enabled is False
    assert loaded.selections[2].block_id == "exit.trailing_stop"
    assert loaded.selections[2].weight == 2


def test_disabling_all_exits_raises_min_blocks_required() -> None:
    """Ensure disabling all exit blocks raises BUILDER_MIN_BLOCKS_REQUIRED."""
    service = SettingsBlocksService()
    selections = (
        BuildingBlockSelection(
            block_id="indicator.rsi", category="INDICATORS", enabled=True, weight=1
        ),
        BuildingBlockSelection(
            block_id="exit.time_limit", category="EXIT_TYPES", enabled=False, weight=1
        ),
    )

    with pytest.raises(DomainError) as exc:
        service.update_selections(selections)
    assert exc.value.code == "BUILDER_MIN_BLOCKS_REQUIRED"


def test_disabling_all_entries_raises_min_blocks_required() -> None:
    """Ensure disabling all entry blocks raises BUILDER_MIN_BLOCKS_REQUIRED."""
    service = SettingsBlocksService()
    selections = (
        BuildingBlockSelection(
            block_id="indicator.rsi", category="INDICATORS", enabled=False, weight=1
        ),
        BuildingBlockSelection(
            block_id="exit.time_limit", category="EXIT_TYPES", enabled=True, weight=1
        ),
    )

    with pytest.raises(DomainError) as exc:
        service.update_selections(selections)
    assert exc.value.code == "BUILDER_MIN_BLOCKS_REQUIRED"


def test_invalid_weight_raises() -> None:
    """Ensure weight < 1 raises BUILDER_INVALID_BLOCK_WEIGHT."""
    service = SettingsBlocksService()
    selections = (
        BuildingBlockSelection(
            block_id="indicator.rsi", category="INDICATORS", enabled=True, weight=0
        ),
        BuildingBlockSelection(
            block_id="exit.time_limit", category="EXIT_TYPES", enabled=True, weight=1
        ),
    )

    with pytest.raises(DomainError) as exc:
        service.update_selections(selections)
    assert exc.value.code == "BUILDER_INVALID_BLOCK_WEIGHT"


def test_invalid_xml_raises() -> None:
    """Ensure malformed XML raises BUILDER_INVALID_BLOCKS_XML."""
    service = SettingsBlocksService()
    with pytest.raises(DomainError) as exc:
        service.load_from_xml("<<not-valid-xml>>")
    assert exc.value.code == "BUILDER_INVALID_BLOCKS_XML"


def test_list_blocks() -> None:
    """Verify list_blocks returns StandardResponse with settings."""
    service = SettingsBlocksService()
    res = service.list_blocks()
    assert res.request_id == "blocks-list"
    assert len(res.data.selections) > 0
    assert res.data.to_dict()["selections"]
