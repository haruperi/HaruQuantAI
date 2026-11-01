"""Strategy source-code rendering, MT paths configuration, and WF calendar export.

Description:
    Implements ResultsSourceCodeService emitting compiled or formatted source
    code across target platforms (EasyLanguage, MetaTrader4, MetaTrader5,
    NinjaScript, PseudoCode, JForex, cTrader), managing MT5 terminal path
    preferences, and exporting Walk-Forward parameter schedules.

Purpose:
    FEAT-RESULTS-SOURCE-CODE: Multi-platform strategy source-code projection.

Key Capabilities:
    - FR-results-source-render: Render platform-specific strategy source code.
    - FR-results-source-mtpaths: Manage MetaTrader terminal directory paths.
    - FR-results-source-wf-calendar: Export Walk-Forward calendar schedule.

Python API Usage:
    from app.workspace.results.results_source_code import (
        ResultsSourceCodeService,
    )
    service = ResultsSourceCodeService()
    res = service.render_source_code(
        "p1", "Results", "Strat_01", target_id="MetaTrader5"
    )

CLI Usage:
    python -m app.cli results source-code --strategy-id Strat_01 --target MetaTrader5
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from app.core.host.logging import get_logger
from app.core.lib.errors import DomainError
from app.core.lib.responses import StandardResponse
from app.core.trading.results.contracts import RunResult
from app.core.trading.results.store import ResultStore
from app.workspace.results.app_results import wrap_response

logger = get_logger(__name__)

SUPPORTED_PLATFORMS: dict[str, dict[str, str]] = {
    "EasyLanguage": {
        "title": "EasyLanguage / TradeStation",
        "file_extension": ".eld",
        "scaffold": (
            "// EasyLanguage Strategy\n"
            "Inputs:\n"
            "    Period(14);\n\n"
            "Begin\n"
            "    // Strategy Logic\n"
            "End;\n"
        ),
    },
    "MetaTrader5": {
        "title": "MetaTrader 5",
        "file_extension": ".mq5",
        "scaffold": (
            "//+------------------------------------------------------------------+\n"
            "//| Expert tick function                                             |\n"
            "//+------------------------------------------------------------------+\n"
            "void OnTick() {\n"
            "    // MT5 Trading Logic\n"
            "}\n"
        ),
    },
    "NinjaScript": {
        "title": "NinjaScript",
        "file_extension": ".cs",
        "scaffold": (
            "using NinjaTrader.NinjaScript.Strategies;\n\n"
            "public class Strategy : NinjaTrader.NinjaScript.Strategies.Strategy {\n"
            "    protected override void OnBarUpdate() {\n"
            "        // NinjaScript Logic\n"
            "    }\n"
            "}\n"
        ),
    },
    "PseudoCode": {
        "title": "PseudoCode",
        "file_extension": ".txt",
        "scaffold": (
            "Strategy Rules:\n"
            "Long Entry:\n"
            "    When Indicator > Threshold\n"
            "Short Entry:\n"
            "    When Indicator < Threshold\n"
        ),
    },
    "JForex": {
        "title": "JForex",
        "file_extension": ".java",
        "scaffold": (
            "import com.dukascopy.api.*;\n\n"
            "public class Strategy implements IStrategy {\n"
            "    public void onTick(Instrument instrument, ITick tick) "
            "throws JFException {\n"
            "        // JForex Logic\n"
            "    }\n"
            "}\n"
        ),
    },
    "cTrader": {
        "title": "cTrader",
        "file_extension": ".cs",
        "scaffold": (
            "using cAlgo.API;\n\n"
            "namespace cAlgo.Robots {\n"
            "    public class Strategy : Robot {\n"
            "        protected override void OnTick() {\n"
            "            // cTrader Logic\n"
            "        }\n"
            "    }\n"
            "}\n"
        ),
    },
}


@dataclass(frozen=True, slots=True)
class SourceCodeProjection:
    """Strategy source-code presentation model."""

    strategy_id: str
    target_id: str
    title: str
    file_extension: str
    param_style: str
    code: str

    def to_dict(self) -> dict[str, Any]:
        """Convert projection to dictionary."""
        return {
            "strategy_id": self.strategy_id,
            "target_id": self.target_id,
            "title": self.title,
            "file_extension": self.file_extension,
            "param_style": self.param_style,
            "code": self.code,
        }


@dataclass(frozen=True, slots=True)
class MTPathsConfig:
    """MetaTrader 5 terminal directory preferences."""

    mt5_terminal_dir: str

    def to_dict(self) -> dict[str, Any]:
        """Convert config to dictionary."""
        return {
            "mt5_terminal_dir": self.mt5_terminal_dir,
        }


class ResultsSourceCodeService:
    """Service providing source-code rendering, MT configuration, and WF calendar."""

    def __init__(self, store: ResultStore | None = None) -> None:
        """Initialize service with optional ResultStore."""
        self.store = store
        self._in_memory_results: dict[str, RunResult] = {}
        self._mt_paths = MTPathsConfig(
            mt5_terminal_dir="",
        )

    def register_in_memory_result(self, result: RunResult) -> None:
        """Register candidate result in memory."""
        self._in_memory_results[result.strategy_id] = result

    def _resolve_result(self, strategy_id: str) -> RunResult:
        if strategy_id in self._in_memory_results:
            return self._in_memory_results[strategy_id]
        if self.store is not None:
            try:
                return self.store.get_result(strategy_id)
            except DomainError:
                pass
        raise DomainError(
            code="RESULTS_STRATEGY_NOT_FOUND",
            message=f"Strategy '{strategy_id}' not found",
            details={"strategy_id": strategy_id},
        )

    def render_source_code(
        self,
        project_id: str,
        databank_name: str,
        strategy_id: str,
        *,
        target_id: str = "PseudoCode",
        param_style: Literal["PARAM_NAMES", "PARAM_VALUES"] = "PARAM_NAMES",
    ) -> StandardResponse[SourceCodeProjection]:
        """Render target platform source code for strategy."""
        logger.info(
            "FR-results-source-render: proj=%s db=%s strat=%s target=%s style=%s",
            project_id,
            databank_name,
            strategy_id,
            target_id,
            param_style,
        )
        if target_id not in SUPPORTED_PLATFORMS:
            raise DomainError(
                code="RESULTS_UNKNOWN_SOURCE_TARGET",
                message=f"Unknown source code target '{target_id}'",
                details={"target_id": target_id},
            )

        run_res = self._resolve_result(strategy_id)
        platform_info = SUPPORTED_PLATFORMS[target_id]

        # Use stored source code if available, otherwise scaffold
        raw_source = run_res.strategy_payload.get(
            f"source_{target_id}",
            run_res.strategy_payload.get("source_code", platform_info["scaffold"]),
        )
        code_str = str(raw_source)

        projection = SourceCodeProjection(
            strategy_id=strategy_id,
            target_id=target_id,
            title=platform_info["title"],
            file_extension=platform_info["file_extension"],
            param_style=param_style,
            code=code_str,
        )

        return wrap_response(
            request_id=f"req_{strategy_id}_source_{target_id}",
            data=projection,
            json_payload=projection.to_dict(),
        )

    def get_mt_paths(self) -> StandardResponse[MTPathsConfig]:
        """Get current MT5 directory paths configuration."""
        logger.info("FR-results-source-mtpaths: retrieved MT terminal directory paths")
        return wrap_response(
            request_id="req_get_mt_paths",
            data=self._mt_paths,
            json_payload=self._mt_paths.to_dict(),
        )

    def save_mt_paths(self, config: MTPathsConfig) -> StandardResponse[MTPathsConfig]:
        """Save updated MT5 directory paths configuration."""
        self._mt_paths = config
        logger.info(
            "FR-results-source-mtpaths: saved MT paths mt5='%s'",
            config.mt5_terminal_dir,
        )
        return wrap_response(
            request_id="req_save_mt_paths",
            data=self._mt_paths,
            json_payload=self._mt_paths.to_dict(),
        )

    def export_wf_calendar(
        self,
        project_id: str,
        databank_name: str,
        strategy_id: str,
    ) -> StandardResponse[str]:
        """Export Walk-Forward schedule calendar table as CSV."""
        logger.info(
            "FR-results-source-wf-calendar: proj=%s db=%s strat=%s",
            project_id,
            databank_name,
            strategy_id,
        )
        run_res = self._resolve_result(strategy_id)
        wf_schedule = run_res.strategy_payload.get(
            "wf_schedule", run_res.parameters.get("wf_schedule")
        )

        if not isinstance(wf_schedule, (list, tuple)) or not wf_schedule:
            raise DomainError(
                code="RESULTS_WF_RESULT_REQUIRED",
                message=(
                    f"Strategy '{strategy_id}' does not contain a Walk-Forward schedule"
                ),
                details={"strategy_id": strategy_id},
            )

        lines = ["RunIndex,StartDate,EndDate,NetProfit,Parameters"]
        for idx, item in enumerate(wf_schedule, start=1):
            if isinstance(item, dict):
                s_date = str(item.get("start_date", ""))
                e_date = str(item.get("end_date", ""))
                np = str(item.get("net_profit", 0.0))
                params = str(item.get("params", ""))
                lines.append(f"{idx},{s_date},{e_date},{np},{params}")

        csv_content = "\n".join(lines) + "\n"
        return wrap_response(
            request_id=f"req_{strategy_id}_wf_calendar",
            data=csv_content,
            json_payload={"csv": csv_content},
        )
