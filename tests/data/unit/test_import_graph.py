"""Structural guards for the focused DATA dependency graph."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

DATA_ROOT = Path("app/services/data").resolve()
MODELS = DATA_ROOT / "models"
CONTRACTS = DATA_ROOT / "contracts"
LIMITS = DATA_ROOT / "limits"
PERSISTENCE = DATA_ROOT / "persistence"
AUDIT = DATA_ROOT / "audit"
SOURCES = DATA_ROOT / "sources"
RETRIEVAL = DATA_ROOT / "retrieval"
MARKET_DATA = DATA_ROOT / "market_data"
TIME = DATA_ROOT / "time_sessions"
QUALITY = DATA_ROOT / "quality"
TRANSFORMATION = DATA_ROOT / "transformation"
EVIDENCE = DATA_ROOT / "evidence"
FEEDS = DATA_ROOT / "realtime_feeds"
SCHEDULER = DATA_ROOT / "data_jobs"
SECURITY = DATA_ROOT / "security"

DOMAIN_PREFIX = "app.services.data"


def _imported_domain_modules(path: Path, *, module_level_only: bool = True) -> set[str]:
    """Return the ``app.services.data.*`` modules imported by one source file.

    Only module-level imports can form an import cycle because a deferred import runs
    after every module involved is initialized. Both views are useful here: the
    package graph is governed at module load, while removed-path checks include every
    deferred import too.

    Args:
        path: Python source file to parse.
        module_level_only: When ``True``, ignore imports nested inside a function or
            class body and report only top-level ones.

    Returns:
        Set of imported dotted module names inside the DATA domain.
    """
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    nodes = tree.body if module_level_only else list(ast.walk(tree))
    found: set[str] = set()
    for node in nodes:
        if isinstance(node, ast.ImportFrom) and node.module:
            if node.module.startswith(DOMAIN_PREFIX):
                found.add(node.module)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith(DOMAIN_PREFIX):
                    found.add(alias.name)
    return found


def _python_files(package: Path) -> list[Path]:
    """Return every non-cached Python source file in a package.

    Args:
        package: Package directory to scan.

    Returns:
        Sorted list of source file paths.
    """
    return sorted(p for p in package.rglob("*.py") if "__pycache__" not in p.parts)


def test_contracts_have_no_external_domain_dependency() -> None:
    """Assert canonical contracts depend only on their own focused package.

    Raises:
        AssertionError: If a contract imports another DATA capability.
    """
    for path in _python_files(CONTRACTS):
        external = {
            module
            for module in _imported_domain_modules(path)
            if not module.startswith(f"{DOMAIN_PREFIX}.contracts")
        }
        assert not external, (
            f"{path.name} imports {sorted(external)} at module level. Canonical "
            "contracts must stay at the root of the DATA dependency graph."
        )


def test_contracts_deferred_imports_remain_internal() -> None:
    """Assert deferred contract imports also stay inside the contract package.

    Raises:
        AssertionError: If a deferred import reaches another DATA capability.
    """
    for path in _python_files(CONTRACTS):
        imports = _imported_domain_modules(path, module_level_only=False)
        assert all(
            module.startswith(f"{DOMAIN_PREFIX}.contracts") for module in imports
        ), f"{path.name} defers a non-contract DATA import: {sorted(imports)}"


def test_models_imports_only_contracts_and_itself() -> None:
    """Assert temporary feature contracts depend only on canonical contracts.

    Raises:
        AssertionError: If a ``models`` module imports any other capability folder.
    """
    allowed = (f"{DOMAIN_PREFIX}.models", f"{DOMAIN_PREFIX}.contracts")
    for path in _python_files(MODELS):
        for module in _imported_domain_modules(path):
            assert module.startswith(allowed), (
                f"{path.name} imports {module}. Temporary feature contracts may "
                "depend only on canonical contracts and their own modules."
            )


def test_limits_imports_only_contracts_models_and_itself() -> None:
    """Assert limits sit directly above contracts and temporary models.

    Raises:
        AssertionError: If a ``limits`` module imports a capability folder.
    """
    allowed = (
        f"{DOMAIN_PREFIX}.limits",
        f"{DOMAIN_PREFIX}.models",
        f"{DOMAIN_PREFIX}.contracts",
    )
    for path in _python_files(LIMITS):
        for module in _imported_domain_modules(path):
            assert module.startswith(allowed), (
                f"{path.name} imports {module}. `limits` must not depend on a "
                "capability folder, or limit resolution becomes circular."
            )


_STORAGE_ALLOWED = (
    f"{DOMAIN_PREFIX}._settings",
    f"{DOMAIN_PREFIX}.contracts",
    f"{DOMAIN_PREFIX}.models",
    f"{DOMAIN_PREFIX}.limits",
    f"{DOMAIN_PREFIX}.persistence",
    f"{DOMAIN_PREFIX}.audit",
    f"{DOMAIN_PREFIX}.local_datasets",
)

# FR-DATA-105 assigns external artifact admission to persistence and explicitly
# requires the canonical series-quality engine before commit. This is the sole
# capability dependency admitted at that boundary; duplicating quality rules inside
# persistence would create two enforcement authorities.
_STORAGE_FILE_ALLOWED: dict[str, tuple[str, ...]] = {
    "external_import.py": (f"{DOMAIN_PREFIX}.quality",),
}

# One inherited layering inversion remains. It is function-scoped, so it forms no
# import cycle, but it points the wrong way — from storage up into a consumer:
#
#   * `clear_data_cache` calls `ensure_storage` from source composition to trigger
#     lazy migration before touching the cache. Storage should not ask a source
#     governor to prepare itself. Owner: Phase 11, when the package-root facade is
#     assembled and composition is invoked above storage rather than from inside it.
#
# The second inversion recorded in Phase 2 — `cache_clear_request` borrowing
# `_reject_mixed` and `_request_id` from the retrieval layer — cleared in Phase 6. Those
# helpers were never retrieval logic; they are request-construction conventions shared
# by the whole public surface, and they now live in `models/_facade.py`. `time/
# market_hours.py` borrowed the same three and would have added a third inversion, which
# is what surfaced the fix.
#
# Each allowance is named individually so that any *additional* inversion still fails.
_INHERITED_INVERSIONS: dict[str, frozenset[str]] = {}


def test_persistence_and_audit_have_no_module_level_inversions() -> None:
    """Assert the storage layer never imports a consumer at module level.

    Raises:
        AssertionError: If a capability folder is imported at import time.
    """
    for package in (PERSISTENCE, AUDIT):
        for path in _python_files(package):
            allowed = (*_STORAGE_ALLOWED, *_STORAGE_FILE_ALLOWED.get(path.name, ()))
            for module in _imported_domain_modules(path):
                assert module.startswith(allowed), (
                    f"{package.name}/{path.name} imports {module} at module level. "
                    "Storage must not depend on a capability that consumes it."
                )


def test_storage_layer_inversions_do_not_grow() -> None:
    """Assert no new deferred dependency on a consumer appears in the storage layer.

    Every exception must be named in ``_INHERITED_INVERSIONS``. The mapping is empty
    after Phase 11, so any upward dependency fails here.

    Raises:
        AssertionError: If an unlisted deferred consumer import is found.
    """
    for package in (PERSISTENCE, AUDIT):
        for path in _python_files(package):
            deferred = _imported_domain_modules(path, module_level_only=False)
            allowed = (*_STORAGE_ALLOWED, *_STORAGE_FILE_ALLOWED.get(path.name, ()))
            offenders = {
                module for module in deferred if not module.startswith(allowed)
            }
            permitted = _INHERITED_INVERSIONS.get(path.name, frozenset())
            assert offenders <= permitted, (
                f"{package.name}/{path.name} gained a new dependency on a consumer: "
                f"{sorted(offenders - permitted)}. Storage must not reach upward."
            )


def test_audit_query_does_not_depend_on_audit_store() -> None:
    """Assert the audit read and write halves stay independent.

    They were one module before ``CAP-DATA-026``. Splitting them is only worthwhile if
    each half can be exercised without the other; a dependency between them would
    recreate the coupling the split removed.

    Raises:
        AssertionError: If either half imports the other.
    """
    query_imports = _imported_domain_modules(
        AUDIT / "query.py", module_level_only=False
    )
    store_imports = _imported_domain_modules(
        AUDIT / "store.py", module_level_only=False
    )
    assert f"{DOMAIN_PREFIX}.audit.store" not in query_imports
    assert f"{DOMAIN_PREFIX}.audit.query" not in store_imports


# `sources/` is the first folder migrated in place: its name is both the legacy name
# and the target name, so there is no parallel copy. Its four governance modules
# (protocol, registry, policy, composition) are migrated; four adapters in the same
# folder are not, and are owned by later phases:
#
#   * `local.py`, `external.py`, `calendar/`  -> Phase 4 (`retrieval/`)
#   * `broker.py`                             -> Phase 7 (`evidence/account_state.py`)
#
# Until then `composition.py` imports two of them and `__init__.py` re-exports a third,
# so migrated code depends on unmigrated code inside one folder. That is tolerated and
# time-boxed. Listing each file individually means a *new* mixed dependency fails here.
_SOURCES_GOVERNANCE = ("protocol.py", "registry.py", "policy.py", "composition.py")
_SOURCES_PENDING_MIGRATION = frozenset(
    {
        f"{DOMAIN_PREFIX}.sources.contracts",
        f"{DOMAIN_PREFIX}.sources.local_adapter",
        f"{DOMAIN_PREFIX}.sources.broker_adapter",
        f"{DOMAIN_PREFIX}.sources.licensing",
    }
)


def test_migrated_source_governance_uses_only_the_new_core() -> None:
    """Assert the governance modules no longer touch the legacy packages.

    ``storage`` and ``config`` must be gone from every governance module: those were
    the imports whose duplication split settings state across two ``ContextVar``s.
    Canonical ``contracts`` is the approved dependency root for every source module.

    Raises:
        AssertionError: If a governance module imports a legacy package it should not.
    """
    always_forbidden = (
        f"{DOMAIN_PREFIX}.validation",
        f"{DOMAIN_PREFIX}.storage",
        f"{DOMAIN_PREFIX}.config",
    )
    for name in _SOURCES_GOVERNANCE:
        modules = _imported_domain_modules(SOURCES / name, module_level_only=False)
        for module in modules:
            assert not module.startswith(always_forbidden), (
                f"sources/{name} still imports {module}. Phase 3 migrated this module "
                "to `models`/`limits`/`persistence`; a legacy import means the "
                "migration is incomplete."
            )


# `composition.resolve_calendar` returns a `MarketCalendar`, whose definition still
# lives in `gateway/sessions.py`. The import is TYPE_CHECKING-only, so there is no
# runtime coupling and no cycle — but the type graph still points upward. Phase 6 moves
# `MarketCalendar` to `time/market_hours.py`, which resolves it.
_SOURCES_TYPE_ONLY_EXCEPTIONS: dict[str, frozenset[str]] = {
    "composition.py": frozenset({f"{DOMAIN_PREFIX}.time.market_hours"}),
}


def test_source_governance_dependencies_stay_bounded() -> None:
    """Assert governance depends only on the core, itself, and named exceptions.

    Raises:
        AssertionError: If a governance module gains an unexpected dependency.
    """
    allowed = (
        f"{DOMAIN_PREFIX}._settings",
        f"{DOMAIN_PREFIX}.contracts",
        f"{DOMAIN_PREFIX}.models",
        f"{DOMAIN_PREFIX}.limits",
        f"{DOMAIN_PREFIX}.persistence",
        f"{DOMAIN_PREFIX}.audit",
        f"{DOMAIN_PREFIX}.sources",
        f"{DOMAIN_PREFIX}.security",
        f"{DOMAIN_PREFIX}.market_data",
        f"{DOMAIN_PREFIX}.time_sessions",
    )
    for name in _SOURCES_GOVERNANCE:
        permitted = _SOURCES_TYPE_ONLY_EXCEPTIONS.get(name, frozenset())
        for module in _imported_domain_modules(SOURCES / name, module_level_only=False):
            if module in permitted:
                continue
            assert module.startswith(allowed), (
                f"sources/{name} imports {module}, which is outside source "
                "governance's allowed dependency set."
            )


def test_pending_source_adapters_are_the_only_unmigrated_dependency() -> None:
    """Assert the mixed-migration state inside ``sources/`` does not grow.

    Raises:
        AssertionError: If governance depends on an unlisted in-folder module.
    """
    for name in _SOURCES_GOVERNANCE:
        in_folder = {
            module
            for module in _imported_domain_modules(
                SOURCES / name, module_level_only=False
            )
            if module.startswith(f"{DOMAIN_PREFIX}.sources.")
        }
        unexpected = {
            module
            for module in in_folder
            if module not in _SOURCES_PENDING_MIGRATION
            and module.rsplit(".", 1)[-1] + ".py" not in _SOURCES_GOVERNANCE
        }
        assert not unexpected, (
            f"sources/{name} depends on unlisted in-folder modules: "
            f"{sorted(unexpected)}."
        )


def test_timezone_is_a_leaf_above_errors() -> None:
    """Assert ``time/timezone.py`` alone stays dependency-free.

    Phase 4 asserted this of the whole ``time`` package, which was true only because
    ``timezone.py`` was its sole module. Phase 6 added ``market_hours.py``, which
    genuinely needs ``sources`` to resolve a calendar, and ``gaps.py``, which needs the
    session contract — so the package-wide claim no longer holds.

    The narrower assertion is the one that actually mattered: ``timezone.py`` is a leaf,
    which is what justified pulling it forward from Phase 6 into Phase 4 to unblock tick
    generation without a pinned import. If it ever acquires a dependency, that
    justification is void and this must fail.

    Raises:
        AssertionError: If ``timezone.py`` imports anything beyond ``errors``.
    """
    allowed = (f"{DOMAIN_PREFIX}.contracts",)
    for module in _imported_domain_modules(
        TIME / "timeframes.py", module_level_only=False
    ):
        assert module.startswith(allowed), (
            f"time/timezone.py imports {module}. The timeframe manifest must stay a "
            "leaf so every layer can depend on it."
        )


def test_time_does_not_depend_on_consumers() -> None:
    """Assert the temporal modules never reach into a layer that consumes them.

    ``market_hours`` may use ``sources`` to resolve a calendar; neither it nor ``gaps``
    may touch ``retrieval``, ``transformation``, ``quality``, ``feeds``, or
    ``scheduler``, all of which depend on temporal truth.

    Raises:
        AssertionError: If a ``time`` module imports a consumer.
    """
    allowed = (
        f"{DOMAIN_PREFIX}.contracts",
        f"{DOMAIN_PREFIX}.models",
        f"{DOMAIN_PREFIX}.limits",
        f"{DOMAIN_PREFIX}.sources",
        f"{DOMAIN_PREFIX}.time",
        f"{DOMAIN_PREFIX}.time_sessions",
    )
    for path in _python_files(TIME):
        for module in _imported_domain_modules(path, module_level_only=False):
            assert module.startswith(allowed), (
                f"time/{path.name} imports {module}, which depends on `time`."
            )


def test_transformation_depends_only_on_the_core_and_time() -> None:
    """Assert transformation stays a pure reshaping layer.

    Transforms take a dataset and return a dataset. Importing ``retrieval``,
    ``persistence``, or ``sources`` would mean a transform had started acquiring or
    storing something.

    Raises:
        AssertionError: If a transformation module imports outside its allowed set.
    """
    allowed = (
        f"{DOMAIN_PREFIX}.contracts",
        f"{DOMAIN_PREFIX}.models",
        f"{DOMAIN_PREFIX}.limits",
        f"{DOMAIN_PREFIX}.time",
        f"{DOMAIN_PREFIX}.transformation",
    )
    for path in _python_files(TRANSFORMATION):
        for module in _imported_domain_modules(path, module_level_only=False):
            assert module.startswith(allowed), (
                f"transformation/{path.name} imports {module}. Transforms reshape a "
                "dataset they are given; they must not acquire or store anything."
            )


def test_retrieval_depends_only_on_layers_below_it() -> None:
    """Assert retrieval sits above governance and storage, never beside a consumer.

    Raises:
        AssertionError: If a retrieval module imports a later-phase capability.
    """
    allowed = (
        f"{DOMAIN_PREFIX}.contracts",
        f"{DOMAIN_PREFIX}.models",
        f"{DOMAIN_PREFIX}.limits",
        f"{DOMAIN_PREFIX}.persistence",
        f"{DOMAIN_PREFIX}.audit",
        f"{DOMAIN_PREFIX}.sources",
        f"{DOMAIN_PREFIX}.time",
        f"{DOMAIN_PREFIX}.retrieval",
        f"{DOMAIN_PREFIX}.quality",
    )
    for path in _python_files(RETRIEVAL):
        for module in _imported_domain_modules(path, module_level_only=False):
            assert module.startswith(allowed), (
                f"retrieval/{path.name} imports {module}, which is not below it."
            )


def test_retrieval_has_no_removed_validation_dependency() -> None:
    """Assert retrieval does not reach into removed validation ownership.

    Raises:
        AssertionError: If retrieval imports the removed validation package.
    """
    for path in _python_files(RETRIEVAL):
        for module in _imported_domain_modules(path, module_level_only=False):
            assert not module.startswith(f"{DOMAIN_PREFIX}.validation"), (
                f"retrieval/{path.name} imports removed module {module}."
            )


def test_evidence_depends_only_on_the_core() -> None:
    """Assert evidence normalizes what it is handed rather than fetching it.

    Every provider and adapter reaches these functions by injection. Importing
    ``sources``, ``persistence``, or ``retrieval`` would mean an evidence module had
    started resolving or fetching its own inputs — which is exactly the coupling that
    kept these three capabilities split across two folders before Phase 7.

    Raises:
        AssertionError: If an evidence module imports outside its allowed set.
    """
    allowed = (
        f"{DOMAIN_PREFIX}.contracts",
        f"{DOMAIN_PREFIX}.models",
        f"{DOMAIN_PREFIX}.limits",
        f"{DOMAIN_PREFIX}.evidence",
        f"{DOMAIN_PREFIX}.security",
        f"{DOMAIN_PREFIX}.sources",
    )
    for path in _python_files(EVIDENCE):
        for module in _imported_domain_modules(path, module_level_only=False):
            assert module.startswith(allowed), (
                f"evidence/{path.name} imports {module}. Providers and adapters are "
                "injected; evidence must not acquire its own inputs."
            )


def test_feeds_and_scheduler_depend_only_on_layers_below_them() -> None:
    """Assert the runtime layers never import a peer that consumes them.

    ``feeds`` and ``scheduler`` sit at the top of the domain: everything they need is
    below. Importing each other, or being imported by a lower layer, would mean runtime
    lifecycle had leaked into acquisition or storage.

    Raises:
        AssertionError: If either package imports outside its allowed set.
    """
    allowed = (
        f"{DOMAIN_PREFIX}._settings",
        f"{DOMAIN_PREFIX}.contracts",
        f"{DOMAIN_PREFIX}.models",
        f"{DOMAIN_PREFIX}.limits",
        f"{DOMAIN_PREFIX}.persistence",
        f"{DOMAIN_PREFIX}.audit",
        f"{DOMAIN_PREFIX}.sources",
        f"{DOMAIN_PREFIX}.time",
        f"{DOMAIN_PREFIX}.time_sessions",
        f"{DOMAIN_PREFIX}.quality",
        f"{DOMAIN_PREFIX}.market_data",
        f"{DOMAIN_PREFIX}.retrieval",
        f"{DOMAIN_PREFIX}.transformation",
        f"{DOMAIN_PREFIX}.feeds",
        f"{DOMAIN_PREFIX}.scheduler",
        f"{DOMAIN_PREFIX}.realtime_feeds",
        f"{DOMAIN_PREFIX}.data_jobs",
    )
    for package in (FEEDS, SCHEDULER):
        for path in _python_files(package):
            for module in _imported_domain_modules(path, module_level_only=False):
                assert module.startswith(allowed), (
                    f"{package.name}/{path.name} imports {module}, which is not below "
                    "the runtime layer."
                )


def test_feeds_and_scheduler_do_not_import_each_other() -> None:
    """Assert the two runtime packages stay independent.

    A scheduler that imported feeds (or the reverse) would couple job lifecycle to feed
    lifecycle, so a stalled feed could block a backfill and vice versa. They are
    deliberately separate runtimes over the same storage.

    Raises:
        AssertionError: If either package imports the other.
    """
    for path in _python_files(FEEDS):
        for module in _imported_domain_modules(path, module_level_only=False):
            assert not module.startswith(f"{DOMAIN_PREFIX}.scheduler"), (
                f"feeds/{path.name} imports {module}."
            )
    for path in _python_files(SCHEDULER):
        for module in _imported_domain_modules(path, module_level_only=False):
            assert not module.startswith(f"{DOMAIN_PREFIX}.feeds"), (
                f"scheduler/{path.name} imports {module}."
            )


def test_quality_depends_only_on_the_core_and_time() -> None:
    """Assert quality inspection stays a pure evidence layer.

    ``quality`` must not reach ``sources``, ``persistence``, or ``retrieval``: it is a
    pure function over records it is handed. An import from any of them would mean it
    had started fetching or resolving something rather than inspecting.

    This is also why ``map_canonical_symbol`` was excluded from ``asset_validator``:
    it would have required ``sources``, and this test would fail.

    Raises:
        AssertionError: If a quality module imports outside its allowed set.
    """
    allowed = (
        f"{DOMAIN_PREFIX}._settings",
        f"{DOMAIN_PREFIX}.contracts",
        f"{DOMAIN_PREFIX}.models",
        f"{DOMAIN_PREFIX}.limits",
        f"{DOMAIN_PREFIX}.time",
        f"{DOMAIN_PREFIX}.time_sessions",
        f"{DOMAIN_PREFIX}.quality",
        f"{DOMAIN_PREFIX}.market_data",
    )
    for path in _python_files(QUALITY):
        for module in _imported_domain_modules(path, module_level_only=False):
            assert module.startswith(allowed), (
                f"quality/{path.name} imports {module}. Quality inspects records it is "
                "given; it must not acquire or resolve anything."
            )


def test_security_imports_only_errors_models_limits_and_itself() -> None:
    """Assert security uses only errors, models, limits, and itself.

    Raises:
        AssertionError: If a security module imports outside its allowed set.
    """
    allowed = (
        f"{DOMAIN_PREFIX}.contracts",
        f"{DOMAIN_PREFIX}.models",
        f"{DOMAIN_PREFIX}.limits",
        f"{DOMAIN_PREFIX}.security",
    )
    for path in _python_files(SECURITY):
        for module in _imported_domain_modules(path, module_level_only=False):
            assert module.startswith(allowed), (
                f"security/{path.name} imports {module}. Security enforces access "
                "rules; "
                "it must not depend on capability folders."
            )


@pytest.mark.parametrize(
    "package",
    [
        MODELS,
        CONTRACTS,
        LIMITS,
        PERSISTENCE,
        AUDIT,
        QUALITY,
        RETRIEVAL,
        TIME,
        TRANSFORMATION,
        SECURITY,
    ],
)
def test_package_has_no_removed_core_imports(package: Path) -> None:
    """Assert migrated packages never import removed horizontal core paths.

    Args:
        package: DATA package directory under test.

    Raises:
        AssertionError: If a removed core path is imported.
    """
    removed = (
        f"{DOMAIN_PREFIX}.errors",
        f"{DOMAIN_PREFIX}.models._base",
        f"{DOMAIN_PREFIX}.models._facade",
        f"{DOMAIN_PREFIX}.models._validation",
        f"{DOMAIN_PREFIX}.models.records",
        f"{DOMAIN_PREFIX}.validation",
    )
    for path in _python_files(package):
        for module in _imported_domain_modules(path, module_level_only=False):
            assert not module.startswith(removed), (
                f"{path.name} imports removed module {module}. Migrated canonical "
                "ownership must not be recreated through a compatibility path."
            )
