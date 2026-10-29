"""Stateless MCP JSON-RPC bridge for compiled custom AI tools."""

from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter
from fastapi.responses import JSONResponse, Response

from app.core.host.logging import get_logger
from app.workspace.code_editor._common import CodeEditorError
from app.workspace.code_editor.registry import registry

logger = get_logger(__name__)
router = APIRouter()


@router.post("/mcp")
def dispatch_mcp(message: dict[str, Any]) -> Response:
    """FR-CODEEDITOR-AI-MCP: Expose compiled tools to stateless MCP clients."""
    identifier = message.get("id")
    method = message.get("method")
    if message.get("jsonrpc") != "2.0" or not isinstance(method, str):
        return JSONResponse(
            {
                "jsonrpc": "2.0",
                "id": identifier,
                "error": {"code": -32600, "message": "Invalid JSON-RPC request"},
            }
        )
    if "id" not in message:
        return Response(status_code=202)
    result: dict[str, Any]
    if method == "initialize":
        result = {
            "protocolVersion": "2025-03-26",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "HaruQuantAI custom snippets", "version": "1.0"},
        }
    elif method == "ping":
        result = {}
    elif method == "tools/list":
        result = {
            "tools": [
                {
                    "name": name,
                    "description": tool.description,
                    "inputSchema": tool.get_input_schema(),
                }
                for name, tool in registry.tools.items()
            ]
        }
    elif method == "tools/call":
        params = message.get("params")
        if (
            not isinstance(params, dict)
            or not isinstance(params.get("name"), str)
            or not isinstance(params.get("arguments", {}), dict)
        ):
            return JSONResponse(
                {
                    "jsonrpc": "2.0",
                    "id": identifier,
                    "error": {
                        "code": -32602,
                        "message": "Tool name and argument mapping required",
                    },
                }
            )
        try:
            output = registry.call_tool(params["name"], params.get("arguments", {}))
            result = {
                "content": [{"type": "text", "text": json.dumps(output)}],
                "isError": False,
            }
        except CodeEditorError as exc:
            result = {"content": [{"type": "text", "text": str(exc)}], "isError": True}
        except Exception as exc:
            logger.exception("Custom MCP tool failed: %s", params["name"])
            result = {"content": [{"type": "text", "text": str(exc)}], "isError": True}
    else:
        return JSONResponse(
            {
                "jsonrpc": "2.0",
                "id": identifier,
                "error": {"code": -32601, "message": "Method not found"},
            }
        )
    return JSONResponse({"jsonrpc": "2.0", "id": identifier, "result": result})
