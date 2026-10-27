"""Data Manager custom indicators catalog service package.

Description:
    Provides external indicator definitions, dated values, CSV imports,
    and CFTC Commitments of Traders (COT) report synchronization.
"""

from __future__ import annotations

from app.workspace.data_manager.cli_formatters import (
    CustomDataCLI,
    format_custom_table,
    format_review_table,
)

from ._cli import (
    register_custom_commands,
    run_custom_command,
)
from ._helpers import (
    CustomDataError,
    definition_file,
    fetch_cot,
    normalize_format,
    parse_cot_reports,
    parse_csv_row,
    read_all,
    read_text,
    response_data,
    timestamp,
    validate_name,
    validate_outputs,
)
from .feature import CustomData
from .http import register_custom_routes

__all__ = [
    "CustomData",
    "CustomDataCLI",
    "CustomDataError",
    "definition_file",
    "fetch_cot",
    "format_custom_table",
    "format_review_table",
    "normalize_format",
    "parse_cot_reports",
    "parse_csv_row",
    "read_all",
    "read_text",
    "register_custom_commands",
    "register_custom_routes",
    "response_data",
    "run_custom_command",
    "timestamp",
    "validate_name",
    "validate_outputs",
]
