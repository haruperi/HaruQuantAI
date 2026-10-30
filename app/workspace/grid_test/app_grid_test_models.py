"""Grid Test workspace data models.

Description:
    Defines Pydantic models for the GridTest application plugin descriptor,
    test row representation, timer intervals, and batch responses.

Purpose:
    FEAT-GRID-TEST: Provide strongly typed schemas for Grid Test plugin
    registration and deterministic table test row models.

Key Capabilities:
    FR-GRID-TEST-PLUGIN-MODELS: Strongly typed plugin descriptor attributes.
    FR-GRID-TEST-ROW-MODELS: Row model and timer intervals schema.

Python API Usage:
    from app.workspace.grid_test.app_grid_test_models import (
        GridTestIntervalsModel,
        GridTestPluginDescriptor,
        GridTestRowModel,
    )

CLI Usage:
    uv run python -c "from app.workspace.grid_test import GridTestPluginDescriptor"
"""

from pydantic import BaseModel, Field


class GridTestRowModel(BaseModel):
    """Data representation of a single grid test row."""

    index: int = Field(..., description="0-based sequential row index")
    value: int = Field(..., description="Multiplier value (index * 2)")
    text: str = Field(..., description="Formatted text label ('{index}-text')")


class GridTestIntervalsModel(BaseModel):
    """Timer intervals in milliseconds for the UI grid stress test."""

    add: int = Field(default=20, description="Row addition timer period in ms")
    remove: int = Field(default=30, description="Row removal timer period in ms")
    change: int = Field(default=40, description="Row mutation timer period in ms")
    count: int = Field(default=50, description="Row count refresh timer period in ms")


class GridTestPluginDescriptor(BaseModel):
    """Plugin registration descriptor for GridTest."""

    name: str = Field(default="GridTest", description="Plugin display name")
    app_code: str = Field(default="GRIDTEST", description="Application code identifier")
    category: str = Field(default="App", description="Plugin category")
    product: str = Field(default="SQUANT", description="Target product")
    preferred_position: int = Field(
        default=10, description="Navigation menu order position"
    )
    context_path: str = Field(default="/gridtest", description="Context root URL path")
    tooltip: str = Field(default="Grid test", description="Hover tooltip description")
    hidden: bool = Field(
        default=True, description="Whether hidden from primary navigation"
    )


class GridTestBatchResponse(BaseModel):
    """Response containing a batch of generated grid test rows."""

    rows: list[GridTestRowModel] = Field(
        default_factory=list, description="List of generated test rows"
    )
    total_count: int = Field(..., description="Total row count in this batch")
