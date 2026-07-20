"""Append-only trading event journal and replay utilities.

The journal stores encrypted JSONL records with hash-chain links, logical
sequence IDs, detached signatures, snapshots, reconciliation scans, and replay
helpers for forensic reconstruction.
"""

from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Iterable
from pathlib import Path
from typing import Self

from app.services.trading.contracts import JsonObject, JsonValue, TradingRoute
from app.services.trading.state.ports import Clock, EncryptionProvider
from app.utils.logger import logger
from app.utils.standard import canonical_json
from pydantic import BaseModel, ConfigDict, Field, model_validator

TERMINAL_EVENT_TYPES = {
    "ExecutionReportEvent",
    "TradingCommandRejected",
    "ReconciliationResolutionEvent",
}
IN_FLIGHT_EVENT_TYPES = {"TradingCommandAccepted", "BrokerDispatchEvent"}
GENESIS_HASH = "0" * 64


class JournalBuildMetadata(BaseModel):
    """Code and configuration provenance for journal records."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    software_version: str
    vcs_commit_hash: str
    dirty_tree: bool
    active_config_hash: str

    @model_validator(mode="after")
    def validate_metadata(self) -> Self:
        """Validate build provenance.

        Returns:
            JournalBuildMetadata: Validated metadata.
        """
        logger.info("Validating journal build metadata.")
        for field_name in ("software_version", "vcs_commit_hash", "active_config_hash"):
            if not str(getattr(self, field_name)).strip():
                message = f"{field_name} must be non-empty."
                raise ValueError(message)
        return self


class JournalEvent(BaseModel):
    """Immutable append-only journal event."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    event_id: str
    previous_event_hash: str
    event_hash: str
    schema_version: str
    timestamp_utc: str
    monotonic_timestamp: float
    sequence_id: int = Field(ge=1)
    request_id: str
    correlation_id: str
    route: TradingRoute
    account_id: str
    symbol: str
    actor: str
    event_type: str
    payload: JsonObject
    software_version: str
    vcs_commit_hash: str
    dirty_tree: bool
    active_config_hash: str

    @model_validator(mode="after")
    def validate_event(self) -> Self:
        """Validate immutable journal event identifiers.

        Returns:
            JournalEvent: Validated event.
        """
        logger.info("Validating journal event {}.", self.event_id)
        for field_name in (
            "event_id",
            "previous_event_hash",
            "event_hash",
            "schema_version",
            "timestamp_utc",
            "request_id",
            "correlation_id",
            "account_id",
            "symbol",
            "actor",
            "event_type",
            "software_version",
            "vcs_commit_hash",
            "active_config_hash",
        ):
            if not str(getattr(self, field_name)).strip():
                message = f"{field_name} must be non-empty."
                raise ValueError(message)
        return self

    def hash_material(self) -> JsonObject:
        """Return event material excluding the event hash.

        Returns:
            JsonObject: Canonical hash material.
        """
        logger.debug("Building hash material for event {}.", self.event_id)
        payload = self.model_dump(mode="json")
        payload.pop("event_hash")
        return payload


class StateSnapshot(BaseModel):
    """Durable projection snapshot."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    snapshot_id: str
    route: TradingRoute
    account_id: str
    created_at: str
    sequence_id: int = Field(ge=0)
    terminal_event_hash: str
    state: JsonObject
    encrypted_payload: str
    signature: str

    @model_validator(mode="after")
    def validate_snapshot(self) -> Self:
        """Validate snapshot identifiers.

        Returns:
            StateSnapshot: Validated snapshot.
        """
        logger.info("Validating state snapshot {}.", self.snapshot_id)
        if not self.snapshot_id.strip():
            raise ValueError("snapshot_id must be non-empty.")
        if not self.account_id.strip():
            raise ValueError("account_id must be non-empty.")
        return self


class ReconciliationLock(BaseModel):
    """Mutation lock generated for unresolved in-flight journal commands."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    account_id: str
    symbol: str
    request_id: str
    reason: str

    @model_validator(mode="after")
    def validate_lock(self) -> Self:
        """Validate reconciliation lock.

        Returns:
            ReconciliationLock: Validated lock.
        """
        logger.info("Validating reconciliation lock for {}.", self.request_id)
        return self


class JournalIntegrityResult(BaseModel):
    """Result of journal hash-chain validation."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    valid: bool
    broken_event_id: str | None = None
    alert: JsonObject | None = None

    @model_validator(mode="after")
    def validate_result(self) -> Self:
        """Validate integrity result.

        Returns:
            JournalIntegrityResult: Validated result.
        """
        logger.info("Validated journal integrity result valid={} .", self.valid)
        return self


class SegmentSeal(BaseModel):
    """Detached journal segment signature."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    seal_id: str
    terminal_hash: str
    signature: str
    sealed_at: str
    sequence_id: int = Field(ge=0)

    @model_validator(mode="after")
    def validate_seal(self) -> Self:
        """Validate segment seal.

        Returns:
            SegmentSeal: Validated seal.
        """
        logger.info("Validating journal segment seal {}.", self.seal_id)
        return self


class JournalRetentionPolicy(BaseModel):
    """Route-aware journal compaction and retention policy."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    route: TradingRoute
    retention_days: int = Field(ge=1)
    archive_after_snapshot: bool = True

    @model_validator(mode="after")
    def validate_policy(self) -> Self:
        """Validate retention policy.

        Returns:
            JournalRetentionPolicy: Validated policy.
        """
        logger.info("Validating retention policy for {}.", self.route.value)
        return self


class AppendOnlyEventJournal:
    """Encrypted append-only JSONL trading journal."""

    def __init__(
        self,
        *,
        path: Path,
        snapshot_path: Path,
        signature_path: Path,
        clock: Clock,
        encryption_provider: EncryptionProvider,
        build_metadata: JournalBuildMetadata,
    ) -> None:
        """Initialize an append-only event journal.

        Args:
            path: Encrypted journal JSONL path.
            snapshot_path: Snapshot JSONL path.
            signature_path: Detached signature JSONL path.
            clock: Injected clock.
            encryption_provider: Injected encryption/signing provider.
            build_metadata: Software/config provenance.
        """
        logger.info("Initializing append-only event journal at {}.", path)
        self._path = path
        self._snapshot_path = snapshot_path
        self._signature_path = signature_path
        self._clock = clock
        self._encryption_provider = encryption_provider
        self._build_metadata = build_metadata

    def append_event(
        self,
        *,
        event_type: str,
        request_id: str,
        correlation_id: str,
        route: TradingRoute,
        account_id: str,
        symbol: str,
        actor: str,
        payload: JsonObject,
    ) -> JournalEvent:
        """Append an immutable journal event.

        Args:
            event_type: Event type name.
            request_id: Request identifier.
            correlation_id: Correlation identifier.
            route: Trading route.
            account_id: Account identifier.
            symbol: Symbol identifier.
            actor: Actor identifier.
            payload: Event payload.

        Returns:
            JournalEvent: Persisted journal event.
        """
        logger.info("Appending journal event type {}.", event_type)
        events = self.read_events()
        previous_hash = events[-1].event_hash if events else GENESIS_HASH
        sequence_id = events[-1].sequence_id + 1 if events else 1
        now = self._clock.now_utc().isoformat()
        base = {
            "previous_event_hash": previous_hash,
            "schema_version": "1.0.0",
            "timestamp_utc": now,
            "monotonic_timestamp": self._clock.monotonic(),
            "sequence_id": sequence_id,
            "request_id": request_id,
            "correlation_id": correlation_id,
            "route": route.value,
            "account_id": account_id,
            "symbol": symbol,
            "actor": actor,
            "event_type": event_type,
            "payload": payload,
            **self._build_metadata.model_dump(mode="json"),
        }
        event_id = _sha256({"event_id_material": base})
        event_hash = _sha256({"event_id": event_id, **base})
        event = JournalEvent(event_id=event_id, event_hash=event_hash, **base)
        self._append_encrypted(event.model_dump(mode="json"))
        return event

    def read_events(self) -> tuple[JournalEvent, ...]:
        """Read and decrypt all journal events.

        Returns:
            tuple[JournalEvent, ...]: Journal events ordered by sequence ID.
        """
        logger.info("Reading journal events.")
        if not self._path.exists():
            return ()
        events: list[JournalEvent] = []
        for line in self._path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            encrypted = json.loads(line)
            if not isinstance(encrypted, str):
                raise TypeError("journal line must contain encrypted text.")
            plaintext = self._encryption_provider.decrypt(encrypted)
            events.append(JournalEvent.model_validate_json(plaintext))
        return tuple(sorted(events, key=lambda event: event.sequence_id))

    def scan_unresolved(
        self,
        *,
        route: TradingRoute,
        account_id: str,
    ) -> tuple[ReconciliationLock, ...]:
        """Scan unresolved in-flight commands and return mutation locks.

        Args:
            route: Trading route.
            account_id: Account identifier.

        Returns:
            tuple[ReconciliationLock, ...]: Per-scope reconciliation locks.
        """
        logger.info("Scanning unresolved journal commands.")
        terminal_request_ids = {
            event.request_id
            for event in self.read_events()
            if event.route is route
            and event.account_id == account_id
            and event.event_type in TERMINAL_EVENT_TYPES
        }
        locks: dict[tuple[str, str, str], ReconciliationLock] = {}
        for event in self.read_events():
            if (
                event.route is route
                and event.account_id == account_id
                and event.event_type in IN_FLIGHT_EVENT_TYPES
                and event.request_id not in terminal_request_ids
            ):
                locks[(event.account_id, event.symbol, event.request_id)] = (
                    ReconciliationLock(
                        account_id=event.account_id,
                        symbol=event.symbol,
                        request_id=event.request_id,
                        reason="journaled command has no terminal event",
                    )
                )
        return tuple(locks.values())

    def write_snapshot(
        self,
        *,
        route: TradingRoute,
        account_id: str,
        state: JsonObject,
    ) -> StateSnapshot:
        """Write a durable encrypted state snapshot.

        Args:
            route: Trading route.
            account_id: Account identifier.
            state: Projection state.

        Returns:
            StateSnapshot: Persisted snapshot metadata.
        """
        logger.info("Writing state snapshot for account {}.", account_id)
        events = self.read_events()
        sequence_id = events[-1].sequence_id if events else 0
        terminal_hash = events[-1].event_hash if events else GENESIS_HASH
        plaintext = canonical_json(state)
        encrypted_payload = self._encryption_provider.encrypt(plaintext)
        signature = self._encryption_provider.sign(plaintext)
        snapshot = StateSnapshot(
            snapshot_id=_sha256(
                {
                    "route": route.value,
                    "account_id": account_id,
                    "sequence_id": sequence_id,
                    "state": state,
                },
            ),
            route=route,
            account_id=account_id,
            created_at=self._clock.now_utc().isoformat(),
            sequence_id=sequence_id,
            terminal_event_hash=terminal_hash,
            state=state,
            encrypted_payload=encrypted_payload,
            signature=signature,
        )
        self._append_jsonl(self._snapshot_path, snapshot.model_dump(mode="json"))
        return snapshot

    def rebuild_from_snapshot(
        self,
        *,
        snapshot: StateSnapshot,
        until_sequence_id: int | None = None,
    ) -> JsonObject:
        """Rebuild state as snapshot plus replay of subsequent events.

        Args:
            snapshot: Historical baseline snapshot.
            until_sequence_id: Optional inclusive sequence cutoff.

        Returns:
            JsonObject: Rebuilt projection state.
        """
        logger.info("Rebuilding projection from snapshot {}.", snapshot.snapshot_id)
        subsequent = [
            event
            for event in self.read_events()
            if event.sequence_id > snapshot.sequence_id
            and (until_sequence_id is None or event.sequence_id <= until_sequence_id)
        ]
        return replay_builder(snapshot=snapshot.state, events=subsequent)

    def verify_hash_chain(self) -> JournalIntegrityResult:
        """Verify the full journal previous-hash chain.

        Returns:
            JournalIntegrityResult: Integrity validation outcome.
        """
        logger.info("Verifying journal hash chain.")
        previous = GENESIS_HASH
        for event in self.read_events():
            expected_hash = _sha256(event.hash_material())
            if (
                event.previous_event_hash != previous
                or event.event_hash != expected_hash
            ):
                alert: JsonObject = {
                    "severity": "critical",
                    "event_id": event.event_id,
                    "message": "Journal hash chain is broken; block live mutation.",
                }
                return JournalIntegrityResult(
                    valid=False,
                    broken_event_id=event.event_id,
                    alert=alert,
                )
            previous = event.event_hash
        return JournalIntegrityResult(valid=True)

    def seal_segment(self) -> SegmentSeal:
        """Write a detached signature for the current journal segment.

        Returns:
            SegmentSeal: Detached segment seal.
        """
        logger.info("Sealing journal segment.")
        events = self.read_events()
        terminal_hash = events[-1].event_hash if events else GENESIS_HASH
        sequence_id = events[-1].sequence_id if events else 0
        signature = self._encryption_provider.sign(terminal_hash)
        seal = SegmentSeal(
            seal_id=_sha256(
                {"terminal_hash": terminal_hash, "sequence_id": sequence_id},
            ),
            terminal_hash=terminal_hash,
            signature=signature,
            sealed_at=self._clock.now_utc().isoformat(),
            sequence_id=sequence_id,
        )
        self._append_jsonl(self._signature_path, seal.model_dump(mode="json"))
        return seal

    def compact_after_snapshot(
        self,
        *,
        snapshot: StateSnapshot,
        retention_policy: JournalRetentionPolicy,
    ) -> JournalEvent:
        """Model route-aware compaction by appending a segment-seal event.

        Args:
            snapshot: Snapshot sealing previous segment.
            retention_policy: Route-aware retention policy.

        Returns:
            JournalEvent: Segment-seal journal event preserving hash chain.
        """
        logger.info("Compacting journal after snapshot {}.", snapshot.snapshot_id)
        return self.append_event(
            event_type="SegmentSealEvent",
            request_id=snapshot.snapshot_id,
            correlation_id=snapshot.snapshot_id,
            route=retention_policy.route,
            account_id=snapshot.account_id,
            symbol="*",
            actor="system",
            payload={
                "terminal_hash": snapshot.terminal_event_hash,
                "retention_days": retention_policy.retention_days,
                "archive_after_snapshot": retention_policy.archive_after_snapshot,
            },
        )

    def _append_encrypted(self, payload: JsonObject) -> None:
        """Append an encrypted journal payload.

        Args:
            payload: JSON payload to encrypt.
        """
        logger.debug("Appending encrypted journal payload.")
        self._append_jsonl(
            self._path,
            self._encryption_provider.encrypt(canonical_json(payload)),
        )

    def _append_jsonl(self, path: Path, payload: JsonValue) -> None:
        """Append a value to JSONL storage with fsync.

        Args:
            path: Target JSONL path.
            payload: JSON value.
        """
        logger.debug("Appending journal JSONL value to {}.", path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, sort_keys=True))
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())


def replay_builder(
    *,
    snapshot: JsonObject,
    events: Iterable[JournalEvent],
) -> JsonObject:
    """Re-materialize projection state from snapshot and journal events.

    Args:
        snapshot: Historical projection snapshot.
        events: Subsequent journal events.

    Returns:
        JsonObject: Reconstructed projection state.
    """
    logger.info("Building replay projection from snapshot.")
    state: JsonObject = dict(snapshot)
    applied: list[JsonValue] = []
    for event in sorted(events, key=lambda item: item.sequence_id):
        applied.append(event.sequence_id)
        state["last_sequence_id"] = event.sequence_id
        state["last_event_hash"] = event.event_hash
        state["last_event_type"] = event.event_type
        projections = state.setdefault("events", [])
        if isinstance(projections, list):
            projections.append(event.payload)
    state["applied_sequence_ids"] = applied
    return state


def _sha256(payload: JsonObject) -> str:
    """Hash canonical JSON payloads with SHA-256.

    Args:
        payload: JSON payload.

    Returns:
        str: SHA-256 hex digest.
    """
    logger.debug("Hashing journal payload.")
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()
