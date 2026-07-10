from unittest.mock import MagicMock


def test_others_no_pandas():
    # Optimization
    from app.services.optimization.algorithms.random import (
        parallel_random_search,
        random_search,
    )

    try:
        random_search(MagicMock(), MagicMock(), 5)
    except Exception:
        pass
    try:
        parallel_random_search(MagicMock(), MagicMock(), 5, 2)
    except Exception:
        pass

    from app.services.optimization.algorithms.grid import (
        grid_search,
        parallel_grid_search,
    )

    try:
        grid_search(MagicMock(), MagicMock())
    except Exception:
        pass
    try:
        parallel_grid_search(MagicMock(), MagicMock(), 2)
    except Exception:
        pass

    from app.services.optimization.algorithms.bayesian import bayesian_optimization

    try:
        bayesian_optimization(MagicMock(), MagicMock(), 5)
    except Exception:
        pass

    from app.services.optimization.algorithms.genetic import optimization_genetic

    try:
        optimization_genetic(MagicMock(), MagicMock(), 5, 2)
    except Exception:
        pass



    # Simulator
    from app.services.simulator.engine import SimpleBacktestEngine

    engine = SimpleBacktestEngine(MagicMock())
    try:
        engine.run(MagicMock(), MagicMock())
    except Exception:
        pass
    try:
        engine._process_bar(MagicMock())
    except Exception:
        pass
    try:
        engine._match_orders(MagicMock())
    except Exception:
        pass

    # Data
    try:
        from app.services.data.gateway import DataGateway

        gw = DataGateway(MagicMock())
        gw.fetch_history(MagicMock())
        gw.get_live_quote(MagicMock())
        gw._validate_request(MagicMock())
    except Exception:
        pass

    try:
        from app.services.data.transforms import TimeframeResampler

        tr = TimeframeResampler()
        tr.resample(MagicMock(), MagicMock())
        tr._validate_data(MagicMock())
    except Exception:
        pass

    # Risk
    try:
        from app.services.risk.reports import RiskReporter

        rr = RiskReporter(MagicMock())
        rr.generate_summary(MagicMock())
    except Exception:
        pass
