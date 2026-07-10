"""Tests for local trading state manager."""

from __future__ import annotations

import base64
from datetime import UTC, datetime
from pathlib import Path

from app.services.trading import TradingRoute
from app.services.trading.contracts import JsonObject
from app.services.trading.state import (
    AppendOnlyEventJournal,
    JournalBuildMetadata,
    LocalStateManager,
)


class FixedClock:
    """Fixed test clock."""

    def now_utc(self) -> datetime:
        """Return fixed UTC timestamp."""
        return datetime(2026, 7, 9, 12, 0, tzinfo=UTC)

    def now_ptp(self) -> datetime:
        """Return fixed PTP timestamp."""
        return datetime(2026, 7, 9, 12, 0, tzinfo=UTC)

    def monotonic(self) -> float:
        """Return fixed monotonic timestamp."""
        return 1.0


class PrefixEncryption:
    """Simple encryption provider."""

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


class MemoryStateStore:
    """Memory state store for manager tests."""

    def __init__(self) -> None:
        """Initialize state store."""
        self.snapshots: list[JsonObject] = []

    def save_state(
        self,
        *,
        route: TradingRoute,
        tenant_id: str,
        snapshot: JsonObject,
        expected_version: int | None,
    ) -> str:
        """Save a state snapshot."""
        self.snapshots.append(snapshot)
        return f"{route.value}:{tenant_id}:{expected_version}:{snapshot['id']}"

    def load_state(
        self,
        *,
        route: TradingRoute,
        tenant_id: str,
        snapshot_id: str,
    ) -> JsonObject | None:
        """Load a state snapshot."""
        return {"route": route.value, "tenant_id": tenant_id, "id": snapshot_id}


def test_local_state_manager_persists_state_and_journal(tmp_path: Path) -> None:
    """State manager coordinates state store and journal updates."""
    clock = FixedClock()
    journal = AppendOnlyEventJournal(
        path=tmp_path / "journal.jsonl",
        snapshot_path=tmp_path / "snapshots.jsonl",
        signature_path=tmp_path / "signatures.jsonl",
        clock=clock,
        encryption_provider=PrefixEncryption(),
        build_metadata=JournalBuildMetadata(
            software_version="1.0.0",
            vcs_commit_hash="abc",
            dirty_tree=False,
            active_config_hash="config",
        ),
    )
    state_store = MemoryStateStore()
    manager = LocalStateManager(state_store=state_store, journal=journal, clock=clock)

    result = manager.apply_state_update(
        route=TradingRoute.PAPER,
        tenant_id="tenant",
        account_id="acct",
        symbol="EURUSD",
        request_id="req-1",
        correlation_id="corr-1",
        actor="system",
        event_type="StateUpdated",
        update={"position": "flat"},
        expected_version=None,
    )

    assert result.state_ref == "paper:tenant:None:req-1"
    assert result.journal_event.sequence_id == 1
    assert state_store.snapshots[0]["update"] == {"position": "flat"}
