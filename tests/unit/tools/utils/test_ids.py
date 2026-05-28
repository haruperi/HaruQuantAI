"""Unit tests for tools.utils.ids."""

from __future__ import annotations

import pytest

from tools.utils.ids import (
    REQUEST_ID_PREFIX,
    RUN_ID_PREFIX,
    TOOL_CALL_ID_PREFIX,
    UUID_HEX_LENGTH,
    WORKFLOW_ID_PREFIX,
    _new_prefixed_id,
    is_request_id,
    is_run_id,
    is_tool_call_id,
    is_valid_prefixed_id,
    is_workflow_id,
    new_request_id,
    new_run_id,
    new_tool_call_id,
    new_workflow_id,
)


def _assert_standard_id(value: str, prefix: str) -> None:
    assert value.startswith(f"{prefix}_")
    suffix = value.split("_", maxsplit=1)[1]
    assert len(suffix) == UUID_HEX_LENGTH
    assert suffix == suffix.lower()
    int(suffix, 16)


@pytest.mark.parametrize(
    ("factory", "prefix"),
    [
        (new_request_id, REQUEST_ID_PREFIX),
        (new_workflow_id, WORKFLOW_ID_PREFIX),
        (new_run_id, RUN_ID_PREFIX),
        (new_tool_call_id, TOOL_CALL_ID_PREFIX),
    ],
)
def test_new_ids_have_expected_format(factory, prefix: str) -> None:
    generated_id = factory()

    _assert_standard_id(generated_id, prefix)


def test_generated_ids_are_unique() -> None:
    ids = {new_request_id() for _ in range(100)}

    assert len(ids) == 100


@pytest.mark.parametrize(
    ("factory", "validator"),
    [
        (new_request_id, is_request_id),
        (new_workflow_id, is_workflow_id),
        (new_run_id, is_run_id),
        (new_tool_call_id, is_tool_call_id),
    ],
)
def test_convenience_validators_accept_matching_ids(factory, validator) -> None:
    assert validator(factory()) is True


def test_is_valid_prefixed_id_accepts_valid_id() -> None:
    request_id = new_request_id()

    assert is_valid_prefixed_id(request_id, REQUEST_ID_PREFIX) is True


def test_is_valid_prefixed_id_rejects_wrong_prefix() -> None:
    request_id = new_request_id()

    assert is_valid_prefixed_id(request_id, WORKFLOW_ID_PREFIX) is False


@pytest.mark.parametrize(
    "value",
    [
        "",
        "req",
        "req_",
        "req_not-a-uuid",
        "req_123",
        "req_" + "g" * 32,
        "REQ_" + "a" * 32,
        123,
        None,
    ],
)
def test_is_valid_prefixed_id_rejects_malformed_values(value) -> None:
    assert is_valid_prefixed_id(value, REQUEST_ID_PREFIX) is False


@pytest.mark.parametrize("prefix", ["", " ", "unknown", "bad prefix", "req\n"])
def test_new_prefixed_id_rejects_invalid_prefix(prefix: str) -> None:
    with pytest.raises(ValueError):
        _new_prefixed_id(prefix)


def test_new_prefixed_id_rejects_non_string_prefix() -> None:
    with pytest.raises(TypeError, match="prefix must be a string"):
        _new_prefixed_id(123)  # type: ignore[arg-type]


def test_is_valid_prefixed_id_rejects_invalid_expected_prefix() -> None:
    with pytest.raises(ValueError):
        is_valid_prefixed_id("req_" + "a" * 32, "bad")
