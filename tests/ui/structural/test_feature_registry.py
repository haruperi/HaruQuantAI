"""Verify the independent API and UI feature registries."""

import re
from pathlib import Path

_REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
_API_README = _REPOSITORY_ROOT / "app" / "services" / "api" / "README.md"
_UI_README = _REPOSITORY_ROOT / "app" / "ui" / "README.md"
_PROJECT_README = _REPOSITORY_ROOT / "docs" / "PROJECT.md"
_STANDARD_SECTIONS = (
    "## 1. Purpose and Boundary",
    "## 2. Final Package Structure",
    "## 3. Workflows",
    "## 4. Module and Requirement Specifications",
    "## 5. Package-Wide Requirements and Shared Configuration",
    "## 6. Open Decisions",
    "## 7. Tests and Definition of Done",
    "## 8. Change Process",
)


def _registry(readme: Path) -> str:
    """Return the single feature-registry section from a package README.

    Args:
        readme: Package README path.

    Returns:
        The feature-registry section text.

    Raises:
        AssertionError: If the README has zero or multiple registry headings.
    """
    text = readme.read_text(encoding="utf-8")
    assert text.count("### Feature Registry") == 1
    section = text.split("### Feature Registry", maxsplit=1)[1]
    return section.split("\n## ", maxsplit=1)[0]


def test_api_and_ui_have_independent_feature_registries() -> None:
    """Require exact backend and frontend feature ownership sets."""
    api_registry = _registry(_API_README)
    ui_registry = _registry(_UI_README)
    api_rows = "\n".join(
        line for line in api_registry.splitlines() if "| `FEAT-API-" in line
    )
    ui_rows = "\n".join(
        line for line in ui_registry.splitlines() if "| `FEAT-UI-" in line
    )

    assert set(re.findall(r"FEAT-API-\d{2}", api_rows)) == {
        f"FEAT-API-{number:02d}" for number in range(1, 27)
    }
    assert set(re.findall(r"FEAT-UI-\d{2}", ui_rows)) == {
        f"FEAT-UI-{number:02d}" for number in range(1, 29)
    } - {"FEAT-UI-07"}
    assert "FEAT-UI-" not in api_rows
    assert "app/ui" not in api_rows


def test_market_and_watchlist_ownership_is_reconciled() -> None:
    """Require completed focused ownership and retired legacy locations."""
    api_registry = _registry(_API_README)
    ui_registry = _registry(_UI_README)

    # The API registry stays fully reconciled; the UI records exactly the
    # nine primary/foundation features (FEAT-UI-01-17) whose requirement
    # coverage or focused-folder ownership is not yet evidenced. Naming them
    # keeps the ratchet: no feature can silently regress.
    assert "| Pending |" not in api_registry
    assert set(re.findall(r"\|\s*Pending\s*\|\s*`(FEAT-UI-\d{2})`", ui_registry)) == {
        f"FEAT-UI-{number:02d}" for number in range(1, 18)
    } - {
        "FEAT-UI-01",
        "FEAT-UI-02",
        "FEAT-UI-03",
        "FEAT-UI-04",
        "FEAT-UI-05",
        "FEAT-UI-06",
        "FEAT-UI-07",
        "FEAT-UI-14",
    }
    assert "| `workstation/watchlists/` |" in api_registry
    assert "| `workstation/markets/` |" in api_registry
    assert re.search(r"\|\s*`src/features/markets/`\s*\|", ui_registry) is not None
    assert re.search(r"\|\s*`src/features/watchlists/`\s*\|", ui_registry) is not None
    assert not (_REPOSITORY_ROOT / "app/services/api/markets_source.py").exists()
    for retired in ("markets", "watchlists"):
        retired_directory = _REPOSITORY_ROOT / "app/services/api" / retired
        assert not any(
            path.is_file() and path.name != "__pycache__"
            for path in retired_directory.glob("*")
        )
    assert not (_REPOSITORY_ROOT / "app/services/api/routes/workstation.py").exists()
    assert not (_REPOSITORY_ROOT / "app/ui/src/components/widgets").exists()

    workstation = _REPOSITORY_ROOT / "app/services/api/workstation"
    for feature in ("operational", "watchlists", "markets"):
        feature_directory = workstation / feature
        assert feature_directory.is_dir()
        assert {
            "README.md",
            "__init__.py",
            "routes.py",
            "schemas.py",
            "orchestration.py",
        } <= {path.name for path in feature_directory.iterdir() if path.is_file()}


def test_ui_evidence_exception_and_widget_ownership_are_documented() -> None:
    """Require explicit UI evidence rules and focused widget ownership."""
    text = _UI_README.read_text(encoding="utf-8")

    assert re.search(
        r"do not require separate numbered\s+standalone usage programs", text
    )
    assert "Production UI is not verification evidence" in text
    owned_widgets = (
        "app/ui/src/features/training-ux/ChallengesWidget.tsx",
        "app/ui/src/features/chart/ChartWidget.tsx",
        "app/ui/src/features/training-ux/EducationWidget.tsx",
        "app/ui/src/features/instrument-panels/OptionsGridWidget.tsx",
        "app/ui/src/features/trading/OrderTicket.tsx",
        "app/ui/src/components/workflow/PositionsWidget.tsx",
        "app/ui/src/features/price-ladder/PriceLadderWidget.tsx",
        "app/ui/src/app/workstation/settings/SystemSettingsModal.tsx",
        "app/ui/src/components/workflow/TradeLogWidget.tsx",
        "app/ui/src/features/planning/TradePlanWidget.tsx",
    )
    assert all((_REPOSITORY_ROOT / path).exists() for path in owned_widgets)
    assert "Widget ownership is resolved in the Feature Registry" in text
    # Open Decisions records unresolved owner choices only; each must stay present
    # until the owner resolves it into a requirement, boundary, or exclusion.
    for unresolved in (
        "No owning backend domain for two surfaces",
        "Fixture data reaches production modules",
        "Remaining overlapping presentation paradigms",
    ):
        assert unresolved in text


def test_redundant_frontend_usage_programs_are_absent() -> None:
    """Ensure migrated UI features do not retain API-owned usage programs."""
    usage_directory = _REPOSITORY_ROOT / "tests" / "api" / "usage"
    for filename in (
        "09_frontend_clients.ts",
        "10_frontend_context.tsx",
        "11_frontend_components.tsx",
        "12_frontend_pages.tsx",
        "15_instrument_panels.tsx",
        "16_planning.tsx",
        "17_workflow_pages.tsx",
        "18_emergency_ux.tsx",
        "19_human_factors.tsx",
        "20_training_ux.tsx",
    ):
        assert not (usage_directory / filename).exists()


def test_ui_readme_follows_standard_section_order() -> None:
    """Require the standard package README sections in canonical order."""
    text = _UI_README.read_text(encoding="utf-8")
    positions = [text.index(heading) for heading in _STANDARD_SECTIONS]

    assert positions == sorted(positions)
    assert text.count("### Feature Registry") == 1
    for required_heading in (
        "### Purpose",
        "### Owns",
        "### Does not own",
        "### Shared contracts",
        "### Persisted state",
        "### Four-level structure",
        "### Package capability map",
        "### Module dependency diagram",
        "### Structure rules",
        "### Status values",
        "### Workflow scope values",
        "### Test and usage locations",
        "### Commands",
        "### Required test levels",
        "### Package completion checklist",
    ):
        assert required_heading in text


def test_repository_feature_inventory_is_reconciled() -> None:
    """Recalculate the canonical registry total and verify the system index."""
    readmes = sorted((_REPOSITORY_ROOT / "app" / "services").glob("*/README.md"))
    readmes.extend(
        (
            _REPOSITORY_ROOT / "app" / "agentic" / "README.md",
            _REPOSITORY_ROOT / "app" / "ui" / "README.md",
            _REPOSITORY_ROOT / "app" / "utils" / "README.md",
        )
    )
    statuses: list[str] = []
    feature_ids: list[str] = []
    for readme in readmes:
        registry = _registry(readme)
        rows = re.findall(
            r"^\|\s*(Completed|Pending|Partial|Missing)\s*\|\s*`(FEAT-[A-Z]+-\d+)`",
            registry,
            flags=re.MULTILINE,
        )
        statuses.extend(status for status, _feature_id in rows)
        feature_ids.extend(feature_id for _status, feature_id in rows)

    assert len(feature_ids) == len(set(feature_ids)) == 245
    assert statuses.count("Completed") == 236
    assert statuses.count("Pending") == 9
    assert statuses.count("Partial") == 0
    project = _PROJECT_README.read_text(encoding="utf-8")
    assert "245 registered application features" in project
    assert "(96.33%)" in project
