"""
Usage example for tools.utils.errors.

Run from the project root:

    python tests/usage/tools/utils/errors.py
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools.utils import (
    descriptor_from_payload,
    descriptor_to_dict,
    error_from_retcode,
    error_info_to_dict,
    exception_from_descriptor,
    is_success_retcode,
    raise_for_retcode,
)


def explain_retcode(code: int) -> None:
    """Print a JSON-safe explanation for an MT5/trade return code."""

    info = error_from_retcode(code)
    print(error_info_to_dict(info))


def map_payload_to_exception() -> None:
    """Build a descriptor from a broker payload and map it to an exception."""

    payload = {
        "code": 10014,
        "message": "The requested lot size is below broker minimum.",
    }
    descriptor = descriptor_from_payload(payload)
    exception = exception_from_descriptor(descriptor)

    print(descriptor_to_dict(descriptor))
    print(type(exception).__name__)


def handle_retcode(code: int) -> None:
    """Raise a typed exception only when the retcode indicates failure."""

    if is_success_retcode(code):
        print(f"Retcode {code} succeeded.")
        return

    try:
        raise_for_retcode(code, message="Broker returned a failure.")
    except Exception as error:
        print(str(error))


if __name__ == "__main__":
    explain_retcode(10018)
    map_payload_to_exception()
    handle_retcode(10014)
