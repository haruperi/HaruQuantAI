"""Credential primitives used by the host session authority.

Passwords use randomly salted PBKDF2-SHA256 verifiers. Bearer tokens are signed
with a caller-owned key and hashed before persistence. No key, credential,
database connection, or logger is initialized here. These helpers do not enforce
session expiry or rate limits; SessionManager owns those checks.
"""

import hashlib
import hmac
import ipaddress
import secrets


def is_loopback(host: str) -> bool:
    """Recognize a literal IPv4 or IPv6 loopback address.

    Args:
        host: Peer or bind address; DNS names and forwarding headers are not resolved.

    Returns:
        True for loopback literals; False for invalid addresses or hostnames.
    """
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def hash_password(password: str) -> str:
    """Create a password verifier with a fresh 32-byte random salt.

    Uses 600,000 PBKDF2-HMAC-SHA256 iterations. This CPU-bound operation does
    not store or log the password; callers own persistence and scheduling.

    Args:
        password: Plaintext password, encoded as UTF-8 without normalization.

    Returns:
        Hex salt and hex digest separated by a colon.
    """
    salt = secrets.token_bytes(32)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 600000)
    return salt.hex() + ":" + digest.hex()


def hash_credentials(
    password: str, salt: str | None = None, iterations: int = 100000
) -> tuple[str, str]:
    """Create a password verifier and salt for user.access persistence.

    Uses PBKDF2-HMAC-SHA256 with 100,000 iterations by default.

    Args:
        password: Plaintext password.
        salt: Optional hexadecimal salt; generated randomly if None.
        iterations: Number of PBKDF2 iterations.

    Returns:
        Tuple of (hex_digest, hex_salt).
    """
    effective_salt = salt if salt is not None else secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode(), bytes.fromhex(effective_salt), iterations
    )
    return digest.hex(), effective_salt


def verify_credentials(
    password: str,
    stored_hash: str,
    stored_salt: str,
) -> bool:
    """Verify candidate password against stored user.access hash and salt.

    Supports both 100,000 and 600,000 iteration counts for compatibility.

    Args:
        password: Candidate plaintext password.
        stored_hash: Hexadecimal hash stored in user.access.
        stored_salt: Hexadecimal salt stored in user.access.

    Returns:
        True if matching, False for mismatch or malformed inputs.
    """
    try:
        salt_bytes = bytes.fromhex(stored_salt)
        for iters in (100000, 600000):
            digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt_bytes, iters)
            if hmac.compare_digest(digest.hex(), stored_hash):
                return True
        return False
    except ValueError, TypeError:
        return False


def verify_password(password: str, stored: str) -> bool:
    """Recompute and compare a stored PBKDF2 password verifier.

    Digest comparison uses compare_digest. The expensive derivation is synchronous;
    callers must apply their own request limits.

    Args:
        password: Candidate plaintext password.
        stored: Colon-separated hex salt and digest from hash_password.

    Returns:
        Whether the digest matches; malformed verifier encodings return False.
    """
    try:
        salt, expected = stored.split(":")
        return verify_credentials(password, expected, salt)
    except ValueError:
        return False


def token_hash(token: str) -> str:
    """Produce the database lookup key for a bearer token.

    Args:
        token: Complete bearer credential, including its signature.

    Returns:
        SHA-256 hexadecimal digest; token validity is not checked here.
    """
    return hashlib.sha256(token.encode()).hexdigest()


def sign(message: str, key: bytes) -> str:
    """Compute a message authentication code with an injected secret.

    Args:
        message: Opaque token identifier encoded as UTF-8.
        key: Process-owned signing bytes; never persisted by this helper.

    Returns:
        Hexadecimal HMAC-SHA256 signature.
    """
    return hmac.new(key, message.encode(), "sha256").hexdigest()
