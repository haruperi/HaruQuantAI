"""Standards-compliant PDF strategy report exporter service (%PDF-1.4).

Description:
    Implements SaverPDFService producing valid %PDF-1.4 binary documents
    containing strategy summary, performance metrics, and optional trades,
    complete with xref tables and trailer.

Purpose:
    FEAT-RESULTS-SAVER-PDF: Standards-compliant %PDF-1.4 report exporter.

Key Capabilities:
    - FR-results-saver-pdf: Generate valid PDF strategy reports.

Python API Usage:
    from app.workspace.results.saver_p_d_f import SaverPDFService
    service = SaverPDFService()
    receipt = service.export_strategy_pdf("p1", "Results", "Strat_01")

CLI Usage:
    python -m app.cli results export-pdf --strategy-id Strat_01
"""

from __future__ import annotations

import io

from app.core.host.logging import get_logger
from app.core.lib.errors import DomainError
from app.core.trading.results.contracts import RunResult
from app.core.trading.results.store import ResultStore
from app.workspace.results.saver_s_q3 import ExportArtifactReceipt

logger = get_logger(__name__)


def _escape_pdf_text(text: str) -> str:
    """Escape parentheses and backslashes for PDF literal text."""
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


class SaverPDFService:
    """Service generating valid %PDF-1.4 documents from strategy results."""

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
            message=f"Strategy '{strategy_id}' not found for PDF export",
            details={"strategy_id": strategy_id},
        )

    def export_strategy_pdf(
        self,
        project_id: str,
        databank_name: str,
        strategy_id: str,
        *,
        result_key: str = "Main",
        include_trades: bool = False,
    ) -> ExportArtifactReceipt:
        """Generate valid %PDF-1.4 binary document."""
        logger.info(
            "FR-results-saver-pdf: exporting proj=%s db=%s strat=%s key=%s",
            project_id,
            databank_name,
            strategy_id,
            result_key,
        )
        run_res = self._resolve_result(strategy_id)
        name = run_res.strategy_name or strategy_id

        # Build text stream content
        hdr_str = (
            f"Project: {project_id} | Databank: {databank_name} | Key: {result_key}"
        )
        stream_lines: list[str] = [
            "BT",
            "/F1 18 Tf",
            "50 740 Td",
            f"({_escape_pdf_text(f'Strategy Report: {name}')}) Tj",
            "0 -25 Td",
            "/F1 11 Tf",
            f"({_escape_pdf_text(hdr_str)}) Tj",
            "0 -25 Td",
            "/F1 14 Tf",
            "(Performance Metrics:) Tj",
            "/F1 10 Tf",
        ]

        for k, v in sorted(run_res.metrics.items())[:15]:
            safe_line = _escape_pdf_text(f"  {k}: {v}")
            stream_lines.extend(["0 -18 Td", f"({safe_line}) Tj"])

        if include_trades and run_res.trades:
            stream_lines.extend(
                [
                    "0 -25 Td",
                    "/F1 14 Tf",
                    "(Recent Trades:) Tj",
                    "/F1 10 Tf",
                ]
            )
            for t in run_res.trades[:10]:
                ticket = t.get("ticket", "")
                t_type = t.get("type", t.get("direction", ""))
                pl = t.get("profit_loss", t.get("pnl", ""))
                t_str = _escape_pdf_text(f"  #{ticket} {t_type} P&L: {pl}")
                stream_lines.extend(["0 -16 Td", f"({t_str}) Tj"])

        stream_lines.append("ET\n")
        stream_bytes = "\n".join(stream_lines).encode("latin-1")

        # Assemble PDF 1.4 objects
        out = io.BytesIO()
        out.write(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")

        offsets: list[int] = []

        # Obj 1: Catalog
        offsets.append(out.tell())
        out.write(b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n")

        # Obj 2: Pages
        offsets.append(out.tell())
        out.write(b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n")

        # Obj 3: Page
        offsets.append(out.tell())
        out.write(
            b"3 0 obj\n"
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\n"
            b"endobj\n"
        )

        # Obj 4: Stream
        offsets.append(out.tell())
        out.write(
            f"4 0 obj\n<< /Length {len(stream_bytes)} >>\nstream\n".encode("ascii")
        )
        out.write(stream_bytes)
        out.write(b"\nendstream\nendobj\n")

        # Obj 5: Font
        offsets.append(out.tell())
        out.write(
            b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n"
        )

        # Xref Table
        xref_offset = out.tell()
        out.write(f"xref\n0 {len(offsets) + 1}\n".encode("ascii"))
        out.write(b"0000000000 65535 f \n")
        for off in offsets:
            out.write(f"{off:010d} 00000 n \n".encode("ascii"))

        # Trailer
        out.write(
            f"trailer\n<< /Size {len(offsets) + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref_offset}\n%%EOF\n".encode("ascii")
        )

        payload = out.getvalue()
        logger.info(
            "FR-results-saver-pdf: emitted %s.pdf (%d bytes)",
            name,
            len(payload),
        )

        return ExportArtifactReceipt(
            filename=f"{name}.pdf",
            mime_type="application/pdf",
            size_bytes=len(payload),
            content_bytes=payload,
        )
