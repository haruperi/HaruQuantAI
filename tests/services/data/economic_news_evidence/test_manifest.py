"""Unit tests for Economic Calendar and News Evidence manifest."""

from app.contracts.data.capabilities import TRACK_MARKET_NEWS_CAPABILITY
from app.kernel.state import RetentionPolicy
from app.services.data.economic_news_evidence.manifest import SPEC


def test_manifest_structure() -> None:
    """Verify FeatureSpec metadata and declarations."""
    assert SPEC.feature_id == "FEAT-DATA-TRACK_MARKET_NEWS"
    assert SPEC.domain == "data"
    assert TRACK_MARKET_NEWS_CAPABILITY in SPEC.provides
    assert SPEC.requires == frozenset()
    assert SPEC.optional == frozenset()
    assert SPEC.conflicts == frozenset()
    assert SPEC.state is not None
    assert SPEC.state.namespace == "data.economic_news"
    assert SPEC.state.retention_policy == RetentionPolicy.RETAIN
    assert "database_path" in SPEC.config_keys
    assert "max_query_results" in SPEC.config_keys
