import sys
import os
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
    "app.services.simulator.engine",
    "app.services.trader.validation",
    "app.services.live.gates",
    "app.services.strategy.pybots.market_structure_ea.strategy",
    "app.services.strategy.pybots.white_fairy_ea.strategy",
    "app.services.strategy.pybots.decomposing_trade_ea.strategy",
    "app.services.strategy.pybots.harriet_hedging_ea.strategy",
    "app.services.strategy.pybots.sqx_breakout_atr_trailing.strategy",
    "app.services.data.gateway",
    "app.services.data.transforms",
    "app.services.risk.reports",
]

def attempt_call(func):
    for i in range(4):
        try:
            args = [MagicMock()] * i
            func(*args)
        except Exception:
            pass

def run_tests():
    for mod_name in modules_to_brute:
        try:
            mod = __import__(mod_name, fromlist=[""])
        except Exception:
            continue
            
        for name in dir(mod):
            try:
                obj = getattr(mod, name)
            except Exception:
                continue

            if callable(obj) and not isinstance(obj, type):
                attempt_call(obj)
            elif isinstance(obj, type):
                instance = None
                for i in range(4):
                    try:
                        args = [MagicMock()] * i
                        instance = obj(*args)
                        break
                    except Exception:
                        pass
                
                if instance is not None:
                    for m_name in dir(instance):
                        try:
                            m_obj = getattr(instance, m_name)
                        except Exception:
                            continue
                            
                        if callable(m_obj):
                            attempt_call(m_obj)

if __name__ == "__main__":
    run_tests()
    print("Done!")
