#!/usr/bin/env python3
"""Project reviewed feature evidence into current repository ledgers."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import tempfile
from pathlib import Path
from typing import Any, Final

from scripts import generate_phase0_evidence

REPO: Final[Path] = Path(__file__).resolve().parent.parent
PLAN_PATH: Final[Path] = REPO / "docs/dev/Phased_Feature_Implementation_Plan.md"
CURRENT_PROJECTION_PATHS: Final[tuple[str, ...]] = (
    "docs/dev/evidence/feature-baseline.json",
    "docs/dev/evidence/path-bindings.json",
    "docs/dev/evidence/usage-bindings.json",
    "docs/dev/evidence/requirement-status.json",
    "docs/dev/evidence/contract-bindings.json",
)
REVIEW_STOP = "STOPPED : REVIEWER"


class ProjectionError(RuntimeError):
    """Raised when evidence cannot be projected without inventing completion."""


def _load_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        message = f"Invalid JSON input: {path}"
        raise ProjectionError(message) from exc
    if not isinstance(value, dict):
        message = f"JSON input must be an object: {path}"
        raise ProjectionError(message)
    return value


def _sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _render(payload: dict[str, Any]) -> bytes:
    return (json.dumps(payload, indent=2, ensure_ascii=False) + "\n").encode()


def current_projection_payloads(*, plan_text: str | None = None) -> dict[str, bytes]:
    """Build only live projections, never pinned Phase-0 source snapshots.

    Returns:
        Repository-relative current-projection bytes.
    """
    payloads = generate_phase0_evidence.build_payloads(plan_text=plan_text)
    return {
        relative: _render(payloads[REPO / relative])
        for relative in CURRENT_PROJECTION_PATHS
    }


def _expected_requirement_ids(packet: dict[str, Any]) -> set[str]:
    return {
        str(item.get("requirement_id", item.get("id", "")))
        for item in [
            *packet.get("requirements", []),
            *packet.get("local_nfrs", []),
        ]
        if str(item.get("requirement_id", item.get("id", "")))
    }


def _validate_receipt(receipt: dict[str, Any]) -> None:
    if (
        receipt.get("receipt_kind") != "controller-validation-receipt"
        or receipt.get("producer") != "haruquant-workflow-controller"
    ):
        raise ProjectionError("Validation receipt provenance is invalid.")
    results = receipt.get("results")
    if not isinstance(results, list) or not results:
        raise ProjectionError("Validation receipt has no results.")
    if any(
        not isinstance(item, dict) or item.get("exit_code") != 0 for item in results
    ):
        raise ProjectionError("Validation receipt contains failed results.")


def _validate_final_shape(final: dict[str, Any]) -> None:
    """Validate the schema-critical acceptance shape before publication.

    Raises:
        ProjectionError: If any required acceptance field is malformed.
    """
    if not re.fullmatch(r"FEAT-[A-Z0-9_-]+", str(final.get("feature_id", ""))):
        raise ProjectionError("Acceptance feature identity is malformed.")
    if not re.fullmatch(r"\d+\.\d+", str(final.get("task_id", ""))):
        raise ProjectionError("Acceptance Task identity is malformed.")
    if not re.fullmatch(r"[a-f0-9]{40}", str(final.get("baseline_commit", ""))):
        raise ProjectionError("Acceptance baseline commit is malformed.")
    owner = str(final.get("owner_specification", ""))
    if not re.fullmatch(r"(?:app|docs)/.+README\.md", owner):
        raise ProjectionError("Acceptance owner specification is malformed.")
    catalogue = final.get("catalogue_entries")
    if not isinstance(catalogue, list) or any(
        not isinstance(item, str) or not item for item in catalogue
    ):
        raise ProjectionError("Acceptance catalogue entries are malformed.")
    required_stages = {
        "contract",
        "provider",
        "composition",
        "interfaces",
        "ui",
        "end_to_end",
    }
    if set(final.get("stages", {})) != required_stages:
        raise ProjectionError("Acceptance stage inventory is incomplete.")


def _final_acceptance(  # noqa: C901, PLR0912
    packet: dict[str, Any],
    draft: dict[str, Any],
    reviewer_text: str,
    receipt: dict[str, Any],
    *,
    run_id: str,
    receipt_sha256: str,
) -> dict[str, Any]:
    identity = packet.get("identity", {})
    if draft.get("feature_id") != identity.get("feature_id"):
        raise ProjectionError("Acceptance draft feature identity differs from packet.")
    if str(draft.get("task_id")) != str(identity.get("task_id")):
        raise ProjectionError("Acceptance draft Task identity differs from packet.")
    if draft.get("status") != "IN_PROGRESS":
        raise ProjectionError("A new acceptance draft must remain IN_PROGRESS.")
    review = draft.get("review")
    if not isinstance(review, dict) or review.get("reviewer_verdict") != "PENDING":
        raise ProjectionError("Acceptance draft must not pre-approve review.")
    handoffs = re.findall(r"(?m)^HANDOFF\s*:\s*(\S+)\s*$", reviewer_text)
    if (
        REVIEW_STOP not in reviewer_text
        or not handoffs
        or handoffs[-1] != "PENDING_COMMIT"
    ):
        raise ProjectionError("Reviewer has not produced PENDING_COMMIT.")
    _validate_receipt(receipt)

    requirements = draft.get("requirements")
    if not isinstance(requirements, list):
        raise ProjectionError("Acceptance draft requirements are missing.")
    by_id = {
        str(item.get("id", "")): item for item in requirements if isinstance(item, dict)
    }
    if len(by_id) != len(requirements) or "" in by_id:
        raise ProjectionError(
            "Acceptance requirement identities are duplicated or empty."
        )
    missing = sorted(_expected_requirement_ids(packet) - set(by_id))
    if missing:
        message = f"Acceptance draft omits requirements: {missing}"
        raise ProjectionError(message)
    for requirement_id in sorted(_expected_requirement_ids(packet)):
        item = by_id[requirement_id]
        if (
            item.get("status") != "PASS"
            or not str(item.get("evidence_target", "")).strip()
        ):
            message = f"Requirement lacks passing explicit evidence: {requirement_id}"
            raise ProjectionError(message)
    if any(
        item.get("status") != "PASS" or not str(item.get("evidence_target", "")).strip()
        for item in by_id.values()
    ):
        raise ProjectionError("Acceptance contains non-passing supplemental evidence.")
    commands = draft.get("commands")
    if (
        not isinstance(commands, list)
        or not commands
        or any(
            not isinstance(item, dict) or item.get("exit_code") != 0
            for item in commands
        )
    ):
        raise ProjectionError("Acceptance draft contains missing or failed commands.")
    stages = draft.get("stages")
    if not isinstance(stages, dict):
        raise ProjectionError("Acceptance draft stages are missing.")
    for name, stage in stages.items():
        if not isinstance(stage, dict) or stage.get("status") not in {
            "PASS",
            "NOT_APPLICABLE",
            "WAIVED",
        }:
            message = f"Acceptance stage is not qualified: {name}"
            raise ProjectionError(message)
        if not str(stage.get("evidence", "")).strip():
            message = f"Acceptance stage has no evidence: {name}"
            raise ProjectionError(message)

    final = dict(draft)
    final["status"] = "ACCEPTED"
    final["acceptance_commit"] = f"task-closeout:{run_id}"
    final["review"] = {
        "reviewer_verdict": "APPROVED",
        "reviewer_notes": (
            "Deterministic projection of Reviewer PENDING_COMMIT; reviewer journal "
            f"SHA-256 {_sha_bytes(reviewer_text.encode())}."
        ),
    }
    final["validation_receipt_sha256"] = receipt_sha256
    _validate_final_shape(final)
    return final


def _updated_plan(plan_text: str, packet: dict[str, Any], *, run_id: str) -> str:
    task_id = re.escape(str(packet["identity"]["task_id"]))
    header = re.search(rf"(?m)^### - \[[ xX]\] Task {task_id}\b.*$", plan_text)
    if not header:
        raise ProjectionError("Task card is missing from the implementation plan.")
    next_header = re.search(r"(?m)^### - \[", plan_text[header.end() :])
    end = header.end() + next_header.start() if next_header else len(plan_text)
    section = plan_text[header.start() : end]
    section = re.sub(r"(?m)^### - \[[ xX]\]", "### - [x]", section, count=1)
    section, status_count = re.subn(
        r"(?m)^\*\*Status:\*\* `[^`]+`",
        "**Status:** `COMPLETE`",
        section,
        count=1,
    )
    section, commit_count = re.subn(
        r"(?m)^\*\*Accepted commit:\*\*.*$",
        (
            f"**Accepted commit:** `task-closeout:{run_id}` · reviewed evidence "
            "projected deterministically; exact Git identities live in the "
            "close-out receipt."
        ),
        section,
        count=1,
    )
    if status_count != 1 or commit_count != 1:
        raise ProjectionError("Task card status/accepted-commit fields are ambiguous.")
    return plan_text[: header.start()] + section + plan_text[end:]


def build_feature_projection(
    *,
    packet_path: Path,
    acceptance_path: Path,
    reviewer_journal_path: Path,
    validation_receipt_path: Path,
    run_id: str,
    repo: Path = REPO,
) -> dict[str, bytes]:
    """Build every final projection byte string without repository mutation.

    Returns:
        Exact repository-relative bytes for transactional publication.
    """
    packet = _load_object(packet_path)
    draft = _load_object(acceptance_path)
    receipt = _load_object(validation_receipt_path)
    reviewer_text = reviewer_journal_path.read_text(encoding="utf-8")
    receipt_sha256 = _sha_bytes(validation_receipt_path.read_bytes())
    final_acceptance = _final_acceptance(
        packet,
        draft,
        reviewer_text,
        receipt,
        run_id=run_id,
        receipt_sha256=receipt_sha256,
    )
    plan_path = repo / "docs/dev/Phased_Feature_Implementation_Plan.md"
    plan_text = plan_path.read_text(encoding="utf-8")
    updated_plan = _updated_plan(plan_text, packet, run_id=run_id)
    outputs = current_projection_payloads(plan_text=updated_plan)
    outputs[acceptance_path.relative_to(repo).as_posix()] = _render(final_acceptance)
    outputs[plan_path.relative_to(repo).as_posix()] = updated_plan.encode()
    return outputs


def apply_outputs(outputs: dict[str, bytes], *, repo: Path = REPO) -> None:
    """Validate and replace an exact output set with rollback on failure.

    Raises:
        OSError: If output staging, replacement, or rollback fails.
    """
    originals: dict[str, bytes | None] = {
        relative: (repo / relative).read_bytes()
        if (repo / relative).is_file()
        else None
        for relative in outputs
    }
    with tempfile.TemporaryDirectory(prefix="hq-evidence-") as temp_name:
        temp = Path(temp_name)
        for relative, content in outputs.items():
            staged = temp / relative
            staged.parent.mkdir(parents=True, exist_ok=True)
            staged.write_bytes(content)
        try:
            for relative in sorted(outputs):
                target = repo / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                Path(temp / relative).replace(target)
        except OSError:
            for relative, original_content in originals.items():
                target = repo / relative
                if original_content is None:
                    target.unlink(missing_ok=True)
                else:
                    target.write_bytes(original_content)
            raise


def check_outputs(outputs: dict[str, bytes], *, repo: Path = REPO) -> list[str]:
    """Return every output whose current bytes differ from the projection."""
    return [
        relative
        for relative, content in sorted(outputs.items())
        if not (repo / relative).is_file() or (repo / relative).read_bytes() != content
    ]


def _request_outputs(path: Path | None) -> dict[str, bytes]:
    if path is None:
        raise ProjectionError("--request is required for feature projection.")
    request = _load_object(path)
    return build_feature_projection(
        packet_path=Path(str(request["packet_path"])),
        acceptance_path=Path(str(request["acceptance_path"])),
        reviewer_journal_path=Path(str(request["reviewer_journal_path"])),
        validation_receipt_path=Path(str(request["validation_receipt_path"])),
        run_id=str(request["run_id"]),
    )


def main() -> int:
    """Run projection discovery, preview, checking, or application.

    Returns:
        Process exit status.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--list-outputs", action="store_true")
    mode.add_argument("--preview", action="store_true")
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--apply", action="store_true")
    mode.add_argument("--check-all", action="store_true")
    parser.add_argument("--request", type=Path)
    parser.add_argument("--current-only", action="store_true")
    args = parser.parse_args()
    if args.list_outputs:
        for relative in (
            *CURRENT_PROJECTION_PATHS,
            PLAN_PATH.relative_to(REPO).as_posix(),
        ):
            print(relative)
        print("docs/dev/evidence/features/<FEATURE_ID>/acceptance.json")
        return 0
    try:
        outputs = (
            current_projection_payloads()
            if args.current_only or args.check_all
            else _request_outputs(args.request)
        )
    except (KeyError, OSError, ProjectionError, TypeError, ValueError) as exc:
        print(f"[FAIL] evidence projection: {exc}")
        return 1
    drift = check_outputs(outputs)
    if args.preview:
        print(
            json.dumps(
                {
                    "outputs": sorted(outputs),
                    "changed": drift,
                    "sha256": {
                        key: _sha_bytes(value) for key, value in sorted(outputs.items())
                    },
                },
                indent=2,
            )
        )
        return 0
    if args.apply:
        apply_outputs(outputs)
        print(f"[OK] applied {len(outputs)} deterministic evidence outputs")
        return 0
    if drift:
        print("[FAIL] current evidence projection drift:")
        for relative in drift:
            print(f"  - {relative}")
        return 1
    print(f"[OK] {len(outputs)} current evidence projections are current")
    return 0


if __name__ == "__main__":
    sys.exit(main())
