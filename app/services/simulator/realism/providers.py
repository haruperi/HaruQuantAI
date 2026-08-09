"""Simulator-owned fill-model calibration provider."""

from __future__ import annotations

from collections.abc import Mapping


class _FillModelProvider:
    """Private provider satisfying Optimization's calibration port."""

    def __init__(self, profiles: Mapping[str, Mapping[str, object]]) -> None:
        self._profiles = {key: dict(value) for key, value in profiles.items()}

    def fill_model_calibration(
        self, *, market_data_ref: str, instrument: str
    ) -> Mapping[str, object]:
        """Return explicit calibration evidence without inferred defaults."""
        profile = self._profiles.get(instrument)
        if profile is None or profile.get("market_data_ref") != market_data_ref:
            return {
                "status": "NOT_CALIBRATED",
                "reason": "matching_profile_absent",
                "instrument": instrument,
            }
        return {"status": "CALIBRATED", "instrument": instrument, **profile}


def build_fill_model_provider(
    profiles: Mapping[str, Mapping[str, object]],
) -> object:
    """Build an opaque fill-model provider from explicit profile evidence.

    Args:
        profiles: Instrument-keyed validated calibration mappings.

    Returns:
        Opaque provider satisfying Optimization's consumer protocol.

    Raises:
        ValueError: If no profiles are supplied.
    """
    if not profiles:
        raise ValueError("fill-model provider requires explicit profiles")
    return _FillModelProvider(profiles)


__all__ = ["build_fill_model_provider"]
