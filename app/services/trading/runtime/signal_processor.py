"""Signal processor translating strategy signals to request envelopes.

Implements TRD-FR-080 through TRD-FR-082.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from app.services.trading.contracts import (
    MutationCapability,
    PromotionStage,
    QuoteSnapshot,
    TradingAction,
    TradingRequestEnvelope,
    TradingRoute,
)
from app.services.trading.security.error_mapping import TradingValidationError
from app.utils.logger import logger

if TYPE_CHECKING:
    from app.services.trading.gates.pipeline import GatePipelineDecision


class SignalProcessor:
    """Processes signals from strategies and wraps them in request envelopes."""

    def _parse_required_enums(
        self, signal: dict[str, Any]
    ) -> tuple[TradingRoute, PromotionStage, MutationCapability, TradingAction]:
        """Parse enums from raw signal, validating their presence and values."""
        route_raw = signal.get("route")
        if route_raw is None:
            msg = "Signal is missing required 'route' attribute."
            raise TradingValidationError(msg)

        stage_raw = signal.get("promotion_stage")
        if stage_raw is None:
            msg = "Signal is missing required 'promotion_stage' attribute."
            raise TradingValidationError(msg)

        cap_raw = signal.get("mutation_capability")
        if cap_raw is None:
            msg = "Signal is missing required 'mutation_capability' attribute."
            raise TradingValidationError(msg)

        action_raw = signal.get("action")
        if action_raw is None:
            msg = "Signal is missing required 'action' attribute."
            raise TradingValidationError(msg)

        try:
            route = TradingRoute(route_raw)
        except ValueError as exc:
            msg = f"Invalid route value: {route_raw}"
            raise TradingValidationError(msg) from exc

        try:
            stage = PromotionStage(stage_raw)
        except ValueError as exc:
            msg = f"Invalid promotion stage value: {stage_raw}"
            raise TradingValidationError(msg) from exc

        try:
            cap = MutationCapability(cap_raw)
        except ValueError as exc:
            msg = f"Invalid mutation capability value: {cap_raw}"
            raise TradingValidationError(msg) from exc

        try:
            action = TradingAction(action_raw)
        except ValueError as exc:
            msg = f"Invalid action value: {action_raw}"
            raise TradingValidationError(msg) from exc

        return route, stage, cap, action

    def _parse_quote(
        self,
        signal: dict[str, Any],
        route: TradingRoute,
        stage: PromotionStage,
    ) -> QuoteSnapshot | None:
        """Parse and validate quote snapshot depending on route mutation status."""
        is_live_mutation = route is TradingRoute.LIVE and stage in (
            PromotionStage.MICRO_LIVE,
            PromotionStage.FULL_LIVE,
        )
        quote = signal.get("quote_snapshot")

        if is_live_mutation:
            risk_ref = signal.get("risk_decision_id")
            if not risk_ref:
                msg = "Live mutation signals require a 'risk_decision_id' reference."
                raise TradingValidationError(msg)

            approvals = signal.get("approvals")
            if approvals is None:
                msg = "Live mutation signals require 'approvals' evidence."
                raise TradingValidationError(msg)

            if quote is None:
                msg = "Live mutation signals require a valid 'quote_snapshot'."
                raise TradingValidationError(msg)

            if not isinstance(quote, QuoteSnapshot):
                try:
                    quote = QuoteSnapshot(**quote)
                except Exception as exc:
                    msg = f"Malformed 'quote_snapshot' in strategy signal: {exc}"
                    raise TradingValidationError(msg) from exc
        elif quote is not None and not isinstance(quote, QuoteSnapshot):
            try:
                quote = QuoteSnapshot(**quote)
            except Exception:  # noqa: BLE001
                quote = None

        return quote

    def process_strategy_signal(
        self,
        *,
        signal: dict[str, Any],
        gate_pipeline_runner: Callable[
            [TradingRequestEnvelope], GatePipelineDecision
        ],
    ) -> tuple[TradingRequestEnvelope, GatePipelineDecision]:
        """Transform signal into envelope and validate via pipeline.

        Tracked requirements: TRD-FR-080, TRD-FR-081, TRD-FR-082.

        Args:
            signal: Raw strategy signal dictionary.
            gate_pipeline_runner: Callback to run the envelope through the
                gate pipeline.

        Returns:
            tuple[TradingRequestEnvelope, GatePipelineDecision]: Prepared
                envelope and gate decision.

        Raises:
            TradingValidationError: If required validation attributes are missing.
        """
        logger.info("Processing strategy signal: {}.", signal)

        # 1. Parse required enums
        route, stage, cap, action = self._parse_enums(signal)

        # 2. Check identifiers
        request_id = signal.get("request_id")
        if not request_id:
            msg = "Signal is missing required 'request_id' attribute."
            raise TradingValidationError(msg)

        correlation_id = signal.get("correlation_id")
        if not correlation_id:
            msg = "Signal is missing required 'correlation_id' attribute."
            raise TradingValidationError(msg)

        # 3. Parse quote snapshot
        quote = self._parse_quote(signal, route, stage)

        # Build payload including strategy_id and risk_decision_id
        strategy_id = signal.get("strategy_id", "unknown-strategy")
        payload = dict(signal.get("payload", {}))
        payload["strategy_id"] = strategy_id
        if "risk_decision_id" in signal:
            payload["risk_decision_id"] = signal["risk_decision_id"]

        # Build canonical request envelope
        envelope = TradingRequestEnvelope(
            route=route,
            action=action,
            promotion_stage=stage,
            mutation_capability=cap,
            request_id=request_id,
            correlation_id=correlation_id,
            symbol=signal.get("symbol"),
            payload=payload,
            allocation_vector=signal.get("allocation_vector"),
            regulatory_tags=signal.get("regulatory_tags"),
            oco_group_id=signal.get("oco_group_id"),
            linked_order_ids=tuple(signal.get("linked_order_ids", [])),
            quote_snapshot=quote,
            deadline_utc=signal.get("deadline_utc"),
        )

        logger.info("Executing gate pipeline validation for signal {}.", request_id)
        decision = gate_pipeline_runner(envelope)

        return envelope, decision

    def _parse_enums(
        self, signal: dict[str, Any]
    ) -> tuple[TradingRoute, PromotionStage, MutationCapability, TradingAction]:
        """Convenience wrapper for enum parser to keep method public surface cleaner."""
        return self._parse_required_enums(signal)
