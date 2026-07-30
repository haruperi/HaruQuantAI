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
from tests.strategy.usage.workflows._support import (
    CONFIG_HASH,
    HASH,
    auth_context,
    current_context,
    live_bars,
    print_market_frame,
    temporary_storage,
    validated_config,
    validated_ref,
)

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
    market = live_bars(limit=12)
    print_market_frame(market)
    ref = validated_ref()
    config = validated_config()
    context = current_context("EVENT_DRIVEN", market=market)
    print(
        "Input:",
        ref.manifest.strategy_id,
        ref.manifest.strategy_version,
        context.seed,
    )

    # Stage 2: Bind all replay inputs.
    _stage(2)
    replay = create_strategy_replay_manifest(
        ref,
        config,
        context,
        HASH,
        CONFIG_HASH,
    )
    print("Replay:", replay.status)
    if replay.data is None:
        raise RuntimeError(f"Replay construction failed: {replay.error}")
    print("Replay manifest:", replay.data.model_dump(mode="json"))

    # Stage 3: Persist only bounded local decision state.
    _stage(3)
    auth = auth_context(checkpoint=True)
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
        if restored.data is None:
            raise RuntimeError(f"Checkpoint restore failed: {restored.error}")
        print("Restored state:", dict(restored.data))

    # Stage 5 — OUTPUT BOUNDARY: Return typed replay/checkpoint outcomes.
    _stage(5)
    print("Output:", replay.status, restored.status)


if __name__ == "__main__":
    main()
