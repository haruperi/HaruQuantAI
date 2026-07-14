"""Demonstrate security helpers for redaction, hashing, and encryption."""

import sys
from pathlib import Path

from pydantic import SecretStr

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.utils import (
    RedactionPolicy,
    SecretVersion,
    SecurityError,
    decrypt_text,
    encrypt_text,
    generate_fernet_key,
    hash_password,
    is_sensitive_key,
    redact_mapping_value,
    redact_text_value,
    select_active_secret_version,
    verify_password,
)


def example_redaction() -> None:
    """Illustrate redacting sensitive text and mappings."""
    print("\n1. Redacting sensitive text and mappings")
    policy = RedactionPolicy()
    text_result = redact_text_value(
        "password=correct-horse-battery-staple",
        policy,
    )
    mapping_result = redact_mapping_value(
        {"account": "demo", "api_token": "secret-value"},
        policy,
    )
    print("Redacted text:", text_result.value)
    print("Redacted mapping:", mapping_result.value)
    print("Redacted paths:", mapping_result.redacted_paths)


def example_key_classification() -> None:
    """Illustrate case-insensitive sensitive-key classification."""
    print("\n2. Key classification")
    assert is_sensitive_key("Authorization")
    assert not is_sensitive_key("account_id")
    print("Authorization is sensitive; account_id is not")


def example_password_hashing() -> None:
    """Illustrate password hashing and constant-time verification."""
    print("\n3. Password hashing and verification")
    password = "correct-horse-battery-staple"  # pragma: allowlist secret
    encoded = hash_password(password)
    assert verify_password(password, encoded)
    assert not verify_password("incorrect-password-value", encoded)
    print("Password hash prefix:", encoded.split("$", maxsplit=1)[0])
    print("Correct password verified; incorrect password rejected")


def example_fernet_encryption() -> None:
    """Illustrate Fernet symmetric encryption and decryption."""
    print("\n4. Fernet symmetric encryption and decryption")
    key = generate_fernet_key()
    token = encrypt_text("sensitive configuration value", key)
    plaintext = decrypt_text(token, key)
    assert plaintext == "sensitive configuration value"
    print("Encrypted token produced and authenticated decryption succeeded")


def example_active_secret_version() -> None:
    """Illustrate selecting exactly one active secret version."""
    print("\n5. Selecting active secret versions")
    versions = (
        SecretVersion(version="v1", value=SecretStr("retired-secret")),
        SecretVersion(version="v2", value=SecretStr("active-secret"), active=True),
    )
    active = select_active_secret_version(versions)
    assert active.version == "v2"
    print("Active version:", active.version, "value:", str(active.value))


def example_policy_validation() -> None:
    """Execute the protected-field allowlist rejection path."""
    try:
        RedactionPolicy(allowlisted_paths=frozenset({"credentials.password"}))
    except SecurityError as error:
        print("Rejected unsafe redaction policy:", error.code)
    else:
        raise AssertionError("protected credential allowlist was accepted")


if __name__ == "__main__":
    example_redaction()
    example_key_classification()
    example_password_hashing()
    example_fernet_encryption()
    example_active_secret_version()
    example_policy_validation()
