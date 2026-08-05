"""Unit evidence for permanent Economic Calendar event definitions."""

from __future__ import annotations

import pytest
from app.services.data.contracts import DataError
from app.services.data.economic_calendar.event_urls import (
    discover_event_definitions,
    parse_event_definition,
)

_PAGE = """
# US Unemployment Rate

## Specs

###### Source:

[Bureau of Labor Statistics](https://www.bls.gov/) ([latest release](http://www.bls.gov/news.release/empsit.nr0.htm))

###### Measures:

Percentage of the total work force that is unemployed;

###### Usual Effect:

'Actual' less than 'Forecast' is good for currency;

###### Frequency:

Released monthly;

###### Also Called:

Jobless Rate;

###### Event Type:

Employment
"""


def test_parse_event_definition_preserves_verified_specs() -> None:
    """The detail parser preserves URLs and provider text exactly."""
    result = parse_event_definition(
        _PAGE,
        "https://www.forexfactory.com/calendar/56-us-unemployment-rate",
    )

    assert result == {
        "provider_definition_id": "56",
        "country": "USD",
        "title": "Unemployment Rate",
        "source_url": ("https://www.forexfactory.com/calendar/56-us-unemployment-rate"),
        "source_original": "https://www.bls.gov/",
        "source_latest": "http://www.bls.gov/news.release/empsit.nr0.htm",
        "measures": "Percentage of the total work force that is unemployed",
        "effect": "'Actual' less than 'Forecast' is good for currency",
        "frequency": "Released monthly",
        "also_called": "Jobless Rate",
        "event_type": "Employment",
    }


def test_parser_rejects_unverified_page() -> None:
    """A calendar URL without a Specs section fails closed."""
    with pytest.raises(DataError):
        parse_event_definition(
            "# US Unemployment Rate",
            "https://www.forexfactory.com/calendar/56",
        )


def test_discovery_skips_non_event_ids_without_inventing_records() -> None:
    """Bounded discovery yields only pages that verify as definitions."""
    pages = {
        "https://www.forexfactory.com/calendar/1": _PAGE,
        "https://www.forexfactory.com/calendar/2": "not an event",
    }

    definitions = list(
        discover_event_definitions(pages.__getitem__, start_id=1, end_id=2)
    )

    assert [item["provider_definition_id"] for item in definitions] == ["1"]
