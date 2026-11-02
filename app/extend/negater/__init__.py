"""Strategy rule and AST node negaters package conforming to SQ.Negater snippets.

Description:
    Provides all 15 StrategyQuant negaters for directional strategy symmetry,
    including the base Negater and NegatersList pipeline, individual modular
    negater classes, and the BlockNegaterRegistry dispatcher.

Purpose:
    FEAT-NEGATER: Complete donor parity for StrategyQuant negaters.

Key Capabilities:
    - FR-NEGATER-EXPORTS: Canonical package exports for all negaters.

Python API Usage:
    from app.extend.negater import (
        BlockNegaterRegistry,
        Negater,
        NegatersList,
        OscillatorComparisonsNegater,
    )

CLI Usage:
    uv run pytest tests/extend/test_negater.py --no-cov
"""

from __future__ import annotations

from app.extend.negater.actions_negater import ActionsNegater
from app.extend.negater.and_or_negater import AndOrNegater
from app.extend.negater.base import Negater, NegatersList
from app.extend.negater.c_block_negater import CBlockNegater
from app.extend.negater.c_data_indy_negater import CDataIndyNegater
from app.extend.negater.catalog import BlockNegaterRegistry
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
