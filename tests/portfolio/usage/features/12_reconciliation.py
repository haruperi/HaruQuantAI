"""Run FEAT-PORT-12 reconciliation usage."""

import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.portfolio import build_lifecycle_postings, reconcile_portfolio


def main() -> None:
    """Exercise reconciliation and lifecycle postings."""
    print(
        reconcile_portfolio(
            {"cash": Decimal(10)},
            {"cash": Decimal(10)},
            tolerance=Decimal("0.01"),
            incident_id="inc_demo",
        )
    )
    print(build_lifecycle_postings("event_demo", "dividend", Decimal(2), "USD"))


if __name__ == "__main__":
    main()
