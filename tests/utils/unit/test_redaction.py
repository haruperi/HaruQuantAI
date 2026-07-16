import pytest
from app.utils import RedactionPolicy, SecurityError, ValidationError


def test_policy_rejects_protected_credential_field() -> None:
    with pytest.raises(SecurityError):
        RedactionPolicy(allowlisted_paths=frozenset({"broker.api_key"}))


def test_policy_rejects_malformed_definition() -> None:
    with pytest.raises(ValidationError):
        RedactionPolicy(max_items=0)
