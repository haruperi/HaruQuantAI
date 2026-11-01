"""Deterministic strategy rename formatter and collision resolution tool.

Description:
    Implements ServletRenameTool formatting sequential strategy display
    names according to prefix, suffix, digits, and separator specifications,
    while skipping collisions against existing or previously assigned names.

Purpose:
    FEAT-RESULTS-RENAME-TOOL: Deterministic strategy rename formatting.

Key Capabilities:
    - FR-results-rename-tool-format: Generate formatted names without collisions.

Python API Usage:
    from app.workspace.results.servlet_rename_tool import (
        RenamePatternSpec,
        ServletRenameTool,
    )
    spec = RenamePatternSpec(prefix="Strat_", digits=2)
    pairs = ServletRenameTool.format_names(["s1", "s2"], spec)

CLI Usage:
    python -m app.cli results rename-tool --prefix "Strat_" --digits 2
"""

from __future__ import annotations

from collections.abc import Sequence
from collections.abc import Set as AbstractSet
from dataclasses import dataclass
from typing import Any

from app.core.host.logging import get_logger
from app.core.lib.errors import DomainError

logger = get_logger(__name__)

MIN_DIGITS = 1
MAX_DIGITS = 10


@dataclass(frozen=True, slots=True)
class RenamePatternSpec:
    """Strategy renaming pattern specification."""

    prefix: str = "Strategy "
    start_number: int = 1
    digits: int = 1
    suffix: str = ""
    separator: str = "."

    def to_dict(self) -> dict[str, Any]:
        """Convert specification to dictionary."""
        return {
            "prefix": self.prefix,
            "start_number": self.start_number,
            "digits": self.digits,
            "suffix": self.suffix,
            "separator": self.separator,
        }


class ServletRenameTool:
    """Deterministic batch rename tool resolving name collisions."""

    @classmethod
    def format_names(
        cls,
        strategy_ids: Sequence[str],
        spec: RenamePatternSpec,
        *,
        existing_names: AbstractSet[str] = frozenset(),
    ) -> tuple[tuple[str, str], ...]:
        """Format sequential unique names for strategy IDs avoiding collisions."""
        logger.info(
            "FR-results-rename-tool-format: formatting %d strategies with prefix '%s'",
            len(strategy_ids),
            spec.prefix,
        )
        if spec.start_number < 0:
            raise DomainError(
                code="RESULTS_INVALID_RENAME_SPEC",
                message=f"Start number must be non-negative, got {spec.start_number}",
                details={"start_number": spec.start_number},
            )
        if spec.digits < MIN_DIGITS or spec.digits > MAX_DIGITS:
            raise DomainError(
                code="RESULTS_INVALID_RENAME_SPEC",
                message=(
                    f"Digits must be between {MIN_DIGITS} and {MAX_DIGITS}, "
                    f"got {spec.digits}"
                ),
                details={"digits": spec.digits},
            )
        if not spec.prefix.strip():
            raise DomainError(
                code="RESULTS_INVALID_RENAME_SPEC",
                message="Prefix cannot be empty or whitespace only",
                details={"prefix": spec.prefix},
            )

        used_names = set(existing_names)
        results: list[tuple[str, str]] = []
        counter = spec.start_number

        for sid in strategy_ids:
            while True:
                num_str = f"{counter:0{spec.digits}d}"
                candidate = f"{spec.prefix}{spec.separator}{num_str}{spec.suffix}"
                counter += 1
                if candidate not in used_names:
                    used_names.add(candidate)
                    results.append((sid, candidate))
                    break

        return tuple(results)
