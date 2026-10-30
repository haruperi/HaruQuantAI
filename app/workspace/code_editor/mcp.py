"""Mcp editor contracts and workflows.

Description:
    Adapts finite JSON-RPC requests to compiled extension tools while retaining MCP
    response behavior. Unexpected tool errors do not expose raw exception text.
Purpose:
    FEAT-CODE-EDITOR-CONTRACTS: Preserve typed editor behavior and host ownership.
Key Capabilities:
    - FR-code-editor-mcp: Observe the associated workflow; fixed-label logs are
      verified by the contract logging tests or HTTP integration checks.
    - FR-code-editor-mcp-dispatch-mcp: Observe the associated workflow; fixed-label logs
      are
      verified by the contract logging tests or HTTP integration checks.
Python API Usage:
    import app.workspace.code_editor.mcp
CLI Usage:
    uv run python -m pytest tests/workspace/code_editor --no-cov
"""

from __future__ import annotations

import json
import logging
from typing import cast

from fastapi import APIRouter
from fastapi.responses import JSONResponse, Response

from app.core.lib.errors import JSONValue, copy_json
from app.workspace.code_editor._common import CodeEditorError
from app.workspace.code_editor.registry import registry

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/mcp")
def dispatch_mcp(message: dict[str, JSONValue]) -> Response:
    """FR-CODEEDITOR-AI-MCP: Expose compiled tools to stateless MCP clients."""
    logger.debug("FR-code-editor-mcp-dispatch-mcp: invoked")
    try:
        copy_json(message)
    except ValueError:
        logger.warning("FR-code-editor-mcp-request: rejected JSON")
        return JSONResponse(
            {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32600, "message": "Invalid JSON-RPC request"},
            }
        )
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
    result: dict[str, JSONValue]
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
            output = registry.call_tool(
                cast("str", params["name"]),
                cast("dict[str, JSONValue]", params.get("arguments", {})),
            )
            result = {
                "content": [{"type": "text", "text": json.dumps(output)}],
                "isError": False,
            }
        except CodeEditorError as exc:
            result = {"content": [{"type": "text", "text": str(exc)}], "isError": True}
        except Exception as exc:
            logger.warning("FR-code-editor-mcp: operation")
            result = {
                "content": [{"type": "text", "text": "Extension tool failed"}],
                "isError": True,
            }
    else:
        return JSONResponse(
            {
                "jsonrpc": "2.0",
                "id": identifier,
                "error": {"code": -32601, "message": "Method not found"},
            }
        )
    return JSONResponse({"jsonrpc": "2.0", "id": identifier, "result": result})
