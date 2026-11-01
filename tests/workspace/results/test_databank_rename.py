"""Unit tests for DatabankRenameService."""

from __future__ import annotations

from app.core.trading.results.contracts import RunResult
from app.workspace.results.databank_rename import (
    DatabankRenameReceipt,
    DatabankRenameRequest,
    DatabankRenameService,
)


def _create_dummy_result(strategy_id: str, strategy_name: str) -> RunResult:
    return RunResult(
        result_id=f"res_{strategy_id}",
        databank_id="Results",
        strategy_id=strategy_id,
        strategy_name=strategy_name,
    )


class TestDatabankRenameService:
    """Test suite for DatabankRenameService."""

    def test_golden_fixture_rename(self) -> None:
        """Verify batch renaming with prefix, start_number, digits, and separator."""
        service = DatabankRenameService()
        r1 = _create_dummy_result("id_1", "OldName1")
        r2 = _create_dummy_result("id_2", "OldName2")
        service.register_in_memory_result(r1)
        service.register_in_memory_result(r2)

        req = DatabankRenameRequest(
            project_id="proj_1",
            databank_name="Results",
            strategy_ids=("id_1", "id_2"),
            prefix="Strat_",
            start_number=5,
            digits=3,
            separator="",
        )
        resp = service.rename_strategies(req)
        receipt = resp.data

        assert receipt.renamed == (("id_1", "Strat_005"), ("id_2", "Strat_006"))
        assert len(receipt.skipped) == 0
        assert service._in_memory_results["id_1"].strategy_name == "Strat_005"
        assert service._in_memory_results["id_2"].strategy_name == "Strat_006"

    def test_rename_with_missing_strategies(self) -> None:
        """Verify missing strategy IDs are recorded in skipped without aborting."""
        service = DatabankRenameService()
        r1 = _create_dummy_result("id_1", "OldName1")
        service.register_in_memory_result(r1)

        req = DatabankRenameRequest(
            project_id="proj_1",
            databank_name="Results",
            strategy_ids=("id_1", "id_missing"),
            prefix="Strategy ",
            start_number=1,
            digits=1,
            separator="",
        )
        resp = service.rename_strategies(req)
        receipt = resp.data

        assert receipt.renamed == (("id_1", "Strategy 1"),)
        assert receipt.skipped == (("id_missing", "NOT_FOUND"),)

    def test_to_dict_serialization(self) -> None:
        """Verify request and receipt dictionary serialization."""
        req = DatabankRenameRequest(
            project_id="p1", databank_name="DB", strategy_ids=("s1",)
        )
        d_req = req.to_dict()
        assert d_req["databank_name"] == "DB"

        receipt = DatabankRenameReceipt(
            renamed=(("s1", "New1"),),
            skipped=(),
            revision=2,
        )
        d_rec = receipt.to_dict()
        assert d_rec["revision"] == 2
        assert d_rec["renamed"] == [["s1", "New1"]]
