"""Export recorded historical prices; MT4 output uses the existing binary codecs."""

from __future__ import annotations

import csv
import json
import re
from datetime import UTC, datetime, timedelta
from functools import partial
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import FileResponse

from app.core.host.transport import TransportError
from app.host.response import ErrorCode
from app.include.market_storage import safe_component
from app.workspace.brokers.files import encode_fxt_bytes, encode_hst_bytes

from .review import DatasetReview

_MT4_SYMBOL_BYTES = 11
_MAX_EXPORTS = 100

ARTIFACT_ROOT = Path("state/data-exports").resolve()


def _csv_token(
    match: Any, stamp: Any, row: Any, options: dict[str, Any], patterns: dict[str, str]
) -> str:
    """Render one explicit CSV token from a recorded observation."""
    key, fmt = match.group(1), match.group(2)
    if key in {"DateTime", "Date", "Time"}:
        fmt = (
            fmt
            or {
                "DateTime": "yyyy-MM-dd HH:mm:ss",
                "Date": "yyyy-MM-dd",
                "Time": "HH:mm:ss",
            }[key]
        )
        fmt = fmt.replace("SSS", "__MILLISECONDS__")
        for old, new in patterns.items():
            fmt = fmt.replace(old, new)
        return str(
            stamp.strftime(fmt).replace(
                "__MILLISECONDS__", f"{stamp.microsecond // 1000:03d}"
            )
        )
    if key == "Text":
        return fmt or ""
    if key == "Symbol":
        return str(options.get("symbol", ""))
    if key == "Spread" and "Ask" in row and "Bid" in row:
        return str(row.Ask - row.Bid)
    if key not in row:
        raise ValueError(f"History does not contain {key}")
    return str(row[key])


class DataExports:
    """Create job-owned output files from the same queries as historical review."""

    def __init__(self, gateway: Any) -> None:
        self.gateway = gateway

    def export_csv(self, frame: Any, path: Path, options: dict[str, Any]) -> None:
        """Write selected column/date tokens using recorded prices."""
        template = options.get("custom_format") or options.get("row_format")
        header = options.get("header", "DateTime,Open,High,Low,Close,Volume")
        patterns = {
            "yyyy": "%Y",
            "MM": "%m",
            "dd": "%d",
            "HH": "%H",
            "mm": "%M",
            "ss": "%S",
            "SSS": "%f",
        }
        with path.open("w", encoding="utf-8-sig", newline="") as stream:
            if template:
                if not re.findall(r"\[([A-Za-z]+)(?::([^\]]*))?\]", template):
                    raise ValueError("Choose a CSV format containing data tokens")
                if options.get("include_header", True) and header:
                    stream.write(header + "\r\n")
                for stamp, row in frame.iterrows():
                    stream.write(
                        re.sub(
                            r"\[([A-Za-z]+)(?::([^\]]*))?\]",
                            partial(
                                _csv_token,
                                stamp=stamp,
                                row=row,
                                options=options,
                                patterns=patterns,
                            ),
                            template,
                        )
                        + "\r\n"
                    )
            else:
                delimiter = options.get("delimiter", ",")
                if not isinstance(delimiter, str) or len(delimiter) != 1:
                    raise ValueError("Choose a single character delimiter")
                writer = csv.writer(stream, delimiter=delimiter)
                if options.get("include_header", True):
                    writer.writerow(["DateTime", *frame.columns])
                for stamp, row in frame.iterrows():
                    writer.writerow([stamp.isoformat(), *row.tolist()])

    def export_mt4(
        self, frame: Any, folder: Path, symbol: str, options: dict[str, Any]
    ) -> list[Path]:
        """Deliver existing codecs' real bytes, with explicit supported model limits."""
        if "Bid" in frame:
            raise ValueError("Select a bar timeframe for HST/FXT output")
        if len(symbol.encode("ascii")) > _MT4_SYMBOL_BYTES:
            raise ValueError("MT4 history symbols must fit the 11-byte header field")
        timeframe = str(options.get("timeframe") or "M1").upper()
        if timeframe not in {"M1", "M5", "M15", "M30", "H1", "H4", "D1", "W1"}:
            raise ValueError("Unsupported MT4 history timeframe")
        period = int(timeframe[1:]) * {"M": 1, "H": 60, "D": 1440, "W": 10080}.get(
            timeframe[0], 1
        )
        rows = [
            {
                "time": int(stamp.timestamp()),
                "open": row.Open,
                "high": row.High,
                "low": row.Low,
                "close": row.Close,
                "tick_volume": int(row.Volume),
                "real_volume": 0,
                "volume": int(row.Volume),
            }
            for stamp, row in frame.iterrows()
        ]
        mode = options.get("mode", "all")
        if mode not in {"all", "hst", "fxt"}:
            raise ValueError("Choose HST, FXT, or both")
        outputs = []
        if mode in {"all", "hst"}:
            path = folder / f"{symbol}{period}.hst"
            path.write_bytes(
                encode_hst_bytes(
                    rows, symbol, period=period, digits=int(options.get("digits", 5))
                )
            )
            outputs.append(path)
        if mode in {"all", "fxt"}:
            path = folder / f"{symbol}{period}_0.fxt"
            path.write_bytes(encode_fxt_bytes(rows, symbol, period=period))
            outputs.append(path)
        return outputs

    def export_mt5(self, frame: Any, path: Path, options: dict[str, Any]) -> None:
        """Write MT5 import columns from recorded bars or bid/ask ticks."""
        tick = "Bid" in frame
        if options.get("spread_mode") == "pips":
            raise ValueError(
                "Use spread points; pip conversion requires a symbol specification"
            )
        spread = float(options.get("fixed_spread", options.get("spread", 0)))
        if spread < 0 or not spread < float("inf"):
            raise ValueError("Spread must be finite and nonnegative")
        if options.get("spread_mode") == "real" and not tick:
            raise ValueError("Stored OHLCV bars do not contain historical real spreads")
        with path.open("w", encoding="utf-8-sig", newline="") as stream:
            writer = csv.writer(stream, delimiter="\t")
            writer.writerow(
                ["<DATE>", "<TIME>", "<BID>", "<ASK>", "<LAST>", "<VOLUME>", "<FLAGS>"]
                if tick
                else [
                    "<DATE>",
                    "<TIME>",
                    "<OPEN>",
                    "<HIGH>",
                    "<LOW>",
                    "<CLOSE>",
                    "<TICKVOL>",
                    "<VOL>",
                    "<SPREAD>",
                ]
            )
            for stamp, row in frame.iterrows():
                date, clock = (
                    stamp.strftime("%Y.%m.%d"),
                    stamp.strftime("%H:%M:%S.%f")[:-3],
                )
                writer.writerow(
                    [date, clock, row.Bid, row.Ask, "", 0, int(row.get("Flags", 6))]
                    if tick
                    else [
                        date,
                        clock,
                        row.Open,
                        row.High,
                        row.Low,
                        row.Close,
                        int(row.Volume),
                        0,
                        spread,
                    ]
                )

    def run_export(
        self, context: Any, payload: dict[str, Any], logs: Any
    ) -> dict[str, Any]:
        """Publish only completed artifacts; cancelled/failed files are removed."""
        folder = ARTIFACT_ROOT / safe_component(context.job_id)
        folder.mkdir(parents=True, exist_ok=False)
        outputs: list[Path] = []
        try:
            series = payload["series"]
            for index, target in enumerate(series):
                context.wait_if_paused()
                context.raise_if_cancelled()
                service = DatasetReview(self.gateway, target["dataset_id"])
                timeframe = target.get("timeframe")
                if timeframe in {"All", "all"}:
                    timeframe = service.record["timeframe"]
                frame = service.frame(
                    timeframe,
                    target.get("session"),
                    target.get("start"),
                    target.get("end"),
                )
                if frame.empty:
                    raise ValueError("No recorded prices in the selected export range")  # noqa: TRY301 - enclosing scope owns rollback
                timezone = target.get("tz")
                if timezone and timezone not in {"original", "Original", "UTC"}:
                    frame.index = frame.index.tz_convert(timezone)
                symbol = safe_component(
                    str(payload.get("mt4_name") or service.record["symbol"])
                )
                options = {
                    **payload,
                    "symbol": symbol,
                    "timeframe": timeframe or service.record["timeframe"],
                }
                prefix = str(payload.get("prefix") or "").strip()
                filename = str(payload.get("filename") or "").strip()
                name = (
                    safe_component(filename)
                    if filename
                    else (
                        f"{safe_component(prefix)}-{symbol}-{options['timeframe']}"
                        if prefix
                        else f"{index + 1}-{symbol}"
                    )
                )
                if payload["format"] == "mt4":
                    outputs.extend(self.export_mt4(frame, folder, symbol, options))
                else:
                    path = folder / f"{name}.csv"
                    (
                        self.export_mt5
                        if payload["format"] == "mt5"
                        else self.export_csv
                    )(frame, path, options)
                    outputs.append(path)
                context.report_progress(
                    100 * (index + 1) / len(series), f"Exported {symbol}"
                )
                logs.record_progress(
                    context.job_id,
                    progress=100 * (index + 1) / len(series),
                    message=f"Exported recorded {symbol} history",
                )
            result = {"artifacts": [path.name for path in outputs]}
            (folder / "manifest.json").write_text(json.dumps(result), encoding="utf-8")
            return result
        except BaseException:
            for path in folder.iterdir():
                if path.is_file():
                    path.unlink()
            folder.rmdir()
            logs.record_progress(
                context.job_id,
                progress=-1,
                level="error",
                message="Export stopped or failed; no completed artifacts",
            )
            raise


def register_export_routes(router: APIRouter) -> None:
    """Export jobs and authenticated job-owned artifact delivery."""
    from app.workspace.data_manager.logs import Logs
    from app.workspace.data_manager.sources.download_jobs import manager

    @router.post("/export")
    def export(request: Request, body: dict[str, Any]) -> dict[str, Any]:
        if (
            body.get("format") not in {"csv", "mt4", "mt5"}
            or not isinstance(body.get("series"), list)
            or not 1 <= len(body["series"]) <= _MAX_EXPORTS
        ):
            raise TransportError(
                ErrorCode.VALIDATION, "Choose an export format and saved datasets"
            )
        for target in body["series"]:
            DatasetReview(request.app.state.persistence, target.get("dataset_id", ""))
        ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)
        for path in ARTIFACT_ROOT.glob("*/*"):
            if path.is_file() and datetime.fromtimestamp(
                path.stat().st_mtime, UTC
            ) < datetime.now(UTC) - timedelta(days=1):
                path.unlink()
        record = manager(request).submit_job(
            DataExports(request.app.state.persistence).run_export,
            body,
            getattr(request.app.state, "data_logs", None) or Logs(),
            owner="data-manager",
            kind="market.export",
            executor_kind="thread",
            pass_context=True,
        )
        return {"success": True, "data": record.to_dict()}

    router.add_api_route(
        "/export-artifacts/{job_id}/{index}", _download_artifact, methods=["GET"]
    )


def _download_artifact(job_id: str, index: int, request: Request) -> FileResponse:
    """Deliver a completed owned artifact, including after host restart."""
    from app.workspace.data_manager.sources.download_jobs import manager

    job = manager(request).get_job(job_id)
    if (
        not job
        or job.owner != "data-manager"
        or job.kind != "market.export"
        or job.status != "COMPLETED"
    ):
        raise TransportError(ErrorCode.NOT_FOUND, "Completed export not found")
    result = job.result
    if result is None:
        manifest = ARTIFACT_ROOT / safe_component(job_id) / "manifest.json"
        result = (
            json.loads(manifest.read_text(encoding="utf-8"))
            if manifest.is_file()
            else {}
        )
    names = result.get("artifacts", [])
    if index < 0 or index >= len(names):
        raise TransportError(ErrorCode.NOT_FOUND, "Artifact not found")
    path = ARTIFACT_ROOT / safe_component(job_id) / safe_component(names[index])
    if not path.is_file():
        raise TransportError(ErrorCode.NOT_FOUND, "Export expired; run it again")
    return FileResponse(path, filename=path.name)
