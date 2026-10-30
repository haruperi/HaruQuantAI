"""FastAPI HTTP routes for AI Assistant workspace, MCP tool integration, and sessions.

Description:
    Provides REST endpoints for chat turn execution, one-shot completions,
    turn cancellation, memory settings, model catalog queries, session lifecycle
    management, and Model Context Protocol (MCP) server & tool orchestration.

Purpose:
    FEAT-AI-ROUTES: HTTP API boundary for AI assistant and MCP tooling.

Key Capabilities:
    - FR-ai-routes-chat: /chat turn processing with intermediate tool telemetry.
    - FR-ai-routes-complete: /complete one-shot generation without persistent session.
    - FR-ai-routes-sessions: CRUD session and conversation history management.
    - FR-ai-routes-mcp: MCP server discovery, connection pinging, and tool execution.

Python API Usage:
    from app.workspace.ai.routes import ai_router

    app.include_router(ai_router)

CLI Usage:
    python -c "from app.workspace.ai.routes import ai_router; print(ai_router.prefix)"
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from app.core.host.logging import get_logger
from app.workspace.ai.assistant import AIAssistantService
from app.workspace.ai.assistant_models import (
    ChatMessage,
    ChatTurnRequest,
    ChatTurnResponse,
    CompletionRequest,
    CompletionResponse,
    MemoryConfig,
    ModelCatalog,
    SessionSummary,
    TurnStatus,
)
from app.workspace.ai.mcp import McpServerRegistry, MCPTools
from app.workspace.ai.mcp_models import (
    CallToolRequest,
    CallToolResult,
    McpServerConfig,
    McpToolSpec,
    PingResult,
)

logger = get_logger(__name__)

ai_router = APIRouter(prefix="/api/v1/ai", tags=["ai"])

# Module-level singletons for session and tool tracking
_mcp_tools = MCPTools()
_mcp_registry = McpServerRegistry()
_assistant_service = AIAssistantService(mcp_tools=_mcp_tools)


def get_assistant_service() -> AIAssistantService:
    """Return the shared AIAssistantService instance."""
    return _assistant_service


def get_mcp_registry() -> McpServerRegistry:
    """Return the shared McpServerRegistry instance."""
    return _mcp_registry


def get_mcp_tools() -> MCPTools:
    """Return the shared MCPTools instance."""
    return _mcp_tools


# --- Config & Models ---


@ai_router.get("/config", response_model=ModelCatalog)
async def get_config() -> ModelCatalog:
    """Get active AI configuration, capabilities, and model selection."""
    logger.info("FR-ai-routes-config: retrieving AI config and models")
    return _assistant_service.get_model_catalog()


@ai_router.get("/model", response_model=ModelCatalog)
async def get_model() -> ModelCatalog:
    """Get currently active model status."""
    return _assistant_service.get_model_catalog()


@ai_router.post("/model")
async def select_model(payload: dict[str, str]) -> dict[str, Any]:
    """Switch active inference model."""
    model_name = payload.get("model", "")
    if not model_name:
        raise HTTPException(
            status_code=422,
            detail="Model name is required",
        )
    _assistant_service.select_model(model_name)
    logger.info("FR-ai-routes-config: selected model '%s'", model_name)
    return {"success": True, "currentModel": model_name}


# --- Chat & Turns ---


@ai_router.post("/chat", response_model=ChatTurnResponse)
async def chat(request: ChatTurnRequest) -> ChatTurnResponse:
    """Execute a conversation turn with optional tool invocations."""
    logger.info(
        "FR-ai-routes-chat: received chat turn for session '%s'",
        request.session_id,
    )
    return _assistant_service.run_turn(request)


@ai_router.post("/complete", response_model=CompletionResponse)
async def complete(request: CompletionRequest) -> CompletionResponse:
    """Produce a fast one-shot completion without history state."""
    logger.info("FR-ai-routes-complete: generating one-shot completion")
    return _assistant_service.complete(request)


@ai_router.get("/turn", response_model=TurnStatus)
async def turn_status(
    session_id: str | None = Query(None, alias="sessionId"),
) -> TurnStatus:
    """Get execution status of the current or specified session turn."""
    return _assistant_service.get_turn_status(session_id)


@ai_router.post("/stop")
async def stop_turn(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """Cancel an active turn."""
    sid = payload.get("sessionId") if payload else None
    stopped = _assistant_service.stop_turn(sid)
    logger.info(
        "FR-ai-routes-chat: turn stop requested for '%s' (stopped=%s)",
        sid,
        stopped,
    )
    return {"accepted": stopped, "success": "Turn stop requested"}


# --- Memory Settings ---


@ai_router.get("/memory", response_model=MemoryConfig)
async def get_memory() -> MemoryConfig:
    """Get active conversation memory settings."""
    return _assistant_service.get_memory_config()


@ai_router.post("/memory", response_model=MemoryConfig)
async def update_memory(config: MemoryConfig) -> MemoryConfig:
    """Update conversation memory settings."""
    logger.info("FR-ai-routes-memory: updated memory config enabled=%s", config.enabled)
    return _assistant_service.set_memory_config(config)


# --- Sessions ---


@ai_router.get("/sessions", response_model=list[SessionSummary])
async def list_sessions() -> list[SessionSummary]:
    """List all available conversation sessions."""
    return _assistant_service.list_sessions()


@ai_router.post("/sessions", response_model=SessionSummary)
async def create_session(payload: dict[str, Any]) -> SessionSummary:
    """Create a new conversation session."""
    name = payload.get("name")
    project = str(payload.get("project", ""))
    summary = _assistant_service.create_session(name=name, project=project)
    logger.info("FR-ai-routes-sessions: created session '%s'", summary.session_id)
    return summary


@ai_router.get("/sessions/{session_id}/history", response_model=list[ChatMessage])
async def get_session_history(session_id: str) -> list[ChatMessage]:
    """Retrieve message history for a conversation session."""
    history = _assistant_service.get_session_history(session_id)
    existing_ids = [s.session_id for s in _assistant_service.list_sessions()]
    if not history and session_id not in existing_ids:
        raise HTTPException(
            status_code=404,
            detail=f"Session '{session_id}' not found",
        )
    return history


@ai_router.delete("/sessions/{session_id}")
async def delete_session(session_id: str) -> dict[str, bool]:
    """Delete a conversation session."""
    deleted = _assistant_service.delete_session(session_id)
    if not deleted:
        raise HTTPException(
            status_code=404,
            detail=f"Session '{session_id}' not found",
        )
    logger.info("FR-ai-routes-sessions: deleted session '%s'", session_id)
    return {"success": True}


@ai_router.post("/sessions/{session_id}/clear")
async def clear_session_history(session_id: str) -> dict[str, bool]:
    """Clear conversation history for a session."""
    cleared = _assistant_service.clear_history(session_id)
    if not cleared:
        raise HTTPException(
            status_code=404,
            detail=f"Session '{session_id}' not found",
        )
    logger.info("FR-ai-routes-sessions: cleared session history '%s'", session_id)
    return {"success": True}


# --- MCP Servers & Tools ---


@ai_router.get("/mcp/servers", response_model=list[McpServerConfig])
async def list_mcp_servers() -> list[McpServerConfig]:
    """List configured Model Context Protocol servers."""
    return _mcp_registry.list_servers()


@ai_router.post("/mcp/servers", response_model=McpServerConfig)
async def save_mcp_server(config: McpServerConfig) -> McpServerConfig:
    """Register or update an MCP server configuration."""
    logger.info("FR-ai-routes-mcp: saved MCP server '%s'", config.id)
    return _mcp_registry.register_server(config)


@ai_router.delete("/mcp/servers/{server_id}")
async def remove_mcp_server(server_id: str) -> dict[str, bool]:
    """Remove an MCP server from the registry."""
    removed = _mcp_registry.remove_server(server_id)
    if not removed:
        raise HTTPException(
            status_code=404,
            detail=f"MCP Server '{server_id}' not found",
        )
    logger.info("FR-ai-routes-mcp: removed MCP server '%s'", server_id)
    return {"success": True}


@ai_router.post("/mcp/servers/ping", response_model=PingResult)
async def ping_mcp_server(config: McpServerConfig) -> PingResult:
    """Execute handshake ping test against an MCP server configuration."""
    logger.info("FR-ai-routes-mcp: ping testing MCP server '%s'", config.url)
    return _mcp_registry.ping_server(config)


@ai_router.get("/mcp/tools", response_model=list[McpToolSpec])
async def list_mcp_tools() -> list[McpToolSpec]:
    """List all available MCP tools."""
    return _mcp_tools.get_tool_specs()


@ai_router.post("/mcp/tools/call", response_model=CallToolResult)
async def call_mcp_tool(request: CallToolRequest) -> CallToolResult:
    """Invoke an MCP tool with provided arguments."""
    logger.info("FR-ai-routes-mcp: invoking tool '%s'", request.name)
    return _mcp_tools.execute_tool(request.name, request.arguments)
