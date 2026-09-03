#!/usr/bin/env python3
"""Generate .agents/task.toml from an implementation-order entry.

Parses tracker entries (both `FEAT-...` features and non-feature tasks)
and their requirement checkboxes (`[ ]`, `[]`, `[x]`, `[X]`), then writes a
ready-to-run task spec wired to the tracker entry.

Usage:
    python .agents/make_task.py --list      # show open entries
    python .agents/make_task.py 1.01        # write spec for foundation task
    python .agents/make_task.py 1.1         # write spec for feature
    python .agents/make_task.py 2.8 --out other.toml
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

AGENTS_DIR = Path(__file__).resolve().parent
REPO = AGENTS_DIR.parent

ENTRY_RE = re.compile(
    r"^(?:#####|####)\s+(?:Foundation task\s+)?(?P<entry_id>\d+\.[\w.-]+|\d+)\s*"
    r"(?P<rest>.*)$"
)
TABLE_ENTRY_ID_RE = re.compile(r"^(?:P\.\d+|\d+(?:\.[A-Za-z0-9_-]+)*)$")
TABLE_STATUSES = frozenset({"complete", "partial", "pending"})
FEAT_RE = re.compile(r"FEAT-[A-Z0-9_-]+")
CHECKBOX_RE = re.compile(r"\[(?P<mark>[ xX]?)\]")
ITEM_RE = re.compile(r"^\d+\.\s+\[(?P<mark>[ xX]?)\]\s*(?P<text>.+)$")
FR_RE = re.compile(r"FR-[A-Z0-9_-]+")


def _toml_string(value: str) -> str:
    """Encode a scalar as a TOML-compatible basic string."""
    return json.dumps(value, ensure_ascii=False)


def _parse_table_entry(line: str) -> dict[str, Any] | None:
    """Parse one current implementation-order Markdown table row."""
    if not line.startswith("|"):
        return None
    cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
    if len(cells) < 3 or not TABLE_ENTRY_ID_RE.fullmatch(cells[0]):
        return None
    status = cells[1].casefold()
    if status not in TABLE_STATUSES:
        return None
    row_text = " | ".join(cells[2:])
    feat_m = FEAT_RE.search(row_text)
    feature = feat_m.group(0) if feat_m else None
    title_cell = cells[3] if feature and len(cells) > 3 else cells[2]
    title = title_cell.strip("` \t") or (feature or f"Task {cells[0]}")
    return {
        "entry_id": cells[0],
        "feature": feature,
        "title": title,
        "done": status == "complete",
        "partial": status == "partial",
        "is_feature": feature is not None,
        "items": [],
        "source_format": "table",
        "tracker_summary": row_text,
    }


def parse_entries(path: Path) -> dict[str, dict[str, Any]]:
    """Return {entry_id: {feature, title, done, partial, is_feature, items: [...]}}."""
    entries: dict[str, dict[str, Any]] = {}
    current: dict[str, Any] | None = None
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        table_entry = _parse_table_entry(line)
        if table_entry is not None:
            entry_id = str(table_entry["entry_id"])
            entries[entry_id] = table_entry
            current = table_entry
            continue
        match = ENTRY_RE.match(line)
        if match:
            entry_id = match.group("entry_id")
            rest = match.group("rest")
            feat_m = FEAT_RE.search(rest)
            cb_m = CHECKBOX_RE.search(rest)
            mark = cb_m.group("mark") if cb_m else ""
            partial = "partial" in rest.lower()
            feature = feat_m.group(0) if feat_m else None

            title = rest
            if cb_m:
                title = title.replace(cb_m.group(0), "")
            title = re.sub(
                r"Partial\s*[\u2014\u2013-]\s*", "", title, flags=re.IGNORECASE
            )
            title = title.strip("` \t\u2014\u2013-")

            current = {
                "entry_id": entry_id,
                "feature": feature,
                "title": title or (feature or f"Task {entry_id}"),
                "done": mark.lower() == "x",
                "partial": partial,
                "is_feature": feature is not None,
                "items": [],
            }
            entries[entry_id] = current
            continue

        item_m = ITEM_RE.match(line)
        if item_m and current is not None:
            imark = item_m.group("mark")
            text = item_m.group("text").strip()
            fr_m = FR_RE.search(text)
            fr_id = fr_m.group(0) if fr_m else None
            current["items"].append(
                {
                    "text": text,
                    "fr_id": fr_id,
                    "done": imark.lower() == "x",
                }
            )
        elif line.startswith("#"):
            current = None
    return entries


def is_entry_complete(entry: dict[str, Any]) -> bool:
    """Return whether the tracker entry or its complete requirement slice is done."""
    if bool(entry.get("done")):
        return True
    items = entry.get("items", [])
    return bool(items) and all(bool(item.get("done")) for item in items)


def _entry_sort_key(eid: str) -> list[tuple[int, int, str]]:
    parts: list[tuple[int, int, str]] = []
    for p in eid.split("."):
        try:
            parts.append((0, int(p), ""))
        except ValueError:
            if p.upper() == "P":
                parts.append((-1, 0, p))
            else:
                parts.append((1, 0, p))
    return parts


def _build_task_spec(
    entry_id: str, entry: dict[str, Any], tracker_file: str
) -> tuple[str, str, list[str]]:
    """Build task spec body, display label, and item previews.

    Returns:
        Tuple of (TOML body text, display label, preview strings for CLI output).
    """
    is_feature = entry["is_feature"]
    partial = entry["partial"]
    title = entry["title"]
    partial_note = (
        "This is a Partial slice: implement ONLY the listed requirement slice."
        if partial
        else ""
    )

    if is_feature:
        task_kind = "feature"
        feature = entry["feature"]
        task_id = feature
        name_part = feature.split("-", 2)[-1]
        task_slug = name_part.lower().replace("_", "-")
        task_name = name_part.replace("_", " ").title()
        fr_ids = [it["fr_id"] for it in entry["items"] if it.get("fr_id")]
        if fr_ids:
            req_summary = ", ".join(fr_ids)
        elif entry["items"]:
            req_summary = "; ".join(it["text"] for it in entry["items"])
        else:
            req_summary = (
                "satisfy the exact scope, disposition, evidence, and donor-bundle "
                "lifecycle declared by the matching tracker table row"
            )
        task_request = (
            f"Implement entry {entry_id} {feature} from {tracker_file}: "
            f"{req_summary}. "
            "Follow the owning README as the sole feature/FR registry and AGENTS.md"
            " for all workflow rules. Mark the tracker entry complete with evidence"
            " when every gate passes."
            f"{' ' + partial_note if partial_note else ''}"
        )
        label = feature
    else:
        task_kind = "task"
        task_id = f"TASK-{entry_id}"
        clean_title = re.sub(
            r"^Foundation\s+task\s*[\u2014\u2013-]\s*", "", title, flags=re.IGNORECASE
        )
        slug_candidate = re.sub(r"[^a-z0-9]+", "-", clean_title.lower()).strip("-")
        task_slug = slug_candidate or f"task-{entry_id.replace('.', '-')}"
        task_name = clean_title or f"Task {entry_id}"
        item_texts = [it["text"] for it in entry["items"]]
        if item_texts:
            req_summary = "; ".join(item_texts)
        elif entry.get("source_format") == "table":
            req_summary = (
                "satisfy the exact gate, evidence, disposition, and donor-bundle "
                "lifecycle declared by the matching tracker table row"
            )
        else:
            req_summary = f"Implement {clean_title}."
        task_request = (
            f"Implement entry {entry_id} ({task_name}) from {tracker_file}: "
            f"{req_summary}. Follow AGENTS.md for all workflow rules."
            " Mark the tracker entry complete with evidence when every gate passes."
            f"{' ' + partial_note if partial_note else ''}"
        )
        label = f"{task_id} ({task_name})"

    body = f"""\
# Generated by .agents/make_task.py from the configured tracker entry.
# Edit freely before running; this file is scratch (gitignored).

task_kind = {_toml_string(task_kind)}
task_id = {_toml_string(task_id)}
task_slug = {_toml_string(task_slug)}
task_name = {_toml_string(task_name)}
task_request = {_toml_string(task_request)}
additional_context = {_toml_string("Owning README is the acceptance authority.")}
exclusions = {_toml_string("No unrelated features; no scope beyond the listed requirements.")}
owner_execution_notes = {_toml_string("None")}
review_focus = {_toml_string("None")}
implementation_file = {_toml_string(tracker_file)}
implementation_entry = {_toml_string(entry_id)}
"""
    previews = [it["fr_id"] or it["text"][:50] for it in entry["items"][:5]]
    return body, f"[{task_kind}] {label}", previews


# Public reusable alias; retain the established private API for compatibility.
build_task_spec = _build_task_spec


def main() -> int:
    """Parse CLI arguments and generate the task spec file.

    Returns:
        Process exit code (0 on success).
    """
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("entry", nargs="?", help="entry id, e.g. 1.01 or 1.1")
    parser.add_argument(
        "--file",
        default="tracker.md",
        help="implementation tracker (default: tracker.md)",
    )
    parser.add_argument(
        "--out",
        default=str(AGENTS_DIR / "task.toml"),
        help="output path (default: .agents/task.toml)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="generate even if the entry is already complete",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="list open entries and exit",
    )
    args = parser.parse_args()

    tracker = (REPO / args.file).resolve()
    if not tracker.exists():
        print(f"[FAIL] tracker not found: {tracker}")
        return 1
    entries = parse_entries(tracker)

    if args.list or not args.entry:
        open_entries = [
            (eid, e)
            for eid, e in sorted(entries.items(), key=lambda x: _entry_sort_key(x[0]))
            if not e["done"]
            and (not e["items"] or not all(it["done"] for it in e["items"]))
        ]
        for eid, e in open_entries[:25]:
            state = "Partial" if e["partial"] else ""
            kind = "feature" if e["is_feature"] else "task"
            label = e["feature"] or e["title"]
            print(f"  {eid:5} [{len(e['items'])} items] [{kind:7}] {state:8} {label}")
        print(f"({len(open_entries)} open entries in {args.file})")
        return 0

    entry = entries.get(args.entry)
    if entry is None:
        print(f"[FAIL] entry {args.entry!r} not found in {tracker}; use --list")
        return 1
    if entry["done"] and not args.force:
        label = entry["feature"] or entry["title"]
        print(
            f"[FAIL] entry {args.entry} ({label}) is already complete; "
            "use --force to regenerate anyway."
        )
        return 1

    body, label, previews = _build_task_spec(args.entry, entry, args.file)
    out_path = Path(args.out)
    out_path.write_text(body, encoding="utf-8")
    print(f"[ok] wrote {out_path} for {args.entry} {label}")
    if previews:
        print(f"     Items: {', '.join(previews)}")
    else:
        print("     Items: (none parsed)")
    print("     next: activate this task through the current orchestrator")
    print(f'     chat: "Activate and run the task defined in {out_path}."')
    print(f"     CLI:  uv run .agents/orchestrator.py start --task-file {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
