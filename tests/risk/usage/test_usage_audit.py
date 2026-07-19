"""Runnable usage examples for the public Risk audit-chain API."""

from datetime import UTC, datetime
from decimal import Decimal
from typing import Literal

from app.services.risk.audit import RiskAuditChain
from app.services.risk.config import RiskConfig
from app.services.risk.contracts import RiskAuditRecord
from app.utils import canonical_json

NOW = datetime(2026, 7, 19, tzinfo=UTC)


class _ExampleStore:
    """Minimal receiver-owned atomic store used by the examples."""

    def __init__(self) -> None:
        """Initialize an empty example chain."""
        self.records: list[RiskAuditRecord] = []

    def read_head(self, *, timeout_seconds: Decimal | None) -> RiskAuditRecord | None:
        """Return the example chain head.

        Args:
            timeout_seconds: Configured persistence timeout.

        Returns:
            Current head or None.
        """
        del timeout_seconds
        return self.records[-1] if self.records else None

    def append_atomic(
        self,
        record: RiskAuditRecord,
        *,
        expected_sequence: int,
        expected_previous_hash: str,
        timeout_seconds: Decimal | None,
    ) -> Literal["appended", "already_appended", "conflict"]:
        """Append one example record atomically.

        Args:
            record: Sealed record.
            expected_sequence: Required next sequence.
            expected_previous_hash: Required head hash.
            timeout_seconds: Configured persistence timeout.

        Returns:
            Append outcome.
        """
        del expected_sequence, expected_previous_hash, timeout_seconds
        self.records.append(record)
        return "appended"

    def read_all(
        self, *, timeout_seconds: Decimal | None
    ) -> tuple[RiskAuditRecord, ...]:
        """Return all example records.

        Args:
            timeout_seconds: Configured persistence timeout.

        Returns:
            Ordered records.
        """
        del timeout_seconds
        return tuple(self.records)


def _config() -> RiskConfig:
    """Build a research configuration suitable for the usage examples."""
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


def _record() -> RiskAuditRecord:
    """Build one unsealed example record."""
    return RiskAuditRecord(
        record_id="audit-example-1",
        event_type="risk.example",
        payload={"outcome": "blocked"},
        evidence_refs={"snapshot": "snapshot-1"},
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


def test_usage_chain_create() -> None:
    """Create the coordinator with receiver-owned dependencies."""
    chain = RiskAuditChain(_config(), _ExampleStore(), lambda: NOW, canonical_json)
    assert chain.verify(()) is True


def test_usage_chain_append() -> None:
    """Append an unsealed event and receive a sealed durable result."""
    chain = RiskAuditChain(_config(), _ExampleStore(), lambda: NOW, canonical_json)
    assert chain.append(_record()).sealed is True


def test_usage_chain_verify() -> None:
    """Verify the complete ordered hash chain."""
    store = _ExampleStore()
    chain = RiskAuditChain(_config(), store, lambda: NOW, canonical_json)
    chain.append(_record())
    assert chain.verify(store.read_all(timeout_seconds=None)) is True
