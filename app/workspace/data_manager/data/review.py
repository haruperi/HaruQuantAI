"""Authoritative historical review.

Description:
    Queries recorded prices, delegates bounded quality analysis and saves reviewed
    edits under the dataset writer lock. Review responses expose price precision.
Purpose:
    FEAT-DATA-REVIEW: Authoritative chart, row and quality review.
Key Capabilities:
    - FR-DATA-REVIEW-price-precision: Log verified price precision and its source.
    - FR-DATA-QUALITY-bounded-analysis: Verify delegated analysis completion logs.
Python API Usage:
    DatasetReview(gateway, dataset_id).rows(limit=500)
CLI Usage:
    uv run pytest tests/workspace/data_manager/test_data_review.py --no-cov
"""

from __future__ import annotations

import json
from decimal import Decimal
from typing import Any, cast

import pandas as pd  # type: ignore[import-untyped]
from fastapi import APIRouter, Request

from app.core.data.contracts import TradingSession
from app.core.data.market_storage import scan_catalog
from app.core.host.logging import get_logger
from app.core.host.transport import TransportError
from app.core.lib.responses import ErrorCode

from ._helpers import _MAX_CHART_ROWS
from .partition_files import dataset_lock
from .quality import analyze_quality
from .storage import publish_frame, require_data

_DATE_LENGTH = 10
_MAX_PRICE_DIGITS = 20
logger = get_logger(__name__)


class DatasetReview:
    """Query one validated dataset; all consumers share time/session semantics."""

    def __init__(self, gateway: Any, dataset_id: str) -> None:
        self.gateway = gateway
        records = require_data(
            gateway.read_records(
                "datamgr_datasets", filters={"id": dataset_id}, limit=1
            )
        )["records"]
        if not records:
            raise TransportError(ErrorCode.NOT_FOUND, "Dataset not found")
        self.record = records[0]

    def frame(
        self,
        timeframe: str | None = None,
        session: str | None = None,
        start: str | None = None,
        end: str | None = None,
    ) -> pd.DataFrame:
        """Read decoded prices and aggregate only from a finer native resolution."""
        if not self.record["bars"]:
            return pd.DataFrame()
        lazy = scan_catalog(self.record, decode=True)
        if start or end:
            import polars as pl

            if start:
                lazy = lazy.filter(
                    pl.col("DateTime") >= pd.Timestamp(start, tz="UTC").to_pydatetime()
                )
            if end:
                upper = pd.Timestamp(end, tz="UTC")
                if len(end) == _DATE_LENGTH:
                    upper += pd.Timedelta(days=1) - pd.Timedelta(microseconds=1)
                lazy = lazy.filter(pl.col("DateTime") <= upper.to_pydatetime())
        frame = lazy.sort("DateTime").collect().to_pandas().set_index("DateTime")
        calendar = self.calendar(session)
        if calendar:
            frame = frame[
                [
                    calendar.is_within_session(stamp.to_pydatetime())
                    for stamp in frame.index
                ]
            ]
        if (
            timeframe
            and timeframe.upper() != self.record["timeframe"]
            and not frame.empty
        ):
            rules = {
                "TICK": 0,
                "M1": 1,
                "M5": 5,
                "M15": 15,
                "M30": 30,
                "H1": 60,
                "H4": 240,
                "D1": 1440,
                "W1": 10080,
                "MN1": 43200,
            }
            target = timeframe.upper()
            if target not in rules or rules[target] < rules.get(
                self.record["timeframe"], 1
            ):
                raise ValueError(
                    "Cannot derive finer history than the stored resolution"
                )
            rule = "MS" if target == "MN1" else f"{rules[target]}min"
            if self.record["timeframe"] == "TICK":
                mid = (frame.Bid + frame.Ask) / 2
                bars = mid.resample(rule).ohlc().rename(columns=str.title)
                bars["Volume"] = mid.resample(rule).count()
                frame = bars.dropna()
            else:
                frame = (
                    frame.resample(rule)
                    .agg(
                        {
                            "Open": "first",
                            "High": "max",
                            "Low": "min",
                            "Close": "last",
                            "Volume": "sum",
                        }
                    )
                    .dropna()
                )
        return frame

    def calendar(self, session: str | None = None) -> TradingSession | None:
        """Use the selected saved schedule instead of inventing trading hours."""
        identifier = self.record.get("session_id")
        if session in ("No Session", "none"):
            return None
        if not identifier and not session:
            return None
        filters = {"name": session} if session else {"id": identifier}
        rows = require_data(
            self.gateway.read_records("datamgr_sessions", filters=filters, limit=1)
        )["records"]
        if not rows:
            raise ValueError("Choose a saved trading session")
        return TradingSession.from_dict(rows[0])

    def rows(self, limit: int = 500, offset: int = 0, **query: Any) -> dict[str, Any]:
        """Return stable timestamp identities and real prices for the requested page."""
        if not 1 <= limit <= _MAX_CHART_ROWS or offset < 0:
            raise ValueError("Invalid review pagination")
        native = (
            not query.get("timeframe") or query["timeframe"] == self.record["timeframe"]
        )
        if (
            self.record["bars"]
            and native
            and self.calendar(query.get("session")) is None
            and not any(query.get(key) for key in ("start", "end"))
        ):
            import polars as pl

            lazy = scan_catalog(self.record, decode=True)
            total = lazy.select(pl.len()).collect().item()
            frame = (
                lazy.sort("DateTime")
                .slice(offset, limit)
                .collect()
                .to_pandas()
                .set_index("DateTime")
            )
            page = frame
        else:
            frame = self.frame(**query)
            total = len(frame)
            page = frame.iloc[offset : offset + limit]
        rows = []
        for stamp, item in page.iterrows():
            tick = "Bid" in item
            mid = (item.Bid + item.Ask) / 2 if tick else item.Close
            rows.append(
                {
                    "id": stamp.isoformat(),
                    "date": stamp.isoformat(),
                    "open": float(mid if tick else item.Open),
                    "high": float(item.Ask if tick else item.High),
                    "low": float(item.Bid if tick else item.Low),
                    "close": float(mid),
                    "volume": int(item.get("Volume", 0)),
                    "bid": float(item.Bid if tick else mid),
                    "ask": float(item.Ask if tick else mid),
                }
            )
        return {
            "rows": rows,
            "total": total,
            "offset": offset,
            "limit": limit,
            "revision": self.record["updated_at"],
            "price_digits": self.price_digits(),
        }

    def summary(self, **query: Any) -> dict[str, Any]:
        """Summarize the same actual history used by chart and export queries."""
        frame = self.frame(**query)
        return {
            "dataset": self.record,
            "count": len(frame),
            "from": frame.index.min().isoformat() if len(frame) else None,
            "to": frame.index.max().isoformat() if len(frame) else None,
            "min": float(frame["Bid" if "Bid" in frame else "Low"].min())
            if len(frame)
            else None,
            "max": float(frame["Ask" if "Ask" in frame else "High"].max())
            if len(frame)
            else None,
            "volume": int(frame.Volume.sum()) if "Volume" in frame else 0,
        }

    def quality(
        self, limit: int = 500, offset: int = 0, **query: Any
    ) -> dict[str, Any]:
        """Audit the complete history and retain only the requested issue page."""
        return analyze_quality(
            self.frame(**query),
            query.get("timeframe") or self.record["timeframe"],
            self.calendar(query.get("session")),
            limit=limit,
            offset=offset,
        )

    def price_digits(self) -> int:
        """Prefer saved instrument digits, otherwise use canonical storage precision."""
        identifier = self.record.get("symbol_definition_id")
        if identifier is not None:
            rows = require_data(
                self.gateway.read_records(
                    "datamgr_symbols", filters={"id": identifier}, limit=1
                )
            )["records"]
            if rows:
                value = rows[0].get("decimals")
                if (
                    isinstance(value, (int, float))
                    and 0 <= value <= _MAX_PRICE_DIGITS
                    and int(value) == value
                ):
                    logger.debug(
                        "FR-DATA-REVIEW-price-precision: instrument digits=%d", value
                    )
                    return int(value)
            logger.warning(
                "FR-DATA-REVIEW-price-precision: linked digits unavailable; "
                "using stored units"
            )
        step = Decimal(str(json.loads(self.record["lineage_json"])["tick_size"]))
        if not step.is_finite() or step <= 0:
            raise ValueError("Stored price precision is unavailable")
        exponent = cast("int", step.normalize().as_tuple().exponent)
        digits = max(0, -exponent)
        if digits > _MAX_PRICE_DIGITS:
            raise ValueError("Stored price precision exceeds review limits")
        logger.debug("FR-DATA-REVIEW-price-precision: stored digits=%d", digits)
        return digits

    def save_changes(
        self, changed: list[dict[str, Any]], deleted: list[str], revision: str | None
    ) -> dict[str, Any]:
        """Publish validated edits under the dataset writer lock."""
        from pathlib import Path

        root = Path(self.record["path"])
        with dataset_lock(root):
            latest = DatasetReview(self.gateway, self.record["id"])
            if revision and revision != latest.record["updated_at"]:
                raise TransportError(
                    ErrorCode.CONFLICT, "History changed; reload before saving"
                )
            frame = latest.frame()
            for value in deleted:
                stamp = pd.Timestamp(value)
                if stamp not in frame.index:
                    raise ValueError("Deleted timestamp is not in saved history")
                frame = frame.drop(stamp)
            for item in changed:
                stamp = pd.Timestamp(item.get("date") or item.get("datetime"))
                if stamp not in frame.index:
                    raise ValueError("Edited timestamp is not in saved history")
                for column in frame.columns:
                    if column.lower() in item:
                        frame.loc[stamp, column] = item[column.lower()]
            if frame.empty:
                from .feature import Data

                return cast(
                    "dict[str, Any]",
                    require_data(Data(self.gateway).clear(self.record["id"])),
                )
            step = json.loads(self.record["lineage_json"])["tick_size"]
            return publish_frame(
                self.gateway,
                root.parent.parent,
                self.record,
                frame,
                step,
                replace_snapshot=True,
                locked=True,
            )


def register_review_routes(router: APIRouter) -> None:
    """Expose existing browser review contracts with authoritative server queries."""

    @router.get("/datasets/{dataset_id}/{action}")
    def review(
        dataset_id: str,
        action: str,
        request: Request,
        *,
        limit: int = 500,
        offset: int = 0,
        timeframe: str | None = None,
        session: str | None = None,
        target_date: str | None = None,
    ) -> dict[str, Any]:
        service = DatasetReview(request.app.state.persistence, dataset_id)
        query = {"timeframe": timeframe, "session": session}
        try:
            if action in {"review-data", "review-chart"}:
                data = service.rows(limit, offset, **query)
            elif action == "review-summary":
                data = service.summary(**query)
            elif action in {"quality-summary", "quality-details"}:
                data = service.quality(
                    limit=limit if action == "quality-details" else 0,
                    offset=offset,
                    **query,
                )
            elif action == "index-for-date":
                data = {
                    "index": int(
                        service.frame().index.searchsorted(
                            pd.Timestamp(target_date, tz="UTC")
                        )
                    )
                }
            else:
                raise TransportError(ErrorCode.NOT_FOUND, "Unknown review operation")
            return {"success": True, "data": data}
        except (ValueError, TypeError) as error:
            raise TransportError(ErrorCode.VALIDATION, str(error)) from error

    @router.post("/datasets/{dataset_id}/save-changes")
    def save(dataset_id: str, request: Request, body: dict[str, Any]) -> dict[str, Any]:
        try:
            return {
                "success": True,
                "data": DatasetReview(
                    request.app.state.persistence, dataset_id
                ).save_changes(
                    body.get("changed_bars", []),
                    body.get("deleted_timestamps", []),
                    body.get("revision"),
                ),
            }
        except (ValueError, TypeError) as error:
            raise TransportError(ErrorCode.VALIDATION, str(error)) from error
