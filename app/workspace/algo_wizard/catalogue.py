"""ServletConstants equivalent service (WizardCatalogueService) for AlgoWizard.

Description:
    Serves the complete HaruQuant Strategy Language (HSL 1.0) building block
    catalogue projected from BlockRegistry, along with standardized wizard
    constants (timeframes, 14 lifecycle events, price fields, relational/crossing
    operators, arithmetic operators, money/risk modes, and broker commission
    models) wrapped in StandardResponse[T] envelopes.

Purpose:
    FEAT-WIZARD-CATALOGUE: Backend service implementing the ServletConstants
    surface (/constants/getAll, /constants/listCommissionMethods, and block
    descriptor inspection) for the visual Strategy Builder and AI Co-Pilot.

Key Capabilities:
    - FR-wizard-catalogue-get-all: Returns WizardConstantsBundle filtered by
      optional category or semantic family.
    - FR-wizard-catalogue-commissions: Lists supported commission calculation
      models (percent, per_lot, per_trade, per_share).
    - FR-wizard-catalogue-block-descriptor: Resolves single block metadata and
      parameter bounds from WizardBlockLibrary.

Python API Usage:
    from app.workspace.algo_wizard.catalogue import WizardCatalogueService
    from app.workspace.algo_wizard.catalogue_models import GetCatalogueRequest

    svc = WizardCatalogueService()
    resp = svc.get_all(GetCatalogueRequest(request_id="r1"))

CLI Usage:
    python -c "from app.workspace.algo_wizard import catalogue; print(1)"
"""

from __future__ import annotations

from typing import Any, cast

from app.core.host.logging import get_logger
from app.core.lib.responses import StandardResponse
from app.workspace.algo_wizard.catalogue_models import (
    CatalogueOptionItem,
    CommissionMethodDescriptor,
    GetBlockDescriptorRequest,
    GetCatalogueRequest,
    HSLBlockCatalogueEntry,
    ListCommissionMethodsRequest,
    WizardConstantsBundle,
)
from app.workspace.algo_wizard.library import WizardBlockLibrary

logger = get_logger(__name__)

_TIMEFRAME_OPTIONS: tuple[CatalogueOptionItem, ...] = (
    CatalogueOptionItem(code="M1", label="1 Minute", category="intraday"),
    CatalogueOptionItem(code="M5", label="5 Minutes", category="intraday"),
    CatalogueOptionItem(code="M15", label="15 Minutes", category="intraday"),
    CatalogueOptionItem(code="M30", label="30 Minutes", category="intraday"),
    CatalogueOptionItem(code="H1", label="1 Hour", category="intraday"),
    CatalogueOptionItem(code="H4", label="4 Hours", category="intraday"),
    CatalogueOptionItem(code="D1", label="Daily", category="daily"),
    CatalogueOptionItem(code="W1", label="Weekly", category="higher"),
    CatalogueOptionItem(code="MN1", label="Monthly", category="higher"),
)

_LIFECYCLE_EVENT_OPTIONS: tuple[CatalogueOptionItem, ...] = (
    CatalogueOptionItem(code="on_start", label="On Strategy Start", category="engine"),
    CatalogueOptionItem(code="on_stop", label="On Strategy Stop", category="engine"),
    CatalogueOptionItem(code="on_timer", label="On Timer", category="engine"),
    CatalogueOptionItem(code="on_tick", label="On Tick", category="market"),
    CatalogueOptionItem(code="on_bar_open", label="On Bar Open", category="market"),
    CatalogueOptionItem(code="on_bar_close", label="On Bar Close", category="market"),
    CatalogueOptionItem(
        code="on_order_submitted", label="On Order Submitted", category="order"
    ),
    CatalogueOptionItem(
        code="on_order_filled", label="On Order Filled", category="order"
    ),
    CatalogueOptionItem(
        code="on_order_cancelled", label="On Order Cancelled", category="order"
    ),
    CatalogueOptionItem(
        code="on_order_rejected", label="On Order Rejected", category="order"
    ),
    CatalogueOptionItem(
        code="on_position_opened", label="On Position Opened", category="position"
    ),
    CatalogueOptionItem(
        code="on_position_closed", label="On Position Closed", category="position"
    ),
    CatalogueOptionItem(
        code="on_session_open", label="On Session Open", category="session"
    ),
    CatalogueOptionItem(
        code="on_session_close", label="On Session Close", category="session"
    ),
)

_PRICE_FIELD_OPTIONS: tuple[CatalogueOptionItem, ...] = (
    CatalogueOptionItem(code="open", label="Open", category="bar"),
    CatalogueOptionItem(code="high", label="High", category="bar"),
    CatalogueOptionItem(code="low", label="Low", category="bar"),
    CatalogueOptionItem(code="close", label="Close", category="bar"),
    CatalogueOptionItem(code="volume", label="Volume", category="bar"),
    CatalogueOptionItem(code="typical", label="Typical (HLC/3)", category="derived"),
    CatalogueOptionItem(code="median", label="Median (HL/2)", category="derived"),
    CatalogueOptionItem(code="weighted", label="Weighted (HLCC/4)", category="derived"),
)

_COMPARISON_OPERATOR_OPTIONS: tuple[CatalogueOptionItem, ...] = (
    CatalogueOptionItem(code="greater_than", label="Greater Than (>)", category="rel"),
    CatalogueOptionItem(
        code="greater_or_equal", label="Greater or Equal (>=)", category="rel"
    ),
    CatalogueOptionItem(code="less_than", label="Less Than (<)", category="rel"),
    CatalogueOptionItem(
        code="less_or_equal", label="Less or Equal (<=)", category="rel"
    ),
    CatalogueOptionItem(code="equal", label="Equal (==)", category="rel"),
    CatalogueOptionItem(code="not_equal", label="Not Equal (!=)", category="rel"),
    CatalogueOptionItem(
        code="crosses_above", label="Crosses Above", category="crossing"
    ),
    CatalogueOptionItem(
        code="crosses_below", label="Crosses Below", category="crossing"
    ),
)

_MATH_OPERATOR_OPTIONS: tuple[CatalogueOptionItem, ...] = (
    CatalogueOptionItem(code="add", label="Add (+)", category="binary"),
    CatalogueOptionItem(code="subtract", label="Subtract (-)", category="binary"),
    CatalogueOptionItem(code="multiply", label="Multiply (*)", category="binary"),
    CatalogueOptionItem(code="divide", label="Divide (/)", category="binary"),
    CatalogueOptionItem(code="min", label="Minimum", category="binary"),
    CatalogueOptionItem(code="max", label="Maximum", category="binary"),
    CatalogueOptionItem(code="abs", label="Absolute Value", category="unary"),
)

_MONEY_MANAGEMENT_OPTIONS: tuple[CatalogueOptionItem, ...] = (
    CatalogueOptionItem(code="fixed_size", label="Fixed Lots / Quantity"),
    CatalogueOptionItem(code="fixed_cash", label="Fixed Cash Amount"),
    CatalogueOptionItem(code="percent_equity", label="Percentage of Equity"),
    CatalogueOptionItem(code="risk_percent", label="Risk Percentage per Trade"),
)

_STOP_LOSS_OPTIONS: tuple[CatalogueOptionItem, ...] = (
    CatalogueOptionItem(code="none", label="No Stop Loss"),
    CatalogueOptionItem(code="fixed_pips", label="Fixed Pips"),
    CatalogueOptionItem(code="fixed_points", label="Fixed Points"),
    CatalogueOptionItem(code="percent", label="Percentage"),
    CatalogueOptionItem(code="atr", label="ATR Multiple"),
    CatalogueOptionItem(code="indicator", label="Indicator Value"),
    CatalogueOptionItem(code="expression", label="Custom Expression"),
)

_TAKE_PROFIT_OPTIONS: tuple[CatalogueOptionItem, ...] = (
    CatalogueOptionItem(code="none", label="No Take Profit"),
    CatalogueOptionItem(code="fixed_pips", label="Fixed Pips"),
    CatalogueOptionItem(code="fixed_points", label="Fixed Points"),
    CatalogueOptionItem(code="percent", label="Percentage"),
    CatalogueOptionItem(code="atr", label="ATR Multiple"),
    CatalogueOptionItem(code="risk_multiple", label="Risk-Reward Multiple"),
    CatalogueOptionItem(code="expression", label="Custom Expression"),
)

_COMMISSION_METHODS: tuple[CommissionMethodDescriptor, ...] = (
    CommissionMethodDescriptor(
        method_id="percentage",
        name="Percentage of Trade Notional",
        unit="percent",
        default_value=0.02,
        min_value=0.0,
        max_value=10.0,
        description="Charges a percentage fee on executed notional value.",
    ),
    CommissionMethodDescriptor(
        method_id="money_per_lot",
        name="Fixed Money per Lot",
        unit="per_lot",
        default_value=7.0,
        min_value=0.0,
        max_value=1000.0,
        description="Charges a flat fee per standard lot traded.",
    ),
    CommissionMethodDescriptor(
        method_id="money_per_trade",
        name="Fixed Money per Order",
        unit="per_trade",
        default_value=1.0,
        min_value=0.0,
        max_value=1000.0,
        description="Charges a flat fee per executed order ticket.",
    ),
    CommissionMethodDescriptor(
        method_id="money_per_share",
        name="Fixed Money per Share / Contract",
        unit="per_share",
        default_value=0.005,
        min_value=0.0,
        max_value=100.0,
        description="Charges a fee per individual share or contract unit.",
    ),
)


def _parse_revision_int(revision_str: str) -> int:
    """Extract integer revision number from 'rev-<n>' strings."""
    tail = revision_str.removeprefix("rev-")
    try:
        return int(tail)
    except ValueError:
        return 1


def _build_typed_response[T](
    *,
    request_id: str,
    data: T,
    json_payload: Any,
    revision: int,
) -> StandardResponse[T]:
    """Validate json_payload through StandardResponse and attach typed data."""
    envelope: StandardResponse[Any] = StandardResponse(
        request_id=request_id,
        data=json_payload,
        revision=revision,
    )
    object.__setattr__(envelope, "data", data)
    return cast("StandardResponse[T]", envelope)


class WizardCatalogueService:
    """Service providing HSL 1.0 block catalogue and ServletConstants options."""

    def __init__(self, library: WizardBlockLibrary | None = None) -> None:
        self._library = library if library is not None else WizardBlockLibrary()

    @property
    def library(self) -> WizardBlockLibrary:
        """Return the underlying WizardBlockLibrary."""
        return self._library

    def get_all(
        self,
        request: GetCatalogueRequest | None = None,
    ) -> StandardResponse[WizardConstantsBundle]:
        """Return the full ServletConstants bundle projected from BlockRegistry."""
        req = request if request is not None else GetCatalogueRequest()
        blocks = self._library.list_entries(
            category=req.category,
            family=req.family,
        )
        rev_str = self._library.revision
        bundle = WizardConstantsBundle(
            revision=rev_str,
            blocks=blocks,
            timeframes=_TIMEFRAME_OPTIONS,
            lifecycle_events=_LIFECYCLE_EVENT_OPTIONS,
            price_fields=_PRICE_FIELD_OPTIONS,
            comparison_operators=_COMPARISON_OPERATOR_OPTIONS,
            math_operators=_MATH_OPERATOR_OPTIONS,
            money_management_modes=_MONEY_MANAGEMENT_OPTIONS,
            stop_loss_modes=_STOP_LOSS_OPTIONS,
            take_profit_modes=_TAKE_PROFIT_OPTIONS,
            commission_methods=_COMMISSION_METHODS,
        )
        logger.info(
            "Served WizardConstantsBundle request_id=%s blocks=%d rev=%s",
            req.request_id,
            len(blocks),
            rev_str,
        )
        return _build_typed_response(
            request_id=req.request_id,
            data=bundle,
            json_payload=bundle.model_dump(mode="json"),
            revision=_parse_revision_int(rev_str),
        )

    def list_commission_methods(
        self,
        request: ListCommissionMethodsRequest | None = None,
    ) -> StandardResponse[tuple[CommissionMethodDescriptor, ...]]:
        """Return all supported broker commission calculation methods."""
        req = request if request is not None else ListCommissionMethodsRequest()
        rev_str = self._library.revision
        logger.info(
            "Served %d commission methods request_id=%s",
            len(_COMMISSION_METHODS),
            req.request_id,
        )
        return _build_typed_response(
            request_id=req.request_id,
            data=_COMMISSION_METHODS,
            json_payload=[item.model_dump(mode="json") for item in _COMMISSION_METHODS],
            revision=_parse_revision_int(rev_str),
        )

    def get_block_descriptor(
        self,
        request: GetBlockDescriptorRequest,
    ) -> StandardResponse[HSLBlockCatalogueEntry]:
        """Return the HSLBlockCatalogueEntry for a semantic or registry block ID."""
        entry = self._library.require(request.block_id)
        rev_str = self._library.revision
        logger.info(
            "Served block descriptor request_id=%s block_id=%s -> semantic_id=%s",
            request.request_id,
            request.block_id,
            entry.semantic_id,
        )
        return _build_typed_response(
            request_id=request.request_id,
            data=entry,
            json_payload=entry.model_dump(mode="json"),
            revision=_parse_revision_int(rev_str),
        )
