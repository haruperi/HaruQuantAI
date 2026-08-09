import pytest
from app.utils import create_validation_error
from app.utils.errors.exceptions import (
    ConfigurationError,
    ExternalServiceError,
    HaruQuantError,
    SecurityError,
    ValidationError,
)


def test_shared_exception_hierarchy() -> None:
    exceptions = (
        ConfigurationError("CONFIG_INVALID"),
        ValidationError("VALUE_INVALID"),
        SecurityError("SECURITY_BLOCKED"),
        ExternalServiceError("PROVIDER_FAILED"),
    )
    assert all(isinstance(error, HaruQuantError) for error in exceptions)


def test_create_validation_error_preserves_safe_symbolic_evidence() -> None:
    error = create_validation_error("VALIDATION_FAILED", "VALUE_INVALID")

    assert isinstance(error, ValidationError)
    assert error.code == "VALIDATION_FAILED"
    assert error.detail == "VALUE_INVALID"


def test_domains_extend_shared_base() -> None:
    class DomainError(HaruQuantError):
        pass

    error = DomainError("DOMAIN_FAILURE", "SAFE_DETAIL")
    assert error.code == "DOMAIN_FAILURE"
    assert error.detail == "SAFE_DETAIL"


def test_exception_rejects_non_symbolic_evidence() -> None:
    with pytest.raises(ValueError, match="uppercase symbolic token"):
        HaruQuantError("bad-code", "secret text")
