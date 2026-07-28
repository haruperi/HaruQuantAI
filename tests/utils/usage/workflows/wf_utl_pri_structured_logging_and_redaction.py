"""WF-UTL-PRI: execute structured logging and redaction end to end."""

from __future__ import annotations

import json
import logging
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.utils import (
    configure_logging,
    flush_logging,
    get_logger,
    load_settings,
    redact_mapping_value,
    shutdown_logging,
)

logger = get_logger(__name__)

WORKFLOW_ID = "WF-UTL-PRI"
STAGES = (
    "Import the global import-safe bound logger without side effects.",
    "Supply structured, JSON-safe context.",
    "Redact before formatting or emission.",
    "Activate an explicit specialized logging profile.",
    "Flush and stop queued delivery deterministically.",
    "Verify the configured sink without exposing the source payload.",
)


def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(
        f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}"
    )


def main() -> None:
    """Run the documented logging workflow from input to sink evidence."""
    print(f"{WORKFLOW_ID} — Structured Logging and Redaction")
    print("INPUT BOUNDARY — domain log record and explicit context")

    # Stage 1 — Import the global import-safe bound logger without side effects.
    _stage(1)
    named_logger = get_logger("workflow.utils")
    assert named_logger.name.endswith("workflow.utils")
    print("Utils-owned handlers before configuration:", len(named_logger.handlers))

    # Stage 2 — Supply structured, JSON-safe context.
    _stage(2)
    context = {
        "request_id": "req-workflow-example",
        "account_id": "demo-account",
        "api_token": "synthetic-secret",
    }
    print("Context keys:", tuple(context))

    # Stage 3 — Redact before formatting or emission.
    _stage(3)
    redacted = redact_mapping_value(context)
    assert isinstance(redacted.value, dict)
    assert redacted.value["api_token"] == "[REDACTED]"
    print("Redacted paths:", redacted.redacted_paths)

    with tempfile.TemporaryDirectory(prefix="wf-utl-001-") as directory:
        log_directory = Path(directory)
        try:
            # Stage 4 — Activate an explicit specialized logging profile.
            _stage(4)
            configure_logging(
                load_settings().logging.model_copy(
                    update={"log_directory": log_directory, "render": "json"}
                )
            )
            logger.info(
                "workflow record token=synthetic-secret",
                extra=dict(redacted.value),
            )
            logger.info("access workflow record", extra={"log_type": "access"})
            logger.debug("debug workflow record")
            logger.error("error workflow record")
            print("Structured records submitted to configured routes")

            # Stage 5 — Flush and stop queued delivery deterministically.
            _stage(5)
            flush_logging()
            shutdown_logging()
            print("Logging queue flushed and stopped")

            # Stage 6 — Verify the configured sink without exposing the source payload.
            _stage(6)
            records = [
                json.loads(line)
                for line in (log_directory / "app.log")
                .read_text(encoding="utf-8")
                .splitlines()
            ]
            rendered = repr(records)
            assert "synthetic-secret" not in rendered
            assert "[REDACTED]" in rendered
            routes = tuple(
                path.name
                for path in sorted(log_directory.glob("*.log"))
                if path.stat().st_size
            )
            print("Verified non-empty sinks:", routes)
        finally:
            shutdown_logging()
            logging.shutdown()

    print("OUTPUT BOUNDARY — redacted structured record reached configured sinks")


if __name__ == "__main__":
    main()
