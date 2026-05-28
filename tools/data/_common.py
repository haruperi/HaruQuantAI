"""Shared data persistence helpers for HaruQuantAI data tools.

This module supports data-domain tools with compact CSV persistence utilities.
It is an internal helper module, not an official AI-tool registry.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, cast

import pandas as pd

PathLike = str | Path

DEFAULT_SAVE_DIR = Path("data/saved")


@dataclass(frozen=True)
class Data:
    """Container for market data and lightweight metadata."""

    df: pd.DataFrame
    symbol: str = "EURUSD"
    timeframe: str = "M1"
    metadata: dict[str, Any] = field(default_factory=dict)


def _saved_data_path(
    *,
    extension: str,
    path: PathLike | None = None,
    symbol: str = "EURUSD",
    timeframe: str = "M1",
) -> Path:
    """Build the target path for a saved data artifact."""
    if path is not None:
        return Path(path).expanduser()
    suffix = extension.lstrip(".")
    return DEFAULT_SAVE_DIR / f"{symbol.upper()}_{timeframe.upper()}.{suffix}"


def _metadata_path(data_path: Path) -> Path:
    """Return the JSON sidecar metadata path for a data artifact."""
    return data_path.with_suffix(f"{data_path.suffix}.metadata.json")


def _frame_from_payload(data: Data | Mapping[str, Any]) -> Data:
    """Convert supported payloads into a Data object."""
    if isinstance(data, Data):
        return data

    if not isinstance(data, Mapping):
        raise TypeError("data must be a Data instance or mapping payload.")

    records = data.get("data") if "data" in data else data.get("candles")
    if not isinstance(records, list):
        raise ValueError("data payload must contain a list under 'data' or 'candles'.")

    frame = pd.DataFrame(records)
    if frame.empty:
        raise ValueError("data payload contains no records.")

    symbol = str(data.get("symbol") or "EURUSD").upper()
    timeframe = str(data.get("timeframe") or "M1").upper()
    metadata = {
        key: value
        for key, value in data.items()
        if key not in {"data", "candles", "symbol", "timeframe"}
    }
    return Data(df=frame, symbol=symbol, timeframe=timeframe, metadata=metadata)


def _data_to_metadata(data: Data) -> dict[str, Any]:
    """Serialize Data metadata to a JSON-safe dictionary."""
    return {
        "symbol": data.symbol,
        "timeframe": data.timeframe,
        "rows": int(len(data.df)),
        "columns": [str(column) for column in data.df.columns],
        **dict(data.metadata),
    }


def _save_data(
    data: Data | Mapping[str, Any],
    *,
    extension: str,
    path: PathLike | None = None,
    is_initial: bool = False,
) -> dict[str, Any]:
    """Save market data and metadata to disk."""
    data_obj = _frame_from_payload(data)
    target_path = _saved_data_path(
        extension=extension,
        path=path,
        symbol=data_obj.symbol,
        timeframe=data_obj.timeframe,
    )
    target_path.parent.mkdir(parents=True, exist_ok=True)
    data_obj.df.to_csv(target_path, index=False)

    metadata = _data_to_metadata(data_obj)
    metadata["is_initial"] = bool(is_initial)
    sidecar_path = _metadata_path(target_path)
    sidecar_path.write_text(
        json.dumps(metadata, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    return {
        "path": str(target_path),
        "metadata_path": str(sidecar_path),
        "metadata": metadata,
    }


def _load_saved_data(
    *,
    extension: str,
    path: PathLike | None = None,
    symbol: str = "EURUSD",
    timeframe: str = "M1",
) -> Data:
    """Load a saved market-data artifact and its metadata."""
    target_path = _saved_data_path(
        extension=extension,
        path=path,
        symbol=symbol,
        timeframe=timeframe,
    )
    if not target_path.exists():
        raise FileNotFoundError(f"Saved data file not found: {target_path}")

    frame = pd.read_csv(target_path)
    sidecar_path = _metadata_path(target_path)
    metadata: dict[str, Any] = {}
    if sidecar_path.exists():
        metadata = json.loads(sidecar_path.read_text(encoding="utf-8"))

    return Data(
        df=frame,
        symbol=str(metadata.get("symbol") or symbol).upper(),
        timeframe=str(metadata.get("timeframe") or timeframe).upper(),
        metadata=metadata,
    )


def _serialize_frame_records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    """Serialize a DataFrame into JSON-safe row dictionaries."""
    serializable = frame.reset_index()
    records = json.loads(serializable.to_json(orient="records", date_format="iso"))
    return cast(list[dict[str, Any]], records)


__all__ = [
    "Data",
    "_data_to_metadata",
    "_load_saved_data",
    "_save_data",
    "_saved_data_path",
    "_serialize_frame_records",
]
