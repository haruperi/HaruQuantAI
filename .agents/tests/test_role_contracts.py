"""Canonical professional role-contract regression tests."""

from __future__ import annotations

from types import ModuleType

ROLE_TITLES = {
    "planner": "HaruQuantAI Principal Software Architect and Implementation Planner",
    "executor": "HaruQuantAI Senior Software Implementation Engineer",
    "reviewer": "HaruQuantAI Principal Software Verification and Code Review Engineer",
    "reviewer_closeout": "HaruQuantAI Release Integrity and Change-Control Engineer",
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
