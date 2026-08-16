"""Pinned concern-stream evidence for seeded execution realism."""

from app.services.simulator import (
    create_realism_stream,
    get_realism_stream_identity,
    restore_realism_stream,
    sample_realism_stream,
    serialize_realism_stream,
)


def test_same_economic_identity_has_golden_cross_concern_streams() -> None:
    """FR-SIM-176: streams are pinned, isolated, and trace-independent."""
    configuration = {
        "seed": 7,
        "symbol": "EURUSD",
        "profile": "canonical",
        "request_id": "trace-a",
    }
    latency = create_realism_stream(configuration, "latency")
    restored = restore_realism_stream(serialize_realism_stream(latency))
    assert sample_realism_stream(latency) == sample_realism_stream(restored)
    other_trace = create_realism_stream(
        {**configuration, "request_id": "trace-b"}, "latency"
    )
    assert sample_realism_stream(other_trace) == sample_realism_stream(
        create_realism_stream(configuration, "latency")
    )
    assert sample_realism_stream(
        create_realism_stream(configuration, "spread")
    ) != sample_realism_stream(create_realism_stream(configuration, "latency"))
    identity = get_realism_stream_identity()
    assert identity["algorithm"] == "sha256-counter-u256-v1"
    assert identity["golden_vectors"] == (
        "0.7262971291629666173232869246",
        "0.8666250147335327889537984437",
        "0.9494562030661535978425881776",
    )


def test_economic_configuration_change_changes_stream() -> None:
    """FR-SIM-176: an execution-affecting change changes the stream."""
    first = create_realism_stream({"seed": 1, "symbol": "EURUSD"}, "latency")
    second = create_realism_stream({"seed": 2, "symbol": "EURUSD"}, "latency")
    assert sample_realism_stream(first) != sample_realism_stream(second)
