"""Simple deterministic replay clock for Python-side simulator playback."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass


@dataclass
class ReplayClock:
    """Deterministic replay cursor over pre-built timeline points."""

    timeline: list[object]
    index: int = 0

    @classmethod
    def from_timeline(cls, timeline: Iterable[object]) -> ReplayClock:
        return cls(list(timeline), index=0)

    @property
    def finished(self) -> bool:
        return self.index >= len(self.timeline)

    @property
    def current(self) -> object | None:
        if self.finished:
            return None
        return self.timeline[self.index]

    def reset(self) -> None:
        self.index = 0

    def advance(self) -> object | None:
        if self.finished:
            return None
        current = self.timeline[self.index]
        self.index += 1
        return current

    def step(self, count: int = 1) -> object | None:
        if count <= 0:
            return self.current
        out = None
        for _ in range(count):
            out = self.advance()
            if out is None:
                break
        return out
