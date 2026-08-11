"""BLS public API response normalization."""

from __future__ import annotations

import json
from datetime import datetime

from app.services.data.contracts.errors import DataError


def parse_payload(
    payload: bytes,
    observed_at: datetime,
) -> tuple[dict[str, object], ...]:
    """Parse BLS series observations with conservative availability.

    Args:
        payload: The ``payload`` argument.
        observed_at: The ``observed_at`` argument.

    Returns:
        The result produced by the operation.

    Raises:
        DataError: If the operation cannot be completed safely.
    """
    try:
        root = json.loads(payload)
        series = root["Results"]["series"]
    except (KeyError, TypeError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise DataError(
            "INVALID_INPUT", safe_details={"field": "bls_payload"}
        ) from error
    records: list[dict[str, object]] = []
    for item in series[:20]:
        series_id = str(item.get("seriesID", ""))
        values = tuple(
            {
                "series_id": series_id,
                "observation_period": f"{row.get('year', '')}-{row.get('period', '')}",
                "value": row.get("value"),
                "unit": None,
            }
            for row in item.get("data", [])[:20]
        )
        records.append(
            {
                "external_id": f"bls-{series_id}-{observed_at.date()}",
                "document_kind": "macro_observations",
                "title": f"BLS series {series_id}",
                "published_at": observed_at.isoformat(),
                "available_at": observed_at.isoformat(),
                "canonical_locator": "https://api.bls.gov/publicAPI/v2/timeseries/data/",
                "parser_version": "bls-v2-v1",
                "observations": values,
            }
        )
    return tuple(records)


__all__: tuple[str, ...] = ()
