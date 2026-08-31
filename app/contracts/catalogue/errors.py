"""Catalogue domain structured failure envelope."""

from typing import Literal

from app.contracts.common.models import ProblemDetails, Uuid7, WireModel

# Closed catalogue failure-code union from the ratified v1 operation rules.
type CatalogueFailureCode = Literal[
    "CATALOGUE_VALIDATION_FAILED",
    "CATALOGUE_NOT_FOUND",
    "CATALOGUE_VERSION_CONFLICT",
    "CATALOGUE_REFERENCE_PROTECTED",
    "CATALOGUE_MAPPING_OVERLAP",
    "CATALOGUE_SESSION_INVALID",
    "CATALOGUE_RULE_UNSUPPORTED",
    "CATALOGUE_UNIVERSE_INVALID",
    "CATALOGUE_FX_PATH_UNAVAILABLE",
    "CATALOGUE_EXCHANGE_INCOMPATIBLE",
    "CAPABILITY_UNAVAILABLE",
]


class CatalogueFailure(WireModel):
    """Structured failure envelope for every catalogue capability."""

    request_id: Uuid7
    code: CatalogueFailureCode
    problem: ProblemDetails
    conflicting_refs: tuple[Uuid7, ...] = ()
    outcome: Literal["FAILURE"] = "FAILURE"
    schema_version: Literal[1] = 1


WIRE_FAILURES: dict[str, type[WireModel]] = {
    "CatalogueFailure": CatalogueFailure,
}
