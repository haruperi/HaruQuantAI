"""Label market data for supervised research workflows.

Purpose:
    Provide AI-callable labeling tools for supervised research datasets.

Exported AI Tools:
    - labeler_lexlb: Label local extrema with the LEXLB method.

Internal Helpers:
    None

Classes:
    None
"""

from __future__ import annotations

import time
from typing import Any

import pandas as pd

from app.services.utils.logger import logger

from .frames import Data, _data_from_payload
from .responses import (
    _data_tool_execution_error,
    _data_tool_response,
    _data_tool_validation_error,
)


def labeler_lexlb(  # noqa: C901
    data: pd.Series | Data | dict[str, Any],
    up_threshold: float,
    down_threshold: float,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Description.
        Label local extrema with the LEXLB method.
    
    Args:
        data: pd.Series | Data | dict[str, Any].
        up_threshold: float.
        down_threshold: float.
        request_id: str | None.
    
    Returns:
        dict[str, Any].
    """
    tool_name = "labeler_lexlb"
    started_at = time.perf_counter()
    logger.info("{} called | request_id={}", tool_name, request_id)

    if data is None:
        return _data_tool_validation_error(
            tool_name=tool_name,
            started_at=started_at,
            request_id=request_id,
            message="data argument is required.",
        )
    if up_threshold <= 0 or down_threshold <= 0:
        return _data_tool_validation_error(
            tool_name=tool_name,
            started_at=started_at,
            request_id=request_id,
            message="up_threshold and down_threshold must be positive.",
        )

    try:
        if isinstance(data, dict):
            series = _data_from_payload(data).close
        elif isinstance(data, Data):
            series = data.close
        else:
            series = data

        labels = pd.Series(0, index=series.index)
        if len(series) < 2:
            logger.info(
                "{} completed successfully | request_id={}", tool_name, request_id
            )
            return _data_tool_response(
                tool_name=tool_name,
                started_at=started_at,
                request_id=request_id,
                status="success",
                message="Not enough data to label extrema.",
                data={"labels": []},
            )

        last_extrema_val = series.iloc[0]
        last_extrema_idx = series.index[0]
        mode = 0
        for idx in range(1, len(series)):
            current_value = series.iloc[idx]
            if mode == 0:
                if current_value >= last_extrema_val * (1 + up_threshold):
                    mode = 1
                    last_extrema_val = current_value
                    last_extrema_idx = series.index[idx]
                elif current_value <= last_extrema_val * (1 - down_threshold):
                    mode = -1
                    last_extrema_val = current_value
                    last_extrema_idx = series.index[idx]
            elif mode == 1:
                if current_value > last_extrema_val:
                    last_extrema_val = current_value
                    last_extrema_idx = series.index[idx]
                elif current_value <= last_extrema_val * (1 - down_threshold):
                    labels.loc[last_extrema_idx] = 1
                    mode = -1
                    last_extrema_val = current_value
                    last_extrema_idx = series.index[idx]
            elif current_value < last_extrema_val:
                last_extrema_val = current_value
                last_extrema_idx = series.index[idx]
            elif current_value >= last_extrema_val * (1 + up_threshold):
                labels.loc[last_extrema_idx] = -1
                mode = 1
                last_extrema_val = current_value
                last_extrema_idx = series.index[idx]

        labels_df = pd.DataFrame({"label": labels})
        if isinstance(labels_df.index, pd.DatetimeIndex):
            records = [
                {
                    "timestamp": ts.isoformat()
                    if hasattr(ts, "isoformat")
                    else str(ts),
                    "label": int(row["label"]),
                }
                for ts, row in labels_df.iterrows()
            ]
        else:
            records = labels.tolist()

        logger.info("{} completed successfully | request_id={}", tool_name, request_id)
        return _data_tool_response(
            tool_name=tool_name,
            started_at=started_at,
            request_id=request_id,
            status="success",
            message="LEXLB labels generated successfully.",
            data={"labels": records},
        )
    except Exception as error:
        return _data_tool_execution_error(
            tool_name=tool_name,
            started_at=started_at,
            request_id=request_id,
            error=error,
        )


__all__ = ["labeler_lexlb"]
