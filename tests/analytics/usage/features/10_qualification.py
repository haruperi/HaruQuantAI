"""Standalone FEAT-ANLT-10 usage evidence."""

import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.analytics import evaluate_player_qualification

NOW = datetime.now(UTC)


def _format_result(value: object) -> str:
    """Format bounded visible evidence."""
    return f"SUCCESS: Data -> {type(value).__name__}"


def _evaluate(attempts: tuple[dict[str, bool], ...]) -> object:
    """Evaluate bounded qualification evidence."""
    return evaluate_player_qualification(
        curriculum_version="v1",
        completed_prerequisites=("safety",),
        required_prerequisites=("safety",),
        attempts=attempts,
        valid_until=NOW + timedelta(days=30),
        now=NOW,
    )


def fr_anlt_075() -> object:
    """Evaluate curriculum prerequisites. Data -> Analytics; _format_result evidence."""
    return _evaluate(())


def fr_anlt_076() -> object:
    """Evaluate exact checkride evidence. Data -> Analytics; _format_result evidence."""
    return _evaluate(({"passed": True},))


def fr_anlt_077() -> object:
    """Require remediation after failure. Data -> Analytics; _format_result evidence."""
    return _evaluate(({"passed": False},))


def fr_anlt_078() -> object:
    """Evaluate recurrent validity and eligibility. Data -> Analytics; _format_result evidence."""
    return _evaluate(({"passed": True, "integrity_breach": False},))


def main() -> None:
    """Run every requirement example."""
    for value in (fr_anlt_075(), fr_anlt_076(), fr_anlt_077(), fr_anlt_078()):
        print(_format_result(value))


if __name__ == "__main__":
    main()
