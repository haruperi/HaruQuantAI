"""Strategy rule and AST block negaters catalog (15 definitions).

Description:
    Implements the 15 StrategyQuant negater snippets used to transform Long rules
    into symmetric Short rules (and vice versa) during symmetric strategy generation.
    Handles action direction inversion, boolean tree recursion, comparison reversal,
    oscillator midpoint reflection, band swapping, and Fibonacci/Pivot level inversion.
    Coordinates all negater components via BlockNegaterRegistry and NegatersList.

Purpose:
    FEAT-NEGATER-CATALOG: Deterministic AST opposite-direction transformation.

Key Capabilities:
    - FR-NEGATER-CATALOG-DISPATCH: Dispatcher for all 15 negater implementations.
    - FR-NEGATER-CATALOG-EXPORTS: Canonical re-exports of all 15 negater classes.

Python API Usage:
    from app.extend.negater.catalog import BlockNegaterRegistry
    short_rule = BlockNegaterRegistry.negate_node("ActionsNegater", long_rule)

CLI Usage:
    uv run pytest tests/extend/test_negater.py --no-cov
"""

from __future__ import annotations

from typing import Any, ClassVar

from app.core.host.logging import get_logger
from app.extend.negater.actions_negater import ActionsNegater
from app.extend.negater.and_or_negater import AndOrNegater
from app.extend.negater.base import Negater, NegatersList
from app.extend.negater.c_block_negater import CBlockNegater
from app.extend.negater.c_data_indy_negater import CDataIndyNegater
from app.extend.negater.comparisons_negater import ComparisonsNegater
from app.extend.negater.conditions_negater import ConditionsNegater
from app.extend.negater.default_negater import DefaultNegater
from app.extend.negater.fibo_negater import FiboNegater
from app.extend.negater.formula_negater import FormulaNegater
from app.extend.negater.fractal_negater import FractalNegater
from app.extend.negater.functions_negater import FunctionsNegater
from app.extend.negater.oscillator_comparisons_negater import (
    OscillatorComparisonsNegater,
)
from app.extend.negater.pivots_negater import PivotsNegater
from app.extend.negater.ulcer_negater import UlcerNegater
from app.extend.negater.upper_lower_negater import UpperLowerNegater

logger = get_logger(__name__)


class BlockNegaterRegistry:
    """Registry coordinating all 15 StrategyQuant negaters."""

    NEGATERS: ClassVar[dict[str, type[Negater]]] = {
        "ActionsNegater": ActionsNegater,
        "AndOrNegater": AndOrNegater,
        "ComparisonsNegater": ComparisonsNegater,
        "OscillatorComparisonsNegater": OscillatorComparisonsNegater,
        "CDataIndyNegater": CDataIndyNegater,
        "ConditionsNegater": ConditionsNegater,
        "UpperLowerNegater": UpperLowerNegater,
        "FiboNegater": FiboNegater,
        "FractalNegater": FractalNegater,
        "PivotsNegater": PivotsNegater,
        "UlcerNegater": UlcerNegater,
        "FormulaNegater": FormulaNegater,
        "FunctionsNegater": FunctionsNegater,
        "CBlockNegater": CBlockNegater,
        "DefaultNegater": DefaultNegater,
    }

    @classmethod
    def list_negaters(cls) -> tuple[str, ...]:
        """List all 15 registered negater identifiers."""
        return tuple(cls.NEGATERS.keys())

    @classmethod
    def build_pipeline(cls) -> NegatersList:
        """Construct a NegatersList with all 15 negaters ordered by priority."""
        return NegatersList(list(cls.NEGATERS.values()))

    @classmethod
    def negate_node(cls, negater_id: str, node: Any, strategy: Any = None) -> Any:
        """Negate an AST node or rule using the designated negater.

        Args:
            negater_id: Name of the negater class.
            node: Node or rule representation (str, dict, or object).
            strategy: Optional StrategyBase context.

        Returns:
            Negated node or rule.

        Raises:
            ValueError: If negater_id is unrecognized.
        """
        negater = cls.NEGATERS.get(negater_id)
        if negater is None:
            raise ValueError(f"Unknown negater: {negater_id}")
        logger.debug(
            "FR-NEGATER-CATALOG-DISPATCH: applying negater '%s' to node", negater_id
        )
        return negater.negate(node, strategy=strategy)


__all__ = [
    "ActionsNegater",
    "AndOrNegater",
    "BlockNegaterRegistry",
    "CBlockNegater",
    "CDataIndyNegater",
    "ComparisonsNegater",
    "ConditionsNegater",
    "DefaultNegater",
    "FiboNegater",
    "FormulaNegater",
    "FractalNegater",
    "FunctionsNegater",
    "Negater",
    "NegatersList",
    "OscillatorComparisonsNegater",
    "PivotsNegater",
    "UlcerNegater",
    "UpperLowerNegater",
]
