/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.pluginlib.program.Program
 *  io.modelcontextprotocol.server.McpServerFeatures$SyncToolSpecification
 *  io.modelcontextprotocol.server.McpSyncServerExchange
 *  io.modelcontextprotocol.spec.McpSchema$CallToolRequest
 *  io.modelcontextprotocol.spec.McpSchema$CallToolResult
 *  io.modelcontextprotocol.spec.McpSchema$JsonSchema
 *  io.modelcontextprotocol.spec.McpSchema$TextContent
 *  io.modelcontextprotocol.spec.McpSchema$Tool
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.project.mcp;

import com.strategyquant.pluginlib.program.Program;
import io.modelcontextprotocol.server.McpServerFeatures;
import io.modelcontextprotocol.server.McpSyncServerExchange;
import io.modelcontextprotocol.spec.McpSchema;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.function.BiFunction;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class MCPTools {
    private static final Logger Log = LoggerFactory.getLogger((String)"MCPTools");

    public static List<McpServerFeatures.SyncToolSpecification> createSpecs() {
        McpSchema.JsonSchema jsonSchema = new McpSchema.JsonSchema("object", Collections.emptyMap(), null, null, null, null);
        McpSchema.JsonSchema jsonSchema2 = new McpSchema.JsonSchema("object", Map.of("name", Map.of("type", "string", "description", "Project name")), List.of("name"), null, null, null);
        McpSchema.JsonSchema jsonSchema3 = new McpSchema.JsonSchema("object", Map.of("name", Map.of("type", "string", "description", "Project name"), "databank", Map.of("type", "string", "description", "Databank name")), List.of("name", "databank"), null, null, null);
        McpSchema.JsonSchema jsonSchema4 = new McpSchema.JsonSchema("object", Map.of("name", Map.of("type", "string", "description", "Project name"), "databank", Map.of("type", "string", "description", "Databank name"), "strategy", Map.of("type", "string", "description", "Strategy name")), List.of("name", "databank", "strategy"), null, null, null);
        return List.of(MCPTools.spec("list_projects", "List all available projects in StrategyQuant X", jsonSchema, (mcpSyncServerExchange, callToolRequest) -> {
            try {
                HashMap hashMap = new HashMap();
                String string = (String)Program.get((String)"Project").call("list", new Object[]{hashMap});
                return MCPTools.result(string);
            }
            catch (Exception exception) {
                return MCPTools.error(exception);
            }
        }), MCPTools.spec("list_databanks", "List all databanks in a project", jsonSchema2, (mcpSyncServerExchange, callToolRequest) -> {
            try {
                String string = (String)callToolRequest.arguments().get("name");
                HashMap<String, String[]> hashMap = new HashMap<String, String[]>();
                hashMap.put("projectName", new String[]{string});
                String string2 = (String)Program.get((String)"Project").call("databankList", new Object[]{hashMap});
                return MCPTools.result(string2);
            }
            catch (Exception exception) {
                return MCPTools.error(exception);
            }
        }), MCPTools.spec("list_strategies", "List strategies in a databank of a project", jsonSchema3, (mcpSyncServerExchange, callToolRequest) -> {
            try {
                String string = (String)callToolRequest.arguments().get("name");
                String string2 = (String)callToolRequest.arguments().get("databank");
                HashMap<String, String[]> hashMap = new HashMap<String, String[]>();
                hashMap.put("projectName", new String[]{string});
                hashMap.put("databankName", new String[]{string2});
                String string3 = (String)Program.get((String)"Project").call("listStrategies", new Object[]{hashMap});
                return MCPTools.result(string3);
            }
            catch (Exception exception) {
                return MCPTools.error(exception);
            }
        }), MCPTools.spec("get_strategy_stats", "Get statistics columns and values for a specific strategy in a databank", jsonSchema4, (mcpSyncServerExchange, callToolRequest) -> {
            try {
                String string = (String)callToolRequest.arguments().get("name");
                String string2 = (String)callToolRequest.arguments().get("databank");
                String string3 = (String)callToolRequest.arguments().get("strategy");
                HashMap<String, String[]> hashMap = new HashMap<String, String[]>();
                hashMap.put("projectName", new String[]{string});
                hashMap.put("databankName", new String[]{string2});
                hashMap.put("strategyName", new String[]{string3});
                String string4 = (String)Program.get((String)"Project").call("getStrategyStats", new Object[]{hashMap});
                return MCPTools.result(string4);
            }
            catch (Exception exception) {
                return MCPTools.error(exception);
            }
        }), MCPTools.spec("run_project", "Start a project in StrategyQuant X", jsonSchema2, (mcpSyncServerExchange, callToolRequest) -> {
            try {
                String string = (String)callToolRequest.arguments().get("name");
                HashMap<String, String[]> hashMap = new HashMap<String, String[]>();
                hashMap.put("projectName", new String[]{string});
                String string2 = (String)Program.get((String)"Project").call("start", new Object[]{hashMap});
                return MCPTools.result(string2);
            }
            catch (Exception exception) {
                return MCPTools.error(exception);
            }
        }), MCPTools.spec("stop_project", "Stop a running project in StrategyQuant X", jsonSchema2, (mcpSyncServerExchange, callToolRequest) -> {
            try {
                String string = (String)callToolRequest.arguments().get("name");
                HashMap<String, String[]> hashMap = new HashMap<String, String[]>();
                hashMap.put("projectName", new String[]{string});
                String string2 = (String)Program.get((String)"Project").call("stop", new Object[]{hashMap});
                return MCPTools.result(string2);
            }
            catch (Exception exception) {
                return MCPTools.error(exception);
            }
        }));
    }

    private static McpServerFeatures.SyncToolSpecification spec(String string, String string2, McpSchema.JsonSchema jsonSchema, BiFunction<McpSyncServerExchange, McpSchema.CallToolRequest, McpSchema.CallToolResult> biFunction) {
        return McpServerFeatures.SyncToolSpecification.builder().tool(McpSchema.Tool.builder().name(string).description(string2).inputSchema(jsonSchema).build()).callHandler(biFunction::apply).build();
    }

    private static McpSchema.CallToolResult result(String string) {
        return McpSchema.CallToolResult.builder().content(List.of(new McpSchema.TextContent(MCPTools.extractMessage(string)))).isError(Boolean.valueOf(false)).build();
    }

    private static McpSchema.CallToolResult error(Exception exception) {
        Log.error("MCP tool error", (Throwable)exception);
        return McpSchema.CallToolResult.builder().content(List.of(new McpSchema.TextContent("Error: " + exception.getMessage()))).isError(Boolean.valueOf(true)).build();
    }

    static String extractMessage(String string) {
        return string;
    }
}

