"""Unit tests for Diagnostic Bundle configuration."""

from app.services.workspace.diagnostic_bundle.config import (
    DiagnosticBundleConfig,
)


def test_diagnostic_bundle_config_defaults() -> None:
    """Verify default values of DiagnosticBundleConfig."""
    cfg = DiagnosticBundleConfig()
    assert cfg.max_log_records == 1000
    assert cfg.max_bundle_size_bytes == 50 * 1024 * 1024
    assert cfg.redact_patterns is True


def test_diagnostic_bundle_config_custom() -> None:
    """Verify custom parameters of DiagnosticBundleConfig."""
    cfg = DiagnosticBundleConfig(
        max_log_records=500,
        max_bundle_size_bytes=10 * 1024 * 1024,
        redact_patterns=False,
    )
    assert cfg.max_log_records == 500
    assert cfg.max_bundle_size_bytes == 10 * 1024 * 1024
    assert cfg.redact_patterns is False
