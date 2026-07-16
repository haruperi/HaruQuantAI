import pytest
from app.utils import ValidationError, derive_stable_id, generate_id, validate_id


def test_generate_id_is_prefixed_and_secret_free() -> None:
    identifier = generate_id("req")
    assert validate_id(identifier, expected_prefix="req") == identifier
    assert "secret" not in identifier


def test_validate_id_rejects_malformed() -> None:
    with pytest.raises(ValidationError):
        validate_id("req-not-a-uuid")
    with pytest.raises(ValidationError):
        generate_id("unknown")
    with pytest.raises(ValidationError):
        validate_id(generate_id("req"), expected_prefix="cor")


def test_derive_stable_id_is_deterministic() -> None:
    first = derive_stable_id("cor", "strategy:v1")
    assert first == derive_stable_id("cor", "strategy:v1")
    assert validate_id(first, expected_prefix="cor") == first
