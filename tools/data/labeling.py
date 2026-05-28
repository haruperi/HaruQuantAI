"""Supervised market-data labeling tools for HaruQuantAI.

This module contains one official AI-callable labeling tool and several
internal helpers for converting market-data inputs into numeric price series.

Exported AI Tools:
    - labeler_lexlb: Label local peaks and troughs using the LEXLB method.

Internal Helpers:
    - _tool_metadata
    - _is_number
    - _validation_error
    - _coerce_price_series
    - _serialize_labels
    - _count_labels

Classes:
    None

Label Semantics:
    - 1: confirmed local peak
    - -1: confirmed local trough
    - 0: no extrema label
"""

from __future__ import annotations

import math
import time
from typing import Any, Dict, Mapping, Optional, Union

import pandas as pd

from tools.utils import logger

from ._common import Data, _frame_from_payload

TOOL_VERSION = "1.0.0"
TOOL_CATEGORY = "data"
TOOL_RISK_LEVEL = "low"
REQUIRES_APPROVAL = False
READ_ONLY = True
WRITES_FILE = False
MODIFIES_DATABASE = False
PLACES_TRADE = False
REQUIRES_NETWORK = False

LABELER_LEXLB_TOOL_NAME = "labeler_lexlb"


def _tool_metadata(tool_name: str) -> Dict[str, Any]:
    """Return static metadata for labeling tools.

    Args:
        tool_name: Official AI Tool name.

    Returns:
        Dict[str, Any]: Tool metadata and side-effect flags.
    """
    return {
        "tool_name": tool_name,
        "tool_version": TOOL_VERSION,
        "tool_category": TOOL_CATEGORY,
        "tool_risk_level": TOOL_RISK_LEVEL,
        "requires_approval": REQUIRES_APPROVAL,
        "read_only": READ_ONLY,
        "writes_file": WRITES_FILE,
        "modifies_database": MODIFIES_DATABASE,
        "places_trade": PLACES_TRADE,
        "requires_network": REQUIRES_NETWORK,
    }


def _is_number(value: Any) -> bool:
    """Return True when a value is a finite int or float, excluding bool."""
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
    )


def _validation_error(
    *,
    tool_name: str,
    started_at: float,
    request_id: Optional[str],
    message: str,
    details: Optional[str] = None,
) -> Dict[str, Any]:
    """Return a standard validation error response with labeling metadata."""
    logger.warning(
        "%s validation failed | request_id=%s | reason=%s",
        tool_name,
        request_id,
        details or message,
    )
    return _tool_response(
        tool_name=tool_name,
        started_at=started_at,
        request_id=request_id,
        status="error",
        message=message,
        error_code="INVALID_INPUT",
        error_details=details or message,
    )


def _execution_ms(started_at: float) -> float:
    """Return elapsed tool execution time in milliseconds."""
    return round((time.perf_counter() - started_at) * 1000, 3)


def _tool_response(
    *,
    tool_name: str,
    started_at: float,
    request_id: Optional[str],
    status: str,
    message: str,
    data: Any = None,
    error_code: Optional[str] = None,
    error_details: Optional[str] = None,
) -> Dict[str, Any]:
    """Build a standard HaruQuantAI tool response."""
    error = None
    if status == "error":
        error = {
            "code": error_code or "TOOL_EXECUTION_FAILED",
            "details": error_details or message,
        }
    metadata = _tool_metadata(tool_name)
    metadata["request_id"] = request_id
    metadata["execution_ms"] = _execution_ms(started_at)
    return {
        "status": status,
        "message": message,
        "data": data if status == "success" else None,
        "error": error,
        "metadata": metadata,
    }


def _execution_error(
    *,
    tool_name: str,
    started_at: float,
    request_id: Optional[str],
    error: Exception,
) -> Dict[str, Any]:
    """Return a logged TOOL_EXECUTION_FAILED response."""
    logger.exception("%s failed | request_id=%s", tool_name, request_id)
    return _tool_response(
        tool_name=tool_name,
        started_at=started_at,
        request_id=request_id,
        status="error",
        message="Tool execution failed.",
        error_code="TOOL_EXECUTION_FAILED",
        error_details=str(error),
    )


def _coerce_price_series(data: Union[pd.Series, Data, Mapping[str, Any]]) -> pd.Series:
    """Convert supported labeling inputs into a numeric price series.

    Args:
        data: A pandas Series, HaruQuant Data object, or market-data payload.

    Returns:
        pd.Series: Numeric price series with NaN values removed.

    Raises:
        TypeError: If the input cannot be converted to a Series.
        ValueError: If the resolved series is empty or non-numeric.
    """
    if isinstance(data, pd.Series):
        series = data.copy()
    elif isinstance(data, Data):
        series = data.df["close"].copy()
    elif isinstance(data, Mapping):
        series = _frame_from_payload(dict(data)).df["close"].copy()
    else:
        raise TypeError(
            "data must be a pandas Series, HaruQuant Data object, "
            "or market-data payload."
        )

    if not isinstance(series, pd.Series):
        raise TypeError("Resolved data is not a pandas Series.")

    series = pd.to_numeric(series, errors="coerce").dropna()
    if series.empty:
        raise ValueError(
            "Resolved price series is empty or contains no numeric values."
        )

    return series.astype(float)


def _serialize_labels(labels: pd.Series) -> list[Dict[str, Any]]:
    """Serialize label series into a consistent JSON-safe record list.

    Args:
        labels: Series containing integer labels.

    Returns:
        list[Dict[str, Any]]: Records with index, timestamp, and label fields.
    """
    records: list[Dict[str, Any]] = []
    for idx, value in labels.items():
        timestamp: Optional[str]
        if isinstance(idx, pd.Timestamp):
            timestamp = idx.isoformat()
            index_value = idx.isoformat()
        elif hasattr(idx, "isoformat"):
            timestamp = idx.isoformat()
            index_value = idx.isoformat()
        else:
            timestamp = None
            index_value = str(idx)

        records.append(
            {
                "index": index_value,
                "timestamp": timestamp,
                "label": int(value),
            }
        )
    return records


def _count_labels(labels: pd.Series) -> Dict[str, int]:
    """Return count summary for LEXLB labels."""
    return {
        "rows": int(len(labels)),
        "positive_labels": int((labels == 1).sum()),
        "negative_labels": int((labels == -1).sum()),
        "neutral_labels": int((labels == 0).sum()),
    }


def labeler_lexlb(  # noqa: C901
    data: Union[pd.Series, Data, Dict[str, Any]],
    up_threshold: float,
    down_threshold: float,
    request_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Label local extrema with the LEXLB method.

    Use this tool when an agent needs supervised-learning labels that identify
    local peaks and troughs in a price series.

    Label semantics:
        - 1: confirmed local peak
        - -1: confirmed local trough
        - 0: no extrema label

    Args:
        data: Price Series, HaruQuant Data object, or JSON-safe market-data
            payload containing close prices.
        up_threshold: Fractional rise required to confirm a trough-to-peak move.
            Example: 0.01 means 1%.
        down_threshold: Fractional drop required to confirm a peak-to-trough
            move. Example: 0.01 means 1%.
        request_id: Optional workflow/request ID used for traceable logs and
            tool metadata.

    Returns:
        Dict[str, Any]: Standard tool response containing serialized labels,
        label counts, error, and metadata.

    Error Cases:
        INVALID_INPUT: data is missing, thresholds are invalid, or no numeric
            series can be resolved.
        TOOL_EXECUTION_FAILED: An unexpected labeling failure occurs.

    Side Effects:
        None. This tool is read-only, does not write files, does not modify a
        database, does not require network access, and does not place trades.
    """
    tool_name = LABELER_LEXLB_TOOL_NAME
    started_at = time.perf_counter()
    logger.info("%s called | request_id=%s", tool_name, request_id)

    if data is None:
        return _validation_error(
            tool_name=tool_name,
            started_at=started_at,
            request_id=request_id,
            message="Invalid input.",
            details="data argument is required.",
        )
    if not _is_number(up_threshold) or float(up_threshold) <= 0:
        return _validation_error(
            tool_name=tool_name,
            started_at=started_at,
            request_id=request_id,
            message="Invalid input.",
            details="up_threshold must be a positive finite number.",
        )
    if not _is_number(down_threshold) or float(down_threshold) <= 0:
        return _validation_error(
            tool_name=tool_name,
            started_at=started_at,
            request_id=request_id,
            message="Invalid input.",
            details="down_threshold must be a positive finite number.",
        )

    try:
        series = _coerce_price_series(data)
        labels = pd.Series(0, index=series.index, dtype="int64")

        if len(series) < 2:
            summary = _count_labels(labels)
            payload = {
                "labels": _serialize_labels(labels),
                "summary": summary,
                "label_semantics": {
                    "1": "confirmed local peak",
                    "-1": "confirmed local trough",
                    "0": "no extrema label",
                },
            }
            logger.info(
                "%s completed successfully | request_id=%s", tool_name, request_id
            )
            return _tool_response(
                tool_name=tool_name,
                started_at=started_at,
                request_id=request_id,
                status="success",
                message="Not enough data to label extrema.",
                data=payload,
            )

        up = float(up_threshold)
        down = float(down_threshold)
        last_extrema_val = float(series.iloc[0])
        last_extrema_idx = series.index[0]
        mode = 0

        for idx in range(1, len(series)):
            current_value = float(series.iloc[idx])
            current_idx = series.index[idx]

            if mode == 0:
                if current_value >= last_extrema_val * (1 + up):
                    mode = 1
                    last_extrema_val = current_value
                    last_extrema_idx = current_idx
                elif current_value <= last_extrema_val * (1 - down):
                    mode = -1
                    last_extrema_val = current_value
                    last_extrema_idx = current_idx
            elif mode == 1:
                if current_value > last_extrema_val:
                    last_extrema_val = current_value
                    last_extrema_idx = current_idx
                elif current_value <= last_extrema_val * (1 - down):
                    labels.loc[last_extrema_idx] = 1
                    mode = -1
                    last_extrema_val = current_value
                    last_extrema_idx = current_idx
            else:
                if current_value < last_extrema_val:
                    last_extrema_val = current_value
                    last_extrema_idx = current_idx
                elif current_value >= last_extrema_val * (1 + up):
                    labels.loc[last_extrema_idx] = -1
                    mode = 1
                    last_extrema_val = current_value
                    last_extrema_idx = current_idx

        summary = _count_labels(labels)
        payload = {
            "labels": _serialize_labels(labels),
            "summary": summary,
            "label_semantics": {
                "1": "confirmed local peak",
                "-1": "confirmed local trough",
                "0": "no extrema label",
            },
        }

        logger.info(
            (
                "%s completed successfully | request_id=%s | rows=%s | "
                "peaks=%s | troughs=%s"
            ),
            tool_name,
            request_id,
            summary["rows"],
            summary["positive_labels"],
            summary["negative_labels"],
        )
        return _tool_response(
            tool_name=tool_name,
            started_at=started_at,
            request_id=request_id,
            status="success",
            message="LEXLB labels generated successfully.",
            data=payload,
        )
    except (TypeError, ValueError) as error:
        return _validation_error(
            tool_name=tool_name,
            started_at=started_at,
            request_id=request_id,
            message="Invalid input.",
            details=str(error),
        )
    except Exception as error:
        return _execution_error(
            tool_name=tool_name,
            started_at=started_at,
            request_id=request_id,
            error=error,
        )


__all__ = ["labeler_lexlb"]
