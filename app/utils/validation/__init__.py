"""Function-only exports for validation outcomes."""

from app.utils.validation.outcomes import (
    build_validation_outcome,
    combine_validation_outcomes,
    parse_validation_outcome,
)
from app.utils.validation.reasons import get_severity_rank, validate_reason_code

__all__ = [
    "build_validation_outcome",
    "combine_validation_outcomes",
    "get_severity_rank",
    "parse_validation_outcome",
    "validate_reason_code",
]
