"""Unit tests for CustomDatabankActionsService."""

from __future__ import annotations

import pytest
from app.core.lib.errors import DomainError
from app.workspace.results.custom_databank_actions import (
    CustomDatabankActionsService,
    DatabankTabOrderReceipt,
)


class TestCustomDatabankActionsService:
    """Test suite for CustomDatabankActionsService."""

    def test_golden_fixture_reorder_and_protection(self) -> None:
        """Verify reorder left/right and protected system databank deletion rejection."""
        service = CustomDatabankActionsService(
            initial_databanks=("Results", "CustomA", "CustomB")
        )

        resp = service.move_left("proj_1", "CustomB")
        assert resp.data.databank_names == ("Results", "CustomB", "CustomA")
        assert resp.data.active_databank == "CustomB"

        with pytest.raises(DomainError) as exc_info:
            service.delete_databank("proj_1", "Results")
        assert exc_info.value.code == "RESULTS_SYSTEM_DATABANK_PROTECTED"

    def test_move_right_and_move_to_position(self) -> None:
        """Verify move right and move to explicit index."""
        service = CustomDatabankActionsService(
            initial_databanks=("Results", "CustomA", "CustomB")
        )
        resp1 = service.move_right("proj_1", "CustomA")
        assert resp1.data.databank_names == ("Results", "CustomB", "CustomA")

        resp2 = service.move_to_position("proj_1", "CustomB", target_index=0)
        assert resp2.data.databank_names == ("CustomB", "Results", "CustomA")

    def test_out_of_range_position(self) -> None:
        """Verify out-of-range position raises DomainError."""
        service = CustomDatabankActionsService(initial_databanks=("Results", "CustomA"))
        with pytest.raises(DomainError) as exc_info:
            service.move_to_position("proj_1", "CustomA", target_index=5)
        assert exc_info.value.code == "RESULTS_DATABANK_INDEX_OUT_OF_RANGE"

    def test_delete_custom_databank(self) -> None:
        """Verify deleting custom databank updates list and active."""
        service = CustomDatabankActionsService(initial_databanks=("Results", "CustomA"))
        resp = service.delete_databank("proj_1", "CustomA")
        assert resp.data.databank_names == ("Results",)

    def test_receipt_to_dict(self) -> None:
        """Verify DatabankTabOrderReceipt to_dict."""
        receipt = DatabankTabOrderReceipt(
            project_id="p1",
            databank_names=("Results",),
            active_databank="Results",
            revision=1,
        )
        d = receipt.to_dict()
        assert d["project_id"] == "p1"
        assert d["databank_names"] == ["Results"]
