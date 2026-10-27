"""CLI commands and formatters for Data Manager external indicators."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable
from typing import Any

from ._helpers import (
    format_custom_table,
    format_review_table,
)
from .feature import CustomData

__all__ = ["register_custom_commands", "run_custom_command"]

_DEFAULT_PAGE_SIZE = 50
_DEFAULT_PREVIEW_LIMIT = 20
_DEFAULT_REVIEW_LIMIT = 100


def _parse_values_arg(value: str) -> list[dict[str, Any]]:
    clean = value.strip()
    if clean.startswith("["):
        try:
            parsed = json.loads(clean)
            if isinstance(parsed, list):
                return parsed
        except json.JSONDecodeError:
            pass
    return [{"name": name.strip()} for name in clean.split(",") if name.strip()]


def _parse_columns_arg(value: str) -> list[str]:
    clean = value.strip()
    if clean.startswith("["):
        try:
            parsed = json.loads(clean)
            if isinstance(parsed, list):
                return [str(c) for c in parsed]
        except json.JSONDecodeError:
            pass
    return [c.strip() for c in clean.split(",") if c.strip()]


def _parse_config_arg(value: str) -> dict[str, Any]:
    try:
        parsed = json.loads(value)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError as error:
        raise argparse.ArgumentTypeError(f"Invalid JSON config: {error}") from error
    raise argparse.ArgumentTypeError("Config must be a JSON object")


def _positive_int(value: str) -> int:
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return number


def register_custom_commands(resources: Any) -> None:
    """Register custom data indicators commands under resources."""
    custom = resources.add_parser(
        "custom", help="Manage external indicators and custom data"
    )
    commands = custom.add_subparsers(dest="custom_command", required=True)
    _add_def_parsers(commands)
    _add_import_parsers(commands)
    _add_transfer_parsers(commands)


def _add_def_parsers(commands: Any) -> None:
    listing = commands.add_parser("list", help="List external indicators")
    listing.add_argument("--page", type=_positive_int, default=1)
    listing.add_argument("--page-size", type=_positive_int, default=_DEFAULT_PAGE_SIZE)

    add = commands.add_parser("add", help="Add external indicator definition")
    add.add_argument("--name", required=True, help="Indicator name")
    add.add_argument(
        "--values",
        required=True,
        help="JSON output definitions or comma-separated names",
    )
    add.add_argument("--data-type", default="custom", help="Indicator data type")
    add.add_argument("--timeframe", default="D1", help="Timeframe (e.g. D1, W1)")
    add.add_argument("--system", action=argparse.BooleanOptionalAction, default=False)

    edit = commands.add_parser("edit", help="Edit external indicator definition")
    edit.add_argument("indicator_name", help="Indicator name to edit")
    edit.add_argument("--name", default=argparse.SUPPRESS, help="New name")
    edit.add_argument(
        "--values",
        default=argparse.SUPPRESS,
        help="New values JSON or comma-separated names",
    )
    edit.add_argument("--data-type", default=argparse.SUPPRESS)
    edit.add_argument("--timeframe", default=argparse.SUPPRESS)

    delete = commands.add_parser(
        "delete", help="Delete external indicator definition and data"
    )
    delete.add_argument("indicator_names", nargs="+", help="Indicator names to delete")

    clear = commands.add_parser("clear", help="Clear external indicator observations")
    clear.add_argument("indicator_names", nargs="+", help="Indicator names to clear")

    review = commands.add_parser(
        "review-data", help="Review dated observations for an indicator"
    )
    review.add_argument("indicator_name", help="Indicator name")
    review.add_argument("--limit", type=_positive_int, default=_DEFAULT_REVIEW_LIMIT)
    review.add_argument("--offset", type=int, default=0)


def _add_import_parsers(commands: Any) -> None:
    recognize = commands.add_parser("recognize", help="Recognize indicator from file")
    recognize.add_argument("file_path", help="Source file path (.json, .mq4, .mq5)")

    imp = commands.add_parser(
        "import-data", help="Import dated observations from CSV file"
    )
    imp.add_argument("indicator_name", help="Indicator name")
    imp.add_argument("file_path", help="CSV file path")
    imp.add_argument("--format-name", default=None, help="Preset import format name")
    imp.add_argument("--replace", action=argparse.BooleanOptionalAction, default=False)
    imp.add_argument("--separator", default=argparse.SUPPRESS)
    imp.add_argument("--date-format", default=argparse.SUPPRESS)
    imp.add_argument("--skip-rows", type=int, default=argparse.SUPPRESS)
    imp.add_argument("--skip-columns", type=int, default=argparse.SUPPRESS)
    imp.add_argument(
        "--columns",
        default=argparse.SUPPRESS,
        help="JSON list or comma-separated column mapping",
    )
    imp.add_argument(
        "--error-handling", choices=["abort", "skip"], default=argparse.SUPPRESS
    )

    preview = commands.add_parser(
        "import-preview", help="Preview observations parsed from CSV file"
    )
    preview.add_argument("indicator_name", help="Indicator name")
    preview.add_argument("file_path", help="CSV file path")
    preview.add_argument("--format-name", default=None)
    preview.add_argument("--limit", type=_positive_int, default=_DEFAULT_PREVIEW_LIMIT)
    preview.add_argument("--separator", default=argparse.SUPPRESS)
    preview.add_argument("--date-format", default=argparse.SUPPRESS)
    preview.add_argument("--skip-rows", type=int, default=argparse.SUPPRESS)
    preview.add_argument("--skip-columns", type=int, default=argparse.SUPPRESS)
    preview.add_argument("--columns", default=argparse.SUPPRESS)
    preview.add_argument(
        "--error-handling", choices=["abort", "skip"], default=argparse.SUPPRESS
    )

    commands.add_parser("import-info", help="Get supported import presets and options")

    action = commands.add_parser(
        "import-action", help="Pause, resume or stop import job"
    )
    action.add_argument("job_id", help="Job ID")
    action.add_argument("action", choices=["pause", "resume", "stop"])


def _add_transfer_parsers(commands: Any) -> None:
    add_fmt = commands.add_parser("add-format", help="Add import format preset")
    add_fmt.add_argument("name", help="Preset format name")
    add_fmt.add_argument("--config", required=True, help="JSON config for format")

    edit_fmt = commands.add_parser("edit-format", help="Edit import format preset")
    edit_fmt.add_argument("name", help="Preset format name")
    edit_fmt.add_argument("--config", required=True, help="JSON config for format")

    del_fmt = commands.add_parser("delete-format", help="Delete import format preset")
    del_fmt.add_argument("name", help="Preset format name")

    exp = commands.add_parser("export-values", help="Export dated observations to CSV")
    exp.add_argument("indicator_name", help="Indicator name")
    exp.add_argument("csv_path", help="Destination CSV path")

    cot = commands.add_parser("update-cot", help="Update Commitments of Traders data")
    cot.add_argument("--years", nargs="*", type=int, default=None)

    save = commands.add_parser("save", help="Save indicator definitions to JSON")
    save.add_argument("json_path", help="Destination JSON path")
    save.add_argument(
        "--indicators", nargs="*", default=None, help="Names of indicators to save"
    )

    load = commands.add_parser("load", help="Load indicator definitions from JSON")
    load.add_argument("json_path", help="Source JSON path")
    load.add_argument(
        "--on-conflict",
        choices=["error", "skip", "overwrite"],
        default="error",
    )


def _cmd_list(
    service: CustomData, args: argparse.Namespace, parser: Any
) -> dict[str, Any] | None:
    result = service.list()
    if not result["success"]:
        return result
    rows = result["data"]
    pages = max(1, (len(rows) + args.page_size - 1) // args.page_size)
    if args.page > pages:
        parser.error("--page exceeds the number of catalog pages")
    print(f"Page {args.page} of {pages} | {len(rows)} indicators")
    start = (args.page - 1) * args.page_size
    print(format_custom_table(rows[start : start + args.page_size], limit=None))
    return None


def _cmd_add(service: CustomData, args: argparse.Namespace) -> dict[str, Any] | None:
    vals = _parse_values_arg(args.values)
    res = service.add(
        args.name,
        values=vals,
        data_type=args.data_type,
        timeframe=args.timeframe,
        system=args.system,
    )
    if res["success"]:
        print(res["message"])
        print(format_custom_table([res["data"]], limit=None))
        return None
    return res


def _cmd_edit(
    service: CustomData, args: argparse.Namespace, parser: Any
) -> dict[str, Any] | None:
    fields: dict[str, Any] = {}
    for key in ("name", "data_type", "timeframe"):
        if hasattr(args, key):
            fields[key] = getattr(args, key)
    if hasattr(args, "values"):
        fields["values"] = _parse_values_arg(args.values)
    if not fields:
        parser.error("custom edit requires at least one field to update")
    res = service.edit(args.indicator_name, fields)
    if res["success"]:
        print(res["message"])
        print(format_custom_table([res["data"]], limit=None))
        return None
    return res


def _cmd_delete(service: CustomData, args: argparse.Namespace) -> dict[str, Any] | None:
    res = service.delete(args.indicator_names)
    if res["success"]:
        print(res["message"])
        for name in res["data"]["names"]:
            print(name)
        return None
    return res


def _cmd_clear(service: CustomData, args: argparse.Namespace) -> dict[str, Any] | None:
    res = service.clear(args.indicator_names)
    if res["success"]:
        count = res["data"]["cleared_records"]
        num = len(res["data"]["names"])
        print(f"Cleared {count} observations across {num} indicators")
        return None
    return res


def _cmd_review(service: CustomData, args: argparse.Namespace) -> dict[str, Any] | None:
    res = service.review_data(args.indicator_name, limit=args.limit, offset=args.offset)
    if res["success"]:
        print(f"Review observations for {res['data']['name']}:")
        print(format_review_table(res["data"]["records"], res["data"]["columns"]))
        return None
    return res


def _cmd_recognize(
    service: CustomData, args: argparse.Namespace
) -> dict[str, Any] | None:
    res = service.recognize_from_file(args.file_path)
    if res["success"]:
        print(res["message"])
        print(format_custom_table([res["data"]], limit=None))
        return None
    return res


def _cmd_import_data(
    service: CustomData, args: argparse.Namespace
) -> dict[str, Any] | None:
    options: dict[str, Any] = {}
    for opt in (
        "separator",
        "date_format",
        "skip_rows",
        "skip_columns",
        "error_handling",
    ):
        if hasattr(args, opt):
            options[opt] = getattr(args, opt)
    if hasattr(args, "columns"):
        options["columns"] = _parse_columns_arg(args.columns)
    res = service.import_data(
        args.indicator_name,
        args.file_path,
        format_name=args.format_name,
        replace=args.replace,
        **options,
    )
    if res["success"]:
        count = res["data"]["imported_count"]
        skipped = res["data"]["skipped_rows"]
        print(f"Imported {count} observations ({skipped} skipped)")
        return None
    return res


def _cmd_import_preview(
    service: CustomData, args: argparse.Namespace
) -> dict[str, Any] | None:
    options: dict[str, Any] = {}
    for opt in (
        "separator",
        "date_format",
        "skip_rows",
        "skip_columns",
        "error_handling",
    ):
        if hasattr(args, opt):
            options[opt] = getattr(args, opt)
    if hasattr(args, "columns"):
        options["columns"] = _parse_columns_arg(args.columns)
    res = service.import_preview(
        args.indicator_name,
        args.file_path,
        format_name=args.format_name,
        limit=args.limit,
        **options,
    )
    if res["success"]:
        total = res["data"]["total_records"]
        print(f"Preview for {args.indicator_name} ({total} records found):")
        cols = [
            c
            for c in res["data"]["format"].get("columns", [])
            if c not in ("date", "ignore")
        ]
        print(format_review_table(res["data"]["records"], cols))
        return None
    return res


def _cmd_import_info(service: CustomData) -> dict[str, Any] | None:
    res = service.import_get_info()
    if res["success"]:
        print("Import Formats & Settings:")
        print(json.dumps(res["data"], indent=2))
        return None
    return res


def _cmd_import_action(
    service: CustomData, args: argparse.Namespace
) -> dict[str, Any] | None:
    res = service.import_action(args.job_id, args.action)
    if res["success"]:
        print(res["message"])
        return None
    return res


def _cmd_format(
    service: CustomData, args: argparse.Namespace, cmd: str
) -> dict[str, Any] | None:
    if cmd == "delete-format":
        res = service.delete_import_format(args.name)
        if res["success"]:
            print(res["message"])
            return None
        return res
    config = _parse_config_arg(args.config)
    action = (
        service.edit_import_format
        if cmd == "edit-format"
        else service.add_import_format
    )
    res = action(args.name, config)
    if res["success"]:
        print(res["message"])
        print(json.dumps(res["data"], indent=2))
        return None
    return res


def _cmd_cot(service: CustomData, args: argparse.Namespace) -> dict[str, Any] | None:
    res = service.update_cot(years=args.years)
    if res["success"]:
        count = res["data"]["updated_count"]
        recs = res["data"]["records"]
        print(f"Updated {count} COT indicators ({recs} records)")
        return None
    return res


def _cmd_file_transfer(
    service: CustomData, args: argparse.Namespace, cmd: str
) -> dict[str, Any] | None:
    if cmd == "export-values":
        res = service.export_values(args.indicator_name, args.csv_path)
        if res["success"]:
            print(f"Exported {res['data']['count']} rows to {res['data']['path']}")
            return None
        return res
    if cmd == "save":
        res = service.save(args.json_path, names=args.indicators)
        if res["success"]:
            print(f"Saved {res['data']['count']} indicators to {res['data']['path']}")
            return None
        return res
    res = service.load(args.json_path, on_conflict=args.on_conflict)
    if res["success"]:
        loaded = res["data"]["loaded_count"]
        skipped = len(res["data"]["skipped"])
        print(f"Loaded {loaded} indicators ({skipped} skipped)")
        return None
    return res


def _get_service() -> Any:
    mod = sys.modules.get("app.workspace.data_manager.custom")
    cls = getattr(mod, "CustomData", CustomData) if mod else CustomData
    return cls()


def run_custom_command(
    arguments: argparse.Namespace, parser: Any
) -> dict[str, Any] | None:
    """Execute custom data indicators command and print formatted output."""
    service = _get_service()
    cmd = arguments.custom_command

    handlers: dict[str, Callable[[], dict[str, Any] | None]] = {
        "list": lambda: _cmd_list(service, arguments, parser),
        "add": lambda: _cmd_add(service, arguments),
        "edit": lambda: _cmd_edit(service, arguments, parser),
        "delete": lambda: _cmd_delete(service, arguments),
        "clear": lambda: _cmd_clear(service, arguments),
        "review-data": lambda: _cmd_review(service, arguments),
        "recognize": lambda: _cmd_recognize(service, arguments),
        "import-data": lambda: _cmd_import_data(service, arguments),
        "import-preview": lambda: _cmd_import_preview(service, arguments),
        "import-info": lambda: _cmd_import_info(service),
        "import-action": lambda: _cmd_import_action(service, arguments),
        "add-format": lambda: _cmd_format(service, arguments, cmd),
        "edit-format": lambda: _cmd_format(service, arguments, cmd),
        "delete-format": lambda: _cmd_format(service, arguments, cmd),
        "export-values": lambda: _cmd_file_transfer(service, arguments, cmd),
        "update-cot": lambda: _cmd_cot(service, arguments),
        "save": lambda: _cmd_file_transfer(service, arguments, cmd),
        "load": lambda: _cmd_file_transfer(service, arguments, cmd),
    }

    handler = handlers.get(cmd)
    if handler is not None:
        return handler()

    return {"success": False, "message": f"Unknown custom command: {cmd}"}
