"""Behaviour guard for the three consolidated DATA contract bases.

The pre-restructure package declared nine near-duplicate ``_Contract`` bases. They were
not identical, so ``CAP-DATA-026`` replaced them with three bases that between them
reproduce all nine exactly. Consolidating to a single base would have loosened
validation for the source, job, and account contracts.

These tests pin the two axes that actually differed — arbitrary type acceptance and
request-identifier validation — so a future simplification cannot quietly change
validation for a contract group.
"""

from __future__ import annotations

import pytest
from app.services.data.contracts import DataError
from app.services.data.contracts._base import (
    DataContractModel,
    FrozenContract,
    TracedContract,
    TracedOpenContract,
)
from pydantic import ConfigDict, ValidationError


class _Frozen(FrozenContract):
    """Probe contract on the untraced base."""

    request_id: str | None = None


class _Traced(TracedContract):
    """Probe contract on the traced base."""

    request_id: str | None = None


class _TracedOpen(TracedOpenContract):
    """Probe contract on the traced, arbitrary-type base."""

    request_id: str | None = None


@pytest.mark.parametrize("base", [_Frozen, _Traced, _TracedOpen])
def test_every_base_is_frozen(base: type) -> None:
    """Assert each base produces immutable contracts.

    Args:
        base: Probe contract class under test.

    Raises:
        AssertionError: If the contract permits mutation.
    """
    instance = base()
    with pytest.raises(ValidationError):
        instance.request_id = "req-mutated"


@pytest.mark.parametrize("base", [_Frozen, _Traced, _TracedOpen])
def test_every_base_forbids_unknown_fields(base: type) -> None:
    """Assert each base rejects an unknown field as ``INVALID_INPUT``.

    Args:
        base: Probe contract class under test.

    Raises:
        AssertionError: If the unknown field is accepted or mismapped.
    """
    with pytest.raises(DataError) as excinfo:
        base(unexpected_field="x")
    assert excinfo.value.code == "INVALID_INPUT"


@pytest.mark.parametrize("base", [_Frozen, _Traced, _TracedOpen])
def test_every_base_maps_validation_failure_to_data_error(base: type) -> None:
    """Assert no raw Pydantic error escapes the DATA boundary.

    Args:
        base: Probe contract class under test.

    Raises:
        AssertionError: If a non-``DataError`` exception escapes.
    """
    with pytest.raises(DataError):
        base(request_id=object())


def test_untraced_base_does_not_validate_request_identity() -> None:
    """Assert ``FrozenContract`` accepts a malformed request identifier.

    This reproduces the former ``contracts/sources.py`` base, which carried no trace
    validation. Adding validation here would newly reject source contracts that are
    valid today.

    Raises:
        AssertionError: If trace validation is applied to the untraced base.
    """
    assert _Frozen(request_id="not-a-valid-request-id").request_id == (
        "not-a-valid-request-id"
    )


@pytest.mark.parametrize("base", [_Traced, _TracedOpen])
def test_traced_bases_reject_a_malformed_request_identifier(base: type) -> None:
    """Assert the traced bases enforce the shared trace policy.

    Args:
        base: Probe contract class under test.

    Raises:
        AssertionError: If a malformed identifier is accepted.
    """
    with pytest.raises(DataError):
        base(request_id="not-a-valid-request-id")


def test_traced_bases_accept_the_legacy_request_identifier_form() -> None:
    """Assert the 68-character legacy request identifier still validates.

    Raises:
        AssertionError: If the documented compatibility fallback regressed.
    """
    legacy = "req-aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
    assert _Traced(request_id=legacy).request_id == legacy


def test_only_the_open_base_permits_arbitrary_types() -> None:
    """Assert arbitrary type acceptance is confined to ``TracedOpenContract``.

    Raises:
        AssertionError: If the configuration axis that separated the legacy bases
            has been lost.
    """
    assert TracedOpenContract.model_config.get("arbitrary_types_allowed") is True
    assert FrozenContract.model_config.get("arbitrary_types_allowed") is not True
    assert TracedContract.model_config.get("arbitrary_types_allowed") is not True


def test_data_contract_model_is_the_shared_root() -> None:
    """Assert all three bases share the error-mapping root.

    Raises:
        AssertionError: If a base bypasses ``DataContractModel``.
    """
    for base in (FrozenContract, TracedContract, TracedOpenContract):
        assert issubclass(base, DataContractModel)
    assert isinstance(FrozenContract.model_config, dict | ConfigDict)
