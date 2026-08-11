"""WF-STR-012: evaluate genuine prepared evidence for research-only signals."""

from __future__ import annotations

import hashlib
import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.data import get_symbol_metadata
from app.services.strategy import (
    create_strategy_signal_evidence,
    evaluate_strategy_signals,
    export_strategy_diagnostics,
    register_strategy_version,
    validate_strategy_config,
    validate_strategy_ref,
)
from tests.strategy.usage.workflows._support import (
    MarketProposalEvaluator,
    auth_context,
    caller_config,
    current_context,
    live_bars,
    policy,
    print_market_frame,
    registration_request,
    temporary_storage,
    unresolved_ref,
)

WORKFLOW_ID = "WF-STR-012"
STAGES = (
    "Receive genuine point-in-time Data evidence prepared for research.",
    "Resolve the exact registered Strategy version and validated configuration.",
    "Evaluate ordered canonical signals without constructing a proposal.",
    "Export bounded diagnostics beside the signal evidence.",
    "Return research-only evidence with no TradeIntent or execution authority.",
)


def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(
        f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}"
    )


def main() -> None:
    """Run the registered Strategy over genuine Data for research consumption."""
    # Stage 1 — INPUT BOUNDARY: Receive genuine bounded MT5-backed Data evidence.
    _stage(1)
    market = live_bars(limit=120)
    print("Genuine prepared market frame:")
    print_market_frame(market, rows=12)
    metadata = get_symbol_metadata(source_id="mt5", symbol=market.symbol)
    point_size = (
        Decimal(str(metadata.data.point))
        if metadata.data is not None
        else Decimal("0.00001")
    )
    context = current_context("EVENT_DRIVEN", market=market)
    evidence = create_strategy_signal_evidence(
        evidence_id=hashlib.sha256(
            f"{market.request_id}:{market.available_at.isoformat()}".encode()
        ).hexdigest(),
        primary_market=market,
        related_markets={},
        point_size=point_size,
        feature_values={},
        feature_available_at={},
        feature_refs={},
        active_position_tags=(),
    )

    # Stage 2: Resolve the registered version and its normalized configuration.
    _stage(2)
    with temporary_storage():
        registration = register_strategy_version(
            registration_request(),
            auth_context(),
            policy(),
        )
        if registration.data is None:
            raise RuntimeError(f"Registration failed: {registration.error}")
        ref_response = validate_strategy_ref(unresolved_ref(), policy())
        if ref_response.data is None:
            raise RuntimeError(f"Reference validation failed: {ref_response.error}")
        config_response = validate_strategy_config(
            ref_response.data,
            caller_config(),
        )
        if config_response.data is None:
            raise RuntimeError(f"Configuration failed: {config_response.error}")
        print(
            "Resolved registry record:",
            ref_response.data.registry_record_hash,
        )
        print(
            "Normalized configuration:",
            dict(config_response.data.normalized_parameters),
        )

        # Stage 3: Evaluate canonical signals; do not call any intent constructor.
        _stage(3)
        outcome = evaluate_strategy_signals(
            ref_response.data,
            config_response.data,
            evidence,
            (),
            context,
            MarketProposalEvaluator(),
        )
    if outcome.data is None:
        raise RuntimeError(f"Research signal evaluation failed: {outcome.error}")
    print("Research signal evidence:")
    for signal in outcome.data:
        print(signal.model_dump(mode="json"))

    # Stage 4: Export bounded diagnostics alongside the actual signal facts.
    _stage(4)
    diagnostics = export_strategy_diagnostics(
        context,
        {
            "strategy_id": "mean-reversion",
            "strategy_version": "1.0.0",
            "signal_ids": tuple(signal.signal_id for signal in outcome.data),
            "source_market_request_id": market.request_id,
        },
    )
    if diagnostics.data is None:
        raise RuntimeError(f"Diagnostics failed: {diagnostics.error}")
    print("Bounded diagnostics:")
    print(diagnostics.data.model_dump(mode="json"))

    # Stage 5 — OUTPUT BOUNDARY: Return signals only, never a TradeIntent.
    _stage(5)
    print("Output signal count:", len(outcome.data))
    print("TradeIntent constructed: False")
    print("Risk approval synthesized: False")
    print("Execution instruction created: False")


if __name__ == "__main__":
    main()
