"""Unit tests for versioned references."""

import pytest
from app.utils import build_profile_ref, parse_profile_ref
from app.utils.errors.exceptions import ValidationError


def test_profile_ref_round_trips_and_fails_closed() -> None:
    value = build_profile_ref(
        profile_kind="risk", profile_id="prf-1", version="1", content_hash="a" * 64
    )
    assert parse_profile_ref(value) == value
    value["contract_version"] = "v2"
    with pytest.raises(ValidationError):
        parse_profile_ref(value)
