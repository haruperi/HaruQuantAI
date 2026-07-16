import pytest
from app.utils import (
    SecurityError,
    decrypt_text,
    encrypt_text,
    generate_fernet_key,
)


def test_encrypt_and_decrypt_text() -> None:
    key = generate_fernet_key()
    token = encrypt_text("sensitive value", key)
    assert token != "sensitive value"
    assert decrypt_text(token, key) == "sensitive value"


def test_decrypt_rejects_wrong_key_and_malformed_token() -> None:
    token = encrypt_text("sensitive value", generate_fernet_key())
    with pytest.raises(SecurityError):
        decrypt_text(token, generate_fernet_key())
    with pytest.raises(SecurityError):
        decrypt_text("not-a-token", generate_fernet_key())
    with pytest.raises(SecurityError):
        encrypt_text("", generate_fernet_key())
