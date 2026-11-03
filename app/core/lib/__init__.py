"""Core library utilities."""

from __future__ import annotations

from app.core.lib.errors import DomainError, JSONValue, SQException, copy_json
from app.core.lib.programs import (
    Program,
    ProgramRegistry,
    default_program_registry,
    get,
    is_registered,
    register,
)
from app.core.lib.random import IRandomGenerator, MersenneTwisterRng, RandomGenerator
from app.core.lib.responses import (
    ErrorCode,
    ResponseMetadata,
    StandardError,
    StandardResponse,
    build_typed_response,
)
from app.core.lib.time import (
    DAY_MILLIS,
    HOUR_MILLIS,
    MINUTE_MILLIS,
    SECOND_MILLIS,
    TimePeriod,
    format_duration_seconds,
)

__all__ = [
    "DAY_MILLIS",
    "HOUR_MILLIS",
    "MINUTE_MILLIS",
    "SECOND_MILLIS",
    "DomainError",
    "ErrorCode",
    "IRandomGenerator",
    "JSONValue",
    "MersenneTwisterRng",
    "Program",
    "ProgramRegistry",
    "RandomGenerator",
    "ResponseMetadata",
    "SQException",
    "StandardError",
    "StandardResponse",
    "TimePeriod",
    "build_typed_response",
    "copy_json",
    "default_program_registry",
    "format_duration_seconds",
    "get",
    "is_registered",
    "register",
]
