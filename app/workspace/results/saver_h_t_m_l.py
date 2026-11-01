"""Standalone HTML strategy report exporter service.

Description:
    Implements SaverHTMLService compiling strategy metadata, Overview
    metrics, Monthly performance, and trade lists into a deterministic,
    self-contained UTF-8 HTML document.

Purpose:
    FEAT-RESULTS-SAVER-HTML: Self-contained HTML report exporter.

Key Capabilities:
    - FR-results-saver-html: Export strategy report to standalone HTML.

Python API Usage:
    from app.workspace.results.saver_h_t_m_l import SaverHTMLService
    service = SaverHTMLService()
    receipt = service.export_strategy_html("p1", "Results", "Strat_01")

CLI Usage:
    python -m app.cli results export-html --strategy-id Strat_01
"""

from __future__ import annotations

import html

from app.core.host.logging import get_logger
from app.core.lib.errors import DomainError
from app.core.trading.results.contracts import RunResult
from app.core.trading.results.store import ResultStore
from app.workspace.results.saver_s_q3 import ExportArtifactReceipt

logger = get_logger(__name__)


class SaverHTMLService:
    """Service exporting strategy backtest results to HTML reports."""

    def __init__(self, store: ResultStore | None = None) -> None:
        """Initialize service with optional ResultStore."""
        self.store = store
        self._in_memory_results: dict[str, RunResult] = {}

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
            message=f"Strategy '{strategy_id}' not found for HTML export",
            details={"strategy_id": strategy_id},
        )

    def export_strategy_html(
        self,
        project_id: str,
        databank_name: str,
        strategy_id: str,
        *,
        result_key: str = "Main",
        include_trades: bool = True,
    ) -> ExportArtifactReceipt:
        """Export self-contained UTF-8 HTML report."""
        logger.info(
            "FR-results-saver-html: exporting proj=%s db=%s strat=%s key=%s",
            project_id,
            databank_name,
            strategy_id,
            result_key,
        )
        run_res = self._resolve_result(strategy_id)
        name = run_res.strategy_name or strategy_id
        safe_name = html.escape(name)
        safe_proj = html.escape(project_id)
        safe_db = html.escape(databank_name)

        # Overview rows
        metrics_rows: list[str] = []
        for k, v in sorted(run_res.metrics.items()):
            metrics_rows.append(
                f"<tr><td>{html.escape(str(k))}</td><td>{html.escape(str(v))}</td></tr>"
            )

        # Trades table
        trades_section = ""
        if include_trades and run_res.trades:
            trade_rows: list[str] = []
            for t in run_res.trades:
                ticket = html.escape(str(t.get("ticket", "")))
                dir_str = html.escape(str(t.get("type", t.get("direction", ""))))
                pl = html.escape(str(t.get("profit_loss", t.get("pnl", ""))))
                trade_rows.append(
                    f"<tr><td>{ticket}</td><td>{dir_str}</td><td>{pl}</td></tr>"
                )
            trades_section = (
                "<h2>Executed Trades</h2>\n"
                "<table>\n"
                "<thead><tr><th>Ticket</th><th>Type</th><th>Profit/Loss</th></tr></thead>\n"
                f"<tbody>\n{''.join(trade_rows)}\n</tbody>\n"
                "</table>\n"
            )

        doc = (
            "<!DOCTYPE html>\n"
            '<html lang="en">\n'
            "<head>\n"
            '<meta charset="utf-8"/>\n'
            f"<title>{safe_name} Report</title>\n"
            "<style>\n"
            "body { font-family: sans-serif; margin: 20px; "
            "background: #fff; color: #222; }\n"
            "h1, h2 { color: #1a365d; }\n"
            "table { border-collapse: collapse; width: 100%; "
            "margin-bottom: 24px; }\n"
            "th, td { border: 1px solid #cbd5e0; padding: 8px 12px; "
            "text-align: left; }\n"
            "th { background: #edf2f7; }\n"
            "</style>\n"
            "</head>\n"
            "<body>\n"
            f"<h1>Strategy Report: {safe_name}</h1>\n"
            f"<p>Project: {safe_proj} | Databank: {safe_db} | "
            f"Key: {html.escape(result_key)}</p>\n"
            "<h2>Key Metrics</h2>\n"
            "<table>\n"
            "<thead><tr><th>Metric</th><th>Value</th></tr></thead>\n"
            f"<tbody>\n{''.join(metrics_rows)}\n</tbody>\n"
            "</table>\n"
            f"{trades_section}"
            "</body>\n"
            "</html>\n"
        )

        content_bytes = doc.encode("utf-8")
        logger.info(
            "FR-results-saver-html: emitted %s.html (%d bytes)",
            name,
            len(content_bytes),
        )

        return ExportArtifactReceipt(
            filename=f"{name}.html",
            mime_type="text/html; charset=utf-8",
            size_bytes=len(content_bytes),
            content_bytes=content_bytes,
        )
