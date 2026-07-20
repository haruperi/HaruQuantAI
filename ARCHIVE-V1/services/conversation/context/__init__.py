"""Page context services and builders for CEO chat."""

from .backtest_detail import build_backtest_detail_context
from .base import infer_page_type
from .dashboard import build_dashboard_context
from .data_workspace import build_data_workspace_context
from .generic import build_generic_context
from .live_trading import build_live_trading_context
from .operator_workflow import build_operator_workflow_context
from .optimization import build_optimization_context
from .portfolio_risk import build_portfolio_risk_context
from .strategy_detail import build_strategy_detail_context

ROUTE_CONTEXT_REGISTRY = {
    "dashboard": build_dashboard_context,
    "strategy_detail": build_strategy_detail_context,
    "backtest_detail": build_backtest_detail_context,
    "optimization_detail": build_optimization_context,
    "portfolio_risk": build_portfolio_risk_context,
    "live_trading": build_live_trading_context,
    "data_workspace": build_data_workspace_context,
    "operator_workflow": build_operator_workflow_context,
    "generic": build_generic_context,
}


def get_context_builder(route: str | None, page_type_hint: str | None = None):
    page_type = infer_page_type(route, page_type_hint)
    return ROUTE_CONTEXT_REGISTRY.get(page_type, build_generic_context), page_type


from .service import ContextAssembler, PageContextService

__all__ = [
    "ROUTE_CONTEXT_REGISTRY",
    "ContextAssembler",
    "PageContextService",
    "get_context_builder",
]
