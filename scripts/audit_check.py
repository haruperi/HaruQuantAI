#!/usr/bin/env python
"""Tier 1 architecture conformance sweep for HaruQuantAI.

Advisory only. This script never fails a build: it always exits 0. It reports
mechanical, statically decidable conformance against the rules declared in
`AGENTS.md` section 1 (Focused Domain Architecture) and section 2 (Coding Style),
and feeds the Tier 1 columns of the audit matrix in `docs/PROJECT.md` section 9.1.

Checks implemented:
    REG   Feature Registry reconciliation (README feature IDs vs module folders)
    GATE  Package-root export gate (external imports resolve through `__all__`)
    FUNC  Function-only public API surface (`__all__` exposes functions only)
    DEEP  No deep cross-domain imports
    ROOT  Root-file rule
    USE   One numbered usage program per registered feature
    WFE   Workflow evidence programs plus `run_all.py`
    UT    Unit test presence
    IT    Integration test presence
    COV   Coverage percentage (read from `coverage.xml` when present)
    HYG   Hygiene (bare `except`, `print` in application code, secret patterns)

Known limits:
    Analysis is static (`ast` and regex). Dynamic re-export, `importlib`, and
    runtime attribute assignment are not resolved and may produce `UNKNOWN`.
    `QUANT`, `SAFE`, `LOG`, `CONTRACT`, and the remaining Tier 2 dimensions have
    no mechanical proxy and are deliberately out of scope for this sweep.

Usage:
    uv run python scripts/audit_check.py
    uv run python scripts/audit_check.py --domain data --domain brokers
    uv run python scripts/audit_check.py --check DEEP --verbose
"""

from __future__ import annotations

import argparse
import ast
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# AGENTS.md section 1, Root-file Rule: allowed package infrastructure.
ALLOWED_ROOT_FILES = frozenset(
    {
        "__init__.py",
        "_settings.py",
        "_limits.py",
        "py.typed",
    }
)

# AGENTS.md section 1, Reconciliation Exclusions: documented non-feature dirs.
NON_FEATURE_DIRS = frozenset(
    {
        "__pycache__",
        "migrations",
        "contracts",
        "schemas",
        "_shared",
        "persistence",
    }
)

# Directories never worth walking (vendored, generated, or cache).
SKIP_DIRS = frozenset(
    {
        ".git",
        ".venv",
        ".next",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".uv-cache",
        "__pycache__",
        "build",
        "coverage",
        "dist",
        "htmlcov",
        "node_modules",
        "scratch",
        "tmp_uv_cache",
        "uv-cache",
    }
)

FEATURE_ID_RE = re.compile(r"\bFEAT-[A-Z]+-\d+\b")
WORKFLOW_ID_RE = re.compile(r"\bWF-[A-Z]+-[A-Z0-9]+\b")
USAGE_PROGRAM_RE = re.compile(r"^(\d+)_")
COVERAGE_PACKAGE_RE = re.compile(
    r"<package\b[^>]*\bname=\"(?P<name>[^\"]+)\"[^>]*\bline-rate=\"(?P<rate>[^\"]+)\""
)
COVERAGE_FLOOR = 80.0

# Deliberately narrow: high-signal literal credential patterns only.
SECRET_RE = re.compile(
    r"(?i)\b(api[_-]?key|secret[_-]?key|password|access[_-]?token)\b\s*[:=]\s*"
    r"[\"'][^\"'\s]{8,}[\"']"
)

STATUS_OK = "OK"
STATUS_WARN = "WARN"
STATUS_FAIL = "FAIL"
STATUS_NA = "N/A"
STATUS_UNKNOWN = "UNKNOWN"

STATUS_GLYPH = {
    STATUS_OK: "[ OK ]",
    STATUS_WARN: "[WARN]",
    STATUS_FAIL: "[FAIL]",
    STATUS_NA: "[ -- ]",
    STATUS_UNKNOWN: "[ ?? ]",
}

CHECK_ORDER = (
    "REG",
    "GATE",
    "FUNC",
    "DEEP",
    "ROOT",
    "USE",
    "WFE",
    "UT",
    "IT",
    "COV",
    "HYG",
)


@dataclass(frozen=True)
class Domain:
    """One audited row of the matrix.

    Attributes:
        row: Matrix row identifier as printed in `docs/PROJECT.md` section 9.1.
        key: Lowercase selector accepted by `--domain`.
        name: Human-readable domain name.
        package: Repository-relative package path, or None when not a package.
        tests: Repository-relative test root, or None when the domain has none.
        kind: One of `python`, `frontend`, `config`, `docs`, or `system`.
    """

    row: str
    key: str
    name: str
    package: str | None
    tests: str | None
    kind: str


@dataclass
class Finding:
    """Outcome of a single check for a single domain.

    Attributes:
        code: Check code, e.g. `DEEP`.
        status: One of the module-level STATUS_* values.
        summary: One-line result suitable for the compact report.
        details: Individual violations, printed only in verbose mode.
    """

    code: str
    status: str
    summary: str
    details: list[str] = field(default_factory=list)


DOMAINS: tuple[Domain, ...] = (
    Domain("0", "system", "System", None, "tests/system", "system"),
    Domain("1", "utils", "Utils", "app/utils", "tests/utils", "python"),
    Domain(
        "2", "brokers", "Brokers", "app/services/brokers", "tests/brokers", "python"
    ),
    Domain("3", "data", "Data", "app/services/data", "tests/data", "python"),
    Domain(
        "4",
        "indicators",
        "Indicators",
        "app/services/indicators",
        "tests/indicators",
        "python",
    ),
    Domain(
        "5", "strategy", "Strategy", "app/services/strategy", "tests/strategy", "python"
    ),
    Domain("6", "risk", "Risk", "app/services/risk", "tests/risk", "python"),
    Domain(
        "7", "trading", "Trading", "app/services/trading", "tests/trading", "python"
    ),
    Domain(
        "8",
        "simulator",
        "Simulator",
        "app/services/simulator",
        "tests/simulator",
        "python",
    ),
    Domain(
        "9",
        "analytics",
        "Analytics",
        "app/services/analytics",
        "tests/analytics",
        "python",
    ),
    Domain(
        "10",
        "optimization",
        "Optimization",
        "app/services/optimization",
        "tests/optimization",
        "python",
    ),
    Domain(
        "11",
        "research",
        "Research",
        "app/services/research",
        "tests/research",
        "python",
    ),
    Domain(
        "12",
        "portfolio",
        "Portfolio",
        "app/services/portfolio",
        "tests/portfolio",
        "python",
    ),
    Domain("13", "agentic", "Agentic", "app/agentic", "tests/agentic", "python"),
    Domain("14", "api", "UI-API", "app/services/api", "tests/api", "python"),
    Domain("15", "configs", "Configs", "app/configs", None, "config"),
    Domain("16", "ui", "UI", "app/ui", None, "frontend"),
    Domain("17", "schema", "Schema Model", "docs/schema", None, "docs"),
)


# Caches. Several checks revisit the same files; the repository may sit on a
# slow mount, so read and parse each file at most once per process.
_SOURCE_CACHE: dict[Path, str | None] = {}
_AST_CACHE: dict[Path, ast.Module | None] = {}
_LISTING_CACHE: dict[Path, list[Path]] = {}

# Files the running interpreter could not parse. Populated by `parse_module`.
# A non-empty list means results are understated and must not be trusted; the
# usual cause is running an interpreter older than the project target, so
# always invoke this script through `uv run python`.
_PARSE_FAILURES: list[str] = []


def read_source(path: Path) -> str | None:
    """Read a source file once and memoize the result.

    Args:
        path: File to read.

    Returns:
        File text, or None when the file cannot be decoded or read.
    """
    if path in _SOURCE_CACHE:
        return _SOURCE_CACHE[path]
    try:
        text: str | None = path.read_text(encoding="utf-8")
    except OSError, UnicodeDecodeError:
        text = None
    _SOURCE_CACHE[path] = text
    return text


def iter_python_files(root: Path) -> list[Path]:
    """Collect every Python file under a root, skipping vendored directories.

    Args:
        root: Directory to walk.

    Returns:
        Sorted list of Python file paths.
    """
    if root in _LISTING_CACHE:
        return _LISTING_CACHE[root]
    if not root.is_dir():
        _LISTING_CACHE[root] = []
        return []
    found: list[Path] = []
    # Prune skipped directories during the walk. Filtering after `rglob` would
    # still traverse vendored trees such as `app/ui/node_modules`.
    for current, dirnames, filenames in os.walk(root):
        dirnames[:] = [name for name in dirnames if name not in SKIP_DIRS]
        for filename in filenames:
            if filename.endswith(".py"):
                found.append(Path(current) / filename)
    found.sort()
    _LISTING_CACHE[root] = found
    return found


def parse_module(path: Path) -> ast.Module | None:
    """Parse a Python file into an AST module.

    Args:
        path: File to parse.

    Returns:
        The parsed module, or None when the file cannot be read or parsed.
    """
    if path in _AST_CACHE:
        return _AST_CACHE[path]
    source = read_source(path)
    module: ast.Module | None
    if source is None:
        module = None
    else:
        try:
            module = ast.parse(source)
        except SyntaxError as exc:
            module = None
            _PARSE_FAILURES.append(f"{rel(path)}:{exc.lineno or 0} {exc.msg}")
    _AST_CACHE[path] = module
    return module


def read_all_exports(init_path: Path) -> list[str] | None:
    """Read the `__all__` list declared by a package root.

    Args:
        init_path: Path to the package `__init__.py`.

    Returns:
        Exported names, or None when `__all__` is absent or not a literal.
    """
    module = parse_module(init_path)
    if module is None:
        return None
    for node in module.body:
        if not isinstance(node, ast.Assign):
            continue
        targets = [t.id for t in node.targets if isinstance(t, ast.Name)]
        if "__all__" not in targets:
            continue
        try:
            value = ast.literal_eval(node.value)
        except ValueError, TypeError:
            return None
        if isinstance(value, (list, tuple)):
            return [str(item) for item in value]
    return None


def collect_definitions(package: Path) -> dict[str, str]:
    """Map every top-level name in a package to its definition kind.

    Args:
        package: Package directory to scan.

    Returns:
        Mapping of name to one of `function`, `class`, or `constant`.
    """
    kinds: dict[str, str] = {}
    for path in iter_python_files(package):
        module = parse_module(path)
        if module is None:
            continue
        for node in module.body:
            _record_definition(node, kinds)
    return kinds


def _record_definition(node: ast.stmt, kinds: dict[str, str]) -> None:
    """Record one top-level statement into the definition map.

    Args:
        node: Top-level AST statement.
        kinds: Mutable mapping updated in place.
    """
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        kinds[node.name] = "function"
    elif isinstance(node, ast.ClassDef):
        kinds.setdefault(node.name, "class")
    elif isinstance(node, ast.Assign):
        for target in node.targets:
            if isinstance(target, ast.Name):
                kinds.setdefault(target.id, "constant")


def module_path_of(package: str) -> str:
    """Convert a repository-relative package path to a dotted module path.

    Args:
        package: Repository-relative path such as `app/services/data`.

    Returns:
        Dotted module path such as `app.services.data`.
    """
    return package.replace("/", ".")


def collect_imports(root: Path) -> list[tuple[Path, int, str, list[str]]]:
    """Collect every `from X import a, b` statement under a root.

    Args:
        root: Directory to walk.

    Returns:
        Tuples of file path, line number, imported module, and imported names.
    """
    records: list[tuple[Path, int, str, list[str]]] = []
    for path in iter_python_files(root):
        module = parse_module(path)
        if module is None:
            continue
        for node in ast.walk(module):
            if isinstance(node, ast.ImportFrom) and node.module:
                names = [alias.name for alias in node.names]
                records.append((path, node.lineno, node.module, names))
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    records.append((path, node.lineno, alias.name, []))
    return records


def rel(path: Path) -> str:
    """Render a path relative to the repository root.

    Args:
        path: Absolute path inside the repository.

    Returns:
        Repository-relative POSIX-style string.
    """
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def feature_dirs(package: Path) -> list[str]:
    """List production feature module folders inside a domain package.

    Args:
        package: Domain package directory.

    Returns:
        Sorted folder names excluding documented non-feature directories.
    """
    if not package.is_dir():
        return []
    return sorted(
        entry.name
        for entry in package.iterdir()
        if entry.is_dir() and entry.name not in NON_FEATURE_DIRS
    )


def registry_feature_ids(readme: Path) -> set[str]:
    """Extract feature IDs from the `### Feature Registry` section of a README.

    Args:
        readme: Path to the owning package README.

    Returns:
        Set of feature IDs, empty when the section is absent or unparsed.
    """
    if not readme.is_file():
        return set()
    text = read_source(readme)
    if text is None:
        return set()
    lines = text.splitlines()
    start = next(
        (i for i, line in enumerate(lines) if line.strip() == "### Feature Registry"),
        None,
    )
    if start is None:
        return set()
    section: list[str] = []
    for line in lines[start + 1 :]:
        if line.startswith(("## ", "### ")):
            break
        section.append(line)
    return set(FEATURE_ID_RE.findall("\n".join(section)))


def check_registry(package: Path) -> Finding:
    """Reconcile README-registered feature IDs against module folders.

    Args:
        package: Domain package directory.

    Returns:
        The REG finding.
    """
    readme = package / "README.md"
    if not readme.is_file():
        return Finding("REG", STATUS_FAIL, f"no README.md at {rel(package)}")
    ids = registry_feature_ids(readme)
    dirs = feature_dirs(package)
    if not ids:
        return Finding(
            "REG",
            STATUS_UNKNOWN,
            f"no parsable '### Feature Registry' IDs; {len(dirs)} module folders",
        )
    if len(ids) == len(dirs):
        return Finding("REG", STATUS_OK, f"{len(ids)} features == {len(dirs)} folders")
    return Finding(
        "REG",
        STATUS_WARN,
        f"{len(ids)} registered features != {len(dirs)} module folders",
        [f"folders: {', '.join(dirs)}"],
    )


def check_export_gate(package: Path) -> Finding:
    """Verify the package root declares `__all__`.

    Args:
        package: Domain package directory.

    Returns:
        The GATE finding.
    """
    init_path = package / "__init__.py"
    if not init_path.is_file():
        return Finding("GATE", STATUS_FAIL, "missing package root __init__.py")
    exports = read_all_exports(init_path)
    if exports is None:
        return Finding("GATE", STATUS_FAIL, "package root declares no literal __all__")
    return Finding("GATE", STATUS_OK, f"__all__ declares {len(exports)} symbols")


def check_function_only(package: Path) -> Finding:
    """Verify every exported symbol resolves to a standalone function.

    Args:
        package: Domain package directory.

    Returns:
        The FUNC finding.
    """
    exports = read_all_exports(package / "__init__.py")
    if exports is None:
        return Finding("FUNC", STATUS_NA, "no __all__ to evaluate")
    kinds = collect_definitions(package)
    offenders = [
        f"{name} -> {kinds[name]}"
        for name in exports
        if kinds.get(name) in {"class", "constant"}
    ]
    unresolved = [name for name in exports if name not in kinds]
    if offenders:
        return Finding(
            "FUNC",
            STATUS_FAIL,
            f"{len(offenders)} of {len(exports)} exports are not functions",
            offenders,
        )
    if unresolved:
        return Finding(
            "FUNC",
            STATUS_UNKNOWN,
            f"{len(unresolved)} exports unresolved by static analysis",
            unresolved,
        )
    return Finding("FUNC", STATUS_OK, f"all {len(exports)} exports are functions")


def check_deep_imports(
    domain: Domain,
    package: Path,
    imports: list[tuple[Path, int, str, list[str]]],
) -> Finding:
    """Detect imports that bypass the domain public boundary.

    Args:
        domain: Domain being audited.
        package: Domain package directory.
        imports: Repository-wide import records.

    Returns:
        The DEEP finding.
    """
    dotted = module_path_of(domain.package or "")
    prefix = f"{dotted}."
    own_root = package.resolve()
    violations: list[str] = []
    exempt = 0
    for path, lineno, module, _names in imports:
        if not module.startswith(prefix):
            continue
        resolved = path.resolve()
        if resolved == own_root or own_root in resolved.parents:
            continue
        # AGENTS.md section 1 names the in-scope consumers: production services,
        # usage examples, workflow scripts, and integration tests. Unit tests are
        # not listed and may exercise domain internals directly.
        if "unit" in rel(path).split("/"):
            exempt += 1
            continue
        violations.append(f"{rel(path)}:{lineno} -> {module}")
    suffix = f" ({exempt} unit-test imports exempt)" if exempt else ""
    if violations:
        return Finding(
            "DEEP",
            STATUS_FAIL,
            f"{len(violations)} deep cross-domain imports{suffix}",
            violations,
        )
    return Finding("DEEP", STATUS_OK, f"no deep cross-domain imports{suffix}")


def check_root_files(package: Path) -> Finding:
    """Verify no production behaviour sits at the domain package root.

    Args:
        package: Domain package directory.

    Returns:
        The ROOT finding.
    """
    offenders = sorted(
        entry.name
        for entry in package.iterdir()
        if entry.is_file()
        and entry.suffix == ".py"
        and entry.name not in ALLOWED_ROOT_FILES
    )
    if offenders:
        return Finding(
            "ROOT",
            STATUS_FAIL,
            f"{len(offenders)} disallowed root modules",
            offenders,
        )
    return Finding("ROOT", STATUS_OK, "root contains only allowed infrastructure")


def check_usage(package: Path, tests: Path) -> Finding:
    """Verify one numbered usage program exists per registered feature.

    Args:
        package: Domain package directory.
        tests: Domain test root.

    Returns:
        The USE finding.
    """
    usage_dir = tests / "usage"
    if not usage_dir.is_dir():
        return Finding("USE", STATUS_FAIL, f"missing {rel(usage_dir)}")
    # Feature programs live in `usage/features/` where that directory exists,
    # and directly in `usage/` otherwise.
    features_dir = usage_dir / "features"
    search_dir = features_dir if features_dir.is_dir() else usage_dir
    programs = sorted(
        path.name
        for path in search_dir.glob("*.py")
        if USAGE_PROGRAM_RE.match(path.name)
    )
    expected = len(registry_feature_ids(package / "README.md"))
    if not expected:
        return Finding(
            "USE", STATUS_UNKNOWN, f"{len(programs)} programs; registry unparsed"
        )
    if len(programs) == expected:
        return Finding(
            "USE", STATUS_OK, f"{len(programs)} programs == {expected} features"
        )
    return Finding(
        "USE",
        STATUS_WARN,
        f"{len(programs)} usage programs != {expected} registered features",
        programs,
    )


def check_workflow_evidence(tests: Path) -> Finding:
    """Verify workflow evidence programs and the `run_all.py` entry point.

    Args:
        tests: Domain test root.

    Returns:
        The WFE finding.
    """
    workflows_dir = tests / "usage" / "workflows"
    if not workflows_dir.is_dir():
        return Finding("WFE", STATUS_FAIL, "missing usage/workflows/")
    programs = [p for p in workflows_dir.glob("*.py") if p.name != "run_all.py"]
    has_runner = (workflows_dir / "run_all.py").is_file()
    if not has_runner:
        return Finding(
            "WFE",
            STATUS_FAIL,
            f"{len(programs)} workflow programs but no run_all.py",
        )
    return Finding(
        "WFE", STATUS_OK, f"{len(programs)} workflow programs plus run_all.py"
    )


def check_test_dir(code: str, tests: Path, subdir: str) -> Finding:
    """Verify a test subdirectory exists and contains test modules.

    Args:
        code: Check code to report.
        tests: Domain test root.
        subdir: Subdirectory name, `unit` or `integration`.

    Returns:
        The UT or IT finding.
    """
    target = tests / subdir
    if not target.is_dir():
        return Finding(code, STATUS_FAIL, f"missing {rel(target)}")
    count = len(list(target.rglob("test_*.py")))
    if count == 0:
        return Finding(code, STATUS_FAIL, f"{rel(target)} contains no test modules")
    return Finding(code, STATUS_OK, f"{count} test modules")


def load_coverage() -> dict[str, float]:
    """Read per-package line coverage from `coverage.xml` when available.

    Returns:
        Mapping of dotted package prefix to coverage percentage.
    """
    report = REPO_ROOT / "coverage.xml"
    if not report.is_file():
        return {}
    text = read_source(report)
    if text is None:
        return {}
    # Attribute-level regex rather than an XML parser: the file is generated by
    # this project's own coverage run, and avoiding an XML parser avoids the
    # untrusted-input parsing risk flagged by the linter.
    results: dict[str, float] = {}
    for match in COVERAGE_PACKAGE_RE.finditer(text):
        try:
            results[match.group("name")] = float(match.group("rate")) * 100.0
        except ValueError:
            continue
    return results


def check_coverage(domain: Domain, coverage: dict[str, float]) -> Finding:
    """Report coverage for a domain against the 80 percent floor.

    Args:
        domain: Domain being audited.
        coverage: Mapping produced by `load_coverage`.

    Returns:
        The COV finding.
    """
    if not coverage:
        return Finding(
            "COV",
            STATUS_UNKNOWN,
            "no coverage.xml (run: uv run pytest --cov --cov-report=xml)",
        )
    dotted = module_path_of(domain.package or "")
    matched = [pct for name, pct in coverage.items() if name.startswith(dotted)]
    if not matched:
        return Finding("COV", STATUS_UNKNOWN, "no coverage rows matched this package")
    average = sum(matched) / len(matched)
    status = STATUS_OK if average >= COVERAGE_FLOOR else STATUS_FAIL
    return Finding("COV", status, f"{average:.1f}% (floor {COVERAGE_FLOOR:.0f}%)")


def check_hygiene(package: Path) -> Finding:
    """Scan for bare excepts, `print` calls, and literal secret patterns.

    Args:
        package: Domain package directory.

    Returns:
        The HYG finding.
    """
    violations: list[str] = []
    for path in iter_python_files(package):
        module = parse_module(path)
        if module is not None:
            violations.extend(_hygiene_from_ast(module, path))
        violations.extend(_hygiene_from_text(path))
    if violations:
        return Finding(
            "HYG", STATUS_FAIL, f"{len(violations)} hygiene violations", violations
        )
    return Finding("HYG", STATUS_OK, "no bare except, print, or literal secrets")


def _hygiene_from_ast(module: ast.Module, path: Path) -> list[str]:
    """Find bare excepts and `print` calls in a parsed module.

    Args:
        module: Parsed AST module.
        path: Source path for reporting.

    Returns:
        Formatted violation strings.
    """
    found: list[str] = []
    for node in ast.walk(module):
        if isinstance(node, ast.ExceptHandler) and node.type is None:
            found.append(f"{rel(path)}:{node.lineno} bare except")
        elif (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "print"
        ):
            found.append(f"{rel(path)}:{node.lineno} print in application code")
    return found


def _hygiene_from_text(path: Path) -> list[str]:
    """Find literal credential assignments in a source file.

    Args:
        path: Source path to scan.

    Returns:
        Formatted violation strings.
    """
    text = read_source(path)
    if text is None:
        return []
    found: list[str] = []
    for number, line in enumerate(text.splitlines(), start=1):
        if SECRET_RE.search(line):
            found.append(f"{rel(path)}:{number} literal credential pattern")
    return found


def audit_domain(
    domain: Domain,
    imports: list[tuple[Path, int, str, list[str]]],
    coverage: dict[str, float],
) -> list[Finding]:
    """Run every Tier 1 check for one domain.

    Args:
        domain: Domain to audit.
        imports: Repository-wide import records.
        coverage: Mapping produced by `load_coverage`.

    Returns:
        Findings in canonical check order.
    """
    if domain.kind != "python" or domain.package is None:
        reason = f"{domain.kind} row; Tier 1 python checks do not apply"
        return [Finding(code, STATUS_NA, reason) for code in CHECK_ORDER]

    package = REPO_ROOT / domain.package
    if not package.is_dir():
        return [
            Finding(code, STATUS_FAIL, f"package {domain.package} not found")
            for code in CHECK_ORDER
        ]

    tests = REPO_ROOT / (domain.tests or "")
    findings = [
        check_registry(package),
        check_export_gate(package),
        check_function_only(package),
        check_deep_imports(domain, package, imports),
        check_root_files(package),
    ]
    if tests.is_dir():
        findings.append(check_usage(package, tests))
        findings.append(check_workflow_evidence(tests))
        findings.append(check_test_dir("UT", tests, "unit"))
        findings.append(check_test_dir("IT", tests, "integration"))
    else:
        missing = f"missing test root {domain.tests}"
        findings.extend(
            Finding(code, STATUS_FAIL, missing) for code in ("USE", "WFE", "UT", "IT")
        )
    findings.append(check_coverage(domain, coverage))
    findings.append(check_hygiene(package))
    return findings


def print_domain_report(domain: Domain, findings: list[Finding], verbose: bool) -> None:
    """Print one domain block of the report.

    Args:
        domain: Domain audited.
        findings: Findings for that domain.
        verbose: Whether to print individual violations.
    """
    header = f"{domain.row}. {domain.name}"
    location = domain.package or "(no package)"
    print(f"\n{header}  [{location}]")
    print("-" * 72)
    for finding in findings:
        glyph = STATUS_GLYPH.get(finding.status, "[ ?? ]")
        print(f"  {glyph} {finding.code:<5} {finding.summary}")
        if verbose and finding.details:
            for detail in finding.details[:40]:
                print(f"           - {detail}")
            remaining = len(finding.details) - 40
            if remaining > 0:
                print(f"           ... {remaining} more")


def print_parse_warning(verbose: bool) -> None:
    """Warn when source files could not be parsed by this interpreter.

    Args:
        verbose: Whether to list every failing file.
    """
    if not _PARSE_FAILURES:
        return
    version = ".".join(str(part) for part in sys.version_info[:3])
    print("\n" + "!" * 72)
    print(
        f"WARNING: {len(_PARSE_FAILURES)} files did not parse under Python {version}."
    )
    print("Results are understated and must not be recorded as evidence.")
    print("Run through the project interpreter: uv run python scripts/audit_check.py")
    print("!" * 72)
    if verbose:
        for failure in _PARSE_FAILURES[:20]:
            print(f"  - {failure}")
        remaining = len(_PARSE_FAILURES) - 20
        if remaining > 0:
            print(f"  ... {remaining} more")


def print_summary(tally: dict[str, int]) -> None:
    """Print the aggregate status tally.

    Args:
        tally: Mapping of status to occurrence count.
    """
    print("\n" + "=" * 72)
    print("TIER 1 SUMMARY")
    print("=" * 72)
    for status in (
        STATUS_OK,
        STATUS_WARN,
        STATUS_FAIL,
        STATUS_UNKNOWN,
        STATUS_NA,
    ):
        print(f"  {STATUS_GLYPH[status]} {status:<8} {tally.get(status, 0)}")
    print("\nAdvisory only. Exit code is always 0.")
    print("Record outcomes in docs/PROJECT.md section 9.1 with path:line evidence.")


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser.

    Returns:
        Configured argument parser.
    """
    parser = argparse.ArgumentParser(
        description="Tier 1 architecture conformance sweep (advisory, never fails).",
    )
    parser.add_argument(
        "--domain",
        action="append",
        default=None,
        help="Domain key to audit; repeatable. Default: all.",
    )
    parser.add_argument(
        "--check",
        action="append",
        default=None,
        help=f"Check code to run; repeatable. One of: {', '.join(CHECK_ORDER)}.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print individual violations under each check.",
    )
    return parser


def select_domains(keys: list[str] | None) -> tuple[Domain, ...]:
    """Filter the domain registry by selector keys.

    Args:
        keys: Domain keys supplied on the command line, or None for all.

    Returns:
        Selected domains in registry order.
    """
    if not keys:
        return DOMAINS
    wanted = {key.lower() for key in keys}
    return tuple(d for d in DOMAINS if d.key in wanted or d.row in wanted)


def main() -> None:
    """Run the Tier 1 sweep and print an advisory report."""
    args = build_parser().parse_args()
    domains = select_domains(args.domain)
    if not domains:
        print("No domains matched the selection.")
        sys.exit(0)

    wanted_checks = {c.upper() for c in args.check} if args.check else set(CHECK_ORDER)

    print("=" * 72)
    print("HaruQuantAI Tier 1 Architecture Conformance Sweep")
    print(f"Repository: {REPO_ROOT}")
    print("=" * 72)

    imports = (
        collect_imports(REPO_ROOT / "app")
        + collect_imports(REPO_ROOT / "tests")
        + collect_imports(REPO_ROOT / "scripts")
    )
    coverage = load_coverage()
    tally: dict[str, int] = {}

    for domain in domains:
        findings = [
            f
            for f in audit_domain(domain, imports, coverage)
            if f.code in wanted_checks
        ]
        print_domain_report(domain, findings, args.verbose)
        for finding in findings:
            tally[finding.status] = tally.get(finding.status, 0) + 1

    print_summary(tally)
    print_parse_warning(args.verbose)
    sys.exit(0)


if __name__ == "__main__":
    main()
