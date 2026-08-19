"""Origin provenance for canonical runs the gateway itself started (FEAT-API-27).

The Simulator knows only that it ran a canonical job; it has no reason to
know that the gateway started that job on behalf of a batch or to reproduce
a finalized session. This bounded in-process index carries exactly that
gateway-owned provenance from the submission site to the completion sink, so
a catalogue row records why the run exists.
"""

from __future__ import annotations

import threading
from collections import OrderedDict
from collections.abc import Mapping

from app.utils import get_logger

logger = get_logger(__name__)

#: Maximum retained in-flight provenance entries before the oldest is evicted.
MAX_TRACKED_RUNS = 1_000


class RunProvenanceIndex:
    """Bounded job-to-origin index shared by the runners and the sink."""

    def __init__(self, *, max_entries: int = MAX_TRACKED_RUNS) -> None:
        """Build one empty bounded provenance index.

        Args:
            max_entries: Maximum retained entries before oldest eviction.
        """
        self._entries: OrderedDict[str, Mapping[str, object]] = OrderedDict()
        self._max_entries = max_entries
        self._lock = threading.Lock()

    def record(self, job_id: str, values: Mapping[str, object]) -> None:
        """Record the gateway-owned origin of one submitted job.

        Args:
            job_id: Simulator job identity returned by submission.
            values: Catalogue origin columns to apply to the finished run.
        """
        if not job_id:
            return
        with self._lock:
            self._entries[job_id] = dict(values)
            self._entries.move_to_end(job_id)
            while len(self._entries) > self._max_entries:
                evicted, _ = self._entries.popitem(last=False)
                logger.warning("Evicted Simulation run provenance for job %s", evicted)

    def resolve(self, job_id: str) -> Mapping[str, object]:
        """Return and release the recorded origin of one finished job.

        Args:
            job_id: Simulator job identity carried by the owner projection.

        Returns:
            Recorded origin columns, or an empty mapping when the run has no
            gateway-owned origin.
        """
        with self._lock:
            return self._entries.pop(job_id, {})


__all__ = ("MAX_TRACKED_RUNS", "RunProvenanceIndex")
