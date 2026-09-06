"""Validate Unified Specification feature and requirement traceability."""

from __future__ import annotations

import ast
import re
from collections import Counter
from collections.abc import Set as AbstractSet
from dataclasses import dataclass
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_SPECIFICATION = _ROOT / "docs" / "dev" / "SQX" / "HaruQuantAI_Unified_Specification.md"
_REGISTER = (
    _ROOT
    / "docs"
    / "dev"
    / "SQX"
    / "HaruQuantAI_Feature_Requirement_Traceability_Register.md"
)

_SURFACE_PREFIXES = {
    "SHELL",
    "RUN",
    "BLD",
    "RET",
    "OPT",
    "DBK",
    "RES-OV",
    "RES-TRD",
    "RES",
    "PFC",
    "PFM",
    "DAT",
    "PRJ",
    "STU",
    "CED",
    "MOD",
    "CHR",
    "UI-DCK",
}
_ENGINE_PREFIXES = {"GEN", "AST", "XCH", "NRL", "WRK"}
_CONTROL_PREFIXES = {
    "DEC",
    "REC",
    "INT",
    "WF",
    "BM",
    "PERF",
    "PERF-G",
    "EXT",
}
_EXPECTED_COUNTS = {
    "surface_functional": 149,
    "engine_functional": 52,
    "agentic_functional": 81,
    "tick_functional": 8,
    "master_overlays": 32,
    "platform_nfr": 33,
    "financial_nfr": 5,
    "agentic_nfr": 14,
    "feature_nfr": 12,
    "extensions": 8,
    "decisions": 17,
    "reconciliations": 30,
    "integrations": 14,
    "workflows": 12,
    "benchmarks": 12,
    "performance_tasks": 17,
    "performance_gates": 12,
    "milestones": 14,
    "agentic_tasks": 41,
    "legacy_agentic_features": 22,
    "legacy_agentic_requirements": 72,
}
_REQUIRED_CARD_SECTIONS = (
    "Owned functional requirements",
    "Feature-specific non-functional requirements",
    "References to applicable shared NFRs",
    "Public contracts and dependencies",
    "Catalogue entries / algorithms / controls delivered",
    "Acceptance tests and evidence",
)
_VALID_STATUSES = {"REGISTERED_CURRENT", "SPECIFIED_TARGET"}
_PREFIX_FAMILIES = (
    ("FR-AGT-", "FR-AGT"),
    ("FR-AGENTIC-", "FR-AGENTIC"),
    ("FR-", "FR"),
    ("NFR-AGT-", "NFR-AGT"),
    ("NFR-F-", "NFR-F"),
    ("NFR-", "NFR"),
    ("PERF-G", "PERF-G"),
    ("BM-", "BM"),
    ("INT-", "INT"),
    ("WF-", "WF"),
    ("AGT-", "AGT-TASK"),
)
_FAMILY_CLASSES = {
    **dict.fromkeys(_SURFACE_PREFIXES, "surface_functional"),
    **dict.fromkeys(_ENGINE_PREFIXES, "engine_functional"),
    "FR-AGT": "agentic_functional",
    "TCK": "tick_functional",
    "FR": "master_overlays",
    "NFR": "platform_nfr",
    "NFR-F": "financial_nfr",
    "NFR-AGT": "agentic_nfr",
    "PER": "feature_nfr",
    "EXT": "extensions",
    "DEC": "decisions",
    "REC": "reconciliations",
    "INT": "integrations",
    "WF": "workflows",
    "BM": "benchmarks",
    "PERF": "performance_tasks",
    "PERF-G": "performance_gates",
    "MILESTONE": "milestones",
    "AGT-TASK": "agentic_tasks",
    "LEGACY-FEAT-AGT": "legacy_agentic_features",
    "FR-AGENTIC": "legacy_agentic_requirements",
}
_SOURCE_COLUMN_INDEX = 2
_ID_RE = re.compile(r"`([A-Z][A-Z0-9]*(?:-[A-Z0-9_]+)+)`")
_FEATURE_REFERENCE_RE = re.compile(r"`(FEAT-[A-Z0-9_-]+)`")
_FEATURE_ID_LITERAL_RE = re.compile(r"FEAT-[A-Z0-9_-]+")
_CARD_STATUS_RE = re.compile(r"^- \*\*Status:\*\* `([^`]+)`;", re.MULTILINE)
_RANGE_RE = re.compile(
    r"`([A-Z][A-Z0-9_-]*-\d{3})`\s*\u2013\s*"
    r"`([A-Z][A-Z0-9_-]*-\d{3})`"
)
_TABLE_FIRST_ID_RE = re.compile(r"^\|\s*`?([A-Z][A-Z0-9]*(?:-[A-Z0-9_]+)+)`?\s*\|")
_TABLE_LEADING_BACKTICK_ID_RE = re.compile(r"^\|\s*`([A-Z][A-Z0-9]*(?:-[A-Z0-9_]+)+)`")
_AGENTIC_FR_RE = re.compile(r"^- \[ \] \*\*(FR-AGT-[A-Z0-9_]+)\*\*")
_AGENTIC_NFR_RE = re.compile(r"`(NFR-AGT-[A-Z0-9_]+)`")
_PENDING_ID_RE = re.compile(
    r"^\|\s*Pending evidence\s*\|\s*`([A-Z][A-Z0-9]*(?:-[A-Z0-9_]+)+)`"
)
_LEGACY_WORKFLOW_RE = re.compile(r"WF-AGT-(?:\d{3}|PRI|SEC|TER)$")
_AGENTIC_TASK_RE = re.compile(
    r"(?<![A-Z0-9-])(AGT-(?:\d+\.(?:\d{2}|GATE)|X-[A-Z]+-\d{2}))"
    r"(?![A-Z0-9-])"
)
_MILESTONE_RE = re.compile(r"(?<![A-Z0-9-])(U(?:[0-9]|1[0-3]))(?![A-Z0-9])")
_LEGACY_FEATURE_RE = re.compile(r"FEAT-AGT-\d{2}")
_LEGACY_FEATURE_RANGE_RE = re.compile(
    r"`(FEAT-AGT-\d{2})`\s*\u2013\s*`(FEAT-AGT-\d{2})`"
)
_LEGACY_REQUIREMENT_RANGE_RE = re.compile(
    r"`FR-AGENTIC-(\d{3})`\s*\u2013\s*`(?:FR-AGENTIC-)?(\d{3})`"
)


@dataclass(frozen=True)
class AuditReport:
    """Deterministic validation result."""

    errors: tuple[str, ...]
    source_counts: dict[str, int]
    feature_count: int
    feature_domain_counts: dict[str, int]
    feature_status_counts: dict[str, int]
    mapping_counts: dict[str, int]


def discover_registered_feature_ids(repository_root: Path) -> set[str]:
    """Discover literal feature identities from runtime manifests.

    Args:
        repository_root: Repository root containing the ``app`` package.

    Returns:
        Exact literal ``feature_id=`` values declared in manifest modules.
    """
    feature_ids: set[str] = set()
    manifest_paths = sorted((repository_root / "app").rglob("manifest.py"))
    for manifest_path in manifest_paths:
        tree = ast.parse(
            manifest_path.read_text(encoding="utf-8"),
            filename=str(manifest_path),
        )
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            for keyword in node.keywords:
                value = keyword.value
                if (
                    keyword.arg == "feature_id"
                    and isinstance(value, ast.Constant)
                    and isinstance(value.value, str)
                    and _FEATURE_ID_LITERAL_RE.fullmatch(value.value) is not None
                ):
                    feature_ids.add(value.value)
    return feature_ids


def _prefix(identifier: str) -> str:
    """Return the identifier family used by the specification."""
    if _LEGACY_FEATURE_RE.fullmatch(identifier) is not None:
        return "LEGACY-FEAT-AGT"
    if _MILESTONE_RE.fullmatch(identifier) is not None:
        return "MILESTONE"
    for prefix, family in _PREFIX_FAMILIES:
        if identifier.startswith(prefix):
            return family
    return identifier.rsplit("-", maxsplit=1)[0]


def _source_ids(specification: str) -> set[str]:
    """Extract exact current stable IDs, excluding source range aliases.

    Returns:
        Current stable source identifiers.
    """
    identifiers: set[str] = set()
    for line in specification.splitlines():
        first = _TABLE_FIRST_ID_RE.match(line)
        if first is not None:
            identifiers.add(first.group(1))
        leading = _TABLE_LEADING_BACKTICK_ID_RE.match(line)
        if leading is not None:
            identifiers.add(leading.group(1))
        agentic_fr = _AGENTIC_FR_RE.match(line)
        if agentic_fr is not None:
            identifiers.add(agentic_fr.group(1))
        if "Pending evidence" in line:
            identifiers.update(_AGENTIC_NFR_RE.findall(line))
            pending = _PENDING_ID_RE.match(line)
            if pending is not None:
                identifiers.add(pending.group(1))
    identifiers.update(_AGENTIC_TASK_RE.findall(specification))
    identifiers.update(_MILESTONE_RE.findall(specification))
    identifiers.update(_LEGACY_FEATURE_RE.findall(specification))
    for start_text, end_text in _LEGACY_REQUIREMENT_RANGE_RE.findall(specification):
        identifiers.update(
            f"FR-AGENTIC-{number:03d}"
            for number in range(int(start_text), int(end_text) + 1)
        )
    return {
        identifier
        for identifier in identifiers
        if _LEGACY_WORKFLOW_RE.fullmatch(identifier) is None
    }


def _classify_source(identifiers: set[str]) -> dict[str, set[str]]:
    """Classify source IDs into non-overlapping traceability sets.

    Returns:
        Identifier sets keyed by the declared count names.
    """
    classes: dict[str, set[str]] = {name: set() for name in _EXPECTED_COUNTS}
    for identifier in identifiers:
        class_name = _FAMILY_CLASSES.get(_prefix(identifier))
        if class_name is not None:
            classes[class_name].add(identifier)
    return classes


def _block(document: str, name: str) -> str:
    """Return one required marked register block."""
    pattern = re.compile(
        rf"<!-- {re.escape(name)}_START -->(.*?)<!-- {re.escape(name)}_END -->",
        flags=re.DOTALL,
    )
    match = pattern.search(document)
    return match.group(1) if match is not None else ""


def _expand_ids(text: str) -> list[str]:
    """Expand backticked inclusive numeric ranges and individual IDs.

    Returns:
        Every expanded identifier in document order.
    """
    expanded: list[str] = []
    consumed: list[tuple[int, int]] = []
    for match in _RANGE_RE.finditer(text):
        start, end = match.groups()
        start_base, start_number = start.rsplit("-", maxsplit=1)
        end_base, end_number = end.rsplit("-", maxsplit=1)
        if start_base != end_base:
            continue
        expanded.extend(
            f"{start_base}-{number:03d}"
            for number in range(int(start_number), int(end_number) + 1)
        )
        consumed.append(match.span())
    for match in _LEGACY_FEATURE_RANGE_RE.finditer(text):
        start, end = match.groups()
        start_number = int(start.rsplit("-", maxsplit=1)[1])
        end_number = int(end.rsplit("-", maxsplit=1)[1])
        expanded.extend(
            f"FEAT-AGT-{number:02d}" for number in range(start_number, end_number + 1)
        )
        consumed.append(match.span())
    remainder = list(text)
    for start, end in consumed:
        remainder[start:end] = " " * (end - start)
    remainder_text = "".join(remainder)
    conventional_ids = _ID_RE.findall(remainder_text)
    expanded.extend(conventional_ids)
    expanded.extend(
        identifier
        for identifier in _AGENTIC_TASK_RE.findall(remainder_text)
        if identifier not in conventional_ids
    )
    expanded.extend(_MILESTONE_RE.findall(remainder_text))
    return expanded


def _mapped_ids(document: str, block_name: str) -> list[str]:
    """Return source IDs in a mapping block's third table column."""
    identifiers: list[str] = []
    for line in _block(document, block_name).splitlines():
        if not line.startswith("|") or line.startswith("|---"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) > _SOURCE_COLUMN_INDEX and cells[0] not in {
            "Class",
            "Disposition",
        }:
            identifiers.extend(_expand_ids(cells[_SOURCE_COLUMN_INDEX]))
    return identifiers


def _feature_index(document: str) -> tuple[dict[str, tuple[str, str]], list[str]]:
    """Parse feature index rows and validate their structure.

    Returns:
        Indexed feature metadata and any row errors.
    """
    features: dict[str, tuple[str, str]] = {}
    errors: list[str] = []
    for line in _block(document, "FEATURE_INDEX").splitlines():
        if not line.startswith("|") or line.startswith("|---"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if not cells or cells[0] == "Feature ID":
            continue
        match = (
            _ID_RE.fullmatch(cells[0]) if len(cells) > _SOURCE_COLUMN_INDEX else None
        )
        if match is None:
            errors.append(f"invalid feature index row: {line}")
            continue
        feature_id = match.group(1)
        if feature_id in features:
            errors.append(f"duplicate feature index ID: {feature_id}")
            continue
        status = cells[2]
        if status not in _VALID_STATUSES:
            errors.append(f"invalid feature status for {feature_id}: {status}")
        if re.fullmatch(r"FEAT-AGT-\d{2}", feature_id):
            errors.append(f"legacy Agentic ID marked current: {feature_id}")
        features[feature_id] = (cells[1], status)
    return features, errors


def _feature_cards(document: str) -> tuple[dict[str, str], list[str]]:
    """Parse marked feature cards and validate required subsections.

    Returns:
        Feature-card bodies and any structure errors.
    """
    cards: dict[str, str] = {}
    errors: list[str] = []
    pattern = re.compile(
        r"<!-- FEATURE_CARD_START (FEAT-[A-Z0-9_-]+) -->(.*?)"
        r"<!-- FEATURE_CARD_END \1 -->",
        flags=re.DOTALL,
    )
    for match in pattern.finditer(document):
        feature_id, body = match.groups()
        if feature_id in cards:
            errors.append(f"duplicate feature card: {feature_id}")
            continue
        cards[feature_id] = body
        for section in _REQUIRED_CARD_SECTIONS:
            if f"#### {section}" not in body:
                errors.append(f"{feature_id} missing card section: {section}")
    return cards, errors


def _duplicates(identifiers: list[str]) -> set[str]:
    """Return identifiers appearing more than once."""
    return {
        identifier for identifier, count in Counter(identifiers).items() if count > 1
    }


def _declared_totals(document: str) -> dict[str, int]:
    """Parse the declared total table.

    Returns:
        Declared totals keyed by count name.
    """
    totals: dict[str, int] = {}
    for line in _block(document, "DECLARED_TOTALS").splitlines():
        match = re.match(r"^\|\s*`([^`]+)`\s*\|\s*(\d+)\s*\|", line)
        if match is not None:
            totals[match.group(1)] = int(match.group(2))
    return totals


def _validate_mapping(
    name: str,
    expected: set[str],
    mapped: list[str],
    errors: list[str],
) -> None:
    """Validate one exact once-only source-to-register mapping."""
    missing = expected - set(mapped)
    extra = set(mapped) - expected
    duplicate = _duplicates(mapped)
    if missing:
        errors.append(f"{name} unmapped IDs: {', '.join(sorted(missing))}")
    if extra:
        errors.append(f"{name} unknown IDs: {', '.join(sorted(extra))}")
    if duplicate:
        errors.append(f"{name} multiply mapped IDs: {', '.join(sorted(duplicate))}")


def validate_documents(  # noqa: C901, PLR0912, PLR0915
    specification: str,
    register: str,
    *,
    registered_feature_ids: AbstractSet[str] | None = None,
) -> AuditReport:
    """Validate source coverage, feature references, cards, and totals.

    Args:
        specification: Unified Specification source text.
        register: Feature-Requirement Traceability Register text.
        registered_feature_ids: Optional exact runtime manifest identities.

    Returns:
        A deterministic report containing every validation error and count.
    """
    errors: list[str] = []
    classes = _classify_source(_source_ids(specification))
    source_counts = {name: len(values) for name, values in classes.items()}
    for name, expected_count in _EXPECTED_COUNTS.items():
        if source_counts[name] != expected_count:
            errors.append(
                f"source count drift for {name}: "
                f"expected {expected_count}, got {source_counts[name]}"
            )

    features, feature_errors = _feature_index(register)
    errors.extend(feature_errors)
    cards, card_errors = _feature_cards(register)
    errors.extend(card_errors)
    if set(features) != set(cards):
        missing_cards = set(features) - set(cards)
        unknown_cards = set(cards) - set(features)
        if missing_cards:
            errors.append(f"features missing cards: {', '.join(sorted(missing_cards))}")
        if unknown_cards:
            errors.append(
                f"cards absent from index: {', '.join(sorted(unknown_cards))}"
            )

    for feature_id, body in cards.items():
        status_matches = _CARD_STATUS_RE.findall(body)
        if len(status_matches) != 1:
            errors.append(
                f"{feature_id} must declare exactly one card status; "
                f"found {len(status_matches)}"
            )
            continue
        card_status = status_matches[0]
        if card_status not in _VALID_STATUSES:
            errors.append(f"invalid card status for {feature_id}: {card_status}")
        indexed = features.get(feature_id)
        if indexed is not None and card_status != indexed[1]:
            errors.append(
                f"card/index status mismatch for {feature_id}: "
                f"card={card_status}, index={indexed[1]}"
            )

    if registered_feature_ids is not None:
        current_ids = {
            feature_id
            for feature_id, (_domain, status) in features.items()
            if status == "REGISTERED_CURRENT"
        }
        missing_manifests = current_ids - registered_feature_ids
        if missing_manifests:
            errors.append(
                "REGISTERED_CURRENT IDs absent from runtime manifests: "
                + ", ".join(sorted(missing_manifests))
            )
        registered_targets = (set(features) & registered_feature_ids) - current_ids
        if registered_targets:
            errors.append(
                "SPECIFIED_TARGET IDs present in runtime manifests: "
                + ", ".join(sorted(registered_targets))
            )

    primary_expected = set().union(
        classes["surface_functional"],
        classes["engine_functional"],
        classes["agentic_functional"],
        classes["tick_functional"],
    )
    shared_expected = set().union(
        classes["platform_nfr"],
        classes["financial_nfr"],
        classes["agentic_nfr"],
    )
    controls_expected = set().union(
        classes["extensions"],
        classes["decisions"],
        classes["reconciliations"],
        classes["integrations"],
        classes["workflows"],
        classes["benchmarks"],
        classes["performance_tasks"],
        classes["performance_gates"],
    )
    delivery_expected = set().union(
        classes["milestones"],
        classes["agentic_tasks"],
    )
    legacy_expected = set().union(
        classes["legacy_agentic_features"],
        classes["legacy_agentic_requirements"],
    )
    mappings = {
        "primary": (primary_expected, _mapped_ids(register, "PRIMARY_REQUIREMENTS")),
        "feature NFR": (
            classes["feature_nfr"],
            _mapped_ids(register, "FEATURE_NFR"),
        ),
        "shared NFR": (shared_expected, _mapped_ids(register, "SHARED_NFR")),
        "overlay": (
            classes["master_overlays"],
            _mapped_ids(register, "OVERLAY_REQUIREMENTS"),
        ),
        "control": (controls_expected, _mapped_ids(register, "CONTROL_COVERAGE")),
        "delivery": (
            delivery_expected,
            _mapped_ids(register, "DELIVERY_COVERAGE"),
        ),
        "legacy": (legacy_expected, _mapped_ids(register, "LEGACY_COVERAGE")),
    }
    for name, (expected, mapped) in mappings.items():
        _validate_mapping(name, expected, mapped, errors)

    for block_name in (
        "PRIMARY_REQUIREMENTS",
        "FEATURE_NFR",
        "OVERLAY_REQUIREMENTS",
        "CONTROL_COVERAGE",
        "DELIVERY_COVERAGE",
    ):
        for feature_id in _FEATURE_REFERENCE_RE.findall(_block(register, block_name)):
            if feature_id not in features:
                errors.append(
                    f"{block_name} references undefined feature: {feature_id}"
                )

    for feature_id, body in cards.items():
        marker = "#### References to applicable shared NFRs"
        section = body.split(marker, maxsplit=1)[1] if marker in body else ""
        section = section.split("#### ", maxsplit=1)[0]
        references = set(_expand_ids(section))
        unknown = references - shared_expected
        if unknown:
            errors.append(
                f"{feature_id} references unknown shared NFRs: "
                f"{', '.join(sorted(unknown))}"
            )
        if not references:
            errors.append(f"{feature_id} has no shared NFR references")

    section_ids: set[int] = set()
    for line in _block(register, "SECTION_COVERAGE").splitlines():
        match = re.match(r"^\|\s*(\d+)(?:\u2013(\d+))?\s*\|", line)
        if match is None:
            continue
        start = int(match.group(1))
        end = int(match.group(2) or start)
        section_ids.update(range(start, end + 1))
    if section_ids != set(range(1, 57)):
        missing = set(range(1, 57)) - section_ids
        extra = section_ids - set(range(1, 57))
        errors.append(
            "section coverage mismatch: "
            f"missing={sorted(missing)}, extra={sorted(extra)}"
        )

    declared = _declared_totals(register)
    status_counts = Counter(status for _domain, status in features.values())
    computed = source_counts | {
        "features": len(features),
        "primary_functional": len(primary_expected),
        "shared_nfr": len(shared_expected),
        "control_records": len(controls_expected),
        "delivery_records": len(delivery_expected),
        "legacy_aliases": len(legacy_expected),
        "registered_current": status_counts["REGISTERED_CURRENT"],
        "specified_target": status_counts["SPECIFIED_TARGET"],
    }
    for name, value in computed.items():
        if declared.get(name) != value:
            errors.append(
                f"declared total drift for {name}: "
                f"expected {value}, got {declared.get(name)}"
            )
    domain_counts = Counter(domain for domain, _status in features.values())
    mapping_counts = {
        name: len(mapped) for name, (_expected, mapped) in mappings.items()
    }
    return AuditReport(
        tuple(sorted(set(errors))),
        source_counts,
        len(features),
        dict(sorted(domain_counts.items())),
        dict(sorted(status_counts.items())),
        mapping_counts,
    )


def main() -> int:
    """Validate the repository documents and print deterministic totals.

    Returns:
        Zero when traceability is complete; otherwise one.
    """
    specification = _SPECIFICATION.read_text(encoding="utf-8")
    register = _REGISTER.read_text(encoding="utf-8")
    report = validate_documents(
        specification,
        register,
        registered_feature_ids=discover_registered_feature_ids(_ROOT),
    )
    if report.errors:
        print("[FAIL] Unified feature traceability drift detected:")
        for error in report.errors:
            print(f"  - {error}")
        return 1
    print("[OK] Unified feature traceability is complete")
    print(f"FEATURES : {report.feature_count}")
    print(
        "FEATURES_BY_DOMAIN : "
        + ", ".join(
            f"{name}={count}" for name, count in report.feature_domain_counts.items()
        )
    )
    print(
        "FEATURES_BY_STATUS : "
        + ", ".join(
            f"{name}={count}" for name, count in report.feature_status_counts.items()
        )
    )
    for name, count in sorted(report.source_counts.items()):
        print(f"{name.upper()} : {count}")
    for name, count in sorted(report.mapping_counts.items()):
        label = name.upper().replace(" ", "_")
        print(f"{label}_MAPPED : {count}")
    print("UNMAPPED_OR_MULTIPLY_MAPPED_IDS : 0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
