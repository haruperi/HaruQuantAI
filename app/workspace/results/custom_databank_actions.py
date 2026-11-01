"""Custom databank reordering and deletion service.

Description:
    Implements CustomDatabankActionsService allowing users to reorder
    databank tabs (move left, move right, move to position) and delete
    custom user databanks while protecting system databanks.

Purpose:
    FEAT-RESULTS-CUSTOM-DATABANK: Databank tab ordering and lifecycle actions.

Key Capabilities:
    - FR-results-databank-tab-order: Reorder and delete databanks with protection.

Python API Usage:
    from app.workspace.results.custom_databank_actions import (
        CustomDatabankActionsService,
    )
    service = CustomDatabankActionsService()
    receipt = service.move_left("proj_1", "CustomA")

CLI Usage:
    python -m app.cli results databank reorder --name CustomA --dir left
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.core.host.logging import get_logger
from app.core.lib.errors import DomainError
from app.core.lib.responses import StandardResponse
from app.workspace.results.app_results import wrap_response

logger = get_logger(__name__)

PROTECTED_SYSTEM_DATABANKS = frozenset({"Results", "Last generation"})


@dataclass(frozen=True, slots=True)
class DatabankTabOrderReceipt:
    """Receipt showing active databank tab arrangement and revision."""

    project_id: str
    databank_names: tuple[str, ...]
    active_databank: str
    revision: int

    def to_dict(self) -> dict[str, Any]:
        """Convert tab order receipt to dictionary."""
        return {
            "project_id": self.project_id,
            "databank_names": list(self.databank_names),
            "active_databank": self.active_databank,
            "revision": self.revision,
        }


class CustomDatabankActionsService:
    """Service managing databank tab order and lifecycle."""

    def __init__(self, initial_databanks: tuple[str, ...] | None = None) -> None:
        """Initialize service with default or specified databanks."""
        self._databanks: list[str] = (
            list(initial_databanks)
            if initial_databanks is not None
            else ["Results", "Last generation"]
        )
        self._active: str = self._databanks[0] if self._databanks else "Results"
        self._revision: int = 1

    def _find_index(self, databank_name: str) -> int:
        try:
            return self._databanks.index(databank_name)
        except ValueError as err:
            raise DomainError(
                code="RESULTS_DATABANK_NOT_FOUND",
                message=f"Databank '{databank_name}' not found",
                details={"databank_name": databank_name},
            ) from err

    def move_left(
        self, project_id: str, databank_name: str
    ) -> StandardResponse[DatabankTabOrderReceipt]:
        """Move specified databank one position to the left if possible."""
        idx = self._find_index(databank_name)
        if idx > 0:
            self._databanks[idx - 1], self._databanks[idx] = (
                self._databanks[idx],
                self._databanks[idx - 1],
            )
            self._revision += 1
            logger.info(
                "FR-results-databank-tab-order: moved '%s' left to index %d",
                databank_name,
                idx - 1,
            )
        self._active = databank_name
        return self._make_response(project_id)

    def move_right(
        self, project_id: str, databank_name: str
    ) -> StandardResponse[DatabankTabOrderReceipt]:
        """Move specified databank one position to the right if possible."""
        idx = self._find_index(databank_name)
        if idx < len(self._databanks) - 1:
            self._databanks[idx], self._databanks[idx + 1] = (
                self._databanks[idx + 1],
                self._databanks[idx],
            )
            self._revision += 1
            logger.info(
                "FR-results-databank-tab-order: moved '%s' right to index %d",
                databank_name,
                idx + 1,
            )
        self._active = databank_name
        return self._make_response(project_id)

    def move_to_position(
        self, project_id: str, databank_name: str, target_index: int
    ) -> StandardResponse[DatabankTabOrderReceipt]:
        """Move specified databank to an explicit target index."""
        if target_index < 0 or target_index >= len(self._databanks):
            max_idx = len(self._databanks) - 1
            raise DomainError(
                code="RESULTS_DATABANK_INDEX_OUT_OF_RANGE",
                message=f"Target index {target_index} out of range [0, {max_idx}]",
                details={"target_index": target_index, "length": len(self._databanks)},
            )
        idx = self._find_index(databank_name)
        if idx != target_index:
            item = self._databanks.pop(idx)
            self._databanks.insert(target_index, item)
            self._revision += 1
            logger.info(
                "FR-results-databank-tab-order: moved '%s' to index %d",
                databank_name,
                target_index,
            )
        self._active = databank_name
        return self._make_response(project_id)

    def delete_databank(
        self, project_id: str, databank_name: str
    ) -> StandardResponse[DatabankTabOrderReceipt]:
        """Delete custom databank, protecting built-in system databanks."""
        if databank_name in PROTECTED_SYSTEM_DATABANKS:
            raise DomainError(
                code="RESULTS_SYSTEM_DATABANK_PROTECTED",
                message=f"Cannot delete protected system databank '{databank_name}'",
                details={"databank_name": databank_name},
            )
        idx = self._find_index(databank_name)
        self._databanks.pop(idx)
        self._revision += 1
        logger.info(
            "FR-results-databank-tab-order: deleted databank '%s'",
            databank_name,
        )
        if self._active == databank_name:
            self._active = self._databanks[0] if self._databanks else "Results"
        return self._make_response(project_id)

    def _make_response(
        self, project_id: str
    ) -> StandardResponse[DatabankTabOrderReceipt]:
        receipt = DatabankTabOrderReceipt(
            project_id=project_id,
            databank_names=tuple(self._databanks),
            active_databank=self._active,
            revision=self._revision,
        )
        return wrap_response(
            request_id=f"req_{project_id}_databank_tab_order",
            data=receipt,
            json_payload=receipt.to_dict(),
            revision=self._revision,
        )
