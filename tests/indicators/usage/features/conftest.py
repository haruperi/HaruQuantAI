"""Pytest collection guard for standalone indicators feature usage programs.

The numbered ``NN_*.py`` files and ``features.py`` in this directory are
intentionally *not* pytest tests: they are standalone, runnable examples that
exercise the public Indicators API against real market data and real connections.
They are executed (and their exit status verified) by
``tests/indicators/integration/test_usage_scripts.py``.

This ``collect_ignore_glob`` keeps them out of direct collection while leaving
the integration subprocess runner free to execute them.
"""

collect_ignore_glob = ["*.py"]
