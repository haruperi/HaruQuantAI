"""Strategy diagnostics model tests."""

from app.services.strategy.diagnostics import StrategyDiagnostics
from app.utils import logger

from tests.strategy.unit.test_models import COR, HASH, NOW, REQ, WF


def test_diagnostics_require_trace_and_redaction_status() -> None:
    """Verify typed diagnostics retain trace and redaction evidence."""
    logger.debug("Testing Strategy diagnostics evidence")
    value = StrategyDiagnostics(
        status="READY",
        strategy_id="s",
        strategy_version="1",
        config_hash=HASH,
        data_checksum=HASH,
        request_id=REQ,
        workflow_id=WF,
        correlation_id=COR,
        decision_timestamp=NOW,
        error_code=None,
        safe_details={},
        dependency_health={},
        metrics={},
        redacted_paths=("token",),
        truncated_paths=(),
        payload_bytes=10,
    )
    assert value.redacted_paths == ("token",)
