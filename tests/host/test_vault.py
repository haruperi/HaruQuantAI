"""OS vault boundaries fail explicitly without exposing stored values."""

import pytest
from app.host.vault import WindowsCredentialVault


def test_foreign_reference_cannot_be_resolved_or_revoked():
    vault = WindowsCredentialVault()
    with pytest.raises(OSError, match="unavailable"):
        vault.resolve("another-application/credential")
    with pytest.raises(OSError, match="unavailable"):
        vault.revoke("another-application/credential")


def test_unavailable_vault_never_falls_back_to_plaintext():
    vault = WindowsCredentialVault()
    vault._api = None
    with pytest.raises(OSError, match="unavailable"):
        vault.store("non-production-test-value")
