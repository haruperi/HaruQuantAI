"""Unit tests for local dataset manifest verification boundary."""

from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

from app.services.data.local_datasets.contracts import DatasetLoadRequest
from app.services.data.local_datasets.manifest import (
    verify_dataset_manifest,
    verify_manifest_compatibility,
)
from app.services.data.persistence.contracts import StorageManifest
from app.utils import generate_id


def test_verify_dataset_manifest_delegates_to_load_dataset() -> None:
    """Verify verify_dataset_manifest delegates to load_dataset."""
    request = MagicMock(spec=DatasetLoadRequest)
    expected_dataset = MagicMock()
    with patch(
        "app.services.data.local_datasets.manifest._load_dataset_raw",
        return_value=expected_dataset,
    ) as mock_load:
        result = verify_dataset_manifest(request)
        mock_load.assert_called_once_with(request)
        assert result is expected_dataset


def _manifest(*, schema_version: str, normalization_version: str) -> StorageManifest:
    """Return one minimal valid StorageManifest fixture (TC-IMP-DATA-07)."""
    now = datetime(2026, 1, 1, tzinfo=UTC)
    return StorageManifest(
        artifact_id="artifact-fixture",
        relative_path=Path("data/raw/EURUSD/fixture.csv"),
        format="csv",
        content_hash="a" * 64,
        schema_version=schema_version,
        normalization_version=normalization_version,
        source_revision="v1",
        row_count=1,
        start=now,
        end=now,
        available_at=now,
        license_metadata={},
        provenance={},
        created_at=now,
        request_id=generate_id("req"),
    )


def test_verify_manifest_compatibility_accepts_matching_versions() -> None:
    """A manifest matching the caller's expectations is compatible."""
    manifest = _manifest(schema_version="v1", normalization_version="v1")
    result = verify_manifest_compatibility(
        manifest, expected_schema_version="v1", expected_normalization_version="v1"
    )
    assert result.compatible is True
    assert result.reasons == ()


def test_verify_manifest_compatibility_rejects_schema_mismatch() -> None:
    """A schema version mismatch is reported with a reason."""
    manifest = _manifest(schema_version="v1", normalization_version="v1")
    result = verify_manifest_compatibility(
        manifest, expected_schema_version="v2", expected_normalization_version="v1"
    )
    assert result.compatible is False
    assert len(result.reasons) == 1
    assert "schema_version" in result.reasons[0]


def test_verify_manifest_compatibility_rejects_normalization_mismatch() -> None:
    """A normalization version mismatch is reported with a reason."""
    manifest = _manifest(schema_version="v1", normalization_version="v1")
    result = verify_manifest_compatibility(
        manifest, expected_schema_version="v1", expected_normalization_version="v2"
    )
    assert result.compatible is False
    assert len(result.reasons) == 1
    assert "normalization_version" in result.reasons[0]


def test_manifest_available_at_is_a_typed_field() -> None:
    """`available_at` round-trips as an aware-UTC field, not free-form text."""
    now = datetime(2026, 1, 1, tzinfo=UTC)
    manifest = _manifest(schema_version="v1", normalization_version="v1")
    assert manifest.available_at == now
    assert manifest.available_at.tzinfo is not None
