"""Unit and parity tests for indicator.williams_r.default provider."""

# ruff: noqa: INP001
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, cast

import pytest
from app.capabilities.indicator.williams_r.v1 import WilliamsRCapabilityV1
from app.composition.facade import bind_runtime
from app.composition.runtime import CompositionRuntime
from app.kernel.effects import EffectScope
from app.kernel.errors import CapabilityReasonCode, CapabilityUnavailableError
from app.kernel.identifiers import CapabilityId
from app.kernel.manifests import load_manifest
from app.kernel.resolver import resolve_providers
from app.services.indicators.core.results import get_indicator_result_values
from app.services.indicators.momentum.williams_r import williams_r
from app.services.indicators.momentum.williams_r_default.plugin import create_provider
from tests.indicators.helpers import build_dataset, unwrap_response
from tests.removability.harness import run_in_fresh_process

_REPO_ROOT = Path(__file__).resolve().parents[4]
_PROVIDER_DIR = (
    _REPO_ROOT / "app" / "services" / "indicators" / "momentum" / "williams_r_default"
)
_MANIFEST_PATH = _PROVIDER_DIR / "manifest.toml"
_GOLDEN_PATH = _REPO_ROOT / "tests" / "indicators" / "fixtures" / "momentum_golden.json"


def _load_golden_dataset() -> tuple[object, dict[str, Any]]:
    """Load the golden dataset and metadata from fixture."""
    golden: dict[str, Any] = json.loads(_GOLDEN_PATH.read_text(encoding="utf-8"))
    bars = [
        (
            float(bar["open"]),
            float(bar["high"]),
            float(bar["low"]),
            float(bar["close"]),
            float(bar["volume"]),
        )
        for bar in golden["williams_r_bars"]
    ]
    dataset = build_dataset(bars)
    return dataset, golden


def test_manifest_exact() -> None:
    """Verify Williams %R manifest matches canonical declaration."""
    manifest = load_manifest(_MANIFEST_PATH)
    assert str(manifest.provider_id) == "indicator.williams_r.default"
    assert str(manifest.provider_version) == "1.0.0"
    assert (
        manifest.entry_point
        == "app.services.indicators.momentum.williams_r_default.plugin:create_provider"
    )
    assert len(manifest.provides) == 1
    assert str(manifest.provides[0].capability_id) == "indicator.williams_r.v1"
    assert str(manifest.provides[0].contract_version) == "1.0.0"
    assert manifest.provides[0].cardinality == "exactly_one"
    assert {p.value for p in manifest.profiles} == {
        "simulation",
        "research",
        "demo",
        "live",
    }
    assert manifest.scopes == ("process",)
    assert manifest.state_schema_id is None


def test_factory_exact() -> None:
    """Verify create_provider returns WilliamsRCapabilityV1 and rejects non-empty deps/config."""
    scope = EffectScope()
    cap = create_provider(
        dependencies={},
        config={},
        scope=scope,
    )
    assert isinstance(cap, WilliamsRCapabilityV1)
    assert callable(cap.calculate)

    # Reject non-empty dependencies
    with pytest.raises(
        ValueError, match="Williams R provider accepts no dependencies or config"
    ):
        create_provider(
            dependencies={CapabilityId.parse("test.dep.v1"): object()},
            config={},
            scope=scope,
        )

    # Reject non-empty config
    with pytest.raises(
        ValueError, match="Williams R provider accepts no dependencies or config"
    ):
        create_provider(
            dependencies={},
            config={"foo": "bar"},
            scope=scope,
        )


def test_contract_call() -> None:
    """Verify calling capability calculate method returns valid IndicatorResult."""
    scope = EffectScope()
    cap = create_provider(dependencies={}, config={}, scope=scope)
    dataset, _ = _load_golden_dataset()

    resp = cap.calculate(cast("Any", dataset), period=3)
    result: Any = unwrap_response(resp)
    assert result.output_columns == ("williams_r_3",)
    values_df = get_indicator_result_values(result)
    assert "williams_r_3" in values_df.columns
    assert len(values_df) == 7


def test_phase0_parity() -> None:
    """Verify Williams %R output matches phase 0 golden fixture numbers exactly."""
    scope = EffectScope()
    cap = create_provider(dependencies={}, config={}, scope=scope)
    dataset, golden = _load_golden_dataset()

    resp = cap.calculate(
        cast("Any", dataset), period=int(golden["williams_r"]["period"])
    )
    result: Any = unwrap_response(resp)
    values_df = get_indicator_result_values(result)
    values: list[float] = values_df[str(golden["williams_r"]["output_column"])].tolist()
    expected = cast("list[float | None]", golden["williams_r"]["expected"])

    assert len(values) == len(expected)
    for actual_val, exp_val in zip(values, expected, strict=True):
        if exp_val is None:
            assert math.isnan(actual_val)
        else:
            assert float(actual_val) == pytest.approx(exp_val, rel=1e-6)


def test_import_no_io() -> None:
    """Verify importing provider plugin in a fresh process performs no I/O."""
    script = """
import sys
import app.services.indicators.momentum.williams_r_default.plugin as plugin
assert hasattr(plugin, "create_provider")
"""
    res = run_in_fresh_process(repository_root=_REPO_ROOT, script=script)
    assert res.returncode == 0, res.stderr


def test_composition_activation() -> None:
    """Verify end-to-end activation and leasing through CompositionRuntime."""
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

    dataset, _ = _load_golden_dataset()
    resp = williams_cap.calculate(cast("Any", dataset), period=3)
    result: Any = unwrap_response(resp)
    assert result.output_columns == ("williams_r_3",)


def test_facade_unbound_raises_capability_unavailable() -> None:
    """Verify calling williams_r without an active provider raises CapabilityUnavailableError."""
    dataset, _ = _load_golden_dataset()
    empty_runtime = CompositionRuntime()
    with (
        bind_runtime(empty_runtime),
        pytest.raises(CapabilityUnavailableError) as exc_info,
    ):
        williams_r(cast("Any", dataset), period=3)

    detail = exc_info.value.detail
    assert detail.reason_code == CapabilityReasonCode.NOT_INSTALLED
    assert detail.capability == "indicator.williams_r.v1"
    assert detail.consumer == "compatibility_facade"
    assert detail.dependency_chain == (
        "compatibility_facade",
        "indicator.williams_r.v1",
    )


def test_facade_bound_success_and_nested_restoration() -> None:
    """Verify williams_r succeeds inside bind_runtime and restores prior runtime on exit."""
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

    dataset, _ = _load_golden_dataset()

    with bind_runtime(runtime):
        resp = williams_r(cast("Any", dataset), period=3)
        result: Any = unwrap_response(resp)
        assert result.output_columns == ("williams_r_3",)

        # Nested empty runtime
        inner_empty = CompositionRuntime()
        with bind_runtime(inner_empty), pytest.raises(CapabilityUnavailableError):
            williams_r(cast("Any", dataset), period=3)

        # Back in outer runtime
        resp_outer = williams_r(cast("Any", dataset), period=3)
        assert unwrap_response(resp_outer).output_columns == ("williams_r_3",)

    # Completely unbound
    with pytest.raises(CapabilityUnavailableError):
        williams_r(cast("Any", dataset), period=3)
