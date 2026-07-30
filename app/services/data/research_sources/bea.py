"""BEA API response normalization."""

from __future__ import annotations

import json
from datetime import datetime

from app.services.data.contracts.errors import DataError


def parse_payload(
    payload: bytes,
    observed_at: datetime,
) -> tuple[dict[str, object], ...]:
    """Parse BEA result rows into point-in-time observations."""
    try:
        root = json.loads(payload)
        results = root["BEAAPI"]["Results"]
        rows = results["Data"]
    except (KeyError, TypeError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise DataError(
            "INVALID_INPUT", safe_details={"field": "bea_payload"}
        ) from error
    observations = tuple(
        {
            "series_id": str(row.get("LineCode", row.get("GeoFIPS", "bea"))),
            "observation_period": str(row.get("TimePeriod", row.get("Year", ""))),
            "value": row.get("DataValue"),
            "unit": row.get("UNIT_MULT"),
        }
        for row in rows[:200]
    )
    return (
        {
            "external_id": f"bea-{observed_at.isoformat()}",
            "document_kind": "macro_observations",
            "title": "BEA published economic statistics",
            "published_at": observed_at.isoformat(),
            "available_at": observed_at.isoformat(),
            "canonical_locator": "https://apps.bea.gov/api/data",
            "parser_version": "bea-api-v1",
            "observations": observations,
        },
    )


__all__: tuple[str, ...] = ()
