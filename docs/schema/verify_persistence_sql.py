"""Verify that every table named in persistence SQL is actually created.

Persistence modules issue SQL as string constants. Nothing in the type system,
the linter, or the test suite connects those strings to the ``CREATE TABLE``
statements in the migration modules, so a table renamed in a migration and
missed in one ``UPDATE`` statement stays invisible until the statement runs
against a real database.

That is not hypothetical. Renaming ``hq_runtime_records`` to
``data_runtime_records`` updated the migration but not the ten statements in
``create.py``, ``read.py`` and ``update.py`` that read the table. Every one
would have failed on first apply, for Trading, Risk, Portfolio, Simulator and
Agentic alike, since all five persist through that store. This check exists so
the next such rename fails here instead.

Run from anywhere::

    python docs/schema/verify_persistence_sql.py

Exits non-zero when a referenced table has no creating statement.
"""

from __future__ import annotations

import pathlib
import re
import sys

_ROOT = pathlib.Path(__file__).resolve().parents[2]

# Every module that may create a table: the ledger-managed migration modules,
# plus the two Data modules that bootstrap the ledger and the write-lock table
# themselves and therefore cannot be ledger-managed without a cycle.
_CREATOR_GLOBS = (
    "app/services/*/migrations/*.py",
    "app/agentic/migrations/*.py",
)
_BOOTSTRAP_CREATORS = (
    "app/services/data/persistence/migrations.py",
    "app/services/data/persistence/locking.py",
)

# Every module that may issue SQL against those tables.
_CONSUMER_GLOBS = (
    "app/services/*/persistence/*.py",
    "app/agentic/*/*.py",
)

_CREATE = re.compile(r"CREATE TABLE(?:\s+IF NOT EXISTS)?\s+(\w+)", re.IGNORECASE)

# String literals, longest form first so a triple-quoted body is not shredded
# into fragments by the single-quoted alternatives.
_LITERAL = re.compile(
    r'"""(.*?)"""|\'\'\'(.*?)\'\'\'|"([^"\n]*)"|\'([^\'\n]*)\'', re.DOTALL
)

# Deliberately case-sensitive. Docstring prose opens with sentence case
# ("Select participants from enabled roles"), SQL constants in this codebase
# open with an uppercase keyword. Matching case-insensitively here reclassifies
# docstrings as SQL and reports words like "it" and "enabled" as missing tables.
_SQL_START = re.compile(r"^\s*(SELECT|INSERT\s+INTO|UPDATE|DELETE\s+FROM|CREATE)\b")

_TABLE_REF = re.compile(r"\b(?:FROM|INTO|UPDATE|JOIN)\s+([a-z_][a-z0-9_]*)")


def _created_tables() -> set[str]:
    """Return every table name some module creates.

    Returns:
        Table names declared by a CREATE TABLE statement anywhere in the tree.
    """
    names: set[str] = set()
    paths = [path for pattern in _CREATOR_GLOBS for path in _ROOT.glob(pattern)]
    paths.extend(_ROOT / relative for relative in _BOOTSTRAP_CREATORS)
    for path in paths:
        names |= set(_CREATE.findall(path.read_text(encoding="utf-8")))
    return names


def _referenced_tables() -> dict[str, set[str]]:
    """Return every table name referenced from a SQL string literal.

    Returns:
        Mapping of referenced table name to the files referencing it.
    """
    references: dict[str, set[str]] = {}
    paths = sorted(path for pattern in _CONSUMER_GLOBS for path in _ROOT.glob(pattern))
    for path in paths:
        source = path.read_text(encoding="utf-8")
        relative = path.relative_to(_ROOT).as_posix()
        for literal in _LITERAL.finditer(source):
            text = next((group for group in literal.groups() if group), "")
            if not _SQL_START.match(text):
                continue
            for reference in _TABLE_REF.finditer(text):
                references.setdefault(reference.group(1), set()).add(relative)
    return references


def main() -> int:
    """Report any persistence SQL naming a table nothing creates.

    Returns:
        Zero when every reference resolves, one otherwise.
    """
    created = _created_tables()
    referenced = _referenced_tables()
    unresolved = {
        name: files for name, files in referenced.items() if name not in created
    }
    print(f"tables created: {len(created)}")
    print(f"tables referenced from SQL literals: {len(referenced)}")
    if unresolved:
        print(f"\nUNRESOLVED {len(unresolved)}:")
        for name, files in sorted(unresolved.items()):
            print(f"  {name}")
            for file in sorted(files):
                print(f"       {file}")
        print("\nFAIL")
        return 1
    print("\nPASS: every referenced table has a creating statement")
    return 0


if __name__ == "__main__":
    sys.exit(main())
