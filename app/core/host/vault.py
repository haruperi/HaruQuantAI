"""Windows Credential Manager storage for opaque, independently owned references."""

from __future__ import annotations

import ctypes
import os
import secrets
import uuid
from ctypes import wintypes
from typing import Any, Literal, Protocol
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field

_MAX_CREDENTIAL_BYTES = 2400


_ERROR_NOT_FOUND = 1168


class _Credential(ctypes.Structure):
    _fields_ = [  # type: ignore[mutable-override]
        ("Flags", wintypes.DWORD),
        ("Type", wintypes.DWORD),
        ("TargetName", wintypes.LPWSTR),
        ("Comment", wintypes.LPWSTR),
        ("LastWritten", wintypes.FILETIME),
        ("CredentialBlobSize", wintypes.DWORD),
        ("CredentialBlob", ctypes.POINTER(ctypes.c_ubyte)),
        ("Persist", wintypes.DWORD),
        ("AttributeCount", wintypes.DWORD),
        ("Attributes", ctypes.c_void_p),
        ("TargetAlias", wintypes.LPWSTR),
        ("UserName", wintypes.LPWSTR),
    ]


class WindowsCredentialVault:
    """Store secrets in the current Windows user's OS-protected credential store."""

    def __init__(self) -> None:
        self._api = (
            ctypes.WinDLL("Advapi32.dll", use_last_error=True)
            if os.name == "nt"
            else None
        )
        if self._api:
            self._api.CredWriteW.argtypes = [
                ctypes.POINTER(_Credential),
                wintypes.DWORD,
            ]
            self._api.CredWriteW.restype = wintypes.BOOL
            self._api.CredReadW.argtypes = [
                wintypes.LPCWSTR,
                wintypes.DWORD,
                wintypes.DWORD,
                ctypes.POINTER(ctypes.POINTER(_Credential)),
            ]
            self._api.CredReadW.restype = wintypes.BOOL
            self._api.CredDeleteW.argtypes = [
                wintypes.LPCWSTR,
                wintypes.DWORD,
                wintypes.DWORD,
            ]
            self._api.CredDeleteW.restype = wintypes.BOOL
            self._api.CredFree.argtypes = [ctypes.c_void_p]

    def store(self, secret: str) -> str:
        """Write a new owned credential; never overwrite another reference."""
        if not self._api:
            raise OSError("The OS credential vault is unavailable")
        if (
            not isinstance(secret, str)
            or not secret
            or len(secret.encode()) > _MAX_CREDENTIAL_BYTES
        ):
            raise ValueError("Supply a nonempty credential up to 2400 bytes")
        reference = "HaruQuantAI/" + uuid.uuid4().hex
        raw = secret.encode("utf-8")
        buffer = (ctypes.c_ubyte * len(raw)).from_buffer_copy(raw)
        credential = _Credential(
            Type=1,
            TargetName=reference,
            CredentialBlobSize=len(raw),
            CredentialBlob=buffer,
            Persist=2,
            UserName="HaruQuantAI",
        )
        if not self._api.CredWriteW(ctypes.byref(credential), 0):
            raise OSError("Unable to store the OS credential")
        return reference

    def resolve(self, reference: str) -> str:
        """Read only references owned by this application's credential namespace."""
        if not self._api or not reference.startswith("HaruQuantAI/"):
            raise OSError("Credential vault or reference is unavailable")
        credential = ctypes.POINTER(_Credential)()
        if not self._api.CredReadW(reference, 1, 0, ctypes.byref(credential)):
            raise OSError("Credential reference is unavailable")
        try:
            value = credential.contents
            return ctypes.string_at(
                value.CredentialBlob, value.CredentialBlobSize
            ).decode("utf-8")
        finally:
            self._api.CredFree(credential)

    def revoke(self, reference: str) -> None:
        """Delete one owned credential; an already deleted reference is successful."""
        if not self._api or not reference.startswith("HaruQuantAI/"):
            raise OSError("Credential vault or reference is unavailable")
        if (
            not self._api.CredDeleteW(reference, 1, 0)
            and ctypes.get_last_error() != _ERROR_NOT_FOUND
        ):
            raise OSError("Unable to revoke the OS credential")


class Vault(Protocol):
    """Injected secret store; revoke must be idempotent and refs independently owned."""

    def store(self, secret: str) -> str:
        """Store a credential and return an opaque owned reference."""
        ...

    def resolve(self, reference: str) -> str:
        """Resolve one opaque reference without logging its secret."""
        ...

    def revoke(self, reference: str) -> None:
        """Permanently revoke a reference; repeated revocation must succeed."""
        ...


class ConnectionMetadata(BaseModel):
    """Allowlisted public connection fields; inline credentials cannot be saved."""

    model_config = ConfigDict(extra="forbid", strict=True)
    connection_id: str = Field(
        default_factory=lambda: secrets.token_hex(16), min_length=1, max_length=128
    )
    name: str = Field(min_length=1, max_length=200)
    provider: str = Field(min_length=1, max_length=100)
    kind: Literal["broker", "exchange"] = "broker"
    endpoint: str
    vault_refs: dict[str, str] = Field(default_factory=dict)


def prepare_credentials(  # noqa: C901 - secret staging and rollback share one scope
    vault: Vault | None, values: dict[str, Any]
) -> tuple[ConnectionMetadata, list[str]]:
    """Stage and validate owned secrets without exposing plaintext in metadata."""
    from app.core.host.transport import TransportError
    from app.core.lib.responses import ErrorCode

    credentials = values.pop("credentials", {})
    if not isinstance(credentials, dict) or any(
        not isinstance(key, str) or not isinstance(value, str)
        for key, value in credentials.items()
    ):
        raise ValueError("Credentials must contain string fields")
    staged: list[str] = []
    try:
        if credentials:
            if vault is None or not callable(getattr(vault, "store", None)):
                raise TransportError(  # noqa: TRY301 - enclosing scope owns rollback
                    ErrorCode.UNAVAILABLE, "Credential vault is not configured"
                )
            refs = dict(values.get("vault_refs") or {})
            for name, secret in credentials.items():
                if secret:
                    reference = vault.store(secret)
                    refs[name] = reference
                    staged.append(reference)
                else:
                    refs.pop(name, None)
            values["vault_refs"] = refs
        record = ConnectionMetadata.model_validate(values)
        _endpoint(record.endpoint)
        if vault is not None:
            for reference in record.vault_refs.values():
                vault.resolve(reference)
        elif record.vault_refs:
            raise TransportError(  # noqa: TRY301 - enclosing scope owns rollback
                ErrorCode.UNAVAILABLE, "Credential vault is not configured"
            )
        return record, staged
    except BaseException:
        if vault is not None:
            for reference in staged:
                vault.revoke(reference)
        raise


def _endpoint(endpoint: str) -> tuple[str, int]:
    p = urlsplit(endpoint)
    bad = (
        p.scheme not in {"http", "https"}
        or not p.hostname
        or p.username is not None
        or p.password is not None
        or p.query
        or p.fragment
    )
    if bad:
        raise ValueError("Invalid endpoint URL")
    return p.hostname or "127.0.0.1", p.port or (443 if p.scheme == "https" else 80)
