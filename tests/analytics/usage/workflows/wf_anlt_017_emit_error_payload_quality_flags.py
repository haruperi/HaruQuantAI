"""WF-ANLT-017: show bounded Analytics failure and quality evidence."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from app.services.analytics import (
    build_quality_flag,
    build_warning,
    to_analytics_error_payload,
)
from tests.analytics.usage.workflows._support import examples

WORKFLOW_ID = "WF-ANLT-017"
STAGES = ("Create a bounded quality flag.", "Emit a redacted error payload.")


def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(f"{'=' * 88}\nStage {number}/{len(STAGES)}\n{'=' * 88}")


def main() -> None:
    """Execute bounded evidence and error-payload operations."""
    # Stage 1: INPUT BOUNDARY -- bounded observed degradation detail.
    _stage(1)
    print(
        "Quality flag:",
        examples.unwrap(
            build_quality_flag(
                "sample_below_threshold",
                section="risk",
                source_context="observed",
                detail={"observed_count": 1, "required_count": 30},
                max_detail_bytes=128,
            )
        ),
    )
    print(
        "Warning:",
        examples.unwrap(
            build_warning(
                "insufficient_samples",
                section="risk",
                source_context="observed",
                detail={"observed_count": 1, "required_count": 30},
                max_detail_bytes=128,
            )
        ),
    )
    # Stage 2: OUTPUT BOUNDARY -- redacted public failure evidence.
    _stage(2)
    print(
        "Error payload:",
        examples.unwrap(
            to_analytics_error_payload(
                ValueError("invalid observed sample"), max_detail_bytes=128
            )
        ),
    )


if __name__ == "__main__":
    main()
