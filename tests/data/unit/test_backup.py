"""Unit coverage for immutable backup, atomic restore, and raw retention."""

from __future__ import annotations

import hashlib
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from app.services.data._settings import DataSettings, data_settings_context
from app.services.data.contracts import DataError
from app.services.data.persistence.backup import (
    create_backup,
    enforce_retention_policy,
    restore_from_backup,
)
from app.services.data.persistence.contracts import (
    BackupTarget,
    StorageManifest,
)
from app.utils import generate_id


def _settings(root: Path) -> DataSettings:
    """Return isolated storage and lock settings for one test root."""
    return DataSettings(
        database_url="sqlite:///data.db",
        data_dir=root,
        sqlite_busy_timeout_seconds=1.0,
        write_lock_lease_seconds=10.0,
        approved_storage_roots=(
            Path("data/raw"),
            Path("data/processed"),
            Path("data/cache"),
            Path("artifacts/data"),
        ),
    )


@pytest.fixture
def data_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Return an isolated Data root with durable audit replaced by a recorder."""
    for relative in (
        Path("data/raw"),
        Path("data/processed"),
        Path("data/cache"),
        Path("artifacts/data"),
    ):
        (tmp_path / relative).mkdir(parents=True)
    monkeypatch.setattr(
        "app.services.data.persistence.backup.persist_audit_event",
        lambda _event: None,
    )
    return tmp_path


def _target(relative_path: str) -> BackupTarget:
    """Return one explicitly versioned backup target."""
    return BackupTarget(
        relative_path=Path(relative_path),
        schema_version="v1",
        normalization_version="v1",
    )


def test_manifest_records_hash_per_target(data_root: Path) -> None:
    """A committed backup records measured hash and byte evidence per file."""
    payload = data_root / "data/raw/EURUSD.csv"
    payload.write_bytes(b"timestamp,close\n2026-01-01T00:00:00Z,1.2\n")

    with data_settings_context(_settings(data_root)):
        manifest = create_backup((_target("data/raw/EURUSD.csv"),))

    entry = manifest.entries[0]
    assert entry.relative_path == Path("data/raw/EURUSD.csv")
    assert entry.byte_count == payload.stat().st_size
    assert entry.content_hash == hashlib.sha256(payload.read_bytes()).hexdigest()
    committed = data_root / "artifacts/data/backups" / manifest.manifest_id
    assert (committed / "manifest.json").is_file()


def test_restore_round_trip(data_root: Path) -> None:
    """Explicit restore replaces a changed target with its verified snapshot."""
    payload = data_root / "data/raw/EURUSD.csv"
    payload.write_text("original", encoding="utf-8")
    with data_settings_context(_settings(data_root)):
        manifest = create_backup((_target("data/raw/EURUSD.csv"),))
        payload.write_text("changed", encoding="utf-8")
        report = restore_from_backup(manifest.manifest_id)

    assert payload.read_text(encoding="utf-8") == "original"
    assert report.restored_paths == (Path("data/raw/EURUSD.csv"),)


def test_restore_is_atomic_on_hash_mismatch(data_root: Path) -> None:
    """Preflight hash failure leaves every current target unchanged."""
    first = data_root / "data/raw/first.csv"
    second = data_root / "data/raw/second.csv"
    first.write_text("first-original", encoding="utf-8")
    second.write_text("second-original", encoding="utf-8")
    with data_settings_context(_settings(data_root)):
        manifest = create_backup((_target("data/raw"),))
        first.write_text("first-current", encoding="utf-8")
        second.write_text("second-current", encoding="utf-8")
        backup_second = (
            data_root
            / "artifacts/data/backups"
            / manifest.manifest_id
            / "payload/data/raw/second.csv"
        )
        backup_second.write_text("corrupted", encoding="utf-8")
        with pytest.raises(DataError) as captured:
            restore_from_backup(manifest.manifest_id)

    assert captured.value.code == "FILE_CORRUPTED"
    assert first.read_text(encoding="utf-8") == "first-current"
    assert second.read_text(encoding="utf-8") == "second-current"


def test_backup_rejects_unapproved_target_before_read(data_root: Path) -> None:
    """A target outside configured approved roots fails at path admission."""
    outside = data_root / "outside"
    outside.mkdir()
    (outside / "secret.csv").write_text("not admitted", encoding="utf-8")

    with data_settings_context(_settings(data_root)), pytest.raises(DataError) as error:
        create_backup((_target("outside/secret.csv"),))

    assert error.value.code == "PERMISSION_DENIED"


def test_retention_dry_run_does_not_delete(data_root: Path) -> None:
    """Dry-run retention reports expired payloads without mutation."""
    dataset = data_root / "data/raw/EURUSD"
    dataset.mkdir()
    payload = dataset / "old.csv"
    payload.write_text("old", encoding="utf-8")
    old = (datetime.now(UTC) - timedelta(days=20)).timestamp()
    os.utime(payload, (old, old))

    with data_settings_context(_settings(data_root)):
        count = enforce_retention_policy("EURUSD", 10)

    assert count == 1
    assert payload.exists()


def test_retention_purges_payload_and_manifest(data_root: Path) -> None:
    """Committed retention removes an expired payload and companion manifest."""
    dataset = data_root / "data/raw/EURUSD"
    dataset.mkdir()
    payload = dataset / "old.csv"
    payload.write_text("old", encoding="utf-8")
    manifest_path = payload.with_suffix(".csv.manifest.json")
    manifest = StorageManifest(
        artifact_id="artifact-old",
        relative_path=Path("data/raw/EURUSD/old.csv"),
        format="csv",
        content_hash=hashlib.sha256(payload.read_bytes()).hexdigest(),
        schema_version="v1",
        normalization_version="v1",
        source_revision="v1",
        row_count=1,
        start=datetime(2026, 1, 1, tzinfo=UTC),
        end=datetime(2026, 1, 1, tzinfo=UTC),
        license_metadata={"status": "approved", "retention_days": "30"},
        provenance={"source_id": "fixture"},
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        request_id=generate_id("req"),
    )
    manifest_path.write_text(manifest.model_dump_json(), encoding="utf-8")
    old = (datetime.now(UTC) - timedelta(days=20)).timestamp()
    os.utime(payload, (old, old))

    with data_settings_context(_settings(data_root)):
        count = enforce_retention_policy("EURUSD", 10, dry_run=False)

    assert count == 1
    assert not payload.exists()
    assert not manifest_path.exists()


def test_retention_never_overrides_licence_terms(data_root: Path) -> None:
    """A looser requested age than the canonical licence permits is rejected."""
    dataset = data_root / "data/raw/EURUSD"
    dataset.mkdir()
    payload = dataset / "licensed.csv"
    payload.write_text("licensed", encoding="utf-8")
    manifest = StorageManifest(
        artifact_id="artifact-licensed",
        relative_path=Path("data/raw/EURUSD/licensed.csv"),
        format="csv",
        content_hash=hashlib.sha256(payload.read_bytes()).hexdigest(),
        schema_version="v1",
        normalization_version="v1",
        source_revision="v1",
        row_count=1,
        start=datetime(2026, 1, 1, tzinfo=UTC),
        end=datetime(2026, 1, 1, tzinfo=UTC),
        license_metadata={"status": "approved", "retention_days": "5"},
        provenance={"source_id": "fixture"},
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        request_id=generate_id("req"),
    )
    payload.with_suffix(".csv.manifest.json").write_text(
        manifest.model_dump_json(),
        encoding="utf-8",
    )

    with data_settings_context(_settings(data_root)), pytest.raises(DataError) as error:
        enforce_retention_policy("EURUSD", 10)

    assert error.value.code == "LICENSE_RESTRICTION"
