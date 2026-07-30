"""Strategy diagnostics model tests."""

from app.services.strategy.diagnostics.models import StrategyDiagnostics
from app.utils import get_logger

from tests.strategy.unit.test_models import COR, HASH, NOW, REQ, WF

logger = get_logger(__name__)


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
