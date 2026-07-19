"""Standalone Trading reporting usage evidence."""

import asyncio
import inspect
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from tests.trading.usage import test_usage_reporting as examples


def _run_examples() -> int:
    """Run every bounded reporting example and return the executed count."""
    executed = 0
    for name, example in vars(examples).items():
        if not name.startswith("test_usage_") or not callable(example):
            continue
        result = example()
        if inspect.isawaitable(result):
            asyncio.run(result)
        executed += 1
    return executed


print("Trading reporting examples executed:", _run_examples())
