"""Execute every active Strategy workflow usage program."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

WORKFLOWS = (
    "wf_str_001_validate_reference_configuration.py",
    "wf_str_pri_generate_vectorized_decisions.py",
    "wf_str_003_run_stateful_event_hook.py",
    "wf_str_sec_build_hand_off_trade_intent.py",
    "wf_str_005_create_replay_manifest_checkpoint.py",
    "wf_str_006_export_structured_diagnostics.py",
    "wf_str_007_supply_paper_live_decisions.py",
    "wf_str_ter_register_immutable_strategy_version.py",
    "wf_str_009_reject_arbitrary_strategy_code.py",
    "wf_str_010_evaluate_recovered_concrete_signals.py",
)


def main() -> None:
    """Import and execute all workflow programs in registry order."""
    package = "tests.strategy.usage.workflows"
    for filename in WORKFLOWS:
        importlib.import_module(f"{package}.{filename[:-3]}").main()
    print(f"\nStrategy workflows completed: {len(WORKFLOWS)}/{len(WORKFLOWS)}")


if __name__ == "__main__":
    main()
