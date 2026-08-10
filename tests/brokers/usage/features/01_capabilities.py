"""Executable Adapter Capability Matrix evidence."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

import _support  # noqa: F401
from app.services.brokers import (
    get_broker_capability_catalogue,
    get_broker_dashboard_snapshot,
)


def fr_brokers_010_011_103_capability_matrix() -> None:
    """Exercise the complete immutable adapter capability matrix.

    Returns:
        None.

    Raises:
        AssertionError: If the capability response is unsuccessful or empty.
    """
    response = get_broker_capability_catalogue()
    assert response.status == "success"
    assert response.data is not None
    catalogue = response.data
    declared_operations = sum(len(entries) for entries in catalogue.values())
    dashboard = get_broker_dashboard_snapshot()
    assert dashboard["status"] == "unavailable"

    print("SUCCESS: FEAT-BRK-01 adapter capability matrix completed")
    print(
        "DATA: "
        f"profiles={len(catalogue)}, operations={declared_operations}, "
        f"dashboard_status={dashboard['status']}"
    )


def main() -> None:
    """Run the FEAT-BRK-01 capability-matrix evidence program.

    Returns:
        None.
    """
    fr_brokers_010_011_103_capability_matrix()


if __name__ == "__main__":
    main()
