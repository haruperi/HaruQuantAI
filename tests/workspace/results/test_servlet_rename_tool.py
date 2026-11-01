"""Unit tests for ServletRenameTool."""

from __future__ import annotations

import pytest
from app.core.lib.errors import DomainError
from app.workspace.results.servlet_rename_tool import (
    RenamePatternSpec,
    ServletRenameTool,
)


class TestServletRenameTool:
    """Test suite for ServletRenameTool."""

    def test_golden_fixture_collision_resolution(self) -> None:
        """Verify collision avoidance when formatted name matches existing name."""
        spec = RenamePatternSpec(
            prefix="Strategy ", start_number=1, digits=2, separator=""
        )
        existing = {"Strategy 01"}
        pairs = ServletRenameTool.format_names(
            ["s1", "s2"], spec, existing_names=existing
        )
        assert pairs == (("s1", "Strategy 02"), ("s2", "Strategy 03"))

    def test_rename_spec_validation(self) -> None:
        """Verify DomainError on invalid rename parameters."""
        with pytest.raises(DomainError) as exc_info:
            ServletRenameTool.format_names(["s1"], RenamePatternSpec(start_number=-1))
        assert exc_info.value.code == "RESULTS_INVALID_RENAME_SPEC"

        with pytest.raises(DomainError) as exc_info:
            ServletRenameTool.format_names(["s1"], RenamePatternSpec(digits=0))
        assert exc_info.value.code == "RESULTS_INVALID_RENAME_SPEC"

        with pytest.raises(DomainError) as exc_info:
            ServletRenameTool.format_names(["s1"], RenamePatternSpec(prefix="   "))
        assert exc_info.value.code == "RESULTS_INVALID_RENAME_SPEC"

    def test_to_dict_serialization(self) -> None:
        """Verify RenamePatternSpec dictionary serialization."""
        spec = RenamePatternSpec(prefix="MyStrat_", digits=3)
        d = spec.to_dict()
        assert d["prefix"] == "MyStrat_"
        assert d["digits"] == 3
