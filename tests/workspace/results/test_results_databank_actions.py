"""Unit tests for ResultsDatabankActionsService."""

from __future__ import annotations

import pytest
from app.core.lib.errors import DomainError
from app.core.trading.results.contracts import RunResult
from app.workspace.results.results_databank_actions import (
    DatabankMutationReceipt,
    ResultsDatabankActionsService,
)


def _create_strategy_result(
    strategy_id: str, name: str, net_profit: float
) -> RunResult:
    return RunResult(
        result_id=f"res_{strategy_id}",
        databank_id="Results",
        strategy_id=strategy_id,
        strategy_name=name,
        metrics={"net_profit": net_profit, "profit_factor": 1.5},
        trades=(
            {"ticket": 1, "profit_loss": net_profit / 2.0},
            {"ticket": 2, "profit_loss": net_profit / 2.0},
        ),
        parameters={"period": 14, "stop": 50},
    )


class TestResultsDatabankActionsService:
    """Test suite for ResultsDatabankActionsService."""

    def test_golden_fixture_portfolio_merge_and_split(self) -> None:
        """Verify merging 2 strategies into Portfolio and splitting back."""
        service = ResultsDatabankActionsService()
        s1 = _create_strategy_result("S1", "Strat1", 500.0)
        s2 = _create_strategy_result("S2", "Strat2", 300.0)
        service.register_in_memory_result(s1, "Results")
        service.register_in_memory_result(s2, "Results")

        port_id = service.merge_portfolio("p1", "Results", ("S1", "S2"))
        port_res = service._in_memory_results[port_id]
        assert port_res.metrics["net_profit"] == 800.0
        assert len(port_res.trades) == 4

        constituents = service.split_portfolio("p1", "Results", port_id)
        assert constituents == ("S1", "S2")

    def test_portfolio_merge_min_strategies_validation(self) -> None:
        """Verify merge requires at least 2 strategies."""
        service = ResultsDatabankActionsService()
        with pytest.raises(DomainError) as exc_info:
            service.merge_portfolio("p1", "Results", ("S1",))
        assert exc_info.value.code == "RESULTS_PORTFOLIO_MIN_STRATEGIES"

    def test_clear_all_and_delete(self) -> None:
        """Verify clear_all and delete_strategies actions."""
        service = ResultsDatabankActionsService()
        s1 = _create_strategy_result("S1", "Strat1", 100.0)
        s2 = _create_strategy_result("S2", "Strat2", -50.0)
        service.register_in_memory_result(s1, "Results")
        service.register_in_memory_result(s2, "Results")

        del_receipt = service.delete_strategies("p1", "Results", ("S1",))
        assert del_receipt.affected_count == 1
        assert "S1" not in service._in_memory_results

        clear_receipt = service.clear_all("p1", "Results")
        assert clear_receipt.affected_count == 1
        assert len(service._databank_members["Results"]) == 0

    def test_select_by_filter(self) -> None:
        """Verify selecting passed and failed strategies."""
        service = ResultsDatabankActionsService()
        s1 = _create_strategy_result("S1", "Strat1", 100.0)
        s2 = _create_strategy_result("S2", "Strat2", -50.0)
        service.register_in_memory_result(s1, "Results")
        service.register_in_memory_result(s2, "Results")

        passed = service.select_by_filter("p1", "Results", "PASSED")
        assert passed == ("S1",)

        failed = service.select_by_filter("p1", "Results", "FAILED")
        assert failed == ("S2",)

    def test_parameters_and_notes(self) -> None:
        """Verify get/set parameters and notes."""
        service = ResultsDatabankActionsService()
        s1 = _create_strategy_result("S1", "Strat1", 100.0)
        service.register_in_memory_result(s1, "Results")

        params = service.get_strategy_parameters("p1", "Results", "S1")
        assert params["period"] == 14

        service.set_strategy_parameters("p1", "Results", "S1", {"period": 21})
        assert service.get_strategy_parameters("p1", "Results", "S1")["period"] == 21

        service.set_note("p1", "Results", "S1", "My Note")
        assert service._in_memory_results["S1"].metrics["note"] == "My Note"

    def test_compare_and_export_csv(self) -> None:
        """Verify compare_strategies and export_databank_csv."""
        service = ResultsDatabankActionsService()
        s1 = _create_strategy_result("S1", "Strat1", 200.0)
        service.register_in_memory_result(s1, "Results")

        comp = service.compare_strategies("p1", "Results", ("S1",))
        assert comp["S1"]["strategy_name"] == "Strat1"
        assert comp["S1"]["net_profit"] == 200.0

        csv_text = service.export_databank_csv(
            "p1", "Results", ("ResultsName", "net_profit")
        )
        lines = csv_text.strip().split("\n")
        assert len(lines) == 2
        assert lines[0] == "ResultsName,net_profit"
        assert lines[1] == "Strat1,200.0"

    def test_receipt_to_dict(self) -> None:
        """Verify DatabankMutationReceipt to_dict."""
        receipt = DatabankMutationReceipt(
            project_id="p1",
            databank_name="Results",
            affected_count=2,
            strategy_ids=("s1", "s2"),
            action="TEST",
            revision=1,
        )
        d = receipt.to_dict()
        assert d["affected_count"] == 2
        assert d["strategy_ids"] == ["s1", "s2"]
