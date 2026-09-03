"""Unit tests for EconomicNewsEvidenceConfig."""

from pathlib import Path

from app.services.data.economic_news_evidence.config import EconomicNewsEvidenceConfig


def test_config_defaults() -> None:
    """Verify default configuration values."""
    cfg = EconomicNewsEvidenceConfig()
    assert cfg.database_path == ":memory:"
    assert cfg.max_query_results == 10_000
    assert cfg.default_rate_limit_per_minute == 60
    assert cfg.max_payload_size_bytes == 5_000_000
    assert cfg.default_freshness_limit_seconds == 86_400
    assert "FOREX_FACTORY" in cfg.allowed_sources


def test_config_custom_values() -> None:
    """Verify custom configuration initialization."""
    custom_path = Path("/var/data/news.db")
    cfg = EconomicNewsEvidenceConfig(
        database_path=custom_path,
        max_query_results=500,
        default_rate_limit_per_minute=30,
        max_payload_size_bytes=1_000_000,
        default_freshness_limit_seconds=3_600,
        allowed_sources=frozenset({"CUSTOM_SRC"}),
    )
    assert cfg.database_path == custom_path
    assert cfg.max_query_results == 500
    assert cfg.default_rate_limit_per_minute == 30
    assert cfg.max_payload_size_bytes == 1_000_000
    assert cfg.default_freshness_limit_seconds == 3_600
    assert cfg.allowed_sources == frozenset({"CUSTOM_SRC"})
