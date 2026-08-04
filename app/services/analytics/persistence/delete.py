"""Delete operations for Analytics-owned records.

Analytics deletes nothing. Every table here is derived and carries the
``source_hash`` of the inputs it was computed from, so a superseded value is
marked stale and recomputed rather than removed. Retaining it preserves what was
reported at the time a decision was made, which is the point of keeping
measurement history at all.

This module exists to satisfy the uniform persistence layout and exports
nothing.
"""

__all__: list[str] = []
