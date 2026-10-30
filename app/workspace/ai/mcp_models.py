"""Model Context Protocol (MCP) data contracts and schema definitions.

Description:
    Provides typed Pydantic models for MCP server configurations, tool
    specifications, tool call requests, execution results, and JSON schema
    descriptors used in AI agent workflows.

Purpose:
    FEAT-AI-MCP: Standardized Model Context Protocol data structures for
    HaruQuantAI tool-augmented AI agent integration.

Key Capabilities:
    - FR-ai-mcp-models: Strongly typed models for server configurations,
      synchronous tool specifications, tool arguments, and results.

Python API Usage:
    from app.workspace.ai.mcp_models import McpServerConfig, CallToolRequest

    config = McpServerConfig(
        id="srv-1",
        name="Quant Gateway",
        url="http://localhost:8080/mcp/v1",
        transport="sse",
    )

CLI Usage:
    python -c "from app.workspace.ai.mcp_models import McpServerConfig; print(1)"
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class McpServerConfig(BaseModel):
    """Configuration record for an external or local Model Context Protocol server."""

    id: str = Field(..., description="Unique server identifier")
    name: str = Field(..., description="Human-readable server name")
    url: str = Field(
        default="http://localhost:8080/mcp/v1",
        description="Endpoint URL for SSE transport or command line for stdio",
    )
    transport: Literal["sse", "stdio"] = Field(
        default="sse",
        description="Transport communication mechanism",
    )
    status: Literal["Connected", "Disconnected", "Error"] = Field(
        default="Connected",
        description="Current server connection status",
    )
    capabilities: list[str] = Field(
        default_factory=lambda: [
            "strategy_generation",
            "backtest_execution",
            "code_synthesis",
        ],
        description="List of advertised agent capabilities",
    )
    active_calls: int = Field(
        default=0,
        description="Count of currently active or executed tool invocations",
    )


class McpToolParameterProperty(BaseModel):
    """Property definition inside a JSON schema object."""

    type: str = Field(default="string", description="Parameter primitive type")
    description: str = Field(default="", description="Description of the parameter")


class McpJsonSchema(BaseModel):
    """JSON Schema definition for MCP tool parameters."""

    type: str = Field(default="object", description="Root schema type")
    properties: dict[str, dict[str, Any]] = Field(
        default_factory=dict,
        description="Map of parameter names to property constraints",
    )
    required: list[str] = Field(
        default_factory=list,
        description="List of required parameter names",
    )


class McpToolSpec(BaseModel):
    """Specification of an available MCP tool that can be invoked by the AI agent."""

    name: str = Field(..., description="Canonical tool identifier")
    description: str = Field(
        ..., description="Human-readable description of functionality"
    )
    input_schema: McpJsonSchema = Field(
        default_factory=McpJsonSchema,
        description="JSON schema defining input argument contracts",
    )


class CallToolRequest(BaseModel):
    """Request payload to invoke a specific tool."""

    name: str = Field(..., description="Tool name to call")
    arguments: dict[str, Any] = Field(
        default_factory=dict,
        description="Execution arguments matching the tool input schema",
    )


class McpTextContent(BaseModel):
    """Text-based content fragment returned in an MCP tool response."""

    type: str = Field(default="text", description="Content block type")
    text: str = Field(default="", description="Resulting text content")


class CallToolResult(BaseModel):
    """Result payload from an MCP tool execution."""

    content: list[McpTextContent] = Field(
        default_factory=list,
        description="List of content fragments returned by the tool",
    )
    is_error: bool = Field(
        default=False,
        description="Whether the tool execution encountered an error",
    )


class PingResult(BaseModel):
    """Result payload from an MCP server ping test."""

    success: bool = Field(..., description="Whether ping handshake succeeded")
    message: str = Field(..., description="Detailed status or handshake report")
    tool_count: int = Field(default=0, description="Discovered tool count")
