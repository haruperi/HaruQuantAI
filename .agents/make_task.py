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
FEAT_RE = re.compile(r"FEAT-[A-Z0-9_-]+")
CHECKBOX_RE = re.compile(r"\[(?P<mark>[ xX]?)\]")
ITEM_RE = re.compile(r"^\d+\.\s+\[(?P<mark>[ xX]?)\]\s*(?P<text>.+)$")
FR_RE = re.compile(r"FR-[A-Z0-9_-]+")


def _toml_string(value: str) -> str:
    """Encode a scalar as a TOML-compatible basic string."""
    return json.dumps(value, ensure_ascii=False)


def parse_entries(path: Path) -> dict[str, dict[str, Any]]:
    """Return {entry_id: {feature, title, done, partial, is_feature, items: [...]}}."""
    entries: dict[str, dict[str, Any]] = {}
    current: dict[str, Any] | None = None
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
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


def _entry_sort_key(eid: str) -> list[int | str]:
    parts: list[int | str] = []
    for p in eid.split("."):
        try:
            parts.append(int(p))
        except ValueError:
            parts.append(p)
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
        req_summary = (
            ", ".join(fr_ids)
            if fr_ids
            else "; ".join(it["text"] for it in entry["items"])
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
        req_summary = (
            "; ".join(item_texts) if item_texts else f"Implement {clean_title}."
        )
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


def main() -> int:
    """Parse CLI arguments and generate the task spec file.

    Returns:
        Process exit code (0 on success).
    """
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("entry", nargs="?", help="entry id, e.g. 1.01 or 1.1")
    parser.add_argument(
        "--file",
        default="docs/dev/IMPLEMENTATION_ORDER.md",
        help="implementation tracker (default: docs/dev/IMPLEMENTATION_ORDER.md)",
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
