"""Unit tests for the deterministic tamper-evident Risk audit chain."""

from datetime import UTC, datetime
from decimal import Decimal
from typing import Literal

import pytest
from app.services.risk.audit import RiskAuditChain
from app.services.risk.config import RiskConfig
from app.services.risk.contracts import RiskAuditRecord, RiskDomainError, RiskErrorCode
from app.utils import canonical_json

NOW = datetime(2026, 7, 19, tzinfo=UTC)


class _MemoryAuditStore:
    """Small atomic in-memory audit store used only by unit tests."""

    def __init__(self, *, unavailable: bool = False) -> None:
        """Initialize test records and failure behavior.

        Args:
            unavailable: Whether every read must fail.
        """
        self.records: list[RiskAuditRecord] = []
        self.unavailable = unavailable

    def read_head(self, *, timeout_seconds: Decimal | None) -> RiskAuditRecord | None:
        """Return the current test-chain head.

        Args:
            timeout_seconds: Configured bounded timeout.

        Returns:
            Current record or None.
        """
        del timeout_seconds
        if self.unavailable:
            raise OSError("store unavailable")
        return self.records[-1] if self.records else None

    def append_atomic(
        self,
        record: RiskAuditRecord,
        *,
        expected_sequence: int,
        expected_previous_hash: str,
        timeout_seconds: Decimal | None,
    ) -> Literal["appended", "already_appended", "conflict"]:
        """Append only when sequence and previous hash match.

        Args:
            record: Sealed test record.
            expected_sequence: Required sequence.
            expected_previous_hash: Required predecessor hash.
            timeout_seconds: Configured bounded timeout.

        Returns:
            Atomic test-store outcome.
        """
        del timeout_seconds
        head = self.records[-1] if self.records else None
        actual_sequence = 0 if head is None else (head.sequence or 0) + 1
        actual_previous = "0" * 64 if head is None else str(head.record_hash)
        if (
            expected_sequence != actual_sequence
            or expected_previous_hash != actual_previous
        ):
            return "conflict"
        self.records.append(record)
        return "appended"

    def read_all(
        self, *, timeout_seconds: Decimal | None
    ) -> tuple[RiskAuditRecord, ...]:
        """Return all test records in sequence order.

        Args:
            timeout_seconds: Configured bounded timeout.

        Returns:
            Immutable ordered records.
        """
        del timeout_seconds
        return tuple(self.records)


def _config() -> RiskConfig:
    """Build the minimum complete deterministic Risk configuration."""
    return RiskConfig(
        profile="research",
        execution_route="none",
        policy_version="policy-1",
        base_currency="USD",
        pending_order_exposure_policy="include_full_remaining_exposure",
        evidence_max_age_seconds={"audit": 60},
        clock_skew_tolerance_seconds=Decimal(0),
        var_min_observations=3,
        var_lookback=3,
        regime_assessment_enabled=False,
        approval_token_ttl_seconds=Decimal(60),
        approval_signing_key_ref="secrets/risk-key",
        decision_ttl_seconds=Decimal(30),
        kill_switch_activation_permissions=("risk.kill.activate",),
        kill_switch_clearance_permissions=("risk.kill.clear",),
        report_timeout_seconds=Decimal(5),
    )


def _record(record_id: str = "audit-1") -> RiskAuditRecord:
    """Build one unsealed material Risk event."""
    return RiskAuditRecord(
        record_id=record_id,
        event_type="risk.decision",
        payload={"status": "blocked"},
        evidence_refs={"portfolio": "snapshot-1"},
        config_hash="a" * 64,
        decision_id="decision-1",
        occurred_at=NOW,
        sequence=None,
        previous_hash=None,
        record_hash=None,
        sealed=False,
        request_id="request-1",
        correlation_id="correlation-1",
    )


def test_chain_requires_deterministic_genesis() -> None:
    """Reject an invalid deterministic genesis even at the chain boundary."""
    invalid = _config().model_construct(audit_genesis_hash="invalid")
    with pytest.raises(RiskDomainError) as captured:
        RiskAuditChain(invalid, _MemoryAuditStore(), lambda: NOW, canonical_json)
    assert captured.value.code == RiskErrorCode.INVALID_RISK_CONFIG.value


def test_append_hashes_and_fails_closed() -> None:
    """Seal idempotently and map unavailable durable storage to STORAGE_ERROR."""
    store = _MemoryAuditStore()
    chain = RiskAuditChain(_config(), store, lambda: NOW, canonical_json)
    sealed = chain.append(_record())
    assert sealed.sealed is True
    assert sealed.sequence == 0
    assert sealed.previous_hash == "0" * 64
    assert len(str(sealed.record_hash)) == 64
    assert chain.append(_record()) == sealed

    unavailable = RiskAuditChain(
        _config(), _MemoryAuditStore(unavailable=True), lambda: NOW, canonical_json
    )
    with pytest.raises(RiskDomainError) as captured:
        unavailable.append(_record("audit-2"))
    assert captured.value.code == RiskErrorCode.STORAGE_ERROR.value


def test_verify_detects_tamper() -> None:
    """Verify a valid chain and deterministically reject changed hash evidence."""
    store = _MemoryAuditStore()
    chain = RiskAuditChain(_config(), store, lambda: NOW, canonical_json)
    sealed = chain.append(_record())
    assert chain.verify((sealed,)) is True

    tampered = sealed.model_copy(update={"record_hash": "f" * 64})
    with pytest.raises(RiskDomainError) as captured:
        chain.verify((tampered,))
    assert captured.value.code == RiskErrorCode.AUDIT_CHAIN_TAMPER_DETECTED.value
