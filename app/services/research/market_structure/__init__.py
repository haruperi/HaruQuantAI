"""Public Research market-structure API."""

from app.services.research.market_structure.calibration import (
    calibrate_market_structure,
)
from app.services.research.market_structure.fit import build_strategy_fit
from app.services.research.market_structure.profile import (
    build_market_structure_profile,
)
from app.services.research.market_structure.quality import (
    evaluate_market_structure_quality,
)
from app.services.research.market_structure.validation import (
    build_validation_summary,
    label_realized_market_behavior,
)

__all__ = (
    "build_market_structure_profile",
    "build_strategy_fit",
    "build_validation_summary",
    "calibrate_market_structure",
    "evaluate_market_structure_quality",
    "label_realized_market_behavior",
)
