"""Usage example for saving a HaruQuant strategy source snapshot."""

from __future__ import annotations

import sys
from pathlib import Path
from tempfile import TemporaryDirectory

PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools.strategy import save_strategy_source_file


def main() -> None:
    """Save a simple local strategy source snapshot."""
    source_code = """
class ExampleStrategy:
    strategy_name = "ExampleStrategy"
""".strip()

    with TemporaryDirectory() as temp_dir:
        result = save_strategy_source_file(
            base_dir=temp_dir,
            strategy_name="example_strategy",
            version="1.0.0",
            source_code=source_code,
            parameters={"symbol": "EURUSD", "timeframe": "H1"},
            request_id="usage-strategy-storage-save-001",
        )
        if result["status"] == "success":
            print(result["data"]["path"])
        else:
            print(result["error"])


if __name__ == "__main__":
    main()
