"""Executable demonstration of indicator.rsi.default provider."""

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

from tests.indicators.helpers import close_dataset

from app.composition.runtime import CompositionRuntime
from app.kernel.identifiers import CapabilityId
from app.kernel.manifests import load_manifest
from app.kernel.resolver import resolve_providers
from app.services.indicators.core.results import get_indicator_result_values
from app.services.indicators.momentum.rsi_default.plugin import create_provider

if TYPE_CHECKING:
    from app.contracts.indicator.rsi.v1 import RsiCapabilityV1

_MANIFEST_PATH = Path(__file__).resolve().parent / "manifest.toml"


def main() -> None:
    """Activate RSI provider via composition runtime and display output."""
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

    cap_id = CapabilityId.parse("indicator.rsi.v1")
    lease = runtime.lease(cap_id)
    rsi_cap = cast("RsiCapabilityV1", lease.instance)

    prices = [
        44.0,
        44.5,
        43.5,
        45.0,
        44.0,
        46.0,
        45.5,
        46.0,
        47.0,
        46.5,
        47.5,
        48.0,
        47.0,
        48.5,
        49.0,
        48.0,
        49.5,
        50.0,
        49.0,
        50.5,
    ]
    dataset = close_dataset(prices)
    resp = rsi_cap.calculate(cast("Any", dataset), period=14)
    data_result = getattr(resp, "data", resp)

    values_df = get_indicator_result_values(data_result)
    values_series = values_df["rsi_14"]
    last_five = []
    for ts, val in values_series.tail(5).items():
        val_float = float(val) if val is not None else float("nan")
        formatted_val = None if math.isnan(val_float) else round(val_float, 4)
        last_five.append({"timestamp": str(ts), "rsi_14": formatted_val})

    print(json.dumps(last_five, indent=2))


if __name__ == "__main__":
    main()
