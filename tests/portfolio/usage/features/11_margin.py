"""Run FEAT-PORT-11 margin usage."""

import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.portfolio import build_portfolio_risk_health, calculate_margin_view


def main() -> None:
    """Exercise margin and risk-health providers."""
    print(
        calculate_margin_view(
            equity=Decimal(100),
            margin_used=Decimal(20),
            reserved=Decimal(5),
            maintenance=Decimal(10),
            policy_version="v1",
        )
    )
    print(
        build_portfolio_risk_health(
            (Decimal(-2), Decimal(1)),
            confidence=Decimal("0.95"),
            model="historical",
            window=2,
            stress_losses={"shock": Decimal(-8)},
            high_water_mark=Decimal(105),
        )
    )


if __name__ == "__main__":
    main()
