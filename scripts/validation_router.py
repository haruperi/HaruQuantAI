#!/usr/bin/env python
"""Conservative change discovery and validation routing for HaruQuantAI."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, replace
from pathlib import Path, PurePosixPath
from typing import Final

PUBLIC_PROFILES: Final[tuple[str, ...]] = (
    "affected",
    "python",
    "ui",
    "workflow",
    "integration",
    "full",
)
FULL_FAMILIES: Final[tuple[str, ...]] = ("python", "ui", "workflow")
TRANSIENT_REVIEW_PATHS: Final[frozenset[str]] = frozenset(
    {
        ".agents/task/planner.md",
        ".agents/task/executor.md",
        ".agents/task/reviewer.md",
        ".agents/task/next-agent.md",
    }
)
SERVICE_PATH_PARTS: Final[int] = 4
UI_GROUP_PATH_PARTS: Final[int] = 3
UI_ROOT_PATH_PARTS: Final[int] = 2
EXACT_CLASSIFICATIONS: Final[dict[str, str]] = {
    ".pre-commit-config.yaml": "full",
    "pyproject.toml": "full",
    "uv.lock": "full",
    "app/ui/package-lock.json": "full",
    "app/ui/package.json": "full",
    "scripts/ci_check.py": "full",
    "scripts/validation_router.py": "full",
    "scripts/generate_contracts.py": "shared",
    "tests/conftest.py": "full",
    "AGENTS.md": "workflow",
}
PREFIX_CLASSIFICATIONS: Final[tuple[tuple[str, str], ...]] = (
    (".github/workflows/", "full"),
    (".agents/", "workflow"),
    ("docs/templates/prompt/", "workflow"),
    ("app/ui/src/contracts/generated/", "shared"),
    ("app/contracts/", "shared"),
    ("app/kernel/", "shared"),
    ("app/composition/", "shared"),
    ("tests/contracts/", "shared"),
    ("tests/kernel/", "shared"),
    ("tests/composition/", "shared"),
    ("app/ui/", "ui"),
    ("app/services/", "python"),
    ("tests/services/", "python"),
    ("docs/", "documentation"),
    ("scripts/", "full"),
)


class RoutingError(ValueError):
    """Raised when validation inputs cannot identify a safe candidate."""


@dataclass(frozen=True)
class CandidateChanges:
    """Resolved candidate identity and complete changed-path inventory."""

    base_ref: str | None
    head_ref: str | None
    base_commit: str | None
    head_commit: str | None
    merge_base: str | None
    paths: tuple[str, ...]
    deleted_paths: tuple[str, ...]
    renamed_paths: tuple[tuple[str, str], ...]
    local_paths: tuple[str, ...]

    @property
    def is_dirty(self) -> bool:
        """Return whether staged, unstaged, or untracked paths exist."""
        return bool(self.local_paths)


@dataclass(frozen=True)
class RoutingDecision:
    """A deterministic validation selection and its supporting explanation."""

    requested_profile: str
    families: tuple[str, ...]
    changed_paths: tuple[str, ...]
    python_test_paths: tuple[str, ...]
    ui_test_paths: tuple[str, ...]
    reasons: tuple[str, ...]
    widened_to_full: bool
    candidate: CandidateChanges


def _normalize_path(value: str) -> str:
    """Return a repository-relative path with stable POSIX separators."""
    return PurePosixPath(value.replace("\\", "/")).as_posix().removeprefix("./")


def _git_bytes(repo: Path, *arguments: str) -> bytes:
    """Run a read-only Git query and return its standard output.

    Args:
        repo: Repository root.
        *arguments: Git arguments.

    Returns:
        Raw standard-output bytes.

    Raises:
        RoutingError: If Git rejects the query.
    """
    result = subprocess.run(
        ["git", *arguments],
        cwd=repo,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        raise RoutingError(detail or f"Git command failed: {' '.join(arguments)}")
    return result.stdout


def resolve_commit(repo: Path, revision: str) -> str:
    """Resolve a revision to one exact commit identity.

    Args:
        repo: Repository root.
        revision: Revision supplied by the caller.

    Returns:
        Full commit SHA.

    Raises:
        RoutingError: If the revision is empty or is not a commit.
    """
    if not revision.strip():
        raise RoutingError("Git revisions cannot be empty.")
    try:
        output = _git_bytes(
            repo,
            "rev-parse",
            "--verify",
            "--end-of-options",
            f"{revision}^{{commit}}",
        )
    except RoutingError as exc:
        message = f"Revision does not resolve to a commit: {revision}"
        raise RoutingError(message) from exc
    return output.decode("ascii").strip()


def _parse_name_status(
    payload: bytes,
) -> tuple[set[str], set[str], set[tuple[str, str]]]:
    """Parse null-delimited ``git diff --name-status`` output.

    Returns:
        Changed paths, deleted paths, and renamed path pairs.

    Raises:
        RoutingError: If Git emits an incomplete record.
    """
    fields = [field for field in payload.split(b"\0") if field]
    paths: set[str] = set()
    deleted: set[str] = set()
    renamed: set[tuple[str, str]] = set()
    index = 0
    while index < len(fields):
        status_field = fields[index].decode("utf-8", errors="surrogateescape")
        index += 1
        embedded_path: str | None = None
        if "\t" in status_field:
            status_field, embedded_path = status_field.split("\t", 1)
        status = status_field[:1]
        if status in {"R", "C"}:
            if embedded_path is None:
                if index >= len(fields):
                    raise RoutingError("Malformed renamed-path Git output.")
                old_path = fields[index].decode("utf-8", errors="surrogateescape")
                index += 1
            else:
                old_path = embedded_path
            if index >= len(fields):
                raise RoutingError("Malformed renamed-path Git output.")
            new_path = fields[index].decode("utf-8", errors="surrogateescape")
            index += 1
            pair = (_normalize_path(old_path), _normalize_path(new_path))
            renamed.add(pair)
            paths.update(pair)
            continue

        if embedded_path is None:
            if index >= len(fields):
                raise RoutingError("Malformed changed-path Git output.")
            path = fields[index].decode("utf-8", errors="surrogateescape")
            index += 1
        else:
            path = embedded_path
        normalized = _normalize_path(path)
        paths.add(normalized)
        if status == "D":
            deleted.add(normalized)
    return paths, deleted, renamed


def _local_changes(repo: Path) -> tuple[set[str], set[str], set[tuple[str, str]]]:
    """Return the union of staged, unstaged, and relevant untracked changes."""
    paths: set[str] = set()
    deleted: set[str] = set()
    renamed: set[tuple[str, str]] = set()
    for arguments in (
        ("diff", "--name-status", "-z", "--find-renames"),
        ("diff", "--cached", "--name-status", "-z", "--find-renames"),
    ):
        found, removed, moved = _parse_name_status(_git_bytes(repo, *arguments))
        paths.update(found)
        deleted.update(removed)
        renamed.update(moved)
    untracked = _git_bytes(repo, "ls-files", "--others", "--exclude-standard", "-z")
    paths.update(
        _normalize_path(field.decode("utf-8", errors="surrogateescape"))
        for field in untracked.split(b"\0")
        if field
    )
    return paths, deleted, renamed


def discover_changes(
    repo: Path,
    *,
    base_ref: str | None,
    head_ref: str | None,
    include_local: bool,
) -> CandidateChanges:
    """Discover committed and optionally local changes for a candidate.

    Args:
        repo: Repository root.
        base_ref: Optional integration base revision.
        head_ref: Optional candidate revision.
        include_local: Whether to union local working-tree changes.

    Returns:
        Resolved candidate and path inventory.

    Raises:
        RoutingError: If only one revision is supplied or Git cannot resolve it.
    """
    if (base_ref is None) != (head_ref is None):
        raise RoutingError("--base and --head must be supplied together.")

    paths: set[str] = set()
    deleted: set[str] = set()
    renamed: set[tuple[str, str]] = set()
    base_commit: str | None = None
    head_commit: str | None = None
    merge_base: str | None = None
    if base_ref is not None and head_ref is not None:
        base_commit = resolve_commit(repo, base_ref)
        head_commit = resolve_commit(repo, head_ref)
        merge_base = (
            _git_bytes(repo, "merge-base", base_commit, head_commit)
            .decode("ascii")
            .strip()
        )
        found, removed, moved = _parse_name_status(
            _git_bytes(
                repo,
                "diff",
                "--name-status",
                "-z",
                "--find-renames",
                f"{merge_base}..{head_commit}",
            )
        )
        paths.update(found)
        deleted.update(removed)
        renamed.update(moved)

    local_paths, local_deleted, local_renamed = _local_changes(repo)
    if include_local:
        paths.update(local_paths)
        deleted.update(local_deleted)
        renamed.update(local_renamed)

    return CandidateChanges(
        base_ref=base_ref,
        head_ref=head_ref,
        base_commit=base_commit,
        head_commit=head_commit,
        merge_base=merge_base,
        paths=tuple(sorted(paths)),
        deleted_paths=tuple(sorted(deleted)),
        renamed_paths=tuple(sorted(renamed)),
        local_paths=tuple(sorted(local_paths)),
    )


def _classify(path: str) -> str:
    """Classify one repository path into a conservative impact family.

    Returns:
        Internal impact-family name.
    """
    exact = EXACT_CLASSIFICATIONS.get(path)
    if exact is not None:
        return exact
    if path.endswith("/conftest.py"):
        return "full"
    for prefix, family in PREFIX_CLASSIFICATIONS:
        if path.startswith(prefix):
            return family
    if path.startswith(("app/", "tests/")) and path.endswith((".py", ".pyi")):
        return "python-uncertain"
    if path.endswith((".toml", ".yaml", ".yml")):
        return "full"
    return "unknown"


def _without_transient_review_paths(candidate: CandidateChanges) -> CandidateChanges:
    """Remove controller coordination files from a reviewed product candidate.

    The controller separately fingerprints and protects these files. They are not
    implementation impact and must not make every feature select workflow tests.

    Returns:
        Candidate containing only implementation-relevant paths.
    """
    return replace(
        candidate,
        paths=tuple(
            path for path in candidate.paths if path not in TRANSIENT_REVIEW_PATHS
        ),
        deleted_paths=tuple(
            path
            for path in candidate.deleted_paths
            if path not in TRANSIENT_REVIEW_PATHS
        ),
        renamed_paths=tuple(
            pair
            for pair in candidate.renamed_paths
            if not set(pair) & TRANSIENT_REVIEW_PATHS
        ),
        local_paths=tuple(
            path for path in candidate.local_paths if path not in TRANSIENT_REVIEW_PATHS
        ),
    )


def _existing(repo: Path, candidates: set[str]) -> tuple[str, ...]:
    """Return sorted candidate paths that currently exist."""
    return tuple(sorted(path for path in candidates if (repo / path).exists()))


def _python_test_targets(repo: Path, paths: tuple[str, ...]) -> tuple[str, ...]:
    """Map focused Python paths to owner and domain-integration tests.

    Returns:
        Existing test directories in stable order.
    """
    targets: set[str] = set()
    for path in paths:
        parts = PurePosixPath(path).parts
        if path.startswith("app/services/") and len(parts) >= SERVICE_PATH_PARTS:
            domain, feature = parts[2], parts[3]
            targets.add(f"tests/services/{domain}/{feature}")
            targets.add(f"tests/services/{domain}/integration")
        elif path.startswith("tests/services/") and len(parts) >= SERVICE_PATH_PARTS:
            domain, feature = parts[2], parts[3]
            targets.add(f"tests/services/{domain}/{feature}")
            if feature != "integration":
                targets.add(f"tests/services/{domain}/integration")
    return _existing(repo, targets)


def _ui_test_targets(paths: tuple[str, ...]) -> tuple[str, ...]:
    """Map UI source paths to the nearest bounded Vitest scope.

    Returns:
        Stable UI-relative Vitest targets.
    """
    targets: set[str] = set()
    for path in paths:
        if not path.startswith("app/ui/src/"):
            continue
        relative = PurePosixPath(path).relative_to("app/ui")
        parts = relative.parts
        if path.endswith((".test.ts", ".test.tsx")):
            targets.add(relative.as_posix())
        elif len(parts) >= UI_GROUP_PATH_PARTS and parts[1] in {
            "widgets",
            "components",
        }:
            targets.add(PurePosixPath(*parts[:UI_GROUP_PATH_PARTS]).as_posix())
        elif len(parts) >= UI_ROOT_PATH_PARTS:
            targets.add(PurePosixPath(*parts[:UI_ROOT_PATH_PARTS]).as_posix())
        else:
            targets.add("src")
    ordered = tuple(sorted(targets))
    return tuple(
        target
        for target in ordered
        if not any(
            target != parent and target.startswith(f"{parent}/") for parent in ordered
        )
    )


def _decision(
    profile: str,
    candidate: CandidateChanges,
    families: tuple[str, ...],
    reasons: tuple[str, ...],
    *,
    widened: bool = False,
    python_targets: tuple[str, ...] = (),
    ui_targets: tuple[str, ...] = (),
) -> RoutingDecision:
    """Construct a routing decision from normalized components.

    Returns:
        Immutable routing decision.
    """
    return RoutingDecision(
        requested_profile=profile,
        families=families,
        changed_paths=candidate.paths,
        python_test_paths=python_targets,
        ui_test_paths=ui_targets,
        reasons=reasons,
        widened_to_full=widened,
        candidate=candidate,
    )


def _route_impacts(
    repo: Path,
    profile: str,
    candidate: CandidateChanges,
) -> RoutingDecision:
    """Route a non-empty affected or integration candidate.

    Returns:
        Conservative impact-derived decision.
    """
    classifications = {path: _classify(path) for path in candidate.paths}
    reasons = tuple(
        f"{path}: {classification}" for path, classification in classifications.items()
    )
    kinds = set(classifications.values())
    if kinds & {"full", "unknown", "python-uncertain"}:
        return _decision(
            profile,
            candidate,
            FULL_FAMILIES,
            (*reasons, "Uncertain or root impact widened validation to full."),
            widened=True,
        )

    families, python_targets, ui_targets, selection_reasons = _select_families(
        repo, profile, candidate, kinds
    )
    reasons = (*reasons, *selection_reasons)
    ordered = tuple(
        family
        for family in (
            "python",
            "python-affected",
            "ui",
            "ui-affected",
            "workflow",
            "documentation",
        )
        if family in families
    )
    if not ordered:
        ordered = FULL_FAMILIES
        reasons = (*reasons, "No safe route remained; selected full validation.")
    return _decision(
        profile,
        candidate,
        ordered,
        reasons,
        widened=ordered == FULL_FAMILIES,
        python_targets=python_targets,
        ui_targets=ui_targets,
    )


def _select_families(
    repo: Path,
    profile: str,
    candidate: CandidateChanges,
    kinds: set[str],
) -> tuple[set[str], tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    """Select bounded families and test targets for known impact kinds.

    Returns:
        Families, Python targets, UI targets, and additional reasons.
    """
    families: set[str] = set()
    for kind, selected in (
        ("shared", {"python", "ui"}),
        ("workflow", {"workflow"}),
        ("documentation", {"documentation"}),
    ):
        if kind in kinds:
            families.update(selected)
    python_targets: tuple[str, ...] = ()
    ui_targets: tuple[str, ...] = ()
    reasons: list[str] = []
    if "python" in kinds:
        if profile == "affected":
            python_targets = _python_test_targets(repo, candidate.paths)
            if not python_targets:
                families.add("python")
                reasons.append("No bounded owner tests found; selected Python.")
            else:
                families.add("python-affected")
        else:
            families.add("python")
    if "ui" in kinds:
        if profile == "affected":
            ui_targets = _ui_test_targets(candidate.paths)
            if not ui_targets:
                families.add("ui")
                reasons.append("No bounded UI tests found; selected full UI.")
            else:
                families.add("ui-affected")
        else:
            families.add("ui")
    return families, python_targets, ui_targets, tuple(reasons)


def route_validation(
    repo: Path,
    *,
    profile: str,
    base_ref: str | None = None,
    head_ref: str | None = None,
    reviewed_worktree: bool = False,
) -> RoutingDecision:
    """Build a conservative routing decision for one requested profile.

    Args:
        repo: Repository root.
        profile: Public validation profile.
        base_ref: Optional integration base revision.
        head_ref: Optional candidate revision.
        reviewed_worktree: Include local changes in an integration candidate that
            has already been frozen by the workflow controller.

    Returns:
        Complete routing decision.

    Raises:
        RoutingError: If the profile or candidate identity is invalid.
    """
    if profile not in PUBLIC_PROFILES:
        message = f"Unknown validation profile: {profile}"
        raise RoutingError(message)
    if reviewed_worktree and profile != "integration":
        raise RoutingError(
            "Reviewed-worktree routing is valid only for integration validation."
        )
    if reviewed_worktree and (base_ref is None or head_ref is None):
        raise RoutingError(
            "Reviewed-worktree integration requires explicit --base and --head."
        )
    candidate = discover_changes(
        repo,
        base_ref=base_ref,
        head_ref=head_ref,
        include_local=profile != "integration" or reviewed_worktree,
    )
    if reviewed_worktree:
        candidate = _without_transient_review_paths(candidate)
    if (
        profile == "integration"
        and base_ref is not None
        and candidate.is_dirty
        and not reviewed_worktree
    ):
        raise RoutingError(
            "Integration validation requires a clean materialized candidate."
        )
    if profile in {"python", "ui", "workflow"}:
        return _decision(
            profile,
            candidate,
            (profile,),
            (f"Explicit {profile} profile selected.",),
        )
    if profile == "full":
        return _decision(
            profile,
            candidate,
            FULL_FAMILIES,
            ("Conservative full validation selected.",),
        )
    if profile == "integration" and base_ref is None:
        return _decision(
            profile,
            candidate,
            FULL_FAMILIES,
            ("Missing integration identities widened validation to full.",),
            widened=True,
        )
    if not candidate.paths:
        return _decision(
            profile,
            candidate,
            FULL_FAMILIES,
            ("Empty or inconclusive impact widened validation to full.",),
            widened=True,
        )
    return _route_impacts(repo, profile, candidate)
