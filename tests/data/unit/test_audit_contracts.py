"""Unit tests for governed audit query and page contracts."""

from datetime import timedelta

import pytest
from app.services.data.contracts import (
    AUDIT_QUERY_HARD_MAX_LIMIT,
    AuditEventPage,
    AuditEventQuery,
)
from app.services.data.contracts.errors import DataError

from tests.data.helpers import END, START, make_audit_event


def test_query_requires_ordered_bounded_filters() -> None:
    """Audit queries enforce UTC ordering and the hard page ceiling."""
    with pytest.raises(DataError) as captured:
        AuditEventQuery(
            start=START,
            end=END,
            limit=AUDIT_QUERY_HARD_MAX_LIMIT + 1,
            request_id="req-c0e73c3b04d55f8a499cc0bc8bbbab30453cd56962a7355d90d3c628dfde0db8",
        )
    assert captured.value.code == "INVALID_INPUT"


def test_page_is_ordered_and_storage_free() -> None:
    """Pages contain only ordered Utils AuditEvent contracts."""
    later = make_audit_event(timestamp=START + timedelta(seconds=1))
    earlier = make_audit_event(timestamp=START)
    with pytest.raises(DataError) as captured:
        AuditEventPage(
            events=(later, earlier),
            request_id="req-b337f6a712c0b80c539c8485688c8399244e55370fbb2e44fd5aa9eebc2dde19",
        )
    assert captured.value.code == "INVALID_INPUT"
    assert "connection" not in AuditEventPage.model_fields
