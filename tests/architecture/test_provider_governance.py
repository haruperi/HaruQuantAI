"""Structural tests enforcing G1 provider architecture and governance rules.

Traces to: P1-T04, Gate G1
Validates that AGENTS.md, docs/ARCHITECTURE.md, and docs/PROJECT.md define
spatiotemporal provider architecture rules, non-feature infrastructure packages,
and invent no forbidden feature prefixes.
"""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

REQUIRED_AGENT_HEADINGS = (
    "Provider Infrastructure Exception",
    "Capability Boundary Export Exception",
    "Provider Test and Example Placement",
    "Manifest Canonical Authority",
    "Migration Tombstones and Uninstall Retention",
)

REQUIRED_ARCHITECTURE_HEADINGS = (
    "## Spatiotemporal Provider Architecture",
    "### Units",
    "### Contract Shape",
    "### Identifiers",
    "### Manifest",
    "### Resolution",
    "### Lifecycle",
    "### Composition",
    "### Profiles",
    "### State Retention",
    "### Removability Tiers",
    "### Frontend Boundary",
)

INFRASTRUCTURE_PATHS = (
    "app/kernel/",
    "app/capabilities/",
    "app/composition/",
)

FORBIDDEN_PREFIXES = (
    "FEAT-KRN",
    "FEAT-CAP",
    "FEAT-CMP",
)


def _read_doc(relative_path: str) -> str:
    """Read document content as UTF-8 string."""
    doc_path = REPO_ROOT / relative_path
    assert doc_path.is_file(), f"Document missing: {relative_path}"
    return doc_path.read_text(encoding="utf-8")


def test_agents_contains_provider_rules_once() -> None:
    """Verify AGENTS.md contains the five required provider architecture headings exactly once."""
    content = _read_doc("AGENTS.md")
    for heading in REQUIRED_AGENT_HEADINGS:
        count = content.count(heading)
        assert count == 1, (
            f"Expected heading {heading!r} to appear exactly once in AGENTS.md, found {count}"
        )


def test_architecture_contains_provider_section_once() -> None:
    """Verify docs/ARCHITECTURE.md contains the provider architecture section and 11 child headings."""
    content = _read_doc("docs/ARCHITECTURE.md")
    for heading in REQUIRED_ARCHITECTURE_HEADINGS:
        count = content.count(heading)
        assert count == 1, (
            f"Expected heading {heading!r} to appear exactly once in docs/ARCHITECTURE.md, found {count}"
        )


def test_project_indexes_non_feature_infrastructure() -> None:
    """Verify docs/PROJECT.md indexes app/kernel/, app/capabilities/, and app/composition/ without feature ownership."""
    content = _read_doc("docs/PROJECT.md")
    for infra_path in INFRASTRUCTURE_PATHS:
        assert infra_path in content, (
            f"Expected infrastructure path {infra_path!r} to be indexed in docs/PROJECT.md"
        )

    assert "System infrastructure" in content, (
        "Expected 'System infrastructure' owner in docs/PROJECT.md"
    )
    assert (
        "composition \u2192 provider factory \u2192 injected capability" in content
    ), "Expected cross-domain provider relationship in docs/PROJECT.md"


def test_no_infrastructure_feature_prefix_was_invented() -> None:
    """Verify no forbidden infrastructure feature prefixes were invented in governance documents."""
    docs_to_check = ("AGENTS.md", "docs/ARCHITECTURE.md", "docs/PROJECT.md")
    for doc_name in docs_to_check:
        content = _read_doc(doc_name)
        for prefix in FORBIDDEN_PREFIXES:
            assert prefix not in content, (
                f"Forbidden infrastructure prefix {prefix!r} found in {doc_name}"
            )
