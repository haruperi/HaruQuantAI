"""Data Manager command registration, execution, and formatting utilities.

Description:
    Owns Data Manager headless parsers, service dispatch, output, and exit codes.
    Provides ASCII table formatters and dashboard presentation for the
    Data Manager workspace, rendering dataset catalogs and database summaries.
"""

from __future__ import annotations

import argparse
import json
from functools import partial
from typing import Any

from app.workspace.data_manager.cli_formatters import (
    BasketsCLI,
    BrokersCLI,
    CustomDataCLI,
    DataCLI,
    SessionsCLI,
    SymbolsCLI,
    format_basket_table,
    format_broker_table,
    format_custom_table,
    format_data_dashboard,
    format_dataset_table,
    format_review_table,
    format_session_table,
    format_symbol_table,
)

__all__ = [
    "BasketsCLI",
    "BrokersCLI",
    "CustomDataCLI",
    "DataCLI",
    "SessionsCLI",
    "SymbolsCLI",
    "format_basket_table",
    "format_broker_table",
    "format_custom_table",
    "format_data_dashboard",
    "format_dataset_table",
    "format_review_table",
    "format_session_table",
    "format_symbol_table",
    "register_commands",
    "run_command",
]


def register_commands(commands: Any) -> None:
    """Register Data Manager parsers and bind the domain command handler."""
    data_manager = commands.add_parser("data-manager", help="Manage workspace data")
    resources = data_manager.add_subparsers(dest="resource", required=True)
    from app.workspace.data_manager.symbols import register_symbol_commands

    register_symbol_commands(resources)
    from app.workspace.data_manager.sessions import register_session_commands

    register_session_commands(resources)
    from app.workspace.data_manager.brokers import register_broker_commands

    register_broker_commands(resources)
    from app.workspace.data_manager.baskets import register_basket_commands

    register_basket_commands(resources)
    from app.workspace.data_manager.custom import register_custom_commands
    from app.workspace.data_manager.dukascopy_cli import register_dukascopy_commands
    from app.workspace.data_manager.help import register_help_commands
    from app.workspace.data_manager.logs import register_log_commands

    register_log_commands(resources)
    register_custom_commands(resources)
    register_help_commands(resources)
    register_dukascopy_commands(resources)
    from app.workspace.data_manager.sources_cli import register_source_commands

    register_source_commands(resources)
    data_manager.set_defaults(handler=partial(run_command, parser=data_manager))


def run_command(
    arguments: argparse.Namespace, *, parser: argparse.ArgumentParser
) -> int:
    """Execute a Data Manager command, emit errors, and return its exit code."""
    from app.workspace.data_manager.baskets import run_basket_command
    from app.workspace.data_manager.brokers import run_broker_command
    from app.workspace.data_manager.custom import run_custom_command
    from app.workspace.data_manager.dukascopy_cli import run_dukascopy_command
    from app.workspace.data_manager.help import run_help_command
    from app.workspace.data_manager.logs import run_log_command
    from app.workspace.data_manager.sessions import run_session_command
    from app.workspace.data_manager.symbols import run_symbol_command

    handlers = {
        "session": run_session_command,
        "symbol": run_symbol_command,
        "broker": run_broker_command,
        "basket": run_basket_command,
        "log": run_log_command,
        "custom": run_custom_command,
        "help": run_help_command,
        "dukascopy": run_dukascopy_command,
    }
    from app.workspace.data_manager.sources import PROVIDERS
    from app.workspace.data_manager.sources_cli import run_source_command

    handlers.update(dict.fromkeys(PROVIDERS, run_source_command))
    result = handlers[arguments.resource](arguments, parser)
    if result is None:
        return 0
    print(json.dumps(result, allow_nan=False))
    return 0 if result["success"] else 1


if __name__ == "__main__":
    from app.workspace.data_manager.data import Data

    data_svc = Data()
    overview = data_svc.overview()
    saved_datasets = data_svc.list()
    print(DataCLI.format_data_dashboard(overview, saved_datasets))
