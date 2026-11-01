"""Unit tests for overview template selection policy."""

from __future__ import annotations

import pytest
from app.workspace.results.overview_template_policy import OverviewTemplatePolicy


class TestOverviewTemplatePolicy:
    """Test suite for OverviewTemplatePolicy."""

    @pytest.mark.parametrize(
        ("candidates", "expected"),
        [
            ((), "SQDefault"),
            (("A", "SQDefault"), "SQDefault"),
            (("A", "B"), "A"),
            (("sqdefault",), "sqdefault"),
        ],
    )
    def test_selection(self, candidates: tuple[str, ...], expected: str) -> None:
        """Verify template selection matches donor precedence rules."""
        result = OverviewTemplatePolicy.select(candidates)
        assert result == expected

    def test_type_error(self) -> None:
        """Verify TypeError raised when argument is not a tuple of strings."""
        with pytest.raises(TypeError, match="values must be a tuple of strings"):
            OverviewTemplatePolicy.select(["SQDefault"])  # type: ignore[arg-type]

        with pytest.raises(TypeError, match="values must be a tuple of strings"):
            OverviewTemplatePolicy.select((None,))  # type: ignore[arg-type]

        valid_input = ("CustomA", "CustomB")
        result = OverviewTemplatePolicy.select(valid_input)
        assert result == "CustomA"
        assert valid_input == ("CustomA", "CustomB")
