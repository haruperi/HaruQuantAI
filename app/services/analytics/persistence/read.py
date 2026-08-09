"""Analytics read-statement construction."""


def build_analytics_select(
    table: str, key_column: str, key: object
) -> tuple[str, tuple[object, ...]]:
    """Build a parameterized record lookup.

    Returns:
        SQL and bound parameters.

    Raises:
        ValueError: If the table or key column is unsupported.
    """
    allowed = {
        "analytics_journal_entries",
        "analytics_adherence_findings",
        "analytics_behavior_findings",
        "analytics_emergency_response_findings",
        "analytics_qualification_records",
    }
    if table not in allowed or not key_column.replace("_", "").isalnum():
        raise ValueError("unsupported Analytics lookup")
    sql = f"SELECT * FROM {table} WHERE {key_column} = ?"  # noqa: S608
    return sql, (key,)
