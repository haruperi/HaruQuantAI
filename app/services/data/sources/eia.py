"""EIA API v2 response normalization."""

from __future__ import annotations

import json
from datetime import datetime

from app.services.data.contracts.errors import DataError


def parse_payload(
    payload: bytes,
    observed_at: datetime,
) -> tuple[dict[str, object], ...]:
    """Parse EIA response rows into point-in-time observations.

    Args:
        payload: The ``payload`` argument.
        observed_at: The ``observed_at`` argument.

    Returns:
        The result produced by the operation.

    Raises:
        DataError: If the operation cannot be completed safely.
    """
    try:
        response = json.loads(payload)["response"]
        rows = response["data"]
    except (KeyError, TypeError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise DataError(
            "INVALID_INPUT", safe_details={"field": "eia_payload"}
        ) from error
    observations: list[dict[str, object]] = []
    for row in rows[:200]:
        period = str(row.get("period", ""))
        for key, value in row.items():
            if key in {"period", "series-description", "unit"}:
                continue
            if isinstance(value, (int, float)):
                observations.append(
                    {
                        "series_id": str(key),
                        "observation_period": period,
                        "value": value,
                        "unit": row.get("unit"),
                    }
                )
    return (
        {
            "external_id": f"eia-{observed_at.isoformat()}",
            "document_kind": "energy_observations",
            "title": str(response.get("name", "EIA published energy data")),
            "published_at": observed_at.isoformat(),
            "available_at": observed_at.isoformat(),
            "canonical_locator": "https://api.eia.gov/v2/",
            "parser_version": "eia-v2-v1",
            "observations": tuple(observations),
        },
    )


__all__: tuple[str, ...] = ()
