"""Standalone usage evidence for FEAT-UTIL-11."""

from datetime import UTC, datetime

from app.utils import build_validation_outcome, combine_validation_outcomes


def main() -> None:
    """Run validation construction and strictest-wins combination."""
    instant = datetime(2026, 1, 1, tzinfo=UTC)
    outcome = build_validation_outcome(
        verdict="UNKNOWN",
        check_id="feed",
        evaluated_at=instant,
        reason_codes=["FEED.UNKNOWN"],
        severity="ERROR",
    )
    result = combine_validation_outcomes([outcome])
    print("SUCCESS: FEAT-UTIL-11 validation completed")
    print(f"Data -> validation={result}")


if __name__ == "__main__":
    main()
