"""Tests for trading event journal persistence."""

from __future__ import annotations

import base64
import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from app.services.trading import TradingRoute
from app.services.trading.state import (
    AppendOnlyEventJournal,
    JournalBuildMetadata,
    JournalRetentionPolicy,
    StateSnapshot,
    replay_builder,
)


class MutableClock:
    """Mutable journal test clock."""

    def __init__(self) -> None:
        """Initialize the clock."""
        self.current = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)
        self.tick = 10.0

    def now_utc(self) -> datetime:
        """Return current UTC timestamp."""
        return self.current

    def now_ptp(self) -> datetime:
        """Return current PTP timestamp."""
        return self.current

    def monotonic(self) -> float:
        """Return and advance deterministic monotonic value."""
        self.tick += 1.0
        return self.tick


class PrefixEncryption:
    """Deterministic encryption and signing provider."""

    def encrypt(self, plaintext: str) -> str:
        """Encrypt plaintext."""
        encoded = base64.b64encode(plaintext.encode("utf-8")).decode("ascii")
        return f"enc:{encoded}"

    def decrypt(self, ciphertext: str) -> str:
        """Decrypt ciphertext."""
        encoded = ciphertext.removeprefix("enc:")
        return base64.b64decode(encoded.encode("ascii")).decode("utf-8")

    def sign(self, payload: str) -> str:
        """Sign payload."""
        return f"sig:{payload}"


def _metadata() -> JournalBuildMetadata:
    """Build journal metadata."""
    return JournalBuildMetadata(
        software_version="1.0.0",
        vcs_commit_hash="abc123",
        dirty_tree=False,
        active_config_hash="config-hash",
    )


def _journal(
    tmp_path: Path,
    clock: MutableClock | None = None,
) -> AppendOnlyEventJournal:
    """Build a test journal."""
    return AppendOnlyEventJournal(
        path=tmp_path / "journal.jsonl",
        snapshot_path=tmp_path / "snapshots.jsonl",
        signature_path=tmp_path / "signatures.jsonl",
        clock=clock or MutableClock(),
        encryption_provider=PrefixEncryption(),
        build_metadata=_metadata(),
    )


def test_append_events_have_hash_chain_sequence_and_provenance(tmp_path: Path) -> None:
    """Journal events carry required forensic metadata."""
    journal = _journal(tmp_path)

    first = journal.append_event(
        event_type="TradingCommandAccepted",
        request_id="req-1",
        correlation_id="corr-1",
        route=TradingRoute.LIVE,
        account_id="acct",
        symbol="EURUSD",
        actor="strategy",
        payload={"command_id": "cmd-1"},
    )
    second = journal.append_event(
        event_type="BrokerDispatchEvent",
        request_id="req-1",
        correlation_id="corr-1",
        route=TradingRoute.LIVE,
        account_id="acct",
        symbol="EURUSD",
        actor="system",
        payload={"broker_request_ref": "broker-1"},
    )

    assert first.sequence_id == 1
    assert second.sequence_id == 2
    assert second.previous_event_hash == first.event_hash
    assert first.software_version == "1.0.0"
    assert "TradingCommandAccepted" not in (tmp_path / "journal.jsonl").read_text(
        encoding="utf-8",
    )
    assert journal.verify_hash_chain().valid is True


def test_scan_unresolved_returns_reconciliation_locks(tmp_path: Path) -> None:
    """Accepted or dispatched commands without terminal events lock scopes."""
    journal = _journal(tmp_path)
    journal.append_event(
        event_type="TradingCommandAccepted",
        request_id="req-open",
        correlation_id="corr",
        route=TradingRoute.LIVE,
        account_id="acct",
        symbol="EURUSD",
        actor="strategy",
        payload={},
    )
    journal.append_event(
        event_type="TradingCommandAccepted",
        request_id="req-done",
        correlation_id="corr",
        route=TradingRoute.LIVE,
        account_id="acct",
        symbol="GBPUSD",
        actor="strategy",
        payload={},
    )
    journal.append_event(
        event_type="ExecutionReportEvent",
        request_id="req-done",
        correlation_id="corr",
        route=TradingRoute.LIVE,
        account_id="acct",
        symbol="GBPUSD",
        actor="broker",
        payload={"execution_state": "filled"},
    )

    locks = journal.scan_unresolved(route=TradingRoute.LIVE, account_id="acct")

    assert len(locks) == 1
    assert locks[0].request_id == "req-open"
    assert locks[0].symbol == "EURUSD"


def test_snapshot_rebuild_replay_and_segment_seal(tmp_path: Path) -> None:
    """Snapshots rebuild via replay and segment seals preserve terminal hashes."""
    journal = _journal(tmp_path)
    event = journal.append_event(
        event_type="TradingCommandAccepted",
        request_id="req-1",
        correlation_id="corr",
        route=TradingRoute.PAPER,
        account_id="acct",
        symbol="EURUSD",
        actor="strategy",
        payload={"accepted": True},
    )
    snapshot = journal.write_snapshot(
        route=TradingRoute.PAPER,
        account_id="acct",
        state={"balance": "1000"},
    )
    later = journal.append_event(
        event_type="ExecutionReportEvent",
        request_id="req-1",
        correlation_id="corr",
        route=TradingRoute.PAPER,
        account_id="acct",
        symbol="EURUSD",
        actor="broker",
        payload={"pnl": "1.00"},
    )

    rebuilt = journal.rebuild_from_snapshot(snapshot=snapshot)
    direct = replay_builder(snapshot={"balance": "1000"}, events=(later,))
    seal = journal.seal_segment()
    compact = journal.compact_after_snapshot(
        snapshot=snapshot,
        retention_policy=JournalRetentionPolicy(
            route=TradingRoute.PAPER,
            retention_days=30,
        ),
    )

    assert snapshot.sequence_id == event.sequence_id
    assert snapshot.encrypted_payload.startswith("enc:")
    assert rebuilt["last_sequence_id"] == later.sequence_id
    assert direct["last_event_type"] == "ExecutionReportEvent"
    assert seal.terminal_hash == later.event_hash
    assert compact.event_type == "SegmentSealEvent"


def test_hash_chain_tampering_blocks_live_mutation(tmp_path: Path) -> None:
    """Broken hash chains return critical incident alerts."""
    journal = _journal(tmp_path)
    journal.append_event(
        event_type="TradingCommandAccepted",
        request_id="req-1",
        correlation_id="corr",
        route=TradingRoute.LIVE,
        account_id="acct",
        symbol="EURUSD",
        actor="strategy",
        payload={},
    )
    lines = (tmp_path / "journal.jsonl").read_text(encoding="utf-8").splitlines()
    crypto = PrefixEncryption()
    decrypted = crypto.decrypt(lines[0].strip('"'))
    tampered = decrypted.replace('"event_hash":"', '"event_hash":"bad')
    (tmp_path / "journal.jsonl").write_text(
        f"{json.dumps(crypto.encrypt(tampered))}\n",
        encoding="utf-8",
    )

    result = journal.verify_hash_chain()

    assert result.valid is False
    assert result.alert is not None
    assert result.alert["severity"] == "critical"


def test_journal_validation_and_read_errors(tmp_path: Path) -> None:
    """Invalid metadata, snapshot, and journal line shapes fail closed."""
    with pytest.raises(ValueError, match="software_version"):
        JournalBuildMetadata(
            software_version=" ",
            vcs_commit_hash="abc",
            dirty_tree=False,
            active_config_hash="config",
        )
    with pytest.raises(ValueError, match="snapshot_id"):
        StateSnapshot(
            snapshot_id=" ",
            route=TradingRoute.SIM,
            account_id="acct",
            created_at="now",
            sequence_id=0,
            terminal_event_hash="hash",
            state={},
            encrypted_payload="enc",
            signature="sig",
        )

    (tmp_path / "journal.jsonl").write_text("{}\n", encoding="utf-8")
    with pytest.raises(TypeError, match="encrypted text"):
        _journal(tmp_path).read_events()
