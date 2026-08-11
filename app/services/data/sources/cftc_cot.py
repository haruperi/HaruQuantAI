"""CFTC Commitments of Traders response normalization."""

from __future__ import annotations

import json
from datetime import datetime

from app.services.data.contracts.errors import DataError


def parse_payload(
    payload: bytes,
    observed_at: datetime,
) -> tuple[dict[str, object], ...]:
    """Parse CFTC public reporting rows without inferring trader intent.

    Args:
        payload: The ``payload`` argument.
        observed_at: The ``observed_at`` argument.

    Returns:
        The result produced by the operation.

    Raises:
        DataError: If the operation cannot be completed safely.
    """
    try:
        rows = json.loads(payload)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise DataError(
            "INVALID_INPUT", safe_details={"field": "cftc_payload"}
        ) from error
    if not isinstance(rows, list):
        raise DataError("INVALID_INPUT", safe_details={"field": "cftc_payload"})
    observations: list[dict[str, object]] = []
    for row in rows[:100]:
        if not isinstance(row, dict):
            continue
        period = str(row.get("report_date_as_yyyy_mm_dd", ""))
        market = str(row.get("market_and_exchange_names", "unknown"))
        for key, value in row.items():
            if key.endswith(("_all", "_old", "_other")):
                observations.append(
                    {
                        "series_id": f"{market}:{key}",
                        "observation_period": period,
                        "value": value,
                        "unit": "contracts",
                    }
                )
    return (
        {
            "external_id": f"cftc-cot-{observed_at.isoformat()}",
            "document_kind": "positioning_report",
            "title": "CFTC Commitments of Traders",
            "published_at": observed_at.isoformat(),
            "available_at": observed_at.isoformat(),
            "canonical_locator": "https://publicreporting.cftc.gov/",
            "parser_version": "cftc-cot-v1",
            "observations": tuple(observations[:200]),
        },
    )


__all__: tuple[str, ...] = ()
