"""Pytest collection guard for the indicators usage examples.

The numbered ``NN_*.py`` files in this directory are intentionally *not*
pytest tests: they are standalone, runnable examples that exercise the public
Indicators API against real market data and real connections. They are
executed (and their exit status verified) by
``tests/indicators/integration/test_usage_scripts.py``.

The repository's global ``python_files`` config includes ``[0-9]*_*.py``, so
without this guard pytest would try to import the numbered scripts as test
modules (running their top-level example code at collection time). This
``collect_ignore_glob`` keeps them out of direct collection while leaving the
integration subprocess runner free to execute them.
"""

collect_ignore_glob = ["[0-9]*_*.py"]
