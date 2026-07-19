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


def _failed_required_sections(
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


def test_builder_emits_blocker_flags_in_diagnostic_partial_mode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A diagnostic partial report always carries cataloged blocker evidence."""
    logger.debug("Testing Analytics diagnostic partial blocker evidence")
    monkeypatch.setattr(
        builder, "calculate_grouped_evidence", _failed_required_sections
    )
    report = builder.build_performance_report(
        _source_with_profit(Decimal(10)),
        source_contract="simulation.result",
        request_id=derive_stable_id("req", "analytics-builder-partial"),
        initial_balance=Decimal(1000),
        account_currency="USD",
        config=_configured(),
        diagnostic_partial_mode=True,
    )
    codes = [flag.code for flag in report.quality_flags]
    assert codes.count("diagnostic_partial_report") == 1
    assert codes.count("required_section_failed") == 1
    partial = next(
        flag
        for flag in report.quality_flags
        if flag.code == "diagnostic_partial_report"
    )
    failed = next(
        flag for flag in report.quality_flags if flag.code == "required_section_failed"
    )
    assert partial.blocker is True
    assert failed.blocker is True
    assert failed.detail["section"] == "trades"
    assert failed.detail["reason"] == "controlled failure"
    assert tuple(partial.detail["failed_sections"]) == ("trades",)


def test_builder_clean_report_carries_no_blocker_flag() -> None:
    """A complete measurement emits no blocker quality flag."""
    logger.debug("Testing Analytics clean-report quality flags")
    report = builder.build_performance_report(
        _source_with_profit(Decimal(10)),
        source_contract="simulation.result",
        request_id=derive_stable_id("req", "analytics-builder-clean"),
        initial_balance=Decimal(1000),
        account_currency="USD",
        config=_configured(),
    )
    codes = {flag.code for flag in report.quality_flags}
    assert not any(flag.blocker for flag in report.quality_flags)
    assert "diagnostic_partial_report" not in codes
    assert "required_section_failed" not in codes
    assert "intratrade_exposure_unobserved" in codes


def test_builder_emits_sample_below_threshold_under_thirty_trades() -> None:
    """A ledger below the cataloged statistical minimum is flagged."""
    logger.debug("Testing Analytics sample-threshold quality flag")
    report = builder.build_performance_report(
        _source_with_profit(Decimal(10)),
        source_contract="simulation.result",
        request_id=derive_stable_id("req", "analytics-builder-samples"),
        initial_balance=Decimal(1000),
        account_currency="USD",
        config=_configured(),
    )
    flag = next(
        item for item in report.quality_flags if item.code == "sample_below_threshold"
    )
    assert flag.blocker is False
    assert flag.detail["required_count"] == 30
