"""Agentic operations journal, containment, and replay eligibility."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import re
from pathlib import Path

from app.contracts.agentic.operations import (
    ContainmentDecision, OperationRecord, ReadinessQuery, ReadinessStatus, ReadinessView,
    ReplayDecision, ReplayValidationRequest,
)
from app.contracts.workspace.persistence import (
    FeatureMigration, FeatureMigrationManifest, NamespaceRegistration, PersistenceCapability,
    PersistenceStatement, PersistenceTransactionRequest,
)

NAMESPACE = "agentic.operations"
TABLES = ("agentic_operation_log", "agentic_readiness")
MIGRATION_SQL = """
CREATE TABLE IF NOT EXISTS agentic_operation_log (
 operation_id TEXT PRIMARY KEY, account_id TEXT NOT NULL, correlation_id TEXT NOT NULL,
 event_class TEXT NOT NULL, safe_payload TEXT NOT NULL, artifact_refs TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS agentic_readiness (
 account_id TEXT PRIMARY KEY, status TEXT NOT NULL, reason_code TEXT NOT NULL,
 generation INTEGER NOT NULL, decision_id TEXT NOT NULL, created_at TEXT NOT NULL
);
""".strip()
MIGRATION = FeatureMigration(1, "agentic-operations-v1", MIGRATION_SQL, hashlib.sha256(MIGRATION_SQL.encode()).hexdigest())
_SECRET = re.compile(r"(?i)(authorization|password|secret|token|api[_-]?key)\s*[:=]\s*[^\s,;]+")


class OperateRunsService:
    def __init__(self, persistence: PersistenceCapability, max_payload_chars: int) -> None:
        self._persistence = persistence
        self._max = max_payload_chars
        self._mounted: set[Path] = set()
        self._closed = False

    def _ensure(self, workspace: Path) -> Path:
        path = workspace.resolve()
        if path not in self._mounted:
            self._persistence.register_namespace(NamespaceRegistration(NAMESPACE, TABLES))
            self._persistence.apply_migrations(path, FeatureMigrationManifest(NAMESPACE, (MIGRATION,)))
            self._mounted.add(path)
        return path

    def _tx(self, workspace: Path, account: str, request_id: str, statements: tuple[PersistenceStatement, ...]) -> tuple[tuple[dict[str, object], ...], ...]:
        result = self._persistence.execute_transaction(PersistenceTransactionRequest(
            request_id=request_id, actor_id="agentic-operations", account_id=account,
            workspace_path=self._ensure(workspace), namespace=NAMESPACE, statements=statements,
        ))
        return result.results

    def _redact(self, payload: str) -> str:
        safe = _SECRET.sub(lambda m: m.group(1) + "=[REDACTED]", payload)
        return safe[: self._max]

    async def record_operation(self, record: OperationRecord) -> OperationRecord:
        if self._closed:
            raise RuntimeError("operate-runs service is closed")
        created = record.created_at or datetime.now(timezone.utc)
        safe = self._redact(record.safe_payload)
        self._tx(record.workspace_path, record.account_id, record.operation_id, (PersistenceStatement(
            "INSERT INTO agentic_operation_log VALUES (?, ?, ?, ?, ?, ?, ?)",
            (record.operation_id, record.account_id, record.correlation_id, record.event_class, safe, json.dumps(record.artifact_refs), created.isoformat()),
        ),))
        return OperationRecord(record.operation_id, record.workspace_path, record.account_id, record.correlation_id, record.event_class, safe, record.artifact_refs, created)

    async def contain(self, decision: ContainmentDecision) -> ReadinessView:
        if self._closed:
            raise RuntimeError("operate-runs service is closed")
        created = decision.created_at or datetime.now(timezone.utc)
        rows = self._tx(decision.workspace_path, decision.account_id, decision.decision_id, (
            PersistenceStatement("SELECT generation FROM agentic_readiness WHERE account_id = ?", (decision.account_id,)),
        ))
        prior = int(rows[0][0]["generation"]) if rows and rows[0] else 0
        if decision.generation <= prior:
            raise ValueError("AGENTIC_READINESS_GENERATION_STALE")
        self._tx(decision.workspace_path, decision.account_id, decision.decision_id + ":commit", (PersistenceStatement(
            "INSERT INTO agentic_readiness VALUES (?, ?, ?, ?, ?, ?) ON CONFLICT(account_id) DO UPDATE SET status=excluded.status, reason_code=excluded.reason_code, generation=excluded.generation, decision_id=excluded.decision_id, created_at=excluded.created_at",
            (decision.account_id, decision.status.value, decision.reason_code, decision.generation, decision.decision_id, created.isoformat()),
        ),))
        return ReadinessView(decision.status, decision.reason_code, decision.generation, created)

    async def readiness(self, query: ReadinessQuery) -> ReadinessView:
        if self._closed:
            raise RuntimeError("operate-runs service is closed")
        rows = self._tx(query.workspace_path, query.account_id, "readiness:" + hashlib.sha256(query.account_id.encode()).hexdigest()[:16], (
            PersistenceStatement("SELECT status, reason_code, generation FROM agentic_readiness WHERE account_id = ?", (query.account_id,)),
        ))
        now = datetime.now(timezone.utc)
        if not rows or not rows[0]:
            return ReadinessView(ReadinessStatus.UNAVAILABLE, "READINESS_NOT_PROVEN", 0, now)
        row = rows[0][0]
        return ReadinessView(ReadinessStatus(str(row["status"])), str(row["reason_code"]), int(row["generation"]), now)

    async def validate_replay(self, request: ReplayValidationRequest) -> ReplayDecision:
        if self._closed:
            raise RuntimeError("operate-runs service is closed")
        reasons: list[str] = []
        if not request.side_effect_free:
            reasons.append("REPLAY_SIDE_EFFECT_PROHIBITED")
        if dict(request.expected_refs) != dict(request.observed_refs):
            reasons.append("REPLAY_REFERENCE_DRIFT")
        if len(dict(request.expected_refs)) != len(request.expected_refs):
            reasons.append("REPLAY_DUPLICATE_REFERENCE")
        return ReplayDecision(not reasons, tuple(reasons), datetime.now(timezone.utc))

    def close(self) -> None:
        self._closed = True
        self._mounted.clear()
