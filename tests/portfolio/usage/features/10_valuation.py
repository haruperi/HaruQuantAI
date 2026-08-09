"""Run FEAT-PORT-10 valuation usage."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.portfolio import calculate_portfolio_valuation


def main() -> None:
    """Exercise valuation."""
    print(
        calculate_portfolio_valuation(
            (
                {
                    "position_id": "p",
                    "side": "long",
                    "mark": "12",
                    "lots": (("2", "10"),),
                },
            ),
            policy_version="v1",
            policy={"long_source": "mark"},
            lot_method="fifo",
            fx_evidence={"status": "current", "evidence_id": "fx_demo"},
        )
    )


if __name__ == "__main__":
    main()
