"""Data Manager dataset operations and persistence service.

Description:
    Provides dataset mutation, maintenance, and data management services for
    the Data Manager workspace, operating directly on the authoritative
    datamgr_datasets catalog table. Validates field constraints, tracks
    modification timestamps, and persists changes through HostPersistence.

Purpose:
    FEAT-DATAMGR-DATA: Data Manager dataset records and market data operations.

Key Capabilities:
    - FR-DATAMGR-DATA-EDIT: Edit dataset values [Data.edit()] (INFO/WARNING/ERROR).

Python API Usage:
    ```python
    from app.workspace.data_manager.data import Data, DataCLI

    service = Data()
    updated = service.edit("dukascopy:EURUSD", {"symbol": "EURUSD"})
    print(DataCLI.format_output(updated))
    ```

CLI Usage:
    ```bash
    uv run python -m app.workspace.data_manager.data
    ```
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from app.host.logging import get_logger
from app.host.persistence import HostPersistence

__all__ = [
    "Data",
    "DataCLI",
]

logger = get_logger(__name__)

EDIT_FR = "FR-DATAMGR-DATA-EDIT"
_CONTROL_START = 32
_TEXT_LIMIT = 500

_ALLOWED_EDIT_COLUMNS = frozenset(
    {
        "source",
        "symbol",
        "underlying",
        "instrument",
        "timeframe",
        "broker",
        "broker_name",
        "timezone",
        "category",
        "date_from",
        "date_to",
        "bars",
        "path",
        "data_kind",
        "quality_score",
        "lineage_json",
        "schema_version",
    }
)


@dataclass(frozen=True)
class _Config:
    """Internal module configuration for Data manager."""

    table: str = "datamgr_datasets"

    def to_dict(self) -> dict[str, Any]:
        """Convert configuration to standard dictionary."""
        return {"table": self.table}


class Data:
    """Service implementing dataset management and mutation logic."""

    def __init__(self, config: _Config | None = None) -> None:
        """Initialize Data service with optional internal configuration."""
        self._config = config or _Config()

    def edit(
        self,
        dataset_id: str,
        updates: Mapping[str, Any] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Edit an existing dataset record in the datamgr_datasets table.

        Args:
            dataset_id: Unique primary key identifier of the dataset.
            updates: Optional mapping of column names to new values.
            **kwargs: Additional column values to update.

        Returns:
            Dictionary representation of the updated dataset record.

        Raises:
            TypeError: If arguments have invalid types.
            ValueError: If dataset_id is empty or updates are empty/invalid.
            LookupError: If dataset_id does not exist in datamgr_datasets.
            RuntimeError: If database persistence fails.
        """
        combined = dict(updates or {})
        combined.update(kwargs)
        extra = {"fr_id": EDIT_FR, "dataset_id": dataset_id}

        try:
            self._validate_dataset_id(dataset_id)
            clean_updates = self._validate_and_prepare_updates(dataset_id, combined)
            self._ensure_dataset_exists(dataset_id)
        except (TypeError, ValueError, LookupError) as err:
            logger.warning("%s: Edit request rejected: %s", EDIT_FR, err, extra=extra)
            raise

        try:
            HostPersistence.update_record(
                self._config.table,
                {"id": dataset_id},
                clean_updates,
            )
        except Exception as err:
            logger.error(  # noqa: TRY400
                "%s: Persistence failed: %s", EDIT_FR, err, extra=extra
            )
            raise RuntimeError(
                f"Failed to update dataset '{dataset_id}': {err}"
            ) from err

        rows = HostPersistence.read_records(
            self._config.table,
            {"id": dataset_id},
            limit=1,
        )
        if not rows:
            logger.error(
                "%s: Record missing after update: %s",
                EDIT_FR,
                dataset_id,
                extra=extra,
            )
            raise RuntimeError(f"Updated dataset '{dataset_id}' could not be re-read.")

        updated_record = rows[0]
        logger.info(
            "%s: Dataset '%s' updated (%s)",
            EDIT_FR,
            dataset_id,
            ", ".join(sorted(clean_updates.keys())),
            extra={**extra, "updated_fields": sorted(clean_updates.keys())},
        )
        return updated_record

    def _validate_dataset_id(self, dataset_id: Any) -> None:
        """Validate that dataset_id is a valid non-empty string."""
        if not isinstance(dataset_id, str):
            raise TypeError("Dataset ID must be a string.")
        if not dataset_id.strip():
            raise ValueError("Dataset ID must be a non-empty string.")
        if any(ord(c) < _CONTROL_START for c in dataset_id):
            raise ValueError("Dataset ID cannot contain control characters.")

    def _ensure_dataset_exists(self, dataset_id: str) -> dict[str, Any]:
        """Ensure that dataset exists in catalog and return existing row."""
        rows = HostPersistence.read_records(
            self._config.table,
            {"id": dataset_id},
            limit=1,
        )
        if not rows:
            raise LookupError(f"Dataset '{dataset_id}' not found in catalog.")
        return rows[0]

    def _validate_and_prepare_updates(
        self,
        dataset_id: str,
        updates: dict[str, Any],
    ) -> dict[str, Any]:
        """Validate updates dictionary and return sanitized persistence dictionary."""
        if not updates:
            raise ValueError("Updates payload cannot be empty.")

        clean: dict[str, Any] = {}
        for key, val in updates.items():
            if not isinstance(key, str):
                raise TypeError("Update column keys must be strings.")
            if key == "id":
                if val != dataset_id:
                    raise ValueError("Dataset primary key 'id' cannot be modified.")
                continue
            if key == "created_at":
                raise ValueError("Field 'created_at' cannot be modified.")
            if key not in _ALLOWED_EDIT_COLUMNS:
                raise ValueError(f"Unknown or non-editable column: '{key}'")
            clean[key] = self._sanitize_column_value(key, val)

        if not clean:
            raise ValueError("No editable values provided in updates payload.")

        clean["updated_at"] = datetime.now(UTC).isoformat()
        return clean

    def _sanitize_column_value(self, column: str, value: Any) -> Any:
        """Validate and cast individual column values according to schema."""
        if column in ("bars", "schema_version", "quality_score"):
            return self._sanitize_numeric(column, value)
        if column == "lineage_json":
            return self._sanitize_json(column, value)
        return self._sanitize_text(column, value)

    def _sanitize_numeric(self, column: str, value: Any) -> int | float:
        """Validate and cast numeric columns."""
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError(f"Column '{column}' must be a number.")

        if column == "bars":
            int_val = int(value)
            if int_val < 0:
                raise ValueError(f"Column '{column}' cannot be negative.")
            return int_val

        if column == "schema_version":
            return int(value)

        float_val = float(value)
        if not (0.0 <= float_val <= 1.0):
            raise ValueError(f"Column '{column}' must be between 0.0 and 1.0.")
        return float_val

    def _sanitize_json(self, column: str, value: Any) -> str:
        """Validate and cast JSON column values."""
        if isinstance(value, Mapping):
            return json.dumps(value)
        if isinstance(value, str):
            try:
                json.loads(value)
            except (ValueError, TypeError) as err:
                raise ValueError(f"Column '{column}' must be valid JSON.") from err
            return value
        raise TypeError(f"Column '{column}' must be JSON string or mapping.")

    def _sanitize_text(self, column: str, value: Any) -> str:
        """Validate string text columns."""
        if not isinstance(value, str):
            raise TypeError(f"Column '{column}' must be a string.")
        if len(value) > _TEXT_LIMIT:
            raise ValueError(
                f"Column '{column}' exceeds length limit of {_TEXT_LIMIT} characters."
            )
        if any(ord(c) < _CONTROL_START for c in value):
            raise ValueError(f"Column '{column}' contains control characters.")
        return value


class DataCLI:
    """Headless CLI formatter for Data service."""

    @classmethod
    def format_output(cls, data: Mapping[str, Any]) -> str:
        """Format dataset record into human-readable terminal output."""
        logger.debug("Formatting CLI output (%d keys)", len(data))
        lines = [f"{k}: {v}" for k, v in sorted(data.items())]
        return "\n".join(lines)


if __name__ == "__main__":
    service = Data()
    records = HostPersistence.read_records("datamgr_datasets", limit=1)
    if records:
        target_id = str(records[0]["id"])
        result = service.edit(target_id, {"broker_name": records[0]["broker_name"]})
        print(DataCLI.format_output(result))
    else:
        print("No datasets found in datamgr_datasets.")
