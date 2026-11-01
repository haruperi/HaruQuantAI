"""Portfolio Composer risk calculations.

Description:
    Computes parametric expected shortfall (Conditional Value at Risk / CVaR)
    under a Gaussian normal distribution.
Purpose:
    FEAT-PORTFOLIO-COMPOSER: Configure composition and evaluation.
Key Capabilities:
    - FR-composer-risk: Calculate parametric expected shortfall (CVaR).
Python API Usage:
    from app.workspace.portfolio_composer.risk import ComposerRisk
    es = ComposerRisk.expected_shortfall(
        mean=0.0, standard_deviation=1.0, confidence=0.5
    )
CLI Usage:
    uv run python -m pytest tests/workspace/portfolio_composer
"""

from __future__ import annotations

import math
from statistics import NormalDist

from app.core.host.logging import get_logger

logger = get_logger(__name__)


class ComposerRisk:
    """Parametric risk computation helper for Portfolio Composer."""

    @staticmethod
    def expected_shortfall(
        *,
        mean: float,
        standard_deviation: float,
        confidence: float,
    ) -> float:
        """Compute parametric expected shortfall (CVaR) using standard normal.

        Args:
            mean: Portfolio or strategy return mean (finite float).
            standard_deviation: Return standard deviation (finite float).
            confidence: Confidence level in the open interval (0.0, 1.0).

        Returns:
            Expected shortfall scalar preserving input units.

        Raises:
            ValueError: If input is not a finite float, or confidence out of bounds.
        """
        for _name, value in (
            ("mean", mean),
            ("standard_deviation", standard_deviation),
            ("confidence", confidence),
        ):
            if type(value) is not float or not math.isfinite(value):
                raise ValueError("risk inputs must be finite floats")

        if not (0.0 < confidence < 1.0):
            raise ValueError("confidence must be between 0 and 1")

        logger.info(
            "FR-composer-risk: computing expected shortfall mean=%f std=%f conf=%f",
            mean,
            standard_deviation,
            confidence,
        )

        dist = NormalDist()
        z = dist.inv_cdf(confidence)
        return mean - standard_deviation * dist.pdf(z) / (1.0 - confidence)
