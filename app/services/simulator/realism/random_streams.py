"""Pinned counter-based deterministic realism streams."""

# ruff: noqa: DOC201, DOC501

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal
from hashlib import sha256

from app.utils import canonical_digest, canonical_json

_ALGORITHM = "sha256-counter-u256-v1"
_TRACE_FIELDS = frozenset(
    {"request_id", "workflow_id", "correlation_id", "causation_id", "trace_id"}
)
_DENOMINATOR = Decimal(2**256)
_PERFORMANCE_BUDGETS: Mapping[str, object] = {
    "annual_m1_events": 370_000,
    "annual_wall_seconds": Decimal("5.0"),
    "multi_symbol_count": 10,
    "multi_symbol_events": 100_000,
    "multi_symbol_wall_seconds": Decimal("2.0"),
    "peak_rss_growth_mib": Decimal(64),
}


def _economic_material(configuration: Mapping[str, object]) -> Mapping[str, object]:
    """Remove trace-only identity before deriving economic streams."""
    material = {
        key: value for key, value in configuration.items() if key not in _TRACE_FIELDS
    }
    canonical_json(material)
    return material


@dataclass(slots=True, kw_only=True)
class _RealismStream:
    """Private mutable counter with immutable derivation identity."""

    stream_id: str
    concern: str
    configuration_hash: str
    seed_digest: str
    counter: int = 0
    algorithm: str = _ALGORITHM

    def draw(self) -> Decimal:
        """Return the next exact uniform Decimal and advance once."""
        material = f"{self.seed_digest}:{self.counter}".encode()
        value = Decimal(int(sha256(material).hexdigest(), 16)) / _DENOMINATOR
        self.counter += 1
        return value


def create(configuration: Mapping[str, object], concern: str) -> _RealismStream:
    """Derive an isolated concern stream from canonical economic configuration."""
    if not concern or concern != concern.strip():
        raise ValueError("realism concern must be non-empty trimmed text")
    configuration_hash = canonical_digest(_economic_material(configuration))
    seed_digest = canonical_digest(
        {
            "algorithm": _ALGORITHM,
            "configuration_hash": configuration_hash,
            "concern": concern,
        }
    )
    return _RealismStream(
        stream_id=f"realism-stream-{seed_digest}",
        concern=concern,
        configuration_hash=configuration_hash,
        seed_digest=seed_digest,
    )


def sample(stream: object) -> Decimal:
    """Draw once from a validated realism stream."""
    if not isinstance(stream, _RealismStream):
        raise TypeError("invalid realism stream")
    return stream.draw()


def serialize(stream: object) -> dict[str, object]:
    """Serialize exact generator identity and counter state."""
    if not isinstance(stream, _RealismStream):
        raise TypeError("invalid realism stream")
    return {
        "stream_id": stream.stream_id,
        "concern": stream.concern,
        "configuration_hash": stream.configuration_hash,
        "seed_digest": stream.seed_digest,
        "counter": stream.counter,
        "algorithm": stream.algorithm,
    }


def restore(state: Mapping[str, object]) -> _RealismStream:
    """Restore a stream only when its pinned identity is internally consistent."""
    stream = _RealismStream(
        stream_id=str(state["stream_id"]),
        concern=str(state["concern"]),
        configuration_hash=str(state["configuration_hash"]),
        seed_digest=str(state["seed_digest"]),
        counter=int(str(state["counter"])),
        algorithm=str(state["algorithm"]),
    )
    expected_seed = canonical_digest(
        {
            "algorithm": _ALGORITHM,
            "configuration_hash": stream.configuration_hash,
            "concern": stream.concern,
        }
    )
    if (
        stream.algorithm != _ALGORITHM
        or stream.seed_digest != expected_seed
        or stream.stream_id != f"realism-stream-{expected_seed}"
        or stream.counter < 0
    ):
        raise ValueError("realism stream state is incompatible")
    return stream


def get_identity() -> Mapping[str, object]:
    """Return pinned algorithm identity and deterministic golden vectors."""
    configuration = {"seed": 7, "symbol": "EURUSD", "profile": "canonical"}
    stream = create(configuration, "latency")
    vectors = tuple(str(sample(stream)) for _ in range(3))
    return {"algorithm": _ALGORITHM, "golden_vectors": vectors}


def get_performance_budgets() -> Mapping[str, object]:
    """Return immutable published annual and multi-symbol sampling budgets."""
    return dict(_PERFORMANCE_BUDGETS)


__all__ = []
