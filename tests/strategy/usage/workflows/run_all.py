"""Execute every active Strategy workflow usage program."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from tests.strategy.usage.workflows._support import temporary_storage

WORKFLOWS = (
    "wf_str_001_validate_reference_configuration.py",
    "wf_str_pri_generate_vectorized_decisions.py",
    "wf_str_003_run_stateful_event_hook.py",
    "wf_str_sec_build_hand_off_trade_intent.py",
    "wf_str_005_create_replay_manifest_checkpoint.py",
    "wf_str_006_export_structured_diagnostics.py",
    "wf_str_007_supply_demo_live_decisions.py",
    "wf_str_ter_register_immutable_strategy_version.py",
    "wf_str_009_reject_arbitrary_strategy_code.py",
    "wf_str_010_evaluate_recovered_concrete_signals.py",
    "wf_str_011_adopt_approved_optimization_parameters.py",
    "wf_str_012_evaluate_signals_for_research.py",
)


def main() -> int:
    """Import and execute all workflow programs in registry order.

    Returns:
        ``0`` only when every workflow completes, otherwise ``1``.
    """
    package = "tests.strategy.usage.workflows"
    completed = 0
    failures: list[tuple[str, str]] = []
    for filename in WORKFLOWS:
        try:
            with temporary_storage():
                importlib.import_module(f"{package}.{filename[:-3]}").main()
        except (ImportError, OSError, RuntimeError, TypeError, ValueError) as error:
            failures.append((filename, type(error).__name__))
            print(f"\n{filename}: FAILED ({type(error).__name__})")
        else:
            completed += 1
    print(f"\nStrategy workflows completed: {completed}/{len(WORKFLOWS)}")
    if failures:
        print("Workflow failures:", tuple(failures))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
