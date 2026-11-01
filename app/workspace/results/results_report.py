"""HTML printable summary report generation service.

Description:
    Implements ResultsReportService rendering printable strategy summary
    reports containing Overview performance statistics, monthly performance
    matrices, and trade distributions formatted as clean, escaped HTML.

Purpose:
    FEAT-RESULTS-REPORT: Printable strategy performance HTML reports.

Key Capabilities:
    - FR-results-report-html: Compose escaped HTML report with overview metrics.

Python API Usage:
    from app.workspace.results.results_report import ResultsReportService
    service = ResultsReportService()
    doc = service.render_report("proj_1", "Results", "Strat_01")

CLI Usage:
    python -m app.cli results report --strategy-id Strat_01
"""

from __future__ import annotations

import html
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from app.core.host.logging import get_logger
from app.core.lib.responses import StandardResponse
from app.core.trading.results.contracts import RunResult
from app.core.trading.results.store import ResultStore
from app.workspace.results.app_results import wrap_response
from app.workspace.results.results_overview import (
    OverviewProjection,
    ResultsOverviewService,
)

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class ResultsReportDocument:
    """Printable HTML strategy summary report document."""

    strategy_id: str
    strategy_name: str
    result_key: str
    generated_at_utc: str
    overview: OverviewProjection
    html_body: str

    def to_dict(self) -> dict[str, Any]:
        """Convert document to dictionary representation."""
        return {
            "strategy_id": self.strategy_id,
            "strategy_name": self.strategy_name,
            "result_key": self.result_key,
            "generated_at_utc": self.generated_at_utc,
            "overview": self.overview.to_dict(),
            "html_body": self.html_body,
        }


class ResultsReportService:
    """HTML report generation service."""

    def __init__(
        self,
        store: ResultStore | None = None,
        overview_service: ResultsOverviewService | None = None,
    ) -> None:
        """Initialize service with optional dependencies."""
        self.store = store
        self.overview_service = overview_service or ResultsOverviewService(store=store)

    def register_in_memory_result(self, result: RunResult) -> None:
        """Register an in-memory result candidate."""
        self.overview_service.register_in_memory_result(result)

    def render_report(
        self,
        project_id: str,
        databank_name: str,
        strategy_id: str,
        *,
        result_key: str = "Main",
        template: str | None = None,
    ) -> StandardResponse[ResultsReportDocument]:
        """Render printable HTML strategy performance report."""
        overview_resp = self.overview_service.get_overview(
            project_id,
            databank_name,
            strategy_id,
            result_key=result_key,
            template=template,
        )
        overview = overview_resp.data

        # Determine strategy name
        run_res = self.overview_service.resolve_result(strategy_id)
        raw_name = run_res.strategy_name or strategy_id
        safe_name = html.escape(raw_name)
        safe_strat_id = html.escape(strategy_id)
        now_utc = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")

        # Render HTML metrics table rows
        metrics_rows_html = "".join(
            f"<tr><td>{html.escape(m.label)}</td>"
            f"<td>{m.all_trades} {html.escape(m.unit)}</td>"
            f"<td>{m.long_trades}</td><td>{m.short_trades}</td></tr>"
            for m in overview.metrics
        )

        # Render Monthly performance rows
        monthly_rows_html = "".join(
            f"<tr><td>{r.year}</td>"
            + "".join(f"<td>{val if val is not None else '-'}</td>" for val in r.months)
            + f"<td><strong>{r.ytd_money}</strong></td>"
            f"<td><strong>{r.ytd_pct}%</strong></td></tr>"
            for r in overview.monthly_matrix
        )

        css_style = (
            "body { font-family: sans-serif; margin: 20px; }\n"
            "table { border-collapse: collapse; width: 100%; margin-bottom: 24px; }\n"
            "th, td { border: 1px solid #dadce0; padding: 8px 12px; "
            "text-align: right; }\n"
            "th:first-child, td:first-child { text-align: left; }\n"
            "th { background-color: #f8f9fa; }"
        )

        month_headers = (
            "<tr><th>Year</th><th>Jan</th><th>Feb</th><th>Mar</th><th>Apr</th>"
            "<th>May</th><th>Jun</th><th>Jul</th><th>Aug</th><th>Sep</th>"
            "<th>Oct</th><th>Nov</th><th>Dec</th><th>YTD ($)</th><th>YTD (%)</th></tr>"
        )

        html_body = (
            '<!DOCTYPE html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
            f"<title>Performance Report - {safe_name}</title>\n"
            f"<style>\n{css_style}\n</style>\n</head>\n<body>\n"
            f"<h1>Strategy Performance: {safe_name}</h1>\n"
            f"<p>Strategy ID: <code>{safe_strat_id}</code> | Generated: {now_utc}</p>\n"
            f"<h2>Overview Metrics ({html.escape(overview.selected_template)})</h2>\n"
            "<table>\n<thead><tr><th>Metric</th><th>All Trades</th>"
            "<th>Long</th><th>Short</th></tr></thead>\n"
            f"<tbody>{metrics_rows_html}</tbody>\n</table>\n"
            "<h2>Monthly Performance Matrix</h2>\n"
            f"<table>\n<thead>{month_headers}</thead>\n"
            f"<tbody>{monthly_rows_html}</tbody>\n</table>\n"
            "</body>\n</html>"
        )

        doc = ResultsReportDocument(
            strategy_id=strategy_id,
            strategy_name=raw_name,
            result_key=result_key,
            generated_at_utc=now_utc,
            overview=overview,
            html_body=html_body,
        )

        logger.info(
            "FR-results-report-html: rendered report for %s (%d bytes)",
            strategy_id,
            len(html_body),
        )
        return wrap_response(
            request_id=f"req_{strategy_id}_report",
            data=doc,
            json_payload=doc.to_dict(),
        )
