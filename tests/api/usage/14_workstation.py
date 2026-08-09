"""Run FEAT-API-14 workstation API usage."""

import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.api import build_workstation_read_model, execute_workstation_command


def main() -> None:
    """Exercise workstation read and command operations."""
    print(
        build_workstation_read_model(
            version=1, as_of=datetime.now(UTC), panels={}, freshness={}
        )
    )
    print(
        execute_workstation_command(
            {
                "expected_version": 1,
                "idempotency_key": "demo",
                "correlation_id": "cor_demo",
            },
            current_version=1,
            owner_handler=lambda _: {"owner": "accepted"},
        )
    )


if __name__ == "__main__":
    main()
