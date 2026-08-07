"""Integration evidence for the newest Analytics supporting workflows."""

from tests.analytics.usage.workflows import (
    wf_anlt_015_equity_curve_worst_day_distribution as workflow_015,
)
from tests.analytics.usage.workflows import (
    wf_anlt_016_validate_contract_and_metric_catalogue as workflow_016,
)
from tests.analytics.usage.workflows import (
    wf_anlt_017_emit_error_payload_quality_flags as workflow_017,
)


def test_workflow_015_executes_observed_distribution(capsys) -> None:
    """Build equity and worst-day evidence from observed trade facts."""
    workflow_015.main()
    output = capsys.readouterr().out
    assert "Worst-day distribution:" in output
    assert "Barrier analysis:" in output


def test_workflow_016_validates_contract_and_catalogue(capsys) -> None:
    """Validate registered compatibility and metric catalogue evidence."""
    workflow_016.main()
    output = capsys.readouterr().out
    assert "Contract result:" in output
    assert "Catalogue validation:" in output


def test_workflow_017_emits_bounded_failure_evidence(capsys) -> None:
    """Emit bounded quality and redacted error evidence."""
    workflow_017.main()
    output = capsys.readouterr().out
    assert "Error payload:" in output
    assert "ANALYTICS_EXECUTION_FAILED" in output
