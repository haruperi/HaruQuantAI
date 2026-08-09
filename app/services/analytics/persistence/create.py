"""Analytics create-statement construction."""

from __future__ import annotations

from collections.abc import Mapping


def build_analytics_insert(
    table: str, record: Mapping[str, object]
) -> tuple[str, tuple[object, ...]]:
    """Build a parameterized insert for an allow-listed Analytics table.

    Returns:
        SQL and bound parameters.

    Raises:
        ValueError: If the table or record is unsupported.
    """
    allowed = {
        "analytics_journal_entries",
        "analytics_adherence_findings",
        "analytics_behavior_findings",
        "analytics_emergency_response_findings",
        "analytics_qualification_records",
    }
    if table not in allowed or not record:
        raise ValueError("unsupported Analytics insert")
    columns = tuple(record)
    sql = (
        f"INSERT INTO {table} ({', '.join(columns)}) "  # noqa: S608
        f"VALUES ({', '.join('?' for _ in columns)})"
    )
    return sql, tuple(record[column] for column in columns)
