import pytest
from app.utils import (
    ConfigurationError,
    ExternalServiceError,
    HaruQuantError,
    SecurityError,
    ValidationError,
)


def test_shared_exception_hierarchy() -> None:
    errors = (
        ConfigurationError("CONFIG_INVALID"),
        ValidationError("VALUE_INVALID"),
        SecurityError("SECURITY_BLOCKED"),
        ExternalServiceError("PROVIDER_FAILED"),
    )
    assert all(isinstance(error, HaruQuantError) for error in errors)


def test_domains_extend_shared_base() -> None:
    class DomainError(HaruQuantError):
        """Domain-owned extension used only by this test."""

    error = DomainError("DOMAIN_FAILURE", "SAFE_DETAIL")
    assert (error.code, error.detail) == ("DOMAIN_FAILURE", "SAFE_DETAIL")


def test_exception_rejects_non_symbolic_evidence() -> None:
    with pytest.raises(ValueError, match="uppercase symbolic token"):
        HaruQuantError("bad-code", "secret text")
