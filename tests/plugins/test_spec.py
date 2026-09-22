"""Unit tests for app.plugins.spec: plugin specifications, contributions, and catalog views."""

import pytest
from app.plugins.schema import PortSpec, ValueKind
from app.plugins.spec import (
    CatalogEntryView,
    CatalogView,
    OperationContribution,
    OperationSpec,
    PluginContribution,
    PluginRef,
    PluginSpec,
    WorkspaceCommand,
    WorkspaceSpec,
    WorkspaceView,
    validate_plugin_id,
)


def test_validate_plugin_id() -> None:
    assert validate_plugin_id("indicator.rsi") == "indicator.rsi"
    assert validate_plugin_id("comparison.greater_than") == "comparison.greater_than"
    assert validate_plugin_id("workspace.builder") == "workspace.builder"

    with pytest.raises(ValueError, match="lowercase dot-namespaced identifier"):
        validate_plugin_id("singleword")
    with pytest.raises(ValueError, match="lowercase dot-namespaced identifier"):
        validate_plugin_id("Indicator.Rsi")
    with pytest.raises(ValueError, match="lowercase dot-namespaced identifier"):
        validate_plugin_id("indicator..rsi")


def test_plugin_ref_parsing_and_formatting() -> None:
    ref = PluginRef(id="indicator.rsi", version=(1, 0, 0))
    assert ref.to_string() == "indicator.rsi@1.0.0"
    assert str(ref) == "indicator.rsi@1.0.0"

    parsed = PluginRef.parse("indicator.rsi@1.2.3")
    assert parsed.id == "indicator.rsi"
    assert parsed.version == (1, 2, 3)

    with pytest.raises(ValueError, match=r"cannot be 0\.0\.0"):
        PluginRef(id="indicator.rsi", version=(0, 0, 0))

    with pytest.raises(ValueError, match="Invalid plugin ref string format"):
        PluginRef.parse("invalid_ref_without_at")


def test_operation_spec_validation() -> None:
    op = OperationSpec(
        operation_id="compute",
        title="Compute RSI",
        inputs=(PortSpec(key="values", kind=ValueKind.ALIGNED_SERIES),),
        outputs=(PortSpec(key="rsi", kind=ValueKind.ALIGNED_SERIES),),
        effects=("pure",),
    )
    assert op.operation_id == "compute"
    assert op.effects == ("pure",)

    with pytest.raises(ValueError, match="Duplicate input port key"):
        OperationSpec(
            operation_id="compute",
            title="Compute",
            inputs=(
                PortSpec(key="values", kind=ValueKind.NUMBER),
                PortSpec(key="values", kind=ValueKind.NUMBER),
            ),
        )


def test_plugin_contribution_validation() -> None:
    ref = PluginRef(id="indicator.rsi", version=(1, 0, 0))
    op_spec = OperationSpec(operation_id="compute", title="Compute RSI")
    plugin_spec = PluginSpec(
        ref=ref,
        kind="indicator",
        title="RSI Indicator",
        operations=(op_spec,),
    )

    class DummyImpl:
        pass

    contrib = PluginContribution(
        spec=plugin_spec,
        operations=(OperationContribution("compute", DummyImpl()),),
    )
    assert contrib.get_implementation("compute") is not None

    # Mismatch between spec and contribution
    with pytest.raises(ValueError, match="operations mismatch"):
        PluginContribution(
            spec=plugin_spec,
            operations=(OperationContribution("other_op", DummyImpl()),),
        )


def test_catalog_views() -> None:
    ref = PluginRef(id="indicator.rsi", version=(1, 0, 0))
    op_spec = OperationSpec(operation_id="compute", title="Compute RSI")
    entry = CatalogEntryView(
        ref=ref,
        kind="indicator",
        title="RSI Indicator",
        operations=(op_spec,),
    )
    assert entry.ref == ref
    assert len(entry.operations) == 1

    catalog = CatalogView(entries=(entry,), catalog_fingerprint="fp123")
    assert catalog.get_entry(ref) == entry
    assert catalog.get_entry_by_id("indicator.rsi") == entry
    assert catalog.get_operation(ref, "compute") == op_spec
    assert catalog.get_operation(ref, "unknown") is None

    unknown_ref = PluginRef(id="indicator.macd", version=(1, 0, 0))
    assert catalog.get_entry(unknown_ref) is None


def test_workspace_spec() -> None:
    ref = PluginRef(id="workspace.builder", version=(1, 0, 0))
    cmd = WorkspaceCommand(command_id="build", title="Build Strategy")
    view = WorkspaceView(view_id="main", title="Builder View", component="Builder")

    wspec = WorkspaceSpec(
        ref=ref,
        title="Strategy Builder",
        commands=(cmd,),
        views=(view,),
        accepted_kinds=("indicator", "comparison"),
    )
    assert wspec.title == "Strategy Builder"
    assert wspec.accepted_kinds == ("indicator", "comparison")
