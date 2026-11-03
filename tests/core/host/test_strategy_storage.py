"""Atomic strategy storage acceptance tests.

Description:
    Exercise isolated record recovery, integrity, locking, and optimistic writes.
Purpose:
    FEAT-WIZARD-HSL-LANGUAGE: Durable strategy evidence.
Key Capabilities:
    - FR-test-hsl-storage: Verify failed writes preserve committed records.
Python API Usage:
    Run pytest against this module.
CLI Usage:
    uv run pytest tests/core/host --no-cov
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from app.core.host.strategy_storage import HostStrategyStorage
from app.core.lib.errors import DomainError


def test_restart_and_revision_conflicts(tmp_path: Path) -> None:
    """A fresh owner reads committed content and rejects stale revisions."""
    storage = HostStrategyStorage(tmp_path)
    assert storage.load("file:first") is None
    assert (
        storage.save("file:first", {"document": {"id": "one"}}, expected_revision=0)
        == 1
    )
    recovered = HostStrategyStorage(tmp_path)
    assert (
        recovered.records("file:")["file:first"]["payload"]["document"]["id"] == "one"
    )
    with pytest.raises(DomainError) as error:
        recovered.save("file:first", {"id": "two"}, expected_revision=0)
    assert error.value.code == "WIZARD_REVISION_CONFLICT"
    assert recovered.load("file:first") == storage.load("file:first")


def test_atomic_failure_preserves_record(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A failed atomic replacement cannot truncate the last committed definition."""
    storage = HostStrategyStorage(tmp_path)
    storage.save("strategy:one", {"id": "one"}, expected_revision=0)
    before = storage.load("strategy:one")

    def unavailable(*_args: Any) -> None:
        raise OSError("isolated test replacement failure")

    monkeypatch.setattr("app.core.host.strategy_storage.os.replace", unavailable)
    with pytest.raises(OSError, match="isolated test"):
        storage.save("strategy:one", {"id": "two"}, expected_revision=1)
    assert storage.load("strategy:one") == before
    assert not list(tmp_path.glob("*.lock"))
    assert not list(tmp_path.glob("*.tmp"))


def test_corruption_and_exclusive_writer(tmp_path: Path) -> None:
    """Conflicting writers and corrupt JSON fail explicitly."""
    storage = HostStrategyStorage(tmp_path)
    storage.save("one", {"id": "one"}, expected_revision=0)
    path = next(tmp_path.glob("*.json"))
    lock = path.with_suffix(".lock")
    lock.touch()
    with pytest.raises(DomainError) as error:
        storage.save("one", {"id": "two"}, expected_revision=1)
    assert error.value.code == "HSL_STORAGE_BUSY"
    lock.unlink()
    path.write_text('{"key":"one", "payload":{}}', encoding="utf-8")
    with pytest.raises(DomainError) as error:
        storage.load("one")
    assert error.value.code == "HSL_STORAGE_CORRUPT"


def test_invalid_keys_and_malformed_records(tmp_path: Path) -> None:
    """Storage rejects empty or non-string keys, malformed envelopes, and negative revisions."""
    import hashlib
    import json

    storage = HostStrategyStorage(tmp_path)
    with pytest.raises(ValueError, match="A strategy storage key is required"):
        storage.load("")
    with pytest.raises(ValueError, match="A strategy storage key is required"):
        storage.load(123)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="A strategy storage key is required"):
        storage.save("", {"id": 1}, expected_revision=0)

    # Valid save
    storage.save("strat:valid", {"id": "ok"}, expected_revision=0)
    file_path = next(tmp_path.glob("*.json"))

    # Test malformed payload (not a dict)
    raw = json.dumps(
        {"key": "strat:valid", "payload": "not-a-dict", "revision": 1},
        sort_keys=True,
        separators=(",", ":"),
    )
    corrupted = {
        "key": "strat:valid",
        "payload": "not-a-dict",
        "revision": 1,
        "sha256": hashlib.sha256(raw.encode()).hexdigest(),
    }
    file_path.write_text(json.dumps(corrupted), encoding="utf-8")
    with pytest.raises(DomainError) as error:
        storage.load("strat:valid")
    assert error.value.code == "HSL_STORAGE_CORRUPT"

    # Test negative revision
    raw = json.dumps(
        {"key": "strat:valid", "payload": {"id": "ok"}, "revision": -1},
        sort_keys=True,
        separators=(",", ":"),
    )
    corrupted_neg = {
        "key": "strat:valid",
        "payload": {"id": "ok"},
        "revision": -1,
        "sha256": hashlib.sha256(raw.encode()).hexdigest(),
    }
    file_path.write_text(json.dumps(corrupted_neg), encoding="utf-8")
    with pytest.raises(DomainError) as error:
        storage.load("strat:valid")
    assert error.value.code == "HSL_STORAGE_CORRUPT"


def test_records_enumeration_corruptions(tmp_path: Path) -> None:
    """Storage enumeration rejects unreadable files and invalid envelope keys."""
    storage = HostStrategyStorage(tmp_path)

    # Corrupt file during enumeration
    bad_file = tmp_path / "bad.json"
    bad_file.write_text("invalid json content", encoding="utf-8")
    with pytest.raises(DomainError) as error:
        storage.records("any:")
    assert error.value.code == "HSL_STORAGE_CORRUPT"
    bad_file.unlink()

    # File with key mismatch (key does not hash to filename)
    mismatched_file = tmp_path / "wrong_hash.json"
    mismatched_file.write_text('{"key": "strat:one"}', encoding="utf-8")
    with pytest.raises(DomainError) as error:
        storage.records("any:")
    assert error.value.code == "HSL_STORAGE_CORRUPT"
    mismatched_file.unlink()
