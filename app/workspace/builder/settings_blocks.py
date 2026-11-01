"""Building blocks configuration, validation, and XML serialization service.

Description:
    Manages the Building Blocks configuration tab in the Builder workspace,
    specifying which technical indicators, entry signals, order types,
    stop/limit blocks, and exit rules are enabled during candidate generation,
    along with their respective sampling weights and custom parameter constraints.

Purpose:
    FEAT-BUILDER-SETTINGS-BLOCKS: Configure building blocks search space
    and sampling weights.

Key Capabilities:
    - FR-builder-blocks-selection: Typed data models for building block
      selections.
    - FR-builder-blocks-validation: Enforce weight bounds and minimum entry/exit
      block requirements.
    - FR-builder-blocks-xml: Round-trip XML serialization and parsing for block
      preset files.

Python API Usage:
    from app.workspace.builder.settings_blocks import (
        BlocksSelectionSettings,
        SettingsBlocksService,
    )
    service = SettingsBlocksService()
    blocks = service.list_blocks()

CLI Usage:
    python -c "from app.workspace.builder.settings_blocks import (
        SettingsBlocksService,
    ); print(1)"
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, Literal

from app.core.host.logging import get_logger
from app.core.lib.errors import DomainError
from app.core.lib.responses import StandardResponse
from app.workspace.builder.common import wrap_response

logger = get_logger(__name__)

_MIN_WEIGHT: int = 1

BlockCategory = Literal[
    "SIGNALS", "INDICATORS", "STOP_LIMIT_BLOCKS", "ORDER_TYPES", "EXIT_TYPES"
]


@dataclass(frozen=True, slots=True)
class BuildingBlockSelection:
    """Selection and sampling configuration for a single building block."""

    block_id: str
    category: BlockCategory
    enabled: bool = True
    weight: int = 1
    custom_params: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert selection to dictionary."""
        return {
            "block_id": self.block_id,
            "category": self.category,
            "enabled": self.enabled,
            "weight": self.weight,
            "custom_params": dict(self.custom_params),
        }


def _build_default_selections() -> tuple[BuildingBlockSelection, ...]:
    """Build default catalog of building blocks across categories."""
    return (
        BuildingBlockSelection(
            block_id="indicator.rsi", category="INDICATORS", enabled=True, weight=1
        ),
        BuildingBlockSelection(
            block_id="indicator.ema", category="INDICATORS", enabled=True, weight=1
        ),
        BuildingBlockSelection(
            block_id="signal.crosses_above", category="SIGNALS", enabled=True, weight=1
        ),
        BuildingBlockSelection(
            block_id="signal.crosses_below", category="SIGNALS", enabled=True, weight=1
        ),
        BuildingBlockSelection(
            block_id="order.market", category="ORDER_TYPES", enabled=True, weight=1
        ),
        BuildingBlockSelection(
            block_id="order.stop", category="ORDER_TYPES", enabled=True, weight=1
        ),
        BuildingBlockSelection(
            block_id="stop_limit.fixed_pips",
            category="STOP_LIMIT_BLOCKS",
            enabled=True,
            weight=1,
        ),
        BuildingBlockSelection(
            block_id="exit.time_limit", category="EXIT_TYPES", enabled=True, weight=1
        ),
        BuildingBlockSelection(
            block_id="exit.trailing_stop", category="EXIT_TYPES", enabled=True, weight=1
        ),
    )


@dataclass(frozen=True, slots=True)
class BlocksSelectionSettings:
    """Settings collection of building block selections."""

    selections: tuple[BuildingBlockSelection, ...] = field(
        default_factory=_build_default_selections
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert settings to dictionary."""
        return {"selections": [s.to_dict() for s in self.selections]}


class SettingsBlocksService:
    """Service managing building block selections, validation, and XML presets."""

    def __init__(self, initial_settings: BlocksSelectionSettings | None = None) -> None:
        """Initialize service with optional initial block selections."""
        self._settings = initial_settings or BlocksSelectionSettings()

    def list_blocks(self) -> StandardResponse[BlocksSelectionSettings]:
        """List active building block selections.

        Returns:
            StandardResponse containing BlocksSelectionSettings.
        """
        logger.debug(
            "Listing %d building block selections", len(self._settings.selections)
        )
        return wrap_response(
            request_id="blocks-list",
            data=self._settings,
            json_payload=self._settings.to_dict(),
        )

    def update_selections(
        self,
        selections: Sequence[BuildingBlockSelection],
    ) -> StandardResponse[BlocksSelectionSettings]:
        """Update and validate building block selections.

        Args:
            selections: Sequence of proposed BuildingBlockSelection items.

        Returns:
            StandardResponse containing updated BlocksSelectionSettings.

        Raises:
            DomainError: If weights are invalid or minimum required blocks are absent.
        """
        logger.debug("Updating %d building block selections", len(selections))
        self._validate_selections(selections)

        new_settings = BlocksSelectionSettings(selections=tuple(selections))
        self._settings = new_settings
        return wrap_response(
            request_id="blocks-update",
            data=new_settings,
            json_payload=new_settings.to_dict(),
        )

    def save_to_xml(self, settings: BlocksSelectionSettings) -> str:
        """Serialize block selection settings to XML string.

        Args:
            settings: BlocksSelectionSettings to serialize.

        Returns:
            XML string representation.
        """
        logger.debug("Serializing %d block selections to XML", len(settings.selections))
        root = ET.Element("BuildingBlocksSettings")

        for sel in settings.selections:
            b_elem = ET.SubElement(
                root,
                "Block",
                id=sel.block_id,
                category=sel.category,
                enabled=str(sel.enabled).lower(),
                weight=str(sel.weight),
            )
            if sel.custom_params:
                params_elem = ET.SubElement(b_elem, "CustomParams")
                for k, v in sel.custom_params.items():
                    p_elem = ET.SubElement(params_elem, "Param", key=k)
                    p_elem.text = str(v)

        return ET.tostring(root, encoding="unicode")

    def load_from_xml(self, xml_text: str) -> BlocksSelectionSettings:
        """Parse XML string into validated BlocksSelectionSettings.

        Args:
            xml_text: XML content to parse.

        Returns:
            Parsed and validated BlocksSelectionSettings.

        Raises:
            DomainError: If XML is malformed or validation checks fail.
        """
        logger.debug("Parsing block selections from XML")
        try:
            root = ET.fromstring(xml_text)  # noqa: S314
        except ET.ParseError as e:
            raise DomainError(
                code="BUILDER_INVALID_BLOCKS_XML",
                message=f"Failed to parse blocks XML: {e}",
            ) from e

        selections: list[BuildingBlockSelection] = []
        for b_elem in root.findall("Block"):
            block_id = b_elem.attrib.get("id", "")
            category = b_elem.attrib.get("category", "INDICATORS")
            enabled = b_elem.attrib.get("enabled", "true").lower() == "true"
            weight = int(b_elem.attrib.get("weight", "1"))

            custom_params: dict[str, Any] = {}
            params_elem = b_elem.find("CustomParams")
            if params_elem is not None:
                for p in params_elem.findall("Param"):
                    key = p.attrib.get("key", "")
                    if key:
                        custom_params[key] = p.text or ""

            selections.append(
                BuildingBlockSelection(
                    block_id=block_id,
                    category=category,  # type: ignore[arg-type]
                    enabled=enabled,
                    weight=weight,
                    custom_params=custom_params,
                )
            )

        self._validate_selections(selections)
        return BlocksSelectionSettings(selections=tuple(selections))

    def _validate_selections(
        self, selections: Sequence[BuildingBlockSelection]
    ) -> None:
        """Validate block selection requirements and constraints."""
        has_entry = False
        has_exit = False

        for sel in selections:
            if sel.weight < _MIN_WEIGHT:
                raise DomainError(
                    code="BUILDER_INVALID_BLOCK_WEIGHT",
                    message=(
                        f"Block '{sel.block_id}' weight must be >= 1 (got {sel.weight})"
                    ),
                )
            if sel.enabled:
                if sel.category in ("SIGNALS", "INDICATORS"):
                    has_entry = True
                elif sel.category == "EXIT_TYPES":
                    has_exit = True

        if not (has_entry and has_exit):
            raise DomainError(
                code="BUILDER_MIN_BLOCKS_REQUIRED",
                message=(
                    "At least one entry block (SIGNALS or INDICATORS) and at least one "
                    "EXIT_TYPES block must remain enabled"
                ),
            )
