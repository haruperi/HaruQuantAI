"""Configuration dataclass for Diagnostic Bundle."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DiagnosticBundleConfig:
    """Configuration options for diagnostic bundle construction.

    Attributes:
        max_log_records: Maximum number of recent log lines to capture.
        max_bundle_size_bytes: Maximum size of generated bundle in bytes.
        redact_patterns: Whether to apply heuristic secret redaction.
    """

    max_log_records: int = 1000
    max_bundle_size_bytes: int = 50 * 1024 * 1024
    redact_patterns: bool = True
