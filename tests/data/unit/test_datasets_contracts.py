"""Unit tests for Data domain dataset load requests and specification revisions."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
from app.kernel.identity import generate_id
from app.services.data.contracts.errors import DataError
from app.services.data.datasets import catalog
from app.services.data.datasets.contracts import (
    DatasetLoadRequest,
    ManifestCompatibility,
    _ProviderSpecificationRevision,
    _relative_path,
)


def test_relative_path_validation() -> None:
    """Verify relative path safety checks."""
    assert _relative_path(Path("data/file.csv")) == Path("data/file.csv")

    with pytest.raises(ValueError, match="path must be relative and traversal-free"):
        _relative_path(Path("C:/abs/path.csv"))

    with pytest.raises(ValueError, match="path must be relative and traversal-free"):
        _relative_path(Path("../traversal.csv"))

    with pytest.raises(ValueError, match="hidden path segments are not allowed"):
        _relative_path(Path(".hidden/path.csv"))


def test_dataset_load_request_and_compatibility() -> None:
    """Verify DatasetLoadRequest and ManifestCompatibility instantiations."""
    req_id = generate_id("req")
    req = DatasetLoadRequest(
        relative_path=Path("dataset.csv"), format="csv", request_id=req_id
    )
    assert req.relative_path == Path("dataset.csv")

    compat = ManifestCompatibility(compatible=True, reasons=("OK",))
    assert compat.compatible is True


def test_provider_specification_revision_validation() -> None:
    """Verify _ProviderSpecificationRevision validation and serializers."""
    now = datetime.now(UTC)
    rev = _ProviderSpecificationRevision(
        revision_id="rev-1",
        broker="mt5",
        server="demo",
        environment="DEMO",
        account_digest="digest-1",
        provider_symbol="EURUSD",
        snapshot_checksum="chk-1",
        observed_at=now,
        effective_from=now,
        effective_to=None,
        retrieval_provenance="direct",
        historical_provenance={"source": "archive"},
        payload={"digits": 5},
        supersedes_revision_id=None,
    )
    assert rev.broker == "mt5"
    assert rev.provider_symbol == "EURUSD"


def test_list_verified_datasets_limit_validation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """list_verified_datasets enforces strict limit bounds."""
    req_id = generate_id("req")
    with pytest.raises(DataError):
        catalog.list_verified_datasets(request_id=req_id, limit=0)

    with pytest.raises(DataError):
        catalog.list_verified_datasets(request_id=req_id, limit=2000)


def test_catalog_provider_identity() -> None:
    """catalog._provider_identity validates text fields."""
    ident = catalog._provider_identity("mt5", "demo", "DEMO", "acc-1", "EURUSD")
    assert ident == ("mt5", "demo", "DEMO", "acc-1", "EURUSD")

    with pytest.raises(DataError):
        catalog._provider_identity("", "demo", "DEMO", "acc-1", "EURUSD")
