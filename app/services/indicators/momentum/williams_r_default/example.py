"""Executable demonstration of indicator.williams_r.default provider."""

# ruff: noqa: E402
from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

_REPO_ROOT = Path(__file__).resolve().parents[5]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tests.indicators.helpers import build_dataset

from app.composition.runtime import CompositionRuntime
from app.kernel.identifiers import CapabilityId
from app.kernel.manifests import load_manifest
from app.kernel.resolver import resolve_providers
from app.services.indicators.core.results import get_indicator_result_values
from app.services.indicators.momentum.williams_r_default.plugin import create_provider

if TYPE_CHECKING:
    from app.capabilities.indicator.williams_r.v1 import WilliamsRCapabilityV1

_MANIFEST_PATH = Path(__file__).resolve().parent / "manifest.toml"


def main() -> None:
    """Activate Williams %R provider via composition runtime and display output."""
    manifest = load_manifest(_MANIFEST_PATH)
    report = resolve_providers(
        (manifest,),
        enabled_provider_ids=frozenset({manifest.provider_id}),
        selected_provider_ids={},
    )
    runtime = CompositionRuntime()
    runtime.activate(
        report,
        factories={manifest.provider_id: create_provider},
        configs={manifest.provider_id: {}},
    )

    cap_id = CapabilityId.parse("indicator.williams_r.v1")
    lease = runtime.lease(cap_id)
    williams_cap = cast("WilliamsRCapabilityV1", lease.instance)

    # 20 bars with diverse high/low spreads
    bars = [
        (44.0, 44.5, 43.5, 44.0, 100.0),
        (44.5, 45.5, 44.0, 44.5, 100.0),
        (43.5, 44.5, 42.5, 43.5, 100.0),
        (45.0, 46.0, 44.5, 45.0, 100.0),
        (44.0, 45.0, 43.5, 44.0, 100.0),
        (46.0, 47.0, 45.5, 46.0, 100.0),
        (45.5, 46.5, 44.5, 45.5, 100.0),
        (46.0, 47.5, 45.5, 46.0, 100.0),
        (47.0, 48.0, 46.5, 47.0, 100.0),
        (46.5, 47.5, 46.0, 46.5, 100.0),
        (47.5, 48.5, 47.0, 47.5, 100.0),
        (48.0, 49.0, 47.5, 48.0, 100.0),
        (47.0, 48.0, 46.5, 47.0, 100.0),
        (48.5, 49.5, 48.0, 48.5, 100.0),
        (49.0, 50.0, 48.5, 49.0, 100.0),
        (48.0, 49.0, 47.5, 48.0, 100.0),
        (49.5, 50.5, 49.0, 49.5, 100.0),
        (50.0, 51.0, 49.5, 50.0, 100.0),
        (49.0, 50.0, 48.5, 49.0, 100.0),
        (50.5, 51.5, 50.0, 50.5, 100.0),
    ]
    dataset = build_dataset(bars)
    resp = williams_cap.calculate(cast("Any", dataset), period=14)
    data_result = getattr(resp, "data", resp)

    values_df = get_indicator_result_values(data_result)
    values_series = values_df["williams_r_14"]
    last_five = []
    for ts, val in values_series.tail(5).items():
        val_float = float(val) if val is not None else float("nan")
        formatted_val = None if math.isnan(val_float) else round(val_float, 4)
        last_five.append({"timestamp": str(ts), "williams_r_14": formatted_val})

    print(json.dumps(last_five, indent=2))


if __name__ == "__main__":
    main()
