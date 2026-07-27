"""WF-STR-005: bind replay identity and round-trip a bounded checkpoint."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.strategy import (
    create_strategy_checkpoint,
    create_strategy_replay_manifest,
    validate_strategy_checkpoint,
)
from tests.strategy.unit.test_models import (
    HASH,
    make_auth,
    make_config,
    make_context,
    make_ref,
)
from tests.strategy.usage.workflows._support import temporary_storage

WORKFLOW_ID = "WF-STR-005"
STAGES = (
    "Accept exact strategy, config, data, indicator, simulation, and seed identities.",
    "Create the immutable replay manifest.",
    "Create a bounded serializable local-state checkpoint.",
    "Validate identity, hashes, authorization, checksum, schema, and size.",
    "Return replay and restored checkpoint evidence or structured failure.",
)


def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(
        f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}"
    )


def main() -> None:
    """Run the documented input-to-output workflow."""
    # Stage 1 — INPUT BOUNDARY: Caller supplies exact immutable replay inputs.
    _stage(1)
    ref, config, context = make_ref(), make_config(), make_context()
    print(
        "Input:",
        ref.manifest.strategy_id,
        ref.manifest.strategy_version,
        context.seed,
    )

    # Stage 2: Bind all replay inputs.
    _stage(2)
    replay = create_strategy_replay_manifest(ref, config, context, HASH, HASH)
    print("Replay:", replay.status)

    # Stage 3: Persist only bounded local decision state.
    _stage(3)
    auth = make_auth(checkpoint=True)
    with temporary_storage():
        checkpoint = create_strategy_checkpoint(
            ref, config, {"counter": 1}, "checkpoint-auth", auth
        )
        print("Checkpoint:", checkpoint.status)

        # Stage 4: Validate before restore.
        _stage(4)
        if checkpoint.data is None:
            raise RuntimeError(f"Checkpoint creation failed: {checkpoint.error}")
        restored = validate_strategy_checkpoint(checkpoint.data, ref, config, auth)
        print("Restore:", restored.status)

    # Stage 5 — OUTPUT BOUNDARY: Return typed replay/checkpoint outcomes.
    _stage(5)
    print("Output:", replay.status, restored.status)


if __name__ == "__main__":
    main()
