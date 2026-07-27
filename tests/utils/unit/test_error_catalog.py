"""Unit tests for shared error definitions and catalogue validation."""

from dataclasses import FrozenInstanceError

import pytest
from app.utils import (
    COMMON_ERROR_CATALOG,
    ErrorDefinition,
    ValidationError,
    require_error_definition,
    validate_error_catalog,
)


def test_common_error_catalog_is_immutable_and_valid() -> None:
    validated = validate_error_catalog(COMMON_ERROR_CATALOG)
    definition = validated["INTERNAL_ERROR"]
    assert definition.description == "Internal error"
    assert definition.domain == "utils"
    runtime_definition = validated["SYSTEM_RUNTIME_ROUTE_INCOMPATIBLE"]
    assert (
        runtime_definition.description
        == "Runtime profile and execution route are incompatible"
    )
    assert runtime_definition.domain == "app"

    with pytest.raises(TypeError):
        validated["NEW_ERROR"] = definition  # type: ignore[index]
    with pytest.raises(FrozenInstanceError):
        definition.description = "changed"  # type: ignore[misc]


def test_catalog_rejects_key_definition_mismatch() -> None:
    definition = ErrorDefinition(
        code="DOMAIN_FAILURE",
        domain="example",
        description="The operation failed",
        category="operation",
        severity="error",
        retryable=False,
        operator_action="Inspect safe diagnostics",
    )
    with pytest.raises(ValidationError) as error:
        validate_error_catalog({"OTHER_FAILURE": definition})
    assert error.value.code == "ERROR_CATALOG_INVALID"
    assert error.value.detail == "CODE_MISMATCH"


def test_require_error_definition_rejects_unknown_code() -> None:
    with pytest.raises(ValidationError) as error:
        require_error_definition("DOMAIN_FAILURE", COMMON_ERROR_CATALOG)
    assert error.value.code == "ERROR_CODE_UNAPPROVED"
