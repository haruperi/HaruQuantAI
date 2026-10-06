"""Load independent bounded fixtures with explicit observation provenance.

Description:
    Reference tests and qualification consume immutable typed fixture descriptions
    through safe JSON reads. A fixture carries independent input and expected/actual
    donor observations; static body inspection never becomes a runtime execution.
    This module performs no database, provider or donor execution.

Purpose:
    FEAT-HOST-EVIDENCE: Validate reference fixture provenance before comparison.
    Implements DEC-HOST-P00-BOUNDED-FIXTURES and DEC-HOST-P00-RELEASE-GATES.

Key Capabilities:
    - FR-HOST-EVIDENCE-FIXTURE-VALIDATION: Validate identities, outputs and capture.
      Associated: `ReferenceFixture`, `FixtureSet`, `load_fixtures()`
      Logging: DEBUG records validation; INFO records accepted counts; ERROR
      records stable codes for schema, provenance or observation mismatch.
      Private validators emit this FR without input values or physical paths.

Python API Usage:
    ```python
    from pathlib import Path
    from tests.reference.fixtures import load_fixtures

    fixtures = load_fixtures(Path("tests/reference/p00-fixtures.json"))
    case_ids = [case.case_id for case in fixtures.cases]
    ```

CLI Usage:
    ```bash
    uv run python -m tests.reference.validate
    ```
"""

from __future__ import annotations

from logging import getLogger as get_logger  # noqa: N813 - approved adapter name
from pathlib import Path
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    JsonValue,
    ValidationError,
    field_validator,
)

from tests.reference.manifest import fail, logical_locator, read_json, timestamp

logger = get_logger(__name__)
FIXTURE_FR = "FR-HOST-EVIDENCE-FIXTURE-VALIDATION"


class ReferenceFixture(BaseModel):
    """An independent fixture with exact static/runtime provenance and results."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    case_id: str = Field(strict=True, pattern=r"^[a-z][a-z0-9-]+$")
    feature_id: Literal["FEAT-HOST-EVIDENCE"]
    requirement_id: str = Field(pattern=r"^FR-HOST-EVIDENCE-[A-Z-]+$")
    decision_ids: list[str]
    evidence_ids: list[str] = Field(min_length=1)
    artifact: str
    artifact_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    location: str = Field(min_length=1)
    observation_kind: Literal["static", "runtime"]
    inspection_method: Literal["archive_inventory", "bytecode_inspection", "black_box"]
    captured_at: str
    capture_artifact: str
    input: JsonValue
    expected: JsonValue
    actual: JsonValue
    units: str = Field(min_length=1)
    tolerance: int = Field(strict=True, ge=0, le=0)
    failure_behavior: str = Field(min_length=1)
    limitations: list[str] = Field(min_length=1)
    _artifact = field_validator("artifact", "capture_artifact")(logical_locator)
    _timestamp = field_validator("captured_at")(timestamp)


class FixtureSet(BaseModel):
    """Versioned independently authored cases and truthful runtime availability."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    schema_version: int = Field(strict=True, ge=1, le=1)
    reference_cohort: Literal["144.2953"]
    runtime_status: Literal["unavailable"]
    cases: list[ReferenceFixture]


def load_fixtures(path: Path) -> FixtureSet:
    """Reject duplicate IDs, inaccurate provenance and unequal exact outputs."""
    logger.debug("%s: validate", FIXTURE_FR, extra={"fr_id": FIXTURE_FR})
    try:
        result = FixtureSet.model_validate(read_json(path))
    except ValidationError:
        fail(FIXTURE_FR, "FIXTURE_INVALID", event_logger=logger)
    if len({case.case_id for case in result.cases}) != len(result.cases):
        fail(FIXTURE_FR, "FIXTURE_DUPLICATE", event_logger=logger)
    for case in result.cases:
        if (case.observation_kind == "runtime") != (
            case.inspection_method == "black_box"
        ) or (
            result.runtime_status == "unavailable"
            and case.observation_kind == "runtime"
        ):
            fail(FIXTURE_FR, "FIXTURE_PROVENANCE", event_logger=logger)
        if case.actual != case.expected or case.actual is None:
            fail(FIXTURE_FR, "FIXTURE_OBSERVATION", event_logger=logger)
        if not case.decision_ids or any(
            not value.startswith("DEC-HOST-P00-") for value in case.decision_ids
        ):
            fail(FIXTURE_FR, "FIXTURE_DECISIONS", event_logger=logger)
        logger.debug(
            "%s: accepted case",
            FIXTURE_FR,
            extra={"fr_id": FIXTURE_FR, "case_id": case.case_id},
        )
    logger.info(
        "%s: accepted",
        FIXTURE_FR,
        extra={"fr_id": FIXTURE_FR, "cases": len(result.cases)},
    )
    return result
