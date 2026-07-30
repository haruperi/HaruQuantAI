"""USDA NASS Quick Stats response normalization."""

from __future__ import annotations

import json
from datetime import datetime

from app.services.data.contracts.errors import DataError


def parse_payload(
    payload: bytes,
    observed_at: datetime,
) -> tuple[dict[str, object], ...]:
    """Parse official agricultural estimates."""
    try:
        rows = json.loads(payload)["data"]
    except (KeyError, TypeError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise DataError(
            "INVALID_INPUT", safe_details={"field": "nass_payload"}
        ) from error
    observations = tuple(
        {
            "series_id": ":".join(
                str(row.get(key, ""))
                for key in ("commodity_desc", "statisticcat_desc", "state_alpha")
            ),
            "observation_period": str(
                row.get("reference_period_desc", row.get("year", ""))
            ),
            "value": row.get("Value"),
            "unit": row.get("unit_desc"),
        }
        for row in rows[:200]
    )
    return (
        {
            "external_id": f"usda-nass-{observed_at.isoformat()}",
            "document_kind": "agricultural_observations",
            "title": "USDA NASS Quick Stats",
            "published_at": observed_at.isoformat(),
            "available_at": observed_at.isoformat(),
            "canonical_locator": "https://quickstats.nass.usda.gov/api/api_GET/",
            "parser_version": "usda-nass-v1",
            "observations": observations,
        },
    )


__all__: tuple[str, ...] = ()
