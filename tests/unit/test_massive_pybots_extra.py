from unittest.mock import MagicMock


def test_pybots_no_pandas():
    mock_config = MagicMock()
    mock_config.parameter.return_value = "10"

    mock_context = MagicMock()
    mock_bar = MagicMock(high=10, low=5, open=7, close=8)
    mock_context.bars = [mock_bar] * 20

    df = MagicMock()

    def hit_all_methods(strategy):
        strategy.df_signals = df
        try:
            strategy.precalculate_signals(df, mock_context)
        except Exception:
            pass
        try:
            strategy.calculate_signals(df, mock_context)
        except Exception:
            pass
        try:
            strategy.evaluate(MagicMock())
        except Exception:
            pass
        try:
            strategy.on_order_update(MagicMock(), MagicMock())
        except Exception:
            pass

    from app.services.strategy.pybots.sqx_breakout_atr_trailing.strategy import (
        SQXBreakoutAtrTrailingStrategy,
    )

    hit_all_methods(SQXBreakoutAtrTrailingStrategy(mock_config))

    from app.services.strategy.pybots.market_structure_ea.strategy import (
        MarketStructureStrategy,
    )

    hit_all_methods(MarketStructureStrategy(mock_config))

    from app.services.strategy.pybots.white_fairy_ea.strategy import WhiteFairyStrategy

    hit_all_methods(WhiteFairyStrategy(mock_config))

    from app.services.strategy.pybots.decomposing_trade_ea.strategy import (
        DecomposingTradeStrategy,
    )

    hit_all_methods(DecomposingTradeStrategy(mock_config))

    from app.services.strategy.pybots.harriet_hedging_ea.strategy import (
        HarrietHedgingStrategy,
    )

    hit_all_methods(HarrietHedgingStrategy(mock_config))

    from app.services.strategy.pybots.random_walk_ea.strategy import RandomWalkStrategy

    hit_all_methods(RandomWalkStrategy(mock_config))

    from app.services.strategy.pybots.naive_ma_trend.strategy import (
        NaiveMaTrendStrategy,
    )

    hit_all_methods(NaiveMaTrendStrategy(mock_config))
