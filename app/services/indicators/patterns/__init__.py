"""Approved pattern-indicator implementation namespace.

The feature owns all candle and chart-pattern calculations. See
``patterns/_shared.py`` for the documented four-state simplification of the
specification's pattern-state model.
"""

from app.services.indicators.patterns.breakout_retest import breakout_retest
from app.services.indicators.patterns.doji import doji
from app.services.indicators.patterns.double_top_bottom import double_top_bottom
from app.services.indicators.patterns.engulfing import engulfing
from app.services.indicators.patterns.evidence import build_chart_pattern_evidence
from app.services.indicators.patterns.flag_pennant import flag_pennant
from app.services.indicators.patterns.head_and_shoulders import head_and_shoulders
from app.services.indicators.patterns.inside_bar import inside_bar
from app.services.indicators.patterns.pinbar import pinbar
from app.services.indicators.patterns.rectangle import rectangle
from app.services.indicators.patterns.three_bar_reversal import three_bar_reversal
from app.services.indicators.patterns.triangle import triangle
from app.services.indicators.patterns.wedge import wedge

__all__ = [
    "breakout_retest",
    "build_chart_pattern_evidence",
    "doji",
    "double_top_bottom",
    "engulfing",
    "flag_pennant",
    "head_and_shoulders",
    "inside_bar",
    "pinbar",
    "rectangle",
    "three_bar_reversal",
    "triangle",
    "wedge",
]
