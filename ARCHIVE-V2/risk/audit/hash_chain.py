# ruff: noqa: ANN401, D105, C901
"""Audit-chain genesis hash, append hash, sequence verification, and tamper-detection.

Ensures the pre-trade risk audit trail is cryptographically continuous and
tamper-evident, allowing live workflows to fail closed when integrity is compromised.
"""

from __future__ import annotations

import hashlib
from collections.abc import Mapping, Sequence
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from pydantic import Field, JsonValue

from app.services.risk.models import RiskAuditEvent, RiskContract
from app.services.risk.models.enums import RiskMode
from app.utils.logger import logger
from app.utils.standard import canonical_json

if TYPE_CHECKING:
    from app.services.risk.validations import ValidationResult


class AuditChainVerification(RiskContract):
    """Result of traversing and verifying the audit chain."""

    valid: bool = Field(
        ...,
        description="True if the chain is sequence-continuous and hashes match.",
    )
    tampered: bool = Field(..., description="True if any tampering was detected.")
    details: dict[str, Any] = Field(
        default_factory=dict, description="Detailed validation breakdown."
    )

    def __bool__(self) -> bool:
        return self.valid


def _coerce_types(v: Any) -> Any:
    """Recursively coerce Decimals to floats and datetimes to ISO strings for JSON."""
    if isinstance(v, Decimal):
        return float(v)
    if isinstance(v, datetime):
        return v.isoformat()
    if isinstance(v, dict):
        return {k: _coerce_types(val) for k, val in v.items()}
    if isinstance(v, list | tuple | set):
        return [_coerce_types(val) for val in v]
    return v


def build_genesis_hash(payload: Mapping[str, JsonValue]) -> str:
    """Computes the first-record hash (genesis block).

    Args:
        payload: The payload mapping representing the genesis event fields.

    Returns:
        str: The SHA256 genesis hash.
    """
    logger.debug("Computing genesis block hash.")
    payload_copy = dict(payload)
    payload_copy["previous_hash"] = "0" * 64
    payload_copy.pop("hash", None)

    canonical_str = canonical_json(_coerce_types(payload_copy))
    return hashlib.sha256(canonical_str.encode()).hexdigest()


def append_audit_hash(previous_hash: str, payload: Mapping[str, JsonValue]) -> str:
    """Computes deterministic chained SHA256 hash.

    Args:
        previous_hash: SHA256 hash of the previous event.
        payload: The payload mapping representing the current event fields.

    Returns:
        str: The chained SHA256 hash.
    """
    logger.debug("Appending audit hash with previous_hash=%s", previous_hash)
    payload_copy = dict(payload)
    payload_copy["previous_hash"] = previous_hash
    payload_copy.pop("hash", None)

    canonical_str = canonical_json(_coerce_types(payload_copy))
    return hashlib.sha256(canonical_str.encode()).hexdigest()


def verify_risk_audit_chain(
    events: Sequence[RiskAuditEvent] | Any,
) -> AuditChainVerification:
    """Validates genesis, sequence continuity, payload hashes, and tamper state.

    Args:
        events: Ordered sequence of audit events or a state store.

    Returns:
        AuditChainVerification: Results of the chain validation.
    """
    if not isinstance(events, (list, tuple)):
        if hasattr(events, "get_all_events"):
            events = list(events.get_all_events())
        elif hasattr(events, "get_events"):
            events = list(events.get_events())
        else:
            try:
                events = list(events)
            except TypeError:
                events = []

    logger.info("Verifying integrity of %d audit events.", len(events))
    if not events:
        logger.debug("No audit events to verify; chain is valid.")
        return AuditChainVerification(
            valid=True,
            tampered=False,
            details={"message": "No events in chain."},
        )

    for i, event in enumerate(events):
        # 1. Check genesis block previous hash
        if i == 0:
            if event.previous_hash != "0" * 64:
                logger.warning(
                    "Genesis block previous hash is invalid: %s",
                    event.previous_hash,
                )
                return AuditChainVerification(
                    valid=False,
                    tampered=True,
                    details={
                        "message": "Genesis previous hash mismatch.",
                        "index": 0,
                    },
                )
        # Check linkage with previous event
        else:
            prev_event = events[i - 1]
            if event.previous_hash != prev_event.hash:
                logger.warning(
                    "Linkage broken at block %d: expected previous_hash %s, got %s",
                    i,
                    prev_event.hash,
                    event.previous_hash,
                )
                return AuditChainVerification(
                    valid=False,
                    tampered=True,
                    details={
                        "message": "Sequence linkage broken.",
                        "index": i,
                        "expected_prev": prev_event.hash,
                        "actual_prev": event.previous_hash,
                    },
                )

        # 2. Re-compute hash and verify
        event_dict = event.model_dump()
        computed_hash = append_audit_hash(event.previous_hash, event_dict)
        if event.hash != computed_hash:
            logger.warning(
                "Hash mismatch at block %d: computed %s, stored %s",
                i,
                computed_hash,
                event.hash,
            )
            return AuditChainVerification(
                valid=False,
                tampered=True,
                details={
                    "message": "Event hash mismatch.",
                    "index": i,
                    "computed_hash": computed_hash,
                    "stored_hash": event.hash,
                },
            )

    logger.info("Audit chain verification completed successfully.")
    return AuditChainVerification(
        valid=True,
        tampered=False,
        details={"message": f"Successfully verified {len(events)} events."},
    )


def require_valid_audit_chain(
    verification: AuditChainVerification, mode: RiskMode
) -> ValidationResult:
    """Fails closed for live-sensitive modes when tampering is detected.

    Args:
        verification: Output of the chain verify check.
        mode: Active trading mode of the system.

    Returns:
        ValidationResult: The fail-closed status and message.
    """
    logger.info("Checking audit chain validation requirement for mode: %s", mode)
    # Check if mode is live-sensitive
    is_live = mode in (RiskMode.MICRO_LIVE, RiskMode.FULL_LIVE)
    if is_live and (verification.tampered or not verification.valid):
        logger.error(
            "FAIL-CLOSED: Audit chain verification failed or tampering "
            "detected in live mode (%s).",
            mode,
        )
        return {
            "valid": False,
            "message": (
                "Audit chain verification failed in live mode: "
                "tampering or invalid sequence detected."
            ),
            "code": "AUDIT_CHAIN_CORRUPT",
            "details": {
                "tampered": verification.tampered,
                "valid": verification.valid,
                "mode": mode,
            },
        }

    logger.debug("Audit chain verification requirement satisfied.")
    return {
        "valid": True,
        "message": "Audit chain verification check passed.",
        "code": "OK",
        "details": {},
    }
