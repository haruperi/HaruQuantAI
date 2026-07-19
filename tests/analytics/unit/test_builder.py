"""Unit tests for canonical Analytics report orchestration."""

# ruff: noqa: INP001

from decimal import Decimal

import pytest
from app.services.analytics.contracts import AnalyticsValidationError, SectionEvidence
from app.services.analytics.reports import builder
from app.utils import derive_stable_id, logger
from tests.analytics.usage.test_usage_reports import _configured, _source_with_profit


def test_builder_fails_closed_on_required_section(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A failed required report section produces no official report."""
    logger.debug("Testing Analytics required-section failure")

    def failed_sections(
        *_args: object, **_kwargs: object
    ) -> tuple[SectionEvidence, ...]:
        """Return one controlled required-section failure.

        Returns:
            Failed required section evidence.
        """
        logger.debug("Returning failed Analytics section test evidence")
        return (
            SectionEvidence(
                section_key="trades",
                criticality="required",
                metrics=(),
                status="failed",
                reason="controlled failure",
            ),
        )

    monkeypatch.setattr(builder, "calculate_grouped_evidence", failed_sections)
    with pytest.raises(AnalyticsValidationError, match="required"):
        builder.build_performance_report(
            _source_with_profit(Decimal(10)),
            source_contract="simulation.result",
            request_id=derive_stable_id("req", "analytics-builder-failure"),
            initial_balance=Decimal(1000),
            account_currency="USD",
            config=_configured(),
        )
