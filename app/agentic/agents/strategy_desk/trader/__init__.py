"""Public `FEAT-AGT-20` Trade Proposal Handoff API."""

from app.agentic.agents.strategy_desk.trader.handoff import submit_trade_proposal
from app.agentic.agents.strategy_desk.trader.schemas import (
    TradeProposal,
    TradeProposalReceipt,
    build_trade_proposal,
    build_trade_proposal_receipt,
)

__all__: tuple[str, ...] = (
    "TradeProposal",
    "TradeProposalReceipt",
    "build_trade_proposal",
    "build_trade_proposal_receipt",
    "submit_trade_proposal",
)
