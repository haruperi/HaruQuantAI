"""Research feature computation, pipelines, and leakage guardrails.

Purpose:
    Research feature computation, pipelines, and leakage guardrails.

Classes:
    None.

Functions:
    None.
"""

from . import calculations as _calculations
from .calculations import *
from .leakage import (
    TimeSplitResult,
    dump_masked_research_json,
    enforce_time_split,
    mask_research_artifact,
    validate_no_lookahead_features,
)
from .pipeline import FeaturePipeline, FeatureSpec

__all__ = [
    *[
        name
        for name, value in vars(_calculations).items()
        if not name.startswith("_")
        and getattr(value, "__module__", None) == _calculations.__name__
    ],
    "FeaturePipeline",
    "FeatureSpec",
    "TimeSplitResult",
    "dump_masked_research_json",
    "enforce_time_split",
    "mask_research_artifact",
    "validate_no_lookahead_features",
]
