"""Standalone usage evidence for FEAT-UTIL-14 notifications."""

import sys
from pathlib import Path

_USAGE_ROOT = Path(__file__).resolve().parents[1]
if str(_USAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(_USAGE_ROOT))

from notification_runtime import run_real_notification_evidence  # noqa: E402


def main() -> None:
    """Run a safe notification composition example without external delivery."""
    actual = dict(run_real_notification_evidence("FEAT-UTIL-14"))
    print("FEAT-UTIL-14 notification usage succeeded")
    print(actual)


if __name__ == "__main__":
    main()
