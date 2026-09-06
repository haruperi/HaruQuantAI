"""Tests for the Unified Specification traceability validator."""

from pathlib import Path

from scripts.validate_unified_feature_traceability import (
    discover_registered_feature_ids,
    validate_documents,
)

_ROOT = Path(__file__).resolve().parent.parent
_SPECIFICATION = _ROOT / "docs" / "dev" / "SQX" / "HaruQuantAI_Unified_Specification.md"
_REGISTER = (
    _ROOT
    / "docs"
    / "dev"
    / "SQX"
    / "HaruQuantAI_Feature_Requirement_Traceability_Register.md"
)


def _documents() -> tuple[str, str]:
    """Load the repository traceability source and projection."""
    return (
        _SPECIFICATION.read_text(encoding="utf-8"),
        _REGISTER.read_text(encoding="utf-8"),
    )


def _fixture(
    *,
    feature_id: str = "FEAT-UI-OPERATE_WORKSPACE",
    mapping_feature: str | None = None,
    source_cell: str = "`SHELL-001`",
    supporting_feature: str = "—",
    declared_primary: int = 1,
    include_acceptance: bool = True,
    index_status: str = "SPECIFIED_TARGET",
    card_status: str | None = None,
) -> tuple[str, str]:
    """Build a bounded in-memory source/register failure fixture."""
    primary_feature = mapping_feature or feature_id
    resolved_card_status = card_status or index_status
    acceptance_heading = (
        "Acceptance tests and evidence" if include_acceptance else "Acceptance evidence"
    )
    specification = "| SHELL-001 | Behavior |\n| NFR-P-001 | Shared quality |\n"
    register = f"""
<!-- DECLARED_TOTALS_START -->
| `primary_functional` | {declared_primary} |
<!-- DECLARED_TOTALS_END -->
<!-- FEATURE_INDEX_START -->
| Feature ID | Domain | Status | Value |
|---|---|---|---|
| `{feature_id}` | UI | {index_status} | Atomic value. |
<!-- FEATURE_INDEX_END -->
<!-- PRIMARY_REQUIREMENTS_START -->
| Class | Primary feature | Source IDs | Supporting features |
|---|---|---|---|
| Workbench | `{primary_feature}` | {source_cell} | {supporting_feature} |
<!-- PRIMARY_REQUIREMENTS_END -->
<!-- FEATURE_NFR_START -->
<!-- FEATURE_NFR_END -->
<!-- SHARED_NFR_START -->
| Class | Applicability | Source IDs |
|---|---|---|
| Platform | All | `NFR-P-001` |
<!-- SHARED_NFR_END -->
<!-- OVERLAY_REQUIREMENTS_START -->
<!-- OVERLAY_REQUIREMENTS_END -->
<!-- CONTROL_COVERAGE_START -->
<!-- CONTROL_COVERAGE_END -->
<!-- SECTION_COVERAGE_START -->
| 1\u201356 | `{feature_id}` |
<!-- SECTION_COVERAGE_END -->
<!-- FEATURE_CARD_START {feature_id} -->
### {feature_id} — Fixture
- **Status:** `{resolved_card_status}`; fixture evidence.
#### Owned functional requirements
- `SHELL-001`
#### Feature-specific non-functional requirements
- None.
#### References to applicable shared NFRs
- `NFR-P-001`
#### Public contracts and dependencies
- Fixture contract.
#### Catalogue entries / algorithms / controls delivered
- None.
#### {acceptance_heading}
- Fixture evidence.
<!-- FEATURE_CARD_END {feature_id} -->
"""
    return specification, register


def test_repository_traceability_is_complete() -> None:
    """The checked-in source and register have exact validated coverage."""
    specification, register = _documents()

    report = validate_documents(
        specification,
        register,
        registered_feature_ids=discover_registered_feature_ids(_ROOT),
    )

    assert report.errors == ()
    assert report.feature_count == 98
    assert report.feature_status_counts == {
        "REGISTERED_CURRENT": 22,
        "SPECIFIED_TARGET": 76,
    }
    assert report.source_counts["surface_functional"] == 149
    assert report.source_counts["engine_functional"] == 52
    assert report.source_counts["agentic_functional"] == 81


def test_duplicate_primary_owner_fails_closed() -> None:
    """A primary requirement cannot acquire a second semantic owner."""
    specification, register = _fixture(source_cell="`SHELL-001`, `SHELL-001`")

    errors = validate_documents(specification, register).errors

    assert any("primary multiply mapped IDs: SHELL-001" in error for error in errors)


def test_omitted_primary_requirement_fails_closed() -> None:
    """A source requirement cannot disappear from the ownership projection."""
    specification, register = _fixture(source_cell="—")

    errors = validate_documents(specification, register).errors

    assert any("primary unmapped IDs: SHELL-001" in error for error in errors)


def test_legacy_agentic_feature_cannot_be_marked_current() -> None:
    """Legacy numeric Agentic aliases are never valid feature identities."""
    specification, register = _fixture(feature_id="FEAT-AGT-01")

    errors = validate_documents(specification, register).errors

    assert any(
        "legacy Agentic ID marked current: FEAT-AGT-01" in error for error in errors
    )


def test_undefined_feature_reference_fails_closed() -> None:
    """Ownership rows may reference only exact indexed feature identities."""
    specification, register = _fixture(mapping_feature="FEAT-NO-SUCH")

    errors = validate_documents(specification, register).errors

    assert any(
        "PRIMARY_REQUIREMENTS references undefined feature: FEAT-NO-SUCH" in error
        for error in errors
    )


def test_undefined_supporting_feature_reference_fails_closed() -> None:
    """Supporting references cannot bypass exact feature identity validation."""
    specification, register = _fixture(supporting_feature="`FEAT-NO-SUPPORT`")

    errors = validate_documents(specification, register).errors

    assert any(
        "PRIMARY_REQUIREMENTS references undefined feature: FEAT-NO-SUPPORT" in error
        for error in errors
    )


def test_declared_total_drift_fails_closed() -> None:
    """Human-readable totals cannot diverge from computed source coverage."""
    specification, register = _fixture(declared_primary=2)

    errors = validate_documents(specification, register).errors

    assert any(
        "declared total drift for primary_functional: expected 1, got 2" in error
        for error in errors
    )


def test_missing_feature_card_section_fails_closed() -> None:
    """Every feature card retains the complete required traceability shape."""
    specification, register = _fixture(include_acceptance=False)

    errors = validate_documents(specification, register).errors

    assert any(
        "missing card section: Acceptance tests and evidence" in error
        for error in errors
    )


def test_registered_current_without_manifest_fails_closed() -> None:
    """A current register status requires an exact runtime manifest identity."""
    specification, register = _fixture(index_status="REGISTERED_CURRENT")

    errors = validate_documents(
        specification,
        register,
        registered_feature_ids=set(),
    ).errors

    assert any(
        "REGISTERED_CURRENT IDs absent from runtime manifests: "
        "FEAT-UI-OPERATE_WORKSPACE" in error
        for error in errors
    )


def test_registered_manifest_cannot_remain_target_status() -> None:
    """An indexed manifest identity cannot remain labeled as a future target."""
    specification, register = _fixture()

    errors = validate_documents(
        specification,
        register,
        registered_feature_ids={"FEAT-UI-OPERATE_WORKSPACE"},
    ).errors

    assert any(
        "SPECIFIED_TARGET IDs present in runtime manifests: "
        "FEAT-UI-OPERATE_WORKSPACE" in error
        for error in errors
    )


def test_card_status_must_match_feature_index() -> None:
    """A card cannot contradict the current/target status in the index."""
    specification, register = _fixture(
        index_status="REGISTERED_CURRENT",
        card_status="SPECIFIED_TARGET",
    )

    errors = validate_documents(
        specification,
        register,
        registered_feature_ids={"FEAT-UI-OPERATE_WORKSPACE"},
    ).errors

    assert any(
        "card/index status mismatch for FEAT-UI-OPERATE_WORKSPACE: "
        "card=SPECIFIED_TARGET, index=REGISTERED_CURRENT" in error
        for error in errors
    )
