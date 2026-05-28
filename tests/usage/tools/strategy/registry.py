"""Usage example for HaruQuant strategy registry tools."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools.strategy import (
    get_strategy_metadata,
    list_strategy_names,
    register_builtin_strategy_tools,
)


def main() -> None:
    """Register built-in strategies and inspect their metadata."""
    register_result = register_builtin_strategy_tools(
        request_id="usage-strategy-registry-register-001"
    )
    if register_result["status"] != "success":
        print(register_result["error"])
        return

    names_result = list_strategy_names(request_id="usage-strategy-registry-list-001")
    if names_result["status"] != "success":
        print(names_result["error"])
        return

    first_strategy = names_result["data"]["strategies"][0]
    metadata_result = get_strategy_metadata(
        first_strategy,
        request_id="usage-strategy-registry-metadata-001",
    )
    if metadata_result["status"] == "success":
        print(metadata_result["data"]["strategy"])
    else:
        print(metadata_result["error"])


if __name__ == "__main__":
    main()
