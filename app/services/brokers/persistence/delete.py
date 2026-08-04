"""Delete operations for Brokers-owned records.

Brokers deletes nothing. Symbol mappings are bitemporal reference data: a
mapping that no longer applies is closed with an ``effective_to`` or disabled,
never removed. Deleting one would make a historical bar unresolvable and change
what a past backtest appears to have traded.

This module exists to satisfy the uniform persistence layout and exports
nothing.
"""

__all__: list[str] = []
