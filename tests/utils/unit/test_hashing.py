import pytest
from app.utils import SecurityError, hash_password, verify_password


def test_hash_and_verify_password() -> None:
    password = "correct-horse-battery-staple"  # pragma: allowlist secret
    encoded = hash_password(password)
    assert encoded.startswith("pbkdf2_sha256$600000$")
    assert password not in encoded
    assert verify_password(password, encoded)
    assert not verify_password("incorrect-password-value", encoded)


def test_password_hashing_rejects_invalid_inputs() -> None:
    with pytest.raises(SecurityError):
        hash_password("too-short")
    with pytest.raises(SecurityError):
        verify_password("too-short", "invalid")
    assert not verify_password("valid-password-value", "malformed")
