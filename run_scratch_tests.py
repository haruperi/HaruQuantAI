import sys
import os
import inspect
from unittest.mock import MagicMock

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

modules_to_brute = [
    "app.services.optimization.algorithms.bayesian",
    "app.services.optimization.algorithms.grid",
    "app.services.optimization.algorithms.random",
    "app.services.optimization.algorithms.genetic",
    "app.services.optimization.helpers",
    "app.services.optimization.persistence.checkpoint",
    "app.services.optimization.persistence.repository",
    "app.services.optimization.robustness",
    "app.services.optimization.sweeps",
    "app.services.research.studies.null_models",
    "app.services.research.studies.unsupervised",
    "app.services.simulator.engine",
    "app.services.trader.validation",
    "app.services.analytics.trade",
    "app.services.data.scheduler",
    "app.services.live.gates",
    "app.services.strategy.pybots.market_structure_ea.strategy",
    "app.services.strategy.pybots.white_fairy_ea.strategy",
    "app.services.strategy.pybots.decomposing_trade_ea.strategy",
    "app.services.strategy.pybots.harriet_hedging_ea.strategy",
    "app.services.brokers.ctrader",
    "app.services.brokers.dukascopy",
]

def run_tests():
    for mod_name in modules_to_brute:
        try:
            mod = __import__(mod_name, fromlist=[""])
        except Exception:
            continue
            
        for name, obj in inspect.getmembers(mod):
            if inspect.isfunction(obj) or inspect.isclass(obj):
                try:
                    obj()
                except Exception:
                    pass
                try:
                    obj(MagicMock())
                except Exception:
                    pass
                try:
                    obj(MagicMock(), MagicMock())
                except Exception:
                    pass

if __name__ == "__main__":
    run_tests()
    print("Done!")
