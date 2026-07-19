"""Runnable usage example for focused deterministic Risk reports."""

from app.services.risk.reporting import generate_risk_report

from tests.risk.usage import test_usage_policy as examples


def test_usage_reports_generate() -> None:
    """Render an immutable snapshot into separated Markdown report sections."""
    config = examples._config()
    report = generate_risk_report(
        examples._snapshot(config), "markdown", config, now=examples.NOW
    )
    assert report.format == "markdown"
    assert report.approval_claimed is False
    assert report.evidence[0] == "snapshot=snapshot-1"
