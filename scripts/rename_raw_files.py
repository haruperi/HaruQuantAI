"""Rename raw market-data CSVs by stripping the legacy export postfix.

Files such as ``EURJPY_M1-M1-Forex_247.csv`` are renamed to
``EURJPY_M1.csv``: the ``-M1-Forex_247`` postfix carries no information the
filename does not already express. Renames never overwrite an existing file
and never cross directory boundaries.

Usage:
    uv run python scripts/rename_raw_files.py           # dry run (default)
    uv run python scripts/rename_raw_files.py --apply   # perform renames
"""

from __future__ import annotations

import argparse
from pathlib import Path

_POSTFIX = "-M1-Forex_247.csv"


def main() -> None:
    """Rename ``*-M1-Forex_247.csv`` files under ``data/raw``."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Perform the renames; without it, only print the plan.",
    )
    parser.add_argument(
        "--directory",
        type=Path,
        default=Path("data/raw"),
        help="Directory containing the raw CSV files (default: data/raw).",
    )
    args = parser.parse_args()

    directory = args.directory
    matches = sorted(directory.glob(f"*{_POSTFIX}"))
    if not matches:
        print(f"No files matching *{_POSTFIX} in {directory}")
        return

    renamed = 0
    for path in matches:
        target = path.with_name(path.name[: -len(_POSTFIX)] + ".csv")
        if target.exists():
            print(f"SKIP (target exists): {path.name} -> {target.name}")
            continue
        action = "RENAME" if args.apply else "DRY-RUN"
        print(f"{action}: {path.name} -> {target.name}")
        if args.apply:
            path.rename(target)
            renamed += 1

    print(
        f"\n{renamed if args.apply else len(matches)} file(s) "
        f"{'renamed' if args.apply else 'planned'}."
    )


if __name__ == "__main__":
    main()
