from dataclasses import FrozenInstanceError

import pytest
from app.utils import (
    ErrorMetadata,
    ValidationError,
    get_error_metadata,
    normalize_error_code,
)


def test_normalize_and_lookup_error_metadata() -> None:
    assert normalize_error_code("validation-failed") == "VALIDATION_FAILED"
    metadata = get_error_metadata("validation failed")
    assert metadata == ErrorMetadata(
        code="VALIDATION_FAILED",
        title="Validation failed",
        severity="warning",
        retryable=False,
    )
    field_name = "title"
    with pytest.raises(FrozenInstanceError):
        setattr(metadata, field_name, "changed")


def test_error_metadata_rejects_malformed_code() -> None:
    with pytest.raises(ValidationError):
        normalize_error_code("***")
    generic = get_error_metadata("domain-owned-code")
    assert generic.code == "DOMAIN_OWNED_CODE"
    assert generic.title == "Application error"
