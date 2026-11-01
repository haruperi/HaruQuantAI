"""Unit tests for ComposerRisk (PC-003)."""

from __future__ import annotations

import pytest
from app.workspace.portfolio_composer.risk import ComposerRisk


class TestComposerRisk:
    """Test suite for ComposerRisk.expected_shortfall."""

    def test_golden_fixtures(self) -> None:
        """Verify numerical accuracy against golden values."""
        val1 = ComposerRisk.expected_shortfall(
            mean=0.0, standard_deviation=1.0, confidence=0.5
        )
        assert pytest.approx(-0.7978845608028654, abs=1e-14) == val1

        val2 = ComposerRisk.expected_shortfall(
            mean=0.01, standard_deviation=0.02, confidence=0.95
        )
        assert pytest.approx(-0.031254256150148575, abs=1e-12) == val2

        val3 = ComposerRisk.expected_shortfall(
            mean=0.25, standard_deviation=0.0, confidence=0.95
        )
        assert val3 == 0.25

    def test_negative_std_dev_allowed_by_scalar_helper(self) -> None:
        """Verify negative standard deviation is computed without rejection."""
        val = ComposerRisk.expected_shortfall(
            mean=0.0, standard_deviation=-1.0, confidence=0.5
        )
        assert pytest.approx(0.7978845608028654, abs=1e-14) == val

    @pytest.mark.parametrize("invalid_conf", [0.0, 1.0, -0.1, 1.1, -1.0])
    def test_confidence_out_of_bounds_raises(self, invalid_conf: float) -> None:
        """Verify confidence <= 0.0 or >= 1.0 raises exact ValueError."""
        with pytest.raises(ValueError, match=r"^confidence must be between 0 and 1$"):
            ComposerRisk.expected_shortfall(
                mean=0.0, standard_deviation=1.0, confidence=invalid_conf
            )

    @pytest.mark.parametrize(
        ("mean", "std", "conf"),
        [
            (0, 1.0, 0.5),
            (0.0, 1, 0.5),
            (0.0, 1.0, 1),
            (True, 1.0, 0.5),
            (0.0, False, 0.5),
            (float("nan"), 1.0, 0.5),
            (0.0, float("inf"), 0.5),
            (0.0, 1.0, float("-inf")),
        ],
    )
    def test_non_finite_float_inputs_raise(
        self,
        mean: object,
        std: object,
        conf: object,
    ) -> None:
        """Verify non-float or non-finite inputs raise exact ValueError."""
        with pytest.raises(ValueError, match=r"^risk inputs must be finite floats$"):
            ComposerRisk.expected_shortfall(
                mean=mean,  # type: ignore[arg-type]
                standard_deviation=std,  # type: ignore[arg-type]
                confidence=conf,  # type: ignore[arg-type]
            )
