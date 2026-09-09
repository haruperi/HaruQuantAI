"""Canonical professional role-contract regression tests."""

from __future__ import annotations

from types import ModuleType

ROLE_TITLES = {
    "planner": "HaruQuantAI Principal Software Architect and Implementation Planner",
    "executor": "HaruQuantAI Senior Software Implementation Engineer",
    "reviewer": "HaruQuantAI Principal Software Verification and Code Review Engineer",
}


def test_templates_own_complete_role_contracts(orc: ModuleType) -> None:
    cfg = orc.assemble_config(str(orc.REPO_ROOT))
    for key, title in ROLE_TITLES.items():
        text = cfg["templates"][key].read_text(encoding="utf-8")
        assert title in text
        assert "defined by `AGENTS.md`" not in text
        assert "Repository-wide authority" in text
        assert "This prompt defines your complete" in text


def test_protected_role_sentinels_match_canonical_templates(orc: ModuleType) -> None:
    cfg = orc.assemble_config(str(orc.REPO_ROOT))
    mapping = {
        "PLANNER": "planner",
        "EXECUTOR": "executor",
        "REVIEWER": "reviewer",
        "REVIEWER_CLOSEOUT": "reviewer_closeout",
    }
    for sentinel_key, template_key in mapping.items():
        text = cfg["templates"][template_key].read_text(encoding="utf-8")
        for sentinel in orc.PROTECTED_SENTINELS[sentinel_key]:
            assert sentinel in text


def test_templates_require_output_discovery_and_check_only_freeze(
    orc: ModuleType,
) -> None:
    """Role contracts discover generated paths and protect reviewed bytes."""
    cfg = orc.assemble_config(str(orc.REPO_ROOT))
    planner = cfg["templates"]["planner"].read_text(encoding="utf-8")
    executor = cfg["templates"]["executor"].read_text(encoding="utf-8")
    closeout = cfg["templates"]["reviewer_closeout"].read_text(encoding="utf-8")

    assert "generate_phase0_evidence.py --list-outputs" in planner
    assert "include every output" in planner
    assert "validation is check-only" in executor
    assert "controller close-out contract" in closeout
    assert "does not repeat already receipted validation" in closeout
    assert "ACTIVATING : CONTROLLER" in closeout
    assert "must never launch or resume" in closeout
