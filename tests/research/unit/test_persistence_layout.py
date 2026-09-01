"""Unit evidence for the Research persistence support layout."""

import importlib
from types import SimpleNamespace

import pytest
from app.kernel.identity import generate_id
from app.services.research.persistence.create import create_artifact_metadata


def test_persistence_verbs_match_registered_feature_needs() -> None:
    """Read/update support evidence while delete remains unsupported."""
    read_module = importlib.import_module("app.services.research.persistence.read")
    update_module = importlib.import_module("app.services.research.persistence.update")
    delete_module = importlib.import_module("app.services.research.persistence.delete")
    assert read_module.__all__
    assert update_module.__all__ == ("update_expectancy_governance",)
    assert delete_module.__all__ == ()


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
