"""Executable credential protection examples."""

import sys
from pathlib import Path

from pydantic import SecretStr

# Add project root to path before importing local modules
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.utils.security import (
    SecretVersion,
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


def _header(title: str) -> None:
    """Print the header for an example section.

    Args:
        title: The title of the section to display.
    """
    print(f"\n\n\n{'=' * 100}")
    print(f"\t\t{title}\t")
    print(f"{'=' * 100}\n")


_header("Example 1: Checks if a configuration key is considered sensitive.")
is_sensitive = is_sensitive_key("client_secret")
print("Is 'client_secret' sensitive:", is_sensitive)

_header("Example 2: Substitutes known secret values in a string with [REDACTED]")
redacted_text = redact_text_value("password=my_secret_password")
print("Redacted text:", redacted_text.value)

_header("Example 3: Substitutes known secret values in a mapping with [REDACTED]")
redacted_map = redact_mapping_value({"username": "user", "password": "pwd"})
print("Redacted mapping:", redacted_map.value)

_header("Example 4: Computes a SHA-256 hash digest of the given password string.")
hashed = hash_password("my_secure_password")
verified = verify_password("my_secure_password", hashed)
print("Password hashed:", hashed[:20] + "...")
print("Password verified:", verified)

_header("Example 5: Generates a URL-safe base64-encoded 32-byte key.")
key = generate_fernet_key()
encrypted = encrypt_text("confidential message", key)
decrypted = decrypt_text(encrypted, key)
print("Fernet Key:", key[:10] + b"...")
print("Encrypted:", encrypted[:20] + "...")
print("Decrypted:", decrypted)

_header("Example 6: Selects the active SecretVersion from a list.")
versions = [
    SecretVersion(version="v1", value=SecretStr("old_secret")),
    SecretVersion(version="v2", value=SecretStr("active_secret"), active=True),
]
selected = select_active_secret_version(versions)
print("Selected Version:", selected.version)
print("Selected Secret Value:", selected.value.get_secret_value())
