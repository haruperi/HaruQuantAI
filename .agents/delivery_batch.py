#!/usr/bin/env python3
"""Conservative preparation and qualification records for DT-09 batches."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Final, cast

from validation_receipts import candidate_fingerprint, create_validation_receipt

BATCH_SCHEMA_VERSION: Final[int] = 1


class DeliveryBatchError(RuntimeError):
    """Raised when a proposed delivery batch is unsafe or incomplete."""


def prepare_batch(
    *,
    batch_id: str,
    baseline: str,
    packets: list[dict[str, Any]],
) -> dict[str, Any]:
    """Freeze a two/three-member batch after conservative packet checks."""
    if len(packets) not in {2, 3}:
        raise DeliveryBatchError(
            "A delivery batch requires exactly two or three packets."
        )
    feature_ids = [
        str(item.get("identity", {}).get("feature_id", "")) for item in packets
    ]
    if not all(feature_ids) or len(set(feature_ids)) != len(feature_ids):
        raise DeliveryBatchError("Batch feature identities must be present and unique.")
    selected_tasks = {
        str(item.get("identity", {}).get("task_id", "")) for item in packets
    }
    leased: set[str] = set()
    packet_hashes: dict[str, str] = {}
    for packet, feature_id in zip(packets, feature_ids, strict=True):
        identity = packet.get("identity", {})
        if identity.get("baseline_commit") != baseline:
            raise DeliveryBatchError(f"Stale packet baseline for {feature_id}.")
        if packet.get("status") == "BLOCKED" or packet.get("unresolved_decisions"):
            raise DeliveryBatchError(f"Packet is not stable for {feature_id}.")
        tier = str(packet.get("risk", {}).get("tier", "CRITICAL"))
        if tier not in {"ROUTINE", "STANDARD"}:
            raise DeliveryBatchError(
                f"Critical feature cannot be batched: {feature_id}."
            )
        shared = {
            str(value)
            for key in (
                "controller_projection_paths",
                "serialized_integration_write_paths",
            )
            for value in packet.get(key, [])
        }
        paths = {
            str(value) for value in packet.get("authorized_write_paths", [])
        } - shared
        overlap = sorted(leased & paths)
        if overlap:
            raise DeliveryBatchError(f"Exclusive path collision: {overlap}")
        leased.update(paths)
        for constraint in packet.get("dependencies", {}).get(
            "schedule_constraints", []
        ):
            predecessor = str(constraint.get("predecessor", ""))
            if predecessor in selected_tasks:
                raise DeliveryBatchError(
                    f"Batch member depends on unaccepted member {predecessor}."
                )
        raw = json.dumps(packet, sort_keys=True, separators=(",", ":"))
        packet_hashes[feature_id] = hashlib.sha256(raw.encode()).hexdigest()
    return {
        "schema_version": BATCH_SCHEMA_VERSION,
        "batch_id": batch_id,
        "baseline": baseline,
        "feature_ids": feature_ids,
        "task_packet_sha256": packet_hashes,
        "status": "PREPARED",
        "shared_preparation_only": True,
        "independent_task_acceptance_required": True,
        "shared_integration_paths": sorted(
            {
                str(value)
                for packet in packets
                for key in (
                    "controller_projection_paths",
                    "serialized_integration_write_paths",
                )
                for value in packet.get(key, [])
            }
        ),
    }


def qualify_batch(
    batch: dict[str, Any],
    *,
    accepted_children: list[dict[str, Any]],
    candidate: str,
    validation_receipt: Path,
) -> dict[str, Any]:
    """Record one exact combined gate after every constituent is accepted."""
    expected = list(batch.get("feature_ids", []))
    actual = [
        str(item.get("feature_id") or item.get("task_id")) for item in accepted_children
    ]
    if actual != expected or any(
        item.get("status") != "ACCEPTED" for item in accepted_children
    ):
        raise DeliveryBatchError(
            "Every ordered batch member must be independently accepted."
        )
    if not validation_receipt.is_file():
        raise DeliveryBatchError("Combined integration receipt is missing.")
    throughput_values: list[dict[str, Any]] = [
        cast("dict[str, Any]", item.get("throughput"))
        for item in accepted_children
        if isinstance(item.get("throughput"), dict)
    ]

    def total(field: str) -> float | None:
        if len(throughput_values) != len(accepted_children):
            return None
        return sum(float(item.get(field, 0.0)) for item in throughput_values)

    result = dict(batch)
    result.update(
        {
            "candidate": candidate,
            "constituent_commits": [
                {
                    "feature_id": feature,
                    "task_commit": child.get("task_commit"),
                    "merge_commit": child.get("merge_commit"),
                }
                for feature, child in zip(expected, accepted_children, strict=True)
            ],
            "validation_receipt": validation_receipt.as_posix(),
            "validation_receipt_sha256": hashlib.sha256(
                validation_receipt.read_bytes()
            ).hexdigest(),
            "status": "PUSH_READY",
            "push_performed": False,
            "task_or_batch_id": batch.get("batch_id"),
            "risk_tier": "STANDARD",
            "planning_elapsed": total("planning_elapsed"),
            "execution_elapsed": total("execution_elapsed"),
            "review_elapsed": total("review_elapsed"),
            "closeout_elapsed": total("closeout_elapsed"),
            "integration_wait": total("integration_wait"),
            "correction_count": sum(
                int(item.get("correction_count", 0)) for item in throughput_values
            ),
            "correction_causes": [
                cause
                for item in throughput_values
                for cause in item.get("correction_causes", [])
            ],
            "acceptance_result": "ACCEPTED",
            "escaped_regression_or_reopen": False,
            "provider_reported_usage_if_available": None,
            "allowance_before": None,
            "allowance_after": None,
            "other_concurrent_usage_known": None,
        }
    )
    return result


def write_batch(path: Path, batch: dict[str, Any]) -> str:
    """Write a canonical delivery-batch record."""
    raw = json.dumps(batch, indent=2, sort_keys=True) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(raw, encoding="utf-8", newline="\n")
    return hashlib.sha256(raw.encode()).hexdigest()


def run_combined_gate(
    repo: Path,
    batch: dict[str, Any],
    *,
    output_dir: Path,
    runner: Any = subprocess.run,
    receipt_builder: Any = create_validation_receipt,
    fingerprint: Any = candidate_fingerprint,
) -> tuple[Path, float]:
    """Run one comprehensive gate for an already accepted batch candidate."""
    report = output_dir / "validation-report.json"
    logs = output_dir / "logs"
    command = [
        sys.executable,
        "scripts/ci_check.py",
        "--profile",
        "full",
        "--report",
        str(report),
        "--log-dir",
        str(logs),
    ]
    started = time.perf_counter()
    completed = runner(command, cwd=repo, check=False)
    elapsed = time.perf_counter() - started
    if completed.returncode != 0 or not report.is_file():
        raise DeliveryBatchError(
            "Combined integration gate failed; grouped push is blocked."
        )
    payload = json.loads(report.read_text(encoding="utf-8"))
    results = payload.get("results")
    if (
        payload.get("explain_only") is not False
        or not isinstance(results, list)
        or not results
        or any(item.get("exit_code") != 0 for item in results if isinstance(item, dict))
    ):
        raise DeliveryBatchError("Combined integration report did not pass.")
    receipt = output_dir / "validation-receipt.json"
    authority = hashlib.sha256(
        json.dumps(batch, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    receipt_builder(
        repo=repo,
        diagnostic_path=report,
        receipt_path=receipt,
        worktree_sha256=fingerprint(repo),
        authority_sha256=authority,
    )
    return receipt, elapsed
