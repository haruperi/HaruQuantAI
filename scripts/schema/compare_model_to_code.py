"""Compare the authoritative schema model against live migration definitions.

Reports, per table, which columns the model declares that the code does not and
vice versa. Exits non-zero on any mismatch.

Run from anywhere::

    python scripts/schema/compare_model_to_code.py

Note on the constraint matcher: ``CHECK``/``UNIQUE`` must be matched with a
following ``(`` and ``PRIMARY KEY``/``FOREIGN KEY`` with the trailing keyword.
Matching the bare words against a line prefix silently swallows any column named
``check*``, ``unique*``, ``primary*`` or ``foreign*`` — a real defect that hid
eight columns from earlier comparisons.
"""

from __future__ import annotations

import pathlib
import re
import sys

_ROOT = pathlib.Path(__file__).resolve().parents[2]
_DOCS = _ROOT

_SPEC_FILES = (
    "app/utils/README.md",
    "app/services/brokers/README.md",
    "app/services/data/README.md",
    "app/services/indicators/README.md",
    "app/services/strategy/README.md",
    "app/services/risk/README.md",
    "app/services/trading/README.md",
    "app/services/simulator/README.md",
    "app/services/analytics/README.md",
    "app/services/optimization/README.md",
    "app/services/research/README.md",
    "app/services/portfolio/README.md",
    "app/agentic/README.md",
    "app/services/api/README.md",
)

# Migration definition modules whose DDL is expected to match the model.
_CODE_MODULES = (
    "app/services/trading/migrations/definitions.py",
    "app/services/risk/migrations/definitions.py",
    "app/services/portfolio/migrations/definitions.py",
    "app/services/optimization/migrations/definitions.py",
    "app/services/indicators/migrations/definitions.py",
    "app/services/analytics/migrations/definitions.py",
    "app/services/brokers/migrations/definitions.py",
    "app/services/data/migrations/core.py",
)

# Modules whose DDL is built by implicit string concatenation.
_CONCAT_MODULES = (
    ("app/services/research/migrations/definitions.py", "research_artifacts"),
    ("app/services/simulator/migrations/definitions.py", "sim_runs"),
    ("app/services/simulator/migrations/definitions.py", "sim_sessions"),
)

# Existence is a broader question than column-level conformance. The modules
# above are the ones whose DDL parses cleanly enough to diff column by column;
# these globs cover every module that creates a table at all, including the two
# Data modules that bootstrap the ledger and lock table outside it.
_CREATOR_GLOBS = ("app/services/*/migrations/*.py", "app/agentic/migrations/*.py")
_BOOTSTRAP_CREATORS = (
    "app/services/data/persistence/migrations.py",
    "app/services/data/persistence/locking.py",
)
_CREATE_NAME = re.compile(r"CREATE TABLE(?:\s+IF NOT EXISTS)?\s+(\w+)", re.IGNORECASE)
_DROP_NAME = re.compile(r"DROP TABLE(?:\s+IF EXISTS)?\s+(\w+)", re.IGNORECASE)

_CONSTRAINT = re.compile(
    r"(PRIMARY KEY|UNIQUE\s*\(|CHECK\s*\(|FOREIGN KEY)",
    re.IGNORECASE,
)


def _split_top_level(body: str) -> list[str]:
    """Split a CREATE TABLE body on commas outside parentheses.

    Splitting by line instead treats a column definition that wraps — a long
    ``CHECK`` or a ``GENERATED ALWAYS AS`` expression — as two entries, yielding
    fragments like ``)`` as column names.

    Args:
        body: Text between the table's opening and closing parenthesis.

    Returns:
        One whitespace-normalised entry per column or table constraint.
    """
    stripped_lines = []
    for line in body.split("\n"):
        # Inline `-- comment` text would otherwise merge two entries together.
        stripped_lines.append(line.split("--", 1)[0] if "--" in line else line)
    body = "\n".join(stripped_lines)
    parts: list[str] = []
    depth = 0
    current = ""
    for char in body:
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
        if char == "," and depth == 0:
            parts.append(current.strip())
            current = ""
        else:
            current += char
    if current.strip():
        parts.append(current.strip())
    return [" ".join(part.split()) for part in parts if part.strip()]


def _columns(body: str) -> set[str]:
    """Return declared column names from one CREATE TABLE body.

    Args:
        body: Text between the table's opening and closing parenthesis.

    Returns:
        Column names, excluding table-level constraint clauses.
    """
    return {
        entry.split()[0]
        for entry in _split_top_level(body)
        if not _CONSTRAINT.match(entry)
    }


def _model_tables() -> dict[str, set[str]]:
    """Return every table declared in the authoritative model.

    Returns:
        Mapping of table name to declared column names.
    """
    tables: dict[str, set[str]] = {}
    for name in _SPEC_FILES:
        text = (_DOCS / name).read_text(encoding="utf-8")
        for match in re.finditer(
            r"CREATE TABLE (\w+)\s*\((.*?)\n\) STRICT", text, re.DOTALL
        ):
            tables[match.group(1)] = _columns(match.group(2))
    return tables


def _code_tables() -> dict[str, set[str]]:
    """Return every table declared by a migration definition module.

    Returns:
        Mapping of table name to declared column names.
    """
    tables: dict[str, set[str]] = {}
    for relative in _CODE_MODULES:
        source = (_ROOT / relative).read_text(encoding="utf-8")
        create_pattern = (
            r"CREATE TABLE(?: IF NOT EXISTS)? (\w+) \((.*?)\n    \) STRICT"
            if relative == "app/services/trading/migrations/definitions.py"
            else r"CREATE TABLE IF NOT EXISTS (\w+) \((.*?)\n    \) STRICT"
        )
        for match in re.finditer(
            create_pattern,
            source,
            re.DOTALL,
        ):
            tables[match.group(1)] = _columns(match.group(2))
        for table in _DROP_NAME.findall(source):
            tables.pop(table, None)
        if relative == "app/services/trading/migrations/definitions.py":
            for source_name, target_name in re.findall(
                r'"ALTER TABLE (\w+) RENAME TO (\w+)"', source
            ):
                columns = tables.pop(source_name, None)
                if columns is not None:
                    tables[target_name] = columns
    for relative, table in _CONCAT_MODULES:
        source = (_ROOT / relative).read_text(encoding="utf-8")
        joined = "".join(re.findall(r'"([^"]*)"', source))
        table_match = re.search(
            rf"CREATE TABLE IF NOT EXISTS {table} \((.*?)\) STRICT", joined, re.DOTALL
        )
        if table_match is None:
            continue
        tables[table] = {
            entry.split()[0]
            for entry in _split_top_level(table_match.group(1))
            if not _CONSTRAINT.match(entry) and entry.split()[0].isidentifier()
        }
    return tables


def _all_created_tables() -> set[str]:
    """Return every table name any module creates.

    Returns:
        Table names declared by a CREATE TABLE statement anywhere in the tree.
    """
    names: set[str] = set()
    paths = [path for pattern in _CREATOR_GLOBS for path in _ROOT.glob(pattern)]
    paths.extend(_ROOT / relative for relative in _BOOTSTRAP_CREATORS)
    for path in paths:
        source = path.read_text(encoding="utf-8")
        names |= set(_CREATE_NAME.findall(source))
        names -= set(_DROP_NAME.findall(source))
    return names


def main() -> int:
    """Compare model and code tables and report any divergence.

    Returns:
        Zero when every conformed table matches, one otherwise.
    """
    model = _model_tables()
    code = _code_tables()
    mismatched = 0
    for table in sorted(code):
        declared = model.get(table, set())
        implemented = code[table]
        model_only = sorted(declared - implemented)
        code_only = sorted(implemented - declared)
        if model_only or code_only:
            mismatched += 1
            print(f"  {table:<34} DIFF")
            if model_only:
                print(f"       model-only: {model_only}")
            if code_only:
                print(f"       code-only : {code_only}")
        else:
            print(f"  {table:<34} MATCH")
    print(f"\n{len(code)} tables compared, {mismatched} mismatched.")

    # A table the model declares and no module creates is aspirational, not a
    # defect — most of the model is deferred Tier B work. It is still worth
    # naming, because silence here reads as agreement: four Trading tables were
    # recorded as shipped while this script reported no drift, since a table
    # absent from code is a table it never compares.
    unbuilt = sorted(set(model) - _all_created_tables())
    print(f"\n{len(unbuilt)} model tables are not created by any module:")
    for table in unbuilt:
        print(f"  {table}")
    return 1 if mismatched else 0


if __name__ == "__main__":
    sys.exit(main())
