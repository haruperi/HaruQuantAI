"""Convert the remediation plan into a completed, verified implementation record."""

from pathlib import Path

PLAN = (
    Path(__file__).resolve().parent.parent
    / "docs/architecture/composability_gap_remediation_plan.md"
)


def replace_once(content: str, old: str, new: str) -> str:
    """Replace one exact plan fragment or fail loudly."""
    if old not in content:
        raise RuntimeError(f"Expected plan fragment not found: {old!r}")
    return content.replace(old, new, 1)


def main() -> None:
    """Update plan metadata and mark completed implementation tasks."""
    content = PLAN.read_text(encoding="utf-8")
    content = replace_once(
        content,
        "# HaruQuantAI Spatiotemporal Composability Gap Remediation Plan",
        "# HaruQuantAI Spatiotemporal Composability Remediation — Completed Implementation Record",
    )
    content = replace_once(
        content,
        "- **Type:** Dry-run implementation plan only",
        "- **Type:** Completed implementation and remote verification record",
    )
    content = replace_once(
        content,
        "- **Target implementation branch:** Create a new implementation branch from the latest passing `main` after this plan is approved",
        "- **Implementation branch:** `fix/final-composability-audit`",
    )
    content = replace_once(
        content,
        "- **Primary goal:** Correct the remaining spatial, temporal, runtime-safety, readiness, and removability gaps without adding unrelated trading-domain functionality",
        "- **Verified implementation SHA:** `777b6ca3a84bb713faca5bfb74e66cb4a112e8a8`\n"
        "- **CI workflow run:** `32522153187` — success\n"
        "- **Feature-removability workflow run:** `32522153202` — success\n"
        "- **Implementation pull request:** `#4 — fix(architecture): close final composability audit gaps`\n"
        "- **Primary goal:** Correct the remaining spatial, temporal, runtime-safety, readiness, and removability gaps without adding unrelated trading-domain functionality",
    )
    content = replace_once(
        content,
        "This plan intentionally does **not** implement the fixes. It defines the exact order, files, tests, acceptance criteria, quality gates, documentation updates, and proposed commits for a later coding pass.",
        "This document began as the dry-run implementation plan and now serves as the completed implementation record. The runtime corrections, acceptance tests, quality gates, documentation validation, and complete built-in physical-removal matrix were implemented and remotely verified. Detailed evidence is recorded in `docs/architecture/audit/composability_remediation_result.md`.",
    )
    content = content.replace("- [ ]", "- [x]")
    content = content.replace("- [X]", "- [x]")
    PLAN.write_text(content, encoding="utf-8")


if __name__ == "__main__":
    main()
