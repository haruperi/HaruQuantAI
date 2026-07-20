"""Data API routes for market instruments and dataset preparation."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Any

import numpy as np
import pandas as pd
from data.database.sqlite.database_operations import DatabaseManager
from fastapi import APIRouter, Header, HTTPException, status
from pydantic import BaseModel

from app.api.auth_utils import get_user_id_from_token
from app.services.brokers import (
    load_dukascopy,
    mt5_data_get_bars_with_credentials,
    mt5_data_list_symbol_details_with_credentials,
)
from app.services.research import (
    CanonicalOHLCVSSchema,
    CleaningAction,
    CleaningConfig,
    DataQualityReportModel,
    DatasetIssue,
    EnrichmentConfig,
    PreparedDataset,
    prepare_research_dataset,
)
from app.services.utils import logger
from app.services.utils.validators import DataSource, prepare_ohlcv_data

router = APIRouter()
db_manager = DatabaseManager()
AUTH_HEADER = Header(None)

# --- Models ---


class DatasetPrepareRequest(BaseModel):
    """Request model for preparing a reusable dataset."""

    symbol: str
    timeframe: str = "M15"
    data_source: str = "mt5"
    range_by: str = "dates"
    start_date: str | None = None
    end_date: str | None = None
    number_of_bars: int | None = None
    session_basis: str = "dataset_index"


# --- Data Sources ---


class MT5DataSource:
    """MT5 data source wrapper."""

    def __init__(
        self,
        user_id: int,
        start_date: datetime | None,
        end_date: datetime | None,
        count: int | None,
    ):
        self._credentials = db_manager.get_mt5_credentials(user_id) or {}
        self.connected = bool(
            self._credentials.get("login")
            and self._credentials.get("password")
            and self._credentials.get("server")
        )
        self.start_date = start_date
        self.end_date = end_date
        self.count = count

    def fetch_data(
        self, symbol: str, timeframe: str, start_pos: int, end_pos: int
    ) -> pd.DataFrame | None:
        if not self.connected:
            logger.error("MT5 not connected")
            return None

        creds = self._credentials
        if self.start_date:
            result = mt5_data_get_bars_with_credentials(
                symbol=symbol,
                timeframe=timeframe,
                login=int(creds.get("login") or 0),
                password=str(creds.get("password") or ""),
                server=str(creds.get("server") or ""),
                path=str(creds.get("path") or ""),
                date_from=self.start_date,
                date_to=self.end_date,
            )
        else:
            count = self.count or max(1, end_pos - start_pos)
            result = mt5_data_get_bars_with_credentials(
                symbol=symbol,
                timeframe=timeframe,
                login=int(creds.get("login") or 0),
                password=str(creds.get("password") or ""),
                server=str(creds.get("server") or ""),
                path=str(creds.get("path") or ""),
                count=count,
                start_pos=start_pos,
            )
        df = extract_mt5_bars_frame(result)
        if df is None or df.empty:
            return None
        return prepare_ohlcv_data(df, schema=CanonicalOHLCVSSchema())


class DukascopyDataSource:
    """Dukascopy data source wrapper."""

    def __init__(
        self,
        start_date: str | None,
        end_date: str | None,
        count: int | None,
    ):
        self.start_date = start_date
        self.end_date = end_date
        self.count = count

    def fetch_data(
        self, symbol: str, timeframe: str, start_pos: int, end_pos: int
    ) -> pd.DataFrame | None:
        df = load_dukascopy(
            symbol=symbol,
            timeframe=timeframe,
            start_date=self.start_date,
            end_date=self.end_date,
            count=self.count,
        )
        if df is None or df.empty:
            return None
        return prepare_ohlcv_data(df, schema=CanonicalOHLCVSSchema())


# --- Shared Logic ---


def json_safe_value(value: Any) -> Any:
    """Safely convert common data types to JSON-serializable values."""
    if value is None:
        return None
    if isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, (datetime, pd.Timestamp)):
        return value.isoformat()
    if isinstance(value, (np.floating, float)):
        value = float(value)
        if np.isnan(value) or np.isinf(value):
            return None
        return value
    if isinstance(value, (np.integer,)):
        return int(value)
    return value


def report_to_dict(report: DataQualityReportModel) -> dict[str, Any]:
    """Serialize a DataQualityReportModel to a dictionary."""
    return {
        "checks_performed": list(report.checks_performed),
        "warnings": [
            {
                "code": item.code,
                "severity": item.severity,
                "message": item.message,
                "count": item.count,
                "details": {k: json_safe_value(v) for k, v in item.details.items()},
            }
            for item in report.warnings
        ],
        "fatal_errors": [
            {
                "code": item.code,
                "severity": item.severity,
                "message": item.message,
                "count": item.count,
                "details": {k: json_safe_value(v) for k, v in item.details.items()},
            }
            for item in report.fatal_errors
        ],
        "cleaning_actions": [
            {
                "action": item.action,
                "count": item.count,
                "details": {k: json_safe_value(v) for k, v in item.details.items()},
            }
            for item in report.cleaning_actions
        ],
        "metadata": {k: json_safe_value(v) for k, v in report.metadata.items()},
        "is_valid": report.is_valid,
    }


def serialize_prepared_dataset(prepared: PreparedDataset) -> dict[str, Any]:
    """Serialize a PreparedDataset to a dictionary."""
    frame = prepared.data.copy()
    frame = frame.reset_index().rename(
        columns={frame.index.name or "index": "timestamp"}
    )
    if "timestamp" not in frame.columns:
        frame = frame.rename(columns={"index": "timestamp"})
    rows: list[dict[str, Any]] = []
    for row in frame.to_dict(orient="records"):
        rows.append({key: json_safe_value(value) for key, value in row.items()})
    preview = rows[:200]
    return {
        "meta": {
            "symbol": prepared.report.metadata.get("symbol"),
            "timeframe": prepared.report.metadata.get("timeframe"),
            "n_rows": len(rows),
            "start": prepared.report.metadata.get("start"),
            "end": prepared.report.metadata.get("end"),
            "session_basis": prepared.report.metadata.get("session_basis"),
            "session_hours": prepared.report.metadata.get("session_hours"),
        },
        "schema": {
            "open": prepared.schema.open,
            "high": prepared.schema.high,
            "low": prepared.schema.low,
            "close": prepared.schema.close,
            "volume": prepared.schema.volume,
            "spread": prepared.schema.spread,
        },
        "report": report_to_dict(prepared.report),
        "rows": rows,
        "preview_rows": preview,
    }


def extract_mt5_bars_frame(result: dict[str, Any]) -> pd.DataFrame | None:
    """Extract MT5 bars from a broker response envelope."""
    if result.get("status") != "success":
        logger.warning(
            "MT5 bars request failed: {}",
            result.get("message", "unknown error"),
        )
        return None

    data = result.get("data")
    if not isinstance(data, dict):
        return None

    rows = data.get("data")
    if isinstance(rows, dict):
        rows = rows.get("data")
    if not isinstance(rows, list) or not rows:
        return None

    normalized_rows: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        normalized = dict(row)
        timestamp = normalized.get("timestamp")
        if isinstance(timestamp, dict):
            normalized["timestamp"] = timestamp.get("data")
        normalized_rows.append(normalized)

    if not normalized_rows:
        return None

    return pd.DataFrame(normalized_rows)


def extract_mt5_symbols(result: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract symbol metadata from a broker response envelope."""
    if result.get("status") != "success":
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(result.get("message") or "MT5 symbols request failed."),
        )

    data = result.get("data")
    if not isinstance(data, dict):
        return []

    symbols = data.get("symbols")
    if not isinstance(symbols, list):
        return []

    return [item for item in symbols if isinstance(item, dict)]


def resolve_symbol_price_metadata(source: DataSource, symbol: str) -> dict[str, Any]:
    """Resolve broker price display metadata for a symbol when available."""
    if not isinstance(source, MT5DataSource) or not source.connected:
        return {}

    result = mt5_data_list_symbol_details_with_credentials(
        path=str(source._credentials.get("path") or ""),
        login=int(source._credentials.get("login") or 0),
        password=str(source._credentials.get("password") or ""),
        server=str(source._credentials.get("server") or ""),
    )
    for item in extract_mt5_symbols(result):
        if str(item.get("symbol") or "") == symbol:
            return {
                "digits": json_safe_value(item.get("digits")),
                "point": json_safe_value(item.get("point")),
                "trade_tick_size": json_safe_value(item.get("trade_tick_size")),
            }
    return {}



def parse_date(value: str | None) -> datetime | None:
    """Parse an ISO date string."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(value)


def hash_jsonable(payload: dict[str, Any]) -> str:
    """Stable hash of a JSON-serializable dictionary."""
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def dataset_fingerprint(prepared: PreparedDataset) -> str:
    """Generate a content-based fingerprint for a prepared dataset."""
    row_hashes = pd.util.hash_pandas_object(prepared.data, index=True)
    digest = hashlib.sha256()
    digest.update(row_hashes.to_numpy().tobytes())
    digest.update(
        "|".join(str(column) for column in prepared.data.columns).encode("utf-8")
    )
    return digest.hexdigest()


def deserialize_prepared_dataset(payload: dict[str, Any]) -> PreparedDataset:
    """Reconstruct a PreparedDataset from its serialized dictionary form."""
    rows = payload.get("rows") or []
    if not rows:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Prepared dataset rows are required.",
        )

    frame = pd.DataFrame(rows)
    if "timestamp" not in frame.columns:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Prepared dataset timestamp column is missing.",
        )
    frame["timestamp"] = pd.to_datetime(frame["timestamp"])
    frame = frame.set_index("timestamp").sort_index()

    schema_payload = payload.get("schema") or {}
    schema = CanonicalOHLCVSSchema(
        open=str(schema_payload.get("open") or "Open"),
        high=str(schema_payload.get("high") or "High"),
        low=str(schema_payload.get("low") or "Low"),
        close=str(schema_payload.get("close") or "Close"),
        volume=str(schema_payload.get("volume") or "Volume"),
        spread=str(schema_payload.get("spread") or "Spread"),
    )

    report_payload = payload.get("report") or {}
    report = DataQualityReportModel(
        checks_performed=list(report_payload.get("checks_performed") or []),
        metadata=dict(report_payload.get("metadata") or {}),
    )
    for item in report_payload.get("warnings") or []:
        report.add_issue(
            DatasetIssue(
                code=str(item.get("code") or ""),
                severity="warning",
                message=str(item.get("message") or ""),
                count=int(item.get("count") or 0),
                details=dict(item.get("details") or {}),
            )
        )
    for item in report_payload.get("fatal_errors") or []:
        report.add_issue(
            DatasetIssue(
                code=str(item.get("code") or ""),
                severity="fatal",
                message=str(item.get("message") or ""),
                count=int(item.get("count") or 0),
                details=dict(item.get("details") or {}),
            )
        )
    for item in report_payload.get("cleaning_actions") or []:
        report.add_action(
            CleaningAction(
                action=str(item.get("action") or ""),
                count=int(item.get("count") or 0),
                details=dict(item.get("details") or {}),
            )
        )
    return PreparedDataset(data=frame, report=report, schema=schema)


def resolve_prepared_dataset_from_payload(
    payload: dict[str, Any] | None,
) -> PreparedDataset | None:
    """Helper to safely resolve a dataset from a request payload."""
    if not payload:
        return None
    return deserialize_prepared_dataset(payload)


def validate_range_params(
    range_by: str,
    start_date_str: str | None,
    end_date_str: str | None,
    number_of_bars: int | None,
) -> tuple[str, datetime | None, datetime | None, int | None]:
    """Validate and parse common range parameters."""
    range_by = range_by.lower()
    if range_by not in ("dates", "bars"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid range_by value.",
        )

    start_date = parse_date(start_date_str) if range_by == "dates" else None
    end_date = parse_date(end_date_str) if range_by == "dates" else None
    number_of_bars_val = number_of_bars if range_by == "bars" else None

    if range_by == "dates" and not start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_date is required when range_by=dates.",
        )
    if range_by == "bars" and not number_of_bars_val:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="number_of_bars is required when range_by=bars.",
        )
    return range_by, start_date, end_date, number_of_bars_val


def create_data_source(
    data_source: str,
    user_id: int,
    start_date: datetime | None,
    end_date: datetime | None,
    number_of_bars: int | None,
    string_dates: tuple[str | None, str | None] = (None, None),
) -> DataSource:
    """Create a data source object based on source type."""
    if data_source == "mt5":
        mt5_source = MT5DataSource(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            count=number_of_bars,
        )
        if not mt5_source.connected:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="MT5 not connected.",
            )
        return mt5_source
    if data_source == "dukascopy":
        return DukascopyDataSource(
            start_date=string_dates[0],
            end_date=string_dates[1],
            count=number_of_bars,
        )

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Invalid data_source value.",
    )


def default_session_hours() -> dict[str, list[int]]:
    """Return default trading session hour buckets."""
    return {
        "sydney": list(range(7)),
        "tokyo": list(range(2, 9)),
        "london": list(range(10, 17)),
        "ny": list(range(15, 22)),
    }


# --- Routes ---


@router.get("/symbols", response_model=list[dict[str, Any]])
async def get_symbols(
    authorization: str = Header(None),
):
    """Get all available symbols from MT5 terminal."""
    try:
        user_id = get_user_id_from_token(authorization)
    except Exception:
        user_id = 1

    creds = db_manager.get_mt5_credentials(user_id)
    if not creds:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MT5 credentials not found.",
        )

    try:
        result = mt5_data_list_symbol_details_with_credentials(
            path=str(creds.get("path") or ""),
            login=int(creds.get("login") or 0),
            password=str(creds.get("password") or ""),
            server=str(creds.get("server") or ""),
        )
        return extract_mt5_symbols(result)
    except Exception as e:
        logger.error(f"Error fetching symbols from MT5: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching symbols: {e!s}",
        )


@router.post("/dataset/prepare", response_model=dict[str, Any])
async def prepare_dataset_endpoint(
    request: DatasetPrepareRequest,
    authorization: str = Header(None),
):
    """Prepare and serialize a reusable dataset."""
    try:
        user_id = get_user_id_from_token(authorization)
    except Exception:
        user_id = 1

    range_by, start_date, end_date, number_of_bars = validate_range_params(
        request.range_by,
        request.start_date,
        request.end_date,
        request.number_of_bars,
    )
    source = create_data_source(
        request.data_source.lower(),
        user_id,
        start_date,
        end_date,
        number_of_bars,
        (request.start_date, request.end_date),
    )
    session_hours = default_session_hours()
    prepared = prepare_research_dataset(
        source=source,
        symbol=request.symbol,
        timeframe=request.timeframe,
        start_pos=0,
        end_pos=number_of_bars or 5000,
        cleaning=CleaningConfig(timeframe=request.timeframe),
        enrichment=EnrichmentConfig(
            symbol=request.symbol,
            session_basis=request.session_basis,
        ),
    )
    payload = serialize_prepared_dataset(prepared)
    payload["request"] = {
        "symbol": request.symbol,
        "timeframe": request.timeframe,
        "data_source": request.data_source.lower(),
        "range_by": range_by,
        "start_date": request.start_date,
        "end_date": request.end_date,
        "number_of_bars": number_of_bars,
        "session_basis": request.session_basis,
        "session_hours": session_hours,
    }
    payload["meta"]["symbol_info"] = resolve_symbol_price_metadata(
        source, request.symbol
    )
    return payload
