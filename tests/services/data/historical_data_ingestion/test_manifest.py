"""Tests for Historical Data Ingestion feature manifest."""

from __future__ import annotations

from app.contracts.data.capabilities import INGEST_HISTORY_CAPABILITY
from app.kernel.state import RetentionPolicy
from app.services.data.historical_data_ingestion.manifest import SPEC


def test_manifest_spec() -> None:
    """Test HistoricalDataIngestion feature specification."""
    assert SPEC.feature_id == "FEAT-DATA-INGEST_HISTORY"
    assert SPEC.domain == "data"
    assert INGEST_HISTORY_CAPABILITY in SPEC.provides
    assert len(SPEC.requires) == 0
    assert SPEC.state is not None
    assert SPEC.state.namespace == "data.historical_ingestion"
    assert SPEC.state.retention_policy == RetentionPolicy.RETAIN
    assert "database_path" in SPEC.config_keys
