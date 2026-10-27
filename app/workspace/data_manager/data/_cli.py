"""CLI formatters and command execution for Data Manager datasets service."""

from __future__ import annotations

from app.workspace.data_manager.cli_formatters import (
    DataCLI,
    format_data_dashboard,
    format_dataset_table,
)

from .feature import Data

__all__ = [
    "DataCLI",
    "format_data_dashboard",
    "format_dataset_table",
    "main",
]


def main() -> None:
    """Print the data overview and datasets dashboard."""
    data_svc = Data()
    overview = data_svc.overview()
    saved_datasets = data_svc.list()
    print(DataCLI.format_data_dashboard(overview, saved_datasets))


if __name__ == "__main__":
    main()
