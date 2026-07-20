"""Cost control and budget verification service.

Implements TRD-FR-077 through TRD-FR-079.
"""

from __future__ import annotations

import threading
from decimal import Decimal
from typing import TYPE_CHECKING

from app.services.trading.security.error_mapping import TradingValidationError
from app.utils.logger import logger

if TYPE_CHECKING:
    from app.services.trading.contracts import TradingRequestEnvelope


class CostController:
    """Evaluates and tracks session/strategy budget ceilings.

    Enforces configured budget limits without performing complex performance
    or analytics metrics calculations (TRD-FR-079).
    """

    def __init__(self, signals_manager: object = None) -> None:
        """Initialize the cost controller.

        Args:
            signals_manager: Injected operational incident signals manager.
        """
        self.signals_manager = signals_manager

        # Accumulated cost maps
        self.session_accumulated_cost = Decimal("0.0")
        self.strategy_accumulated_costs: dict[str, Decimal] = {}
        self.account_accumulated_costs: dict[str, Decimal] = {}
        self.workflow_accumulated_costs: dict[str, Decimal] = {}
        self._lock = threading.Lock()

    def validate_pre_dispatch_budget(
        self,
        *,
        request: TradingRequestEnvelope,
        estimated_cost: Decimal,
        limits: dict[str, Decimal],
    ) -> None:
        """Check estimated cost against budget limits before broker dispatch.

        Tracked requirements: TRD-FR-077, TRD-FR-078.

        Args:
            request: Ingress trading request envelope.
            estimated_cost: Estimated cost of executing this mutation.
            limits: Configured budget limits per category (request, workflow,
                strategy, account, session).

        Raises:
            TradingValidationError: If any budget limits are violated.
        """
        if estimated_cost <= 0:
            return

        with self._lock:
            # 1. Request budget limit
            req_limit = limits.get("request_max", Decimal("inf"))
            if estimated_cost > req_limit:
                msg = (
                    f"Estimated cost {estimated_cost} exceeds "
                    f"configured request budget limit {req_limit}."
                )
                raise TradingValidationError(msg)

            # 2. Workflow / Correlation budget limit
            wf_limit = limits.get("workflow_max", Decimal("inf"))
            wf_acc = self.workflow_accumulated_costs.get(
                request.correlation_id, Decimal("0.0")
            )
            if wf_acc + estimated_cost > wf_limit:
                msg = (
                    f"Workflow cost {wf_acc + estimated_cost} exceeds "
                    f"configured workflow budget limit {wf_limit}."
                )
                raise TradingValidationError(msg)

            # 3. Strategy budget limit
            strat_limit = limits.get("strategy_max", Decimal("inf"))
            strat_id = str(request.payload.get("strategy_id", "unknown-strategy"))
            strat_acc = self.strategy_accumulated_costs.get(strat_id, Decimal("0.0"))
            if strat_acc + estimated_cost > strat_limit:
                msg = (
                    f"Strategy cost {strat_acc + estimated_cost} exceeds "
                    f"configured strategy budget limit {strat_limit}."
                )
                raise TradingValidationError(msg)

            # 4. Account budget limit
            acct_limit = limits.get("account_max", Decimal("inf"))
            val = request.payload.get("tenant_id")
            acct_id = str(val) if val is not None else "default"
            acct_acc = self.account_accumulated_costs.get(acct_id, Decimal("0.0"))
            if acct_acc + estimated_cost > acct_limit:
                msg = (
                    f"Account cost {acct_acc + estimated_cost} exceeds "
                    f"configured account budget limit {acct_limit}."
                )
                raise TradingValidationError(msg)

            # 5. Session budget limit
            sess_limit = limits.get("session_max", Decimal("inf"))
            if self.session_accumulated_cost + estimated_cost > sess_limit:
                msg = (
                    f"Session cost {self.session_accumulated_cost + estimated_cost} "
                    f"exceeds configured session budget limit {sess_limit}."
                )
                raise TradingValidationError(msg)

        logger.debug(
            "Pre-dispatch budget validation passed. Estimated cost: {}.",
            estimated_cost,
        )

    def record_cost(
        self,
        *,
        request: TradingRequestEnvelope,
        actual_cost: Decimal,
        limits: dict[str, Decimal],
        post_dispatch: bool = False,
    ) -> None:
        """Accumulate cost and raise critical incident if limits are breached.

        Tracked requirements: TRD-FR-078.

        Args:
            request: Completed trading request envelope.
            actual_cost: Actual transaction fee / cost captured.
            limits: Configured budget limits per category.
            post_dispatch: True if recorded after the order was dispatched.
        """
        if actual_cost <= 0:
            return

        with self._lock:
            self.session_accumulated_cost += actual_cost

            strat_id = str(request.payload.get("strategy_id", "unknown-strategy"))
            self.strategy_accumulated_costs[strat_id] = (
                self.strategy_accumulated_costs.get(strat_id, Decimal("0.0"))
                + actual_cost
            )

            val = request.payload.get("tenant_id")
            acct_id = str(val) if val is not None else "default"
            self.account_accumulated_costs[acct_id] = (
                self.account_accumulated_costs.get(acct_id, Decimal("0.0"))
                + actual_cost
            )

            wf_id = request.correlation_id
            self.workflow_accumulated_costs[wf_id] = (
                self.workflow_accumulated_costs.get(wf_id, Decimal("0.0")) + actual_cost
            )

            # Post-dispatch budget checks
            if post_dispatch:
                violated = False
                violation_msg = ""

                # Evaluate ceilings
                sess_limit = limits.get("session_max", Decimal("inf"))
                strat_limit = limits.get("strategy_max", Decimal("inf"))
                wf_limit = limits.get("workflow_max", Decimal("inf"))

                if self.session_accumulated_cost > sess_limit:
                    violated = True
                    violation_msg = (
                        f"Session cost {self.session_accumulated_cost} "
                        f"exceeds session budget {sess_limit}."
                    )
                elif self.strategy_accumulated_costs[strat_id] > strat_limit:
                    violated = True
                    violation_msg = (
                        f"Strategy cost {self.strategy_accumulated_costs[strat_id]} "
                        f"exceeds strategy budget {strat_limit}."
                    )
                elif self.workflow_accumulated_costs[wf_id] > wf_limit:
                    violated = True
                    violation_msg = (
                        f"Workflow cost {self.workflow_accumulated_costs[wf_id]} "
                        f"exceeds workflow budget {wf_limit}."
                    )

                if violated:
                    logger.critical("CRITICAL COST BUDGET INCIDENT: {}.", violation_msg)
                    if self.signals_manager and hasattr(
                        self.signals_manager, "emit_signal"
                    ):
                        err_msg = (
                            f"Cost budget limit violated post-dispatch: {violation_msg}"
                        )
                        self.signals_manager.emit_signal(
                            incident_class="cost_budget_breach",
                            severity="CRITICAL",
                            message=err_msg,
                        )

    def reset_accumulated_costs(self) -> None:
        """Reset all accumulated cost state statistics."""
        with self._lock:
            self.session_accumulated_cost = Decimal("0.0")
            self.strategy_accumulated_costs.clear()
            self.account_accumulated_costs.clear()
            self.workflow_accumulated_costs.clear()
