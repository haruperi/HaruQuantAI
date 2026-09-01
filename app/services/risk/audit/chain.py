"""Thread-safe tamper-evident Risk audit-chain coordination."""

from __future__ import annotations

import hashlib
from collections.abc import Callable, Mapping, Sequence
from datetime import datetime, timedelta
from threading import RLock
from typing import TYPE_CHECKING, Literal

from app.composition.logging import get_logger
from app.kernel.redaction import redact_mapping_value
from app.services.risk.contracts import RiskAuditRecord, RiskDomainError, RiskErrorCode
from app.services.risk.contracts.responses import guard_risk_boundary

RiskLevel = Literal["none", "low", "medium", "high", "critical"]

logger = get_logger(__name__)

if TYPE_CHECKING:
    from app.services.risk.audit.storage import _KillSwitchStateStore, _RiskAuditStore
    from app.services.risk.config import RiskConfig
    from app.services.risk.contracts import KillSwitchState

_SHA256_HEX_LENGTH = 64


def _utc(value: datetime) -> datetime:
    """Require aware UTC time.

    Args:
        value: Time to validate.

    Returns:
        Validated time.

    Raises:
        ValueError: If time is not aware UTC.
    """
    logger.debug("Validating Risk audit clock time")
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ValueError("audit clock must return aware UTC")
    return value


def _validate_dependencies(config: RiskConfig, clock: Callable[[], datetime]) -> None:
    """Validate deterministic audit dependencies.

    Args:
        config: Active audit policy.
        clock: Injected UTC clock.

    Raises:
        ValueError: If an audit dependency is invalid.
    """
    logger.debug("Validating deterministic Risk audit dependencies")
    if config.audit_hash_algorithm != "sha256":
        raise ValueError("unsupported audit hash algorithm")
    if len(config.audit_genesis_hash) != _SHA256_HEX_LENGTH:
        raise ValueError("invalid audit genesis hash")
    _utc(clock())


class RiskAuditChain:
    """Coordinate canonical redaction, hashing, persistence, and verification."""

    def __init__(
        self,
        config: RiskConfig,
        store: _RiskAuditStore,
        clock: Callable[[], datetime],
        serializer: Callable[[object], str],
    ) -> None:
        """Initialize a deterministic Risk audit chain.

        Args:
            config: Active audit policy.
            store: Injected atomic Risk audit store.
            clock: Injected UTC clock.
            serializer: Injected canonical serializer.

        Raises:
            RiskDomainError: If chain configuration or dependencies are invalid.
        """
        logger.info("Initializing deterministic Risk audit chain")
        try:
            _validate_dependencies(config, clock)
        except (TypeError, ValueError) as error:
            raise RiskDomainError(
                RiskErrorCode.INVALID_RISK_CONFIG, "audit chain configuration invalid"
            ) from error
        self._config = config
        self._store = store
        self._clock = clock
        self._serializer = serializer
        self._lock = RLock()

    def _serialized_material(
        self,
        record: RiskAuditRecord,
        *,
        sequence: int,
        previous_hash: str,
        payload: Mapping[str, object],
    ) -> str:
        """Serialize exact hash material for one record.

        Args:
            record: Source record.
            sequence: Assigned sequence.
            previous_hash: Assigned previous hash.
            payload: Redacted payload.

        Returns:
            Canonical serialized material.

        Raises:
            TypeError: If the serializer does not return text.
        """
        logger.debug("Serializing canonical Risk audit hash material")
        material = {
            "record_id": record.record_id,
            "event_type": record.event_type,
            "payload": dict(payload),
            "evidence_refs": dict(record.evidence_refs),
            "config_hash": record.config_hash,
            "decision_id": record.decision_id,
            "occurred_at": record.occurred_at.isoformat(),
            "sequence": sequence,
            "previous_hash": previous_hash,
            "request_id": record.request_id,
            "correlation_id": record.correlation_id,
        }
        serialized = self._serializer(material)
        if not isinstance(serialized, str):
            raise TypeError("audit serializer must return text")
        return serialized

    def _seal(
        self, record: RiskAuditRecord, sequence: int, previous_hash: str
    ) -> RiskAuditRecord:
        """Redact and seal one unsealed record.

        Args:
            record: Unsealed append input.
            sequence: Assigned sequence.
            previous_hash: Assigned previous hash.

        Returns:
            Sealed hash-bound record.

        Raises:
            TypeError: If redaction does not return a mapping.
            ValueError: If serialization or record time is invalid.
        """
        logger.debug("Redacting and sealing one Risk audit record")
        if record.occurred_at > _utc(self._clock()):
            raise ValueError("audit record time cannot be in the future")
        redacted = redact_mapping_value(record.payload).value
        if not isinstance(redacted, Mapping):
            raise TypeError("audit payload redaction is invalid")
        payload = {str(key): value for key, value in redacted.items()}
        serialized = self._serialized_material(
            record,
            sequence=sequence,
            previous_hash=previous_hash,
            payload=payload,
        )
        record_hash = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
        values = record.model_dump(warnings=False, mode="python")
        values.update(
            payload=payload,
            sequence=sequence,
            previous_hash=previous_hash,
            record_hash=record_hash,
            sealed=True,
        )
        return RiskAuditRecord.model_validate(values)

    @guard_risk_boundary(
        risk_level="critical",
        read_only=False,
        modifies_database=True,
    )
    def append(self, record: RiskAuditRecord) -> RiskAuditRecord:
        """Seal and durably append one unsealed Risk audit record.

        Args:
            record: Unsealed append input.

        Returns:
            Durably appended sealed record.

        Raises:
            RiskDomainError: If input, persistence, or retry exhaustion fails.
        """
        logger.info("Appending one material Risk audit event")
        if record.sealed:
            raise RiskDomainError(RiskErrorCode.STORAGE_ERROR, "sealed append input")
        with self._lock:
            return self._append_locked(record)

    @guard_risk_boundary(
        risk_level="critical",
        read_only=False,
        modifies_database=True,
    )
    def append_kill_switch_transition(
        self,
        record: RiskAuditRecord,
        state: KillSwitchState,
        store: _KillSwitchStateStore,
        *,
        expected_version: int,
    ) -> RiskAuditRecord:
        """Atomically persist one kill-switch state transition and audit record.

        The state and audit ports must be the same receiver-owned transactional
        adapter. This identity requirement prevents an apparent transaction from
        spanning unrelated persistence resources.

        Args:
            record: Unsealed audit input for the exact transition.
            state: Canonical resulting kill-switch state.
            store: Combined kill-switch state and audit adapter.
            expected_version: Required predecessor state version.

        Returns:
            Durably committed sealed audit record.

        Raises:
            RiskDomainError: If ports differ, persistence fails, or concurrency
                conflicts exhaust the configured retry budget.
        """
        logger.info("Atomically appending one Risk kill-switch transition")
        if record.sealed or store is not self._store:
            raise RiskDomainError(
                RiskErrorCode.STORAGE_ERROR,
                "kill-switch state and audit require one transactional store",
            )
        with self._lock:
            try:
                attempts = self._config.audit_retry_attempts + 1
                for _ in range(attempts):
                    head = self._store.read_head(
                        timeout_seconds=self._config.audit_timeout_seconds
                    )
                    sequence = 0 if head is None else (head.sequence or 0) + 1
                    previous_hash = (
                        self._config.audit_genesis_hash
                        if head is None
                        else str(head.record_hash)
                    )
                    sealed = self._seal(record, sequence, previous_hash)
                    outcome = store.compare_and_swap_with_audit(
                        state,
                        sealed,
                        expected_version=expected_version,
                        expected_sequence=sequence,
                        expected_previous_hash=previous_hash,
                        timeout_seconds=self._config.dependency_timeouts_seconds.get(
                            "kill_switch"
                        ),
                    )
                    if outcome == "committed":
                        return sealed
                    if outcome == "already_committed":
                        current = self._store.read_head(
                            timeout_seconds=self._config.audit_timeout_seconds
                        )
                        if (
                            current is not None
                            and current.record_id == sealed.record_id
                            and current.record_hash == sealed.record_hash
                        ):
                            return current
                        break
            except RiskDomainError:
                logger.exception("Risk kill-switch atomic transition failed closed")
                raise
            except Exception as error:
                logger.exception("Risk kill-switch transactional store access failed")
                raise RiskDomainError(
                    RiskErrorCode.STORAGE_ERROR,
                    "kill-switch atomic persistence unavailable",
                ) from error
            raise RiskDomainError(
                RiskErrorCode.STORAGE_ERROR,
                "kill-switch atomic transition conflict exhausted",
            )

    def _append_locked(self, record: RiskAuditRecord) -> RiskAuditRecord:
        """Append under local synchronization and atomic store concurrency.

        Args:
            record: Unsealed append input.

        Returns:
            Durably appended sealed record.

        Raises:
            RiskDomainError: If store access or retry exhaustion fails.
        """
        logger.debug("Appending Risk audit record under local lock")
        try:
            return self._append_to_store(record)
        except RiskDomainError:
            logger.exception("Risk audit append failed closed")
            raise
        except Exception as error:
            logger.exception("Risk audit store access failed")
            raise RiskDomainError(
                RiskErrorCode.STORAGE_ERROR, "audit persistence unavailable"
            ) from error

    def _append_to_store(self, record: RiskAuditRecord) -> RiskAuditRecord:
        """Attempt an idempotent atomic append within the retry budget.

        Args:
            record: Unsealed append input.

        Returns:
            Durably appended sealed record.

        Raises:
            RiskDomainError: If atomic conflicts exhaust the retry budget.
        """
        logger.debug("Attempting atomic Risk audit persistence")
        attempts = self._config.audit_retry_attempts + 1
        for _ in range(attempts):
            head = self._store.read_head(
                timeout_seconds=self._config.audit_timeout_seconds
            )
            if head is not None and head.record_id == record.record_id:
                candidate = self._seal(
                    record,
                    head.sequence or 0,
                    str(head.previous_hash),
                )
                if candidate.record_hash == head.record_hash:
                    return head
                raise RiskDomainError(
                    RiskErrorCode.STORAGE_ERROR,
                    "audit record identity conflicts with durable record",
                )
            sequence = 0 if head is None else (head.sequence or 0) + 1
            previous_hash = (
                self._config.audit_genesis_hash
                if head is None
                else str(head.record_hash)
            )
            sealed = self._seal(record, sequence, previous_hash)
            outcome = self._store.append_atomic(
                sealed,
                expected_sequence=sequence,
                expected_previous_hash=previous_hash,
                timeout_seconds=self._config.audit_timeout_seconds,
            )
            if outcome == "appended":
                return sealed
            if outcome == "already_appended":
                current = self._store.read_head(
                    timeout_seconds=self._config.audit_timeout_seconds
                )
                if (
                    current is not None
                    and current.record_id == sealed.record_id
                    and current.record_hash == sealed.record_hash
                ):
                    return current
                break
        raise RiskDomainError(
            RiskErrorCode.STORAGE_ERROR, "audit append conflict exhausted"
        )

    @guard_risk_boundary(risk_level="critical", read_only=True)
    def verify(self, records: Sequence[RiskAuditRecord]) -> bool:
        """Verify genesis, sequence, continuity, and every record hash.

        Args:
            records: Ordered sealed records.

        Returns:
            True when the complete chain is valid.

        Raises:
            RiskDomainError: If tamper or malformed chain evidence is detected.
        """
        logger.info("Verifying complete Risk audit chain")
        try:
            return self._verify_records(records)
        except (TypeError, ValueError) as error:
            logger.exception("Risk audit-chain tamper detected")
            raise RiskDomainError(
                RiskErrorCode.AUDIT_CHAIN_TAMPER_DETECTED,
                "audit chain verification failed",
            ) from error

    def _verify_records(self, records: Sequence[RiskAuditRecord]) -> bool:
        """Verify exact chain material outside the public error boundary.

        Args:
            records: Ordered sealed records.

        Returns:
            True when every record is valid.

        Raises:
            TypeError: If canonical serialization is invalid.
            ValueError: If continuity or hash evidence is invalid.
        """
        logger.debug("Checking Risk audit chain continuity and hashes")
        previous_hash = self._config.audit_genesis_hash
        for sequence, record in enumerate(records):
            if (
                not record.sealed
                or record.sequence != sequence
                or record.previous_hash != previous_hash
            ):
                raise ValueError("audit chain continuity invalid")
            serialized = self._serialized_material(
                record,
                sequence=sequence,
                previous_hash=previous_hash,
                payload=record.payload,
            )
            expected = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
            if record.record_hash != expected:
                raise ValueError("audit record hash invalid")
            previous_hash = expected
        return True


def create_risk_audit_chain(
    config: RiskConfig,
    store: _RiskAuditStore,
    clock: Callable[[], datetime],
    serializer: Callable[[object], str],
) -> RiskAuditChain:
    """Create an opaque tamper-evident Risk audit coordinator.

    Args:
        config: Validated Risk configuration.
        store: Injected atomic Risk audit store.
        clock: Injected aware-UTC clock.
        serializer: Injected canonical serializer.

    Returns:
        Opaque internal audit coordinator.
    """
    return RiskAuditChain(config, store, clock, serializer)


def append_risk_audit_record(audit: RiskAuditChain, record: RiskAuditRecord) -> object:
    """Append one Risk audit record through an opaque coordinator.

    Args:
        audit: Opaque coordinator returned by :func:`create_risk_audit_chain`.
        record: Unsealed Risk audit record.

    Returns:
        Standard response carrying the sealed record.

    Raises:
        TypeError: If ``audit`` is not a Risk audit coordinator.
    """
    if not isinstance(audit, RiskAuditChain):
        raise TypeError("audit must be created by create_risk_audit_chain")
    return audit.append(record)


def append_risk_kill_switch_transition(
    audit: RiskAuditChain,
    record: RiskAuditRecord,
    state: KillSwitchState,
    store: _KillSwitchStateStore,
    *,
    expected_version: int,
) -> object:
    """Atomically append one kill-switch transition and audit record.

    Args:
        audit: Opaque coordinator returned by :func:`create_risk_audit_chain`.
        record: Unsealed Risk audit record.
        state: Resulting canonical kill-switch state.
        store: Combined state and audit persistence adapter.
        expected_version: Required predecessor state version.

    Returns:
        Standard response carrying the sealed record.

    Raises:
        TypeError: If ``audit`` is not a Risk audit coordinator.
    """
    if not isinstance(audit, RiskAuditChain):
        raise TypeError("audit must be created by create_risk_audit_chain")
    return audit.append_kill_switch_transition(
        record,
        state,
        store,
        expected_version=expected_version,
    )


def verify_risk_audit_chain(
    audit: RiskAuditChain, records: Sequence[RiskAuditRecord]
) -> object:
    """Verify a complete Risk audit chain through an opaque coordinator.

    Args:
        audit: Opaque coordinator returned by :func:`create_risk_audit_chain`.
        records: Ordered sealed Risk audit records.

    Returns:
        Standard response carrying the verification result.

    Raises:
        TypeError: If ``audit`` is not a Risk audit coordinator.
    """
    if not isinstance(audit, RiskAuditChain):
        raise TypeError("audit must be created by create_risk_audit_chain")
    return audit.verify(records)


__all__ = [
    "RiskAuditChain",
    "append_risk_audit_record",
    "append_risk_kill_switch_transition",
    "create_risk_audit_chain",
    "verify_risk_audit_chain",
]
