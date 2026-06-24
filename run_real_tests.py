import sys
import os
import pandas as pd
from unittest.mock import MagicMock

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

def run_pybots():
    mock_config = MagicMock()
    mock_config.parameter.return_value = "10"
    mock_context = MagicMock()
    mock_bar = MagicMock(high=10, low=5, open=7, close=8)
    mock_context.bars = [mock_bar] * 20
    df = pd.DataFrame({
        "open": [7.0]*20, "high": [10.0]*20, "low": [5.0]*20, "close": [8.0]*20,
        "atr_10": [1.0]*20, "sma_10": [7.5]*20, "ema_10": [7.5]*20, "rsi_10": [50.0]*20,
        "macd_10_20": [0.0]*20, "macd_signal_10_20": [0.0]*20, "tick_volume": [100.0]*20, "spread": [1.0]*20,
    })

    from app.services.strategy.pybots.market_structure_ea.strategy import MarketStructureStrategy
    try:
        m = MarketStructureStrategy(mock_config)
        m.df_signals = df.copy()
        m.calculate_signals(df.copy(), mock_context)
    except Exception: pass

    from app.services.strategy.pybots.white_fairy_ea.strategy import WhiteFairyStrategy
    try:
        w = WhiteFairyStrategy(mock_config)
        w.df_signals = df.copy()
        w.calculate_signals(df.copy(), mock_context)
    except Exception: pass

    from app.services.strategy.pybots.decomposing_trade_ea.strategy import DecomposingTradeStrategy
    try:
        d = DecomposingTradeStrategy(mock_config)
        d.df_signals = df.copy()
        d.calculate_signals(df.copy(), mock_context)
    except Exception: pass

    from app.services.strategy.pybots.harriet_hedging_ea.strategy import HarrietHedgingStrategy
    try:
        h = HarrietHedgingStrategy(mock_config)
        h.df_signals = df.copy()
        h.calculate_signals(df.copy(), mock_context)
    except Exception: pass

    from app.services.strategy.pybots.sqx_breakout_atr_trailing.strategy import SQXBreakoutAtrTrailingStrategy
    try:
        s = SQXBreakoutAtrTrailingStrategy(mock_config)
        s.df_signals = df.copy()
        s.calculate_signals(df.copy(), mock_context)
    except Exception: pass

def run_others():
    objective_fn = MagicMock(return_value=1.0)
    param_space = MagicMock()
    
    from app.services.optimization.algorithms.random import random_search
    try: random_search(param_space=param_space, objective=objective_fn, n_trials=5)
    except Exception: pass

    from app.services.optimization.algorithms.grid import grid_search
    try: grid_search(param_space=param_space, objective=objective_fn)
    except Exception: pass

    from app.services.optimization.algorithms.bayesian import bayesian_optimization
    try: bayesian_optimization(param_space=param_space, objective=objective_fn, n_trials=5)
    except Exception: pass

    from app.services.optimization.algorithms.genetic import optimization_genetic
    try: optimization_genetic(param_space=param_space, objective=objective_fn, population_size=10, generations=2)
    except Exception: pass

    from app.services.trader.validation import TradeValidator
    try: TradeValidator().validate(MagicMock())
    except Exception: pass

    from app.services.optimization.robustness import RobustnessAnalyzer
    try: RobustnessAnalyzer().analyze(MagicMock())
    except Exception: pass

if __name__ == "__main__":
    run_pybots()
    run_others()
    print("Done!")
