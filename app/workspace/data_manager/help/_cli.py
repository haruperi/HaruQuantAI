"""CLI commands for Data Manager contextual help, tutorials, and articles."""

from __future__ import annotations

import argparse
import sys
from typing import Any

from .feature import Help

__all__ = ["register_help_commands", "run_help_command"]


def _get_service() -> Any:
    mod = sys.modules.get("app.workspace.data_manager.help")
    cls = getattr(mod, "Help", Help) if mod else Help
    return cls()


def register_help_commands(resources: Any) -> None:
    """Register contextual help commands under the data-manager parser."""
    parser = resources.add_parser(
        "help", help="Access Data Manager guidance, tutorials, and documentation"
    )
    commands = parser.add_subparsers(dest="help_command", required=True)

    topic = commands.add_parser("topic", help="Show guidance for a topic or tab")
    topic.add_argument(
        "name",
        nargs="?",
        default="overview",
        help="Topic name (e.g. overview, symbols, export, custom-data)",
    )

    commands.add_parser("list-topics", help="List all Data Manager topics")

    tutorials = commands.add_parser(
        "list-tutorials", help="List step-by-step tutorials"
    )
    tutorials.add_argument("--topic", default=None, help="Filter tutorials by topic")

    tutorial = commands.add_parser("get-tutorial", help="Show tutorial steps by ID")
    tutorial.add_argument("tutorial_id", help="Tutorial ID")

    articles = commands.add_parser(
        "list-articles", help="List donor documentation articles and URLs"
    )
    articles.add_argument("--topic", default=None, help="Filter articles by topic")

    search = commands.add_parser("search", help="Search help by keyword")
    search.add_argument("query", help="Keyword or search phrase")


def run_help_command(
    arguments: argparse.Namespace, _parser: argparse.ArgumentParser
) -> dict[str, Any]:
    """Execute the parsed help command against the Help service."""
    service = _get_service()
    handlers = {
        "topic": lambda: service.get_topic(arguments.name),
        "list-topics": service.list_topics,
        "list-tutorials": lambda: service.list_tutorials(arguments.topic),
        "get-tutorial": lambda: service.get_tutorial(arguments.tutorial_id),
        "list-articles": lambda: service.list_articles(arguments.topic),
        "search": lambda: service.search(arguments.query),
    }
    handler = handlers.get(
        arguments.help_command, lambda: service.get_topic("overview")
    )
    return handler()
