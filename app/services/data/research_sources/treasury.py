"""Treasury Fiscal Data API response normalization."""

from __future__ import annotations

import json
from datetime import datetime

from app.services.data.contracts.errors import DataError

_METADATA_FIELDS = {
    "record_date",
    "record_calendar_day",
    "record_calendar_month",
    "record_calendar_quarter",
    "record_calendar_year",
    "record_fiscal_quarter",
    "record_fiscal_year",
    "src_line_nbr",
}


def parse_payload(
    payload: bytes,
    observed_at: datetime,
) -> tuple[dict[str, object], ...]:
    """Parse Treasury Fiscal Data rows."""
    try:
        rows = json.loads(payload)["data"]
    except (KeyError, TypeError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise DataError(
            "INVALID_INPUT", safe_details={"field": "treasury_payload"}
        ) from error
    observations: list[dict[str, object]] = []
    for row in rows[:100]:
        period = str(row.get("record_date", ""))
        for key, value in row.items():
            if key in _METADATA_FIELDS or value in (None, ""):
                continue
            observations.append(
                {
                    "series_id": str(key),
                    "observation_period": period,
                    "value": value,
                    "unit": "USD" if key.endswith("_amt") else None,
                }
            )
    return (
        {
            "external_id": f"treasury-{observed_at.isoformat()}",
            "document_kind": "fiscal_observations",
            "title": "U.S. Treasury Fiscal Data",
            "published_at": observed_at.isoformat(),
            "available_at": observed_at.isoformat(),
            "canonical_locator": "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/",
            "parser_version": "treasury-fiscal-data-v1",
            "observations": tuple(observations[:200]),
        },
    )


__all__: tuple[str, ...] = ()
