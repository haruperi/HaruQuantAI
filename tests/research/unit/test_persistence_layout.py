"""Unit evidence for the Research persistence support layout."""

import importlib
from types import SimpleNamespace

import pytest
from app.services.research.persistence.create import create_artifact_metadata
from app.utils import generate_id


def test_unsupported_persistence_verbs_are_explicitly_empty() -> None:
    """Read, update, and delete modules remain explicit unsupported seams."""
    for verb in ("read", "update", "delete"):
        module = importlib.import_module(f"app.services.research.persistence.{verb}")
        assert module.__all__ == ()


def test_metadata_create_fails_when_migration_is_unconfirmed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Metadata creation fails closed before SQL when migration is unconfirmed."""
    monkeypatch.setattr(
        "app.services.research.persistence.create.run_domain_migrations",
        lambda _request: SimpleNamespace(status="error", data=None),
    )
    with pytest.raises(ValueError, match="MIGRATION_FAILED"):
        create_artifact_metadata(
            relative_path="report.json",
            format_name="json",
            size_bytes=1,
            sha256="e" * 64,
            atomic=True,
            schema_version="v1",
            audit_event_id="evt-test",
            request_id=generate_id("req"),
            correlation_id=generate_id("cor"),
        )
