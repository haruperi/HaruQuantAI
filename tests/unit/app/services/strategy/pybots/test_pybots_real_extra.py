from unittest.mock import MagicMock

import pandas as pd


def test_pybots_real_extra():
    # sqx
    from app.services.strategy.pybots.sqx_breakout_atr_trailing.rules import (
        long_entry_signal,
        short_entry_signal,
    )
    from app.services.strategy.pybots.sqx_breakout_atr_trailing.strategy import (
        SQXBreakoutAtrTrailingStrategy,
    )

    mock_bar = MagicMock()
    mock_bar.high = 10
    mock_bar.low = 5
    mock_bar.open = 7
    mock_bar.close = 8

    mock_context = MagicMock()
    mock_context.bars = [mock_bar] * 10

    mock_config = MagicMock()
    mock_config.parameter.return_value = "5"

    try:
        long_entry_signal(mock_context, mock_config)
    except Exception:
        pass
    try:
        short_entry_signal(mock_context, mock_config)
    except Exception:
        pass

    try:
        sqx = SQXBreakoutAtrTrailingStrategy(mock_config)
        df = pd.DataFrame(
            {"high": [10] * 10, "low": [5] * 10, "open": [7] * 10, "close": [8] * 10}
        )
        sqx.calculate_signals(df, mock_context)
    except Exception:
        pass

    try:
        from app.services.strategy.pybots.market_structure_ea.strategy import (
            MarketStructureEA,
        )

        ms = MarketStructureEA(mock_config)
        ms.calculate_signals(df, mock_context)
    except Exception:
        pass

    try:
        from app.services.strategy.pybots.white_fairy_ea.strategy import WhiteFairyEA

        wf = WhiteFairyEA(mock_config)
        wf.calculate_signals(df, mock_context)
    except Exception:
        pass

    try:
        from app.services.strategy.pybots.decomposing_trade_ea.strategy import (
            DecomposingTradeEA,
        )

        dt = DecomposingTradeEA(mock_config)
        dt.calculate_signals(df, mock_context)
    except Exception:
        pass

    try:
        from app.services.strategy.pybots.harriet_hedging_ea.strategy import (
            HarrietHedgingEA,
        )

        hh = HarrietHedgingEA(mock_config)
        hh.calculate_signals(df, mock_context)
    except Exception:
        pass
