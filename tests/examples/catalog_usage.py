"""Run with `uv run python -m tests.examples.catalog_usage`."""

import asyncio
import tempfile
from pathlib import Path

from app.host.bootstrap import create_runtime
from app.host.catalog import HOST_CATALOG, CatalogRoot, SelectionRequest
from app.plugins.spec import PluginRef

SAMPLE_PLUGIN_SOURCE = """
from app.plugins.spec import PluginSpec, PluginRef, OperationSpec, PluginContribution, OperationContribution
from app.plugins.schema import ParameterSchema, ParameterSpec, PortSpec, ValueKind, NumericConstraint

def plugin() -> PluginContribution:
    ref = PluginRef(id="example.probe", version=(1, 0, 0))
    op = OperationSpec(
        operation_id="evaluate",
        title="Example Probe Operation",
        parameters=ParameterSchema((
            ParameterSpec(key="threshold", kind=ValueKind.NUMBER, label="Threshold", default=0.5, constraint=NumericConstraint(min_value=0.0, max_value=1.0)),
        )),
        inputs=(PortSpec(key="in_val", kind=ValueKind.NUMBER),),
        outputs=(PortSpec(key="out_val", kind=ValueKind.NUMBER),),
        effects=("pure",),
    )
    spec = PluginSpec(ref=ref, kind="example", title="Example Probe Plugin", operations=(op,))
    class ExampleImpl:
        pass
    return PluginContribution(spec=spec, operations=(OperationContribution("evaluate", ExampleImpl()),))
"""


async def example_catalog() -> None:
    """Prove bounded discovery, snapshot publication, selection, and admission offline."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        plugin_file = temp_path / "probe.py"
        plugin_file.write_text(SAMPLE_PLUGIN_SOURCE, encoding="utf-8")

        root = CatalogRoot(
            logical_family="examples",
            path=temp_path,
            accepted_kinds=("example",),
        )

        async with create_runtime(catalog_roots=(root,)) as runtime:
            catalog = runtime.require(HOST_CATALOG)
            assert catalog.is_ready()

            # Inspect snapshot
            snapshot = catalog.snapshot()
            assert len(snapshot.view.entries) == 1
            entry = snapshot.view.entries[0]
            probe_ref = PluginRef(id="example.probe", version=(1, 0, 0))
            assert entry.ref == probe_ref
            assert entry.kind == "example"

            # Selection
            sel = catalog.select(SelectionRequest(enabled_refs=(probe_ref,)))
            assert sel.available_operations == ((probe_ref, "evaluate"),)

            # Admission
            admitted = catalog.admit(probe_ref, "evaluate")
            assert admitted.ref == probe_ref
            assert admitted.operation_id == "evaluate"
            assert admitted.source_digest
            assert admitted.entry_fingerprint
            assert admitted.snapshot_fingerprint == snapshot.whole_fingerprint


if __name__ == "__main__":
    asyncio.run(example_catalog())
