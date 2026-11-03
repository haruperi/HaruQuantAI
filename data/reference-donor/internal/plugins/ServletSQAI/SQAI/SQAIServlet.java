/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.ailib.agent.SQAIAgentLoop
 *  com.strategyquant.ailib.agent.SQAIAgentLoop$StepSink
 *  com.strategyquant.ailib.agent.SQAIHarness
 *  com.strategyquant.ailib.agent.SQAIWakeup
 *  com.strategyquant.ailib.chat.QProduct
 *  com.strategyquant.ailib.chat.SQAIBackendUrls
 *  com.strategyquant.ailib.chat.SQAIExtensionCommands
 *  com.strategyquant.ailib.chat.SQAIHttp
 *  com.strategyquant.ailib.chat.SQAIPathGrants
 *  com.strategyquant.ailib.chat.SQAIProgressPublisher
 *  com.strategyquant.ailib.chat.SQAIProjectStore
 *  com.strategyquant.ailib.chat.SQAISessionStore
 *  com.strategyquant.ailib.chat.SQAITerms
 *  com.strategyquant.ailib.chat.SQAITurns
 *  com.strategyquant.ailib.chat.SQAITurns$Turn
 *  com.strategyquant.ailib.chat.SQAIUploads
 *  com.strategyquant.ailib.extensions.AIExtensions
 *  com.strategyquant.ailib.model.SQAIConfig
 *  com.strategyquant.ailib.model.SQAIModelFactory
 *  com.strategyquant.ailib.reports.AIReports
 *  com.strategyquant.ailib.tools.MCPTools
 *  com.strategyquant.ailib.ui.SQAIUiContext
 *  com.strategyquant.ailib.ui.SQAIUiGate
 *  com.strategyquant.lib.app.MainApp
 *  com.strategyquant.webguilib.servlet.HttpJSONServlet
 *  io.agentscope.core.model.Model
 *  org.json.JSONArray
 *  org.json.JSONException
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.Servlet.impl.SQAI;

import com.strategyquant.ailib.agent.SQAIAgentLoop;
import com.strategyquant.ailib.agent.SQAIHarness;
import com.strategyquant.ailib.agent.SQAIWakeup;
import com.strategyquant.ailib.chat.QProduct;
import com.strategyquant.ailib.chat.SQAIBackendUrls;
import com.strategyquant.ailib.chat.SQAIExtensionCommands;
import com.strategyquant.ailib.chat.SQAIHttp;
import com.strategyquant.ailib.chat.SQAIPathGrants;
import com.strategyquant.ailib.chat.SQAIProgressPublisher;
import com.strategyquant.ailib.chat.SQAIProjectStore;
import com.strategyquant.ailib.chat.SQAISessionStore;
import com.strategyquant.ailib.chat.SQAITerms;
import com.strategyquant.ailib.chat.SQAITurns;
import com.strategyquant.ailib.chat.SQAIUploads;
import com.strategyquant.ailib.extensions.AIExtensions;
import com.strategyquant.ailib.model.SQAIConfig;
import com.strategyquant.ailib.model.SQAIModelFactory;
import com.strategyquant.ailib.reports.AIReports;
import com.strategyquant.ailib.tools.MCPTools;
import com.strategyquant.ailib.ui.SQAIUiContext;
import com.strategyquant.ailib.ui.SQAIUiGate;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.webguilib.servlet.HttpJSONServlet;
import io.agentscope.core.model.Model;
import java.io.File;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.OpenOption;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.concurrent.Semaphore;
import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

class SQAIServlet
extends HttpJSONServlet {
    private static final Logger Log = LoggerFactory.getLogger((String)"SQAIServlet");
    private static final Semaphore completionSlots = new Semaphore(2);

    SQAIServlet() {
    }

    protected String execute(String command, Map<String, String[]> params, String method) throws Exception {
        switch (command) {
            case "config": {
                return this.getConfigStatus();
            }
            case "reinit": {
                return this.handleReinit();
            }
            case "rescan": {
                AIExtensions.syncClaudeWiring();
                return "{\"success\":\"AI plugins rescanned\"}";
            }
            case "extensions": {
                return SQAIExtensionCommands.handleExtensions();
            }
            case "chat": {
                return this.handleChat(params);
            }
            case "upload": {
                return SQAIUploads.handleUpload(params);
            }
            case "complete": {
                return this.handleComplete(params);
            }
            case "turn": {
                return this.handleTurnStatus(params);
            }
            case "stop": {
                return this.handleStop(params);
            }
            case "wakeup": {
                return "DELETE".equals(method) ? SQAIWakeup.get().cancel("user").toString() : SQAIWakeup.get().status().toString();
            }
            case "model": {
                return this.handleModelSelect(params);
            }
            case "terms": {
                return "POST".equals(method) ? SQAITerms.accept() : SQAITerms.status();
            }
            case "history": {
                return "DELETE".equals(method) ? this.clearHistory(params) : this.getHistory(params);
            }
            case "sessions": {
                return "POST".equals(method) || "PUT".equals(method) ? this.renameSession(params) : this.listSessions();
            }
            case "projects": {
                return this.handleProjects(params, method);
            }
            case "open-strategy": {
                return this.handleOpenStrategy(params);
            }
            case "report-pdf": {
                return this.handleReportPdf(params);
            }
            case "catalog": {
                return MCPTools.loadUiCatalogArray().toString();
            }
            case "flows": {
                return MCPTools.loadUiFlowsArray().toString();
            }
            case "audit-result": {
                return this.handleAuditResult(params);
            }
            case "skills": {
                return this.handleSkills(params, method);
            }
            case "workspace": {
                return this.handleWorkspace(params, method);
            }
            case "memory": {
                return this.handleMemory(params, method);
            }
            case "ui-context": {
                return this.handleUiContext(params);
            }
        }
        return SQAIServlet.apiErrorJSON((String)("Unknown command: " + command), null);
    }

    private String handleOpenStrategy(Map<String, String[]> params) {
        try {
            JSONObject resp = MCPTools.openInAlgoWizardPayload((String)SQAIHttp.getParamOrNull(params, (String)"file"), (String)SQAIHttp.getParamOrNull(params, (String)"name"), (String)SQAIHttp.getParamOrNull(params, (String)"databank"), (String)SQAIHttp.getParamOrNull(params, (String)"strategy"), (!"0".equals(SQAIHttp.getParamOrNull(params, (String)"askName")) ? 1 : 0) != 0);
            if (resp.has("error")) {
                return SQAIServlet.apiErrorJSON((String)resp.getString("error"), null);
            }
            JSONObject out = new JSONObject();
            out.put("success", (Object)resp.optString("success", "ok"));
            out.put("actions", (Object)new JSONArray().put((Object)resp.getJSONObject("_action")));
            return out.toString();
        }
        catch (Exception e) {
            return SQAIServlet.apiErrorJSON((String)("Cannot open the strategy: " + SQAIHttp.message((Throwable)e)), null);
        }
    }

    private String handleReportPdf(Map<String, String[]> params) {
        try {
            String htmlFile = SQAIHttp.getParamOrNull(params, (String)"htmlFile");
            String pdfFile = SQAIHttp.getParamOrNull(params, (String)"pdfFile");
            if (htmlFile == null || htmlFile.trim().isEmpty()) {
                return SQAIServlet.apiErrorJSON((String)"htmlFile is required", null);
            }
            JSONObject resp = MCPTools.reportPdfToChosenFile((String)htmlFile, (String)pdfFile);
            if (resp.has("error")) {
                return SQAIServlet.apiErrorJSON((String)resp.getString("error"), null);
            }
            return resp.toString();
        }
        catch (Exception e) {
            return SQAIServlet.apiErrorJSON((String)("Cannot save the PDF: " + SQAIHttp.message((Throwable)e)), null);
        }
    }

    private String getConfigStatus() throws Exception {
        JSONObject catalog;
        JSONObject cfg = SQAIConfig.readConfigFile();
        JSONObject result = new JSONObject();
        result.put("success", (Object)"Config loaded");
        result.put("provider", (Object)"sq");
        result.put("modelName", (Object)SQAIModelFactory.getModelName((JSONObject)cfg));
        result.put("status", (Object)SQAIModelFactory.modelStatus);
        result.put("ready", SQAIModelFactory.model != null);
        if (SQAIModelFactory.model == null) {
            result.put("error", (Object)SQAIModelFactory.modelStatus);
        }
        if ((catalog = SQAIModelFactory.getGatewayModels()) != null) {
            result.put("models", (Object)catalog.optJSONArray("models"));
            if (catalog.has("default")) {
                result.put("defaultModel", (Object)catalog.getJSONObject("default"));
            }
            result.put("modelsSource", (Object)"gateway");
        } else {
            result.put("modelsError", (Object)(SQAIConfig.isTestMode() ? "Model list disabled - test mode (testmode.txt)" : "Model list unavailable - could not reach " + SQAIModelFactory.gatewayLabel()));
        }
        result.put("sqModel", (Object)SQAIModelFactory.resolveSqModel((JSONObject)SQAIConfig.sqSection((JSONObject)cfg)));
        JSONObject backendUrls = SQAIBackendUrls.toJSON();
        if (backendUrls.length() > 0) {
            result.put("backendUrls", (Object)backendUrls);
        }
        result.put("product", (Object)QProduct.key());
        return result.toString();
    }

    private String handleModelSelect(Map<String, String[]> params) {
        String model;
        String provider = SQAIHttp.optParam(params, (String)"provider");
        if (!provider.isEmpty() && !"sq".equals(provider)) {
            return SQAIHttp.errorJSON((String)"Only the StrategyQuant AI service is available.");
        }
        JSONObject cfg = SQAIConfig.readConfigFile();
        JSONObject gw = cfg.optJSONObject("sq");
        if (gw == null) {
            gw = new JSONObject();
            cfg.put("sq", (Object)gw);
        }
        if (!(model = SQAIHttp.optParam(params, (String)"model")).isEmpty()) {
            gw.put("model", (Object)model);
        }
        return this.applyConfig(cfg);
    }

    private String applyConfig(JSONObject candidate) {
        try {
            return SQAIModelFactory.switchModel((JSONObject)candidate).toString();
        }
        catch (Exception e) {
            Log.warn("SQAI: rejected model configuration for '{}' \u2014 {}", (Object)candidate.optString("provider", ""), (Object)SQAIHttp.message((Throwable)e));
            return SQAIHttp.errorJSON((String)("Could not use this model: " + SQAIHttp.message((Throwable)e)));
        }
    }

    private String handleReinit() {
        SQAIModelFactory.initModel();
        JSONObject result = new JSONObject();
        if (SQAIModelFactory.model == null) {
            result.put("error", (Object)SQAIModelFactory.modelStatus);
        } else {
            result.put("success", (Object)SQAIModelFactory.modelStatus);
        }
        return result.toString();
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private String handleChat(Map<String, String[]> params) throws Exception {
        String reply;
        SQAITurns.Turn running;
        if (SQAIModelFactory.model == null) {
            return SQAIServlet.apiErrorJSON((String)("No model is running (" + SQAIModelFactory.modelStatus + "). Pick a model in the chat, or fix internal/web/SQAI/sqai.config and POST /sqai/reinit."), null);
        }
        String message = SQAIHttp.getParamOrNull(params, (String)"message");
        if (message == null) {
            message = "";
        }
        boolean async = SQAIHttp.isTruthy((String)SQAIHttp.getParamOrNull(params, (String)"async"));
        String sid = SQAITurns.sanitizeSessionId((String)SQAIHttp.getParamOrNull(params, (String)"sessionId"));
        if (sid != null) {
            SQAITurns.currentSessionId = sid;
            AIReports.setCurrentSession((String)SQAITurns.currentSessionId);
        }
        JSONArray attachments = SQAIUploads.resolveAttachments((String)SQAITurns.sessionOrDefault(), (String)SQAIHttp.getParamOrNull(params, (String)"attachments"));
        if (message.trim().isEmpty()) {
            if (attachments == null) {
                return SQAIServlet.apiErrorJSON((String)"Missing 'message'.", null);
            }
            message = "(The user shared the attached file" + (attachments.length() == 1 ? "" : "s") + ".)";
        }
        if ((running = (SQAITurns.Turn)SQAITurns.runningTurns.get(SQAITurns.sessionOrDefault())) != null && running.wakeup) {
            return SQAIServlet.apiErrorJSON((String)("A scheduled continuation is running in this conversation (" + running.toolCalls + " tool calls, " + SQAITurns.formatElapsed((long)running.elapsedMs()) + "). Stop it first, or wait for it to finish."), null);
        }
        if (async) {
            SQAITurns.Turn turn = new SQAITurns.Turn(false, message, attachments, sid);
            if (SQAITurns.runningTurns.putIfAbsent(turn.sessionId, turn) != null) {
                return SQAIServlet.apiErrorJSON((String)"A turn is already running in this conversation. Stop it first, or wait for its chat_reply.", null);
            }
            SQAITurns.asyncTurnRunner.execute(() -> SQAITurns.runAsyncTurn((String)turn.message, (SQAITurns.Turn)turn));
            JSONObject accepted = new JSONObject();
            accepted.put("accepted", true);
            accepted.put("async", true);
            accepted.put("sessionId", (Object)turn.sessionId);
            accepted.put("success", (Object)"Turn started. Steps stream over the WebSocket; the reply arrives as a chat_reply event. Re-attach state: GET /sqai/turn.");
            return accepted.toString();
        }
        SQAITurns.Turn turn = new SQAITurns.Turn(false, message, attachments, sid);
        if (SQAITurns.runningTurns.putIfAbsent(turn.sessionId, turn) != null) {
            return SQAIServlet.apiErrorJSON((String)"A turn is already running in this conversation. Stop it first, or wait for it to finish.", null);
        }
        JSONArray steps = new JSONArray();
        List collectedActions = SQAITurns.newActionList();
        try {
            reply = SQAITurns.runChatTurn((String)message, (List)collectedActions, (SQAIAgentLoop.StepSink)SQAITurns.stepCollector((JSONArray)steps, (SQAITurns.Turn)turn, arg_0 -> ((SQAIProgressPublisher)SQAIProgressPublisher.get()).add(arg_0)), (SQAITurns.Turn)turn);
        }
        catch (Exception e) {
            Log.error("SQAI: turn failed", (Throwable)e);
            reply = SQAITurns.failedTurnReply((SQAITurns.Turn)turn, (Exception)e);
            SQAITurns.persistFailedTurn((SQAITurns.Turn)turn, (String)message, (String)reply);
        }
        finally {
            SQAITurns.runningTurns.remove(turn.sessionId, turn);
        }
        SQAIProgressPublisher.get().add(new JSONObject().put("type", (Object)"done").put("sessionId", (Object)turn.sessionId).put("elapsedMs", turn.elapsedMs()).put("toolCalls", turn.toolCalls).put("stopped", turn.stopped));
        JSONObject result = new JSONObject();
        result.put("success", (Object)reply);
        result.put("history", (Object)SQAISessionStore.loadTail((String)turn.sessionId, (int)15));
        result.put("elapsedMs", turn.elapsedMs());
        result.put("toolCalls", turn.toolCalls);
        if (turn.stopped) {
            result.put("stopped", true);
        }
        if (steps.length() > 0) {
            result.put("steps", (Object)steps);
        }
        if (!collectedActions.isEmpty()) {
            JSONArray actionsArr = new JSONArray();
            for (JSONObject a : collectedActions) {
                actionsArr.put((Object)a);
            }
            result.put("actions", (Object)actionsArr);
        }
        if (turn.reports != null && turn.reports.length() > 0) {
            result.put("reports", (Object)turn.reports);
        }
        return result.toString();
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private String handleComplete(Map<String, String[]> params) {
        if (SQAIModelFactory.model == null) {
            return SQAIServlet.apiErrorJSON((String)("No model is running (" + SQAIModelFactory.modelStatus + "). Pick a model in the AI chat, or fix internal/web/SQAI/sqai.config and POST /sqai/reinit."), null);
        }
        String prompt = SQAIHttp.getParamOrNull(params, (String)"prompt");
        if (prompt == null || prompt.trim().isEmpty()) {
            return SQAIServlet.apiErrorJSON((String)"Missing 'prompt'.", null);
        }
        String system = SQAIHttp.getParamOrNull(params, (String)"system");
        if (!completionSlots.tryAcquire()) {
            return SQAIServlet.apiErrorJSON((String)"Too many completions in flight (max 2). Retry in a moment.", null);
        }
        long startedAt = System.currentTimeMillis();
        try {
            String text = SQAIAgentLoop.oneShotCompletion((String)(system != null && !system.trim().isEmpty() ? system : "You are a concise assistant embedded in StrategyQuant X. Answer directly, without preamble."), (String)prompt);
            if (text == null || text.trim().isEmpty()) {
                String string = SQAIServlet.apiErrorJSON((String)"The model returned no text.", null);
                return string;
            }
            JSONObject result = new JSONObject();
            result.put("success", (Object)text);
            result.put("elapsedMs", System.currentTimeMillis() - startedAt);
            String string = result.toString();
            return string;
        }
        catch (Exception e) {
            Log.error("SQAI: completion failed", (Throwable)e);
            String string = SQAIServlet.apiErrorJSON((String)("Completion failed: " + SQAIHttp.message((Throwable)e)), null);
            return string;
        }
        finally {
            completionSlots.release();
        }
    }

    private String handleTurnStatus(Map<String, String[]> params) {
        String sid = SQAITurns.sanitizeSessionId((String)SQAIHttp.getParamOrNull(params, (String)"sessionId"));
        SQAITurns.Turn turn = sid != null ? (SQAITurns.Turn)SQAITurns.runningTurns.get(sid) : SQAITurns.anyRunningTurn();
        JSONObject result = new JSONObject();
        result.put("running", turn != null);
        if (turn != null) {
            result.put("sessionId", (Object)turn.sessionId);
            result.put("wakeup", turn.wakeup);
            result.put("message", (Object)(turn.message == null ? "" : turn.message));
            result.put("toolCalls", turn.toolCalls);
            result.put("elapsedMs", turn.elapsedMs());
            result.put("stopRequested", turn.cancelled);
        } else if (sid != null) {
            result.put("sessionId", (Object)sid);
        } else if (!SQAITurns.currentSessionId.isEmpty()) {
            result.put("sessionId", (Object)SQAITurns.currentSessionId);
        }
        JSONArray running = new JSONArray();
        for (SQAITurns.Turn t : SQAITurns.runningTurns.values()) {
            running.put((Object)new JSONObject().put("sessionId", (Object)t.sessionId).put("wakeup", t.wakeup).put("message", (Object)(t.message == null ? "" : t.message)).put("toolCalls", t.toolCalls).put("elapsedMs", t.elapsedMs()));
        }
        result.put("turns", (Object)running);
        return result.toString();
    }

    private String handleStop(Map<String, String[]> params) {
        boolean wakeupCancelled = SQAIWakeup.get().cancel("stop").optBoolean("cancelled", false);
        String sid = SQAITurns.sanitizeSessionId((String)SQAIHttp.getParamOrNull(params, (String)"sessionId"));
        ArrayList<Object> targets = new ArrayList<Object>();
        if (sid != null) {
            SQAITurns.Turn t = (SQAITurns.Turn)SQAITurns.runningTurns.get(sid);
            if (t != null) {
                targets.add(t);
            }
        } else {
            targets.addAll(SQAITurns.runningTurns.values());
        }
        JSONObject result = new JSONObject();
        if (targets.isEmpty()) {
            result.put("success", (Object)(wakeupCancelled ? "Pending scheduled wakeup cancelled. No chat turn is running." : "No chat turn is running."));
            result.put("accepted", false);
            result.put("wakeupCancelled", wakeupCancelled);
            return result.toString();
        }
        int toolCalls = 0;
        long elapsed = 0L;
        for (SQAITurns.Turn turn : targets) {
            SQAITurns.cancel((SQAITurns.Turn)turn);
            toolCalls += turn.toolCalls;
            elapsed = Math.max(elapsed, turn.elapsedMs());
            Log.info("SQAI: stop requested for session {} after {} tool call(s), {}", new Object[]{turn.sessionId, turn.toolCalls, SQAITurns.formatElapsed((long)turn.elapsedMs())});
        }
        result.put("success", (Object)("Stopping after " + toolCalls + " tool call(s)."));
        result.put("accepted", true);
        result.put("elapsedMs", elapsed);
        result.put("toolCalls", toolCalls);
        result.put("wakeupCancelled", wakeupCancelled);
        return result.toString();
    }

    private String handleUiContext(Map<String, String[]> params) throws Exception {
        JSONObject answer;
        String requestId = SQAIHttp.optParam(params, (String)"requestId");
        if (requestId.isEmpty()) {
            return SQAIHttp.errorJSON((String)"requestId is required");
        }
        String context = SQAIHttp.getParamOrNull(params, (String)"context");
        if (context == null) {
            return SQAIHttp.errorJSON((String)"context is required");
        }
        try {
            answer = new JSONObject(context);
        }
        catch (JSONException e) {
            return SQAIHttp.errorJSON((String)"context is not a JSON object");
        }
        boolean accepted = SQAIUiContext.complete((String)requestId, (JSONObject)answer);
        JSONObject result = new JSONObject();
        result.put("success", (Object)(accepted ? "Answer delivered to the waiting tool call." : "No tool call is waiting for this answer."));
        result.put("accepted", accepted);
        return result.toString();
    }

    private String handleAuditResult(Map<String, String[]> params) throws Exception {
        String data = SQAIHttp.getParamOrNull(params, (String)"data");
        if (data == null) {
            return SQAIHttp.errorJSON((String)"data is required");
        }
        File f = new File(MainApp.getDataPath(), "internal/web/SQAI/audit-result.json");
        Files.write(f.toPath(), data.getBytes(StandardCharsets.UTF_8), new OpenOption[0]);
        Log.info("SQAI audit result saved: {} ({} bytes)", (Object)f.getAbsolutePath(), (Object)data.length());
        JSONObject r = new JSONObject();
        r.put("saved", (Object)"internal/web/SQAI/audit-result.json");
        r.put("bytes", data.length());
        return r.toString();
    }

    private String handleWorkspace(Map<String, String[]> params, String method) throws Exception {
        String path = SQAIHttp.optParam(params, (String)"path");
        if ("POST".equals(method) || "PUT".equals(method)) {
            String content = SQAIHttp.getParamOrNull(params, (String)"content");
            if (content == null) {
                return SQAIHttp.errorJSON((String)"content is required");
            }
            return SQAIHarness.saveWorkspaceFile((String)path, (String)content).toString();
        }
        if (path.isEmpty()) {
            return SQAIHarness.workspaceOverview((JSONObject)SQAIConfig.readConfigFile()).toString();
        }
        return SQAIHarness.readWorkspaceFile((String)path).toString();
    }

    private String handleMemory(Map<String, String[]> params, String method) throws Exception {
        JSONObject cfg = SQAIConfig.readConfigFile();
        if ("POST".equals(method) || "PUT".equals(method)) {
            String v = SQAIHttp.optParam(params, (String)"enabled").trim().toLowerCase();
            if (v.isEmpty()) {
                return SQAIHttp.errorJSON((String)"enabled=true|false is required");
            }
            cfg.put("memoryEnabled", v.equals("true") || v.equals("1") || v.equals("on"));
            SQAIConfig.writeConfigFile((JSONObject)cfg);
            Log.info("SQAI: memory switched {}", (Object)(SQAIHarness.memoryEnabled((JSONObject)cfg) ? "on" : "off"));
        }
        return new JSONObject().put("enabled", SQAIHarness.memoryEnabled((JSONObject)cfg)).toString();
    }

    private String handleSkills(Map<String, String[]> params, String method) {
        if (!"POST".equals(method)) {
            return SQAIHarness.skillsStatus().toString();
        }
        String action = SQAIHttp.optParam(params, (String)"action");
        String name = SQAIHttp.getParamOrNull(params, (String)"name");
        switch (action) {
            case "promote": {
                return SQAIHarness.promoteSkill((String)name, (Model)SQAIModelFactory.model, (JSONObject)SQAIConfig.readConfigFile()).toString();
            }
            case "discard": {
                return SQAIHarness.discardDraft((String)name).toString();
            }
        }
        return SQAIHttp.errorJSON((String)("unknown action: " + action));
    }

    private String getHistory(Map<String, String[]> params) {
        String sid = SQAITurns.sanitizeSessionId((String)SQAIHttp.getParamOrNull(params, (String)"sessionId"));
        if (sid == null) {
            sid = SQAITurns.sessionOrDefault();
        }
        SQAITurns.currentSessionId = sid;
        AIReports.setCurrentSession((String)sid);
        JSONObject result = new JSONObject();
        result.put("success", (Object)"ok");
        JSONArray combined = SQAISessionStore.load((String)sid);
        for (JSONObject orphan : AIReports.orphanHistoryEntries((JSONArray)combined)) {
            String orphanSid = orphan.optString("sessionId", "");
            if (orphanSid.isEmpty()) {
                orphanSid = "default";
            }
            if (!sid.equals(orphanSid)) continue;
            combined.put((Object)orphan);
        }
        result.put("history", (Object)combined);
        result.put("sessionId", (Object)sid);
        return result.toString();
    }

    private String clearHistory(Map<String, String[]> params) {
        SQAITurns.Turn running;
        String sid = SQAITurns.sanitizeSessionId((String)SQAIHttp.getParamOrNull(params, (String)"sessionId"));
        SQAITurns.Turn turn = running = sid != null ? (SQAITurns.Turn)SQAITurns.runningTurns.get(sid) : null;
        if (sid != null) {
            SQAISessionStore.delete((String)sid);
            SQAIHarness.clearSession((String)sid);
            AIReports.deleteSession((String)sid);
            MCPTools.deleteSessionWorkspace((String)sid);
            SQAIProjectStore.forgetSession((String)sid);
            if (running != null && sid.equals(running.sessionId)) {
                running.discardFromHistory = true;
            }
            if (sid.equals(SQAITurns.currentSessionId)) {
                SQAIUiGate.reset();
                SQAIPathGrants.reset();
                SQAITurns.currentSessionId = "";
                AIReports.setCurrentSession((String)"");
            }
            return "{\"success\":\"Session deleted\"}";
        }
        JSONArray all = SQAISessionStore.sessions();
        for (int i = 0; i < all.length(); ++i) {
            String id = all.getJSONObject(i).optString("id");
            if (id.isEmpty()) continue;
            AIReports.deleteSession((String)id);
            MCPTools.deleteSessionWorkspace((String)id);
        }
        SQAISessionStore.deleteAll();
        SQAIHarness.clearAllSessions();
        SQAIProjectStore.forgetAllSessions();
        SQAIUiGate.reset();
        SQAIPathGrants.reset();
        for (SQAITurns.Turn t : SQAITurns.runningTurns.values()) {
            t.discardFromHistory = true;
        }
        if (!SQAITurns.currentSessionId.isEmpty()) {
            SQAITurns.currentSessionId = "";
            AIReports.setCurrentSession((String)"");
        }
        return "{\"success\":\"History cleared\"}";
    }

    private String listSessions() {
        return new JSONObject().put("success", (Object)"ok").put("sessions", (Object)SQAISessionStore.sessions()).put("projects", (Object)SQAIProjectStore.projects()).put("pinned", (Object)SQAIProjectStore.pinned()).toString();
    }

    private String handleProjects(Map<String, String[]> params, String method) {
        if (!"POST".equals(method) && !"PUT".equals(method)) {
            return new JSONObject().put("success", (Object)"ok").put("projects", (Object)SQAIProjectStore.projects()).put("pinned", (Object)SQAIProjectStore.pinned()).toString();
        }
        String action = SQAIHttp.getParamOrNull(params, (String)"action");
        if (action == null) {
            return SQAIServlet.apiErrorJSON((String)"action is required(create|rename|delete|move|pin|unpin)", null);
        }
        switch (action) {
            case "create": {
                String id = SQAIProjectStore.createProject((String)SQAIHttp.getParamOrNull(params, (String)"name"));
                if (id == null) {
                    return SQAIServlet.apiErrorJSON((String)"name is required", null);
                }
                return new JSONObject().put("success", (Object)"Project created").put("projectId", (Object)id).toString();
            }
            case "rename": {
                boolean ok = SQAIProjectStore.renameProject((String)SQAIHttp.getParamOrNull(params, (String)"projectId"), (String)SQAIHttp.getParamOrNull(params, (String)"name"));
                return ok ? "{\"success\":\"Project renamed\"}" : SQAIServlet.apiErrorJSON((String)"projectId and name are required(and the project must exist)", null);
            }
            case "delete": {
                boolean ok = SQAIProjectStore.deleteProject((String)SQAIHttp.getParamOrNull(params, (String)"projectId"));
                return ok ? "{\"success\":\"Project deleted, its conversations moved to Chats\"}" : SQAIServlet.apiErrorJSON((String)"unknown projectId", null);
            }
            case "move": {
                String sid = SQAITurns.sanitizeSessionId((String)SQAIHttp.getParamOrNull(params, (String)"sessionId"));
                if (sid == null) {
                    return SQAIServlet.apiErrorJSON((String)"sessionId is required", null);
                }
                SQAIProjectStore.moveSession((String)sid, (String)SQAIHttp.getParamOrNull(params, (String)"projectId"));
                return "{\"success\":\"Session moved\"}";
            }
            case "pin": {
                String sid = SQAITurns.sanitizeSessionId((String)SQAIHttp.getParamOrNull(params, (String)"sessionId"));
                if (sid == null) {
                    return SQAIServlet.apiErrorJSON((String)"sessionId is required", null);
                }
                SQAIProjectStore.pin((String)sid);
                return "{\"success\":\"Session pinned\"}";
            }
            case "unpin": {
                String sid = SQAITurns.sanitizeSessionId((String)SQAIHttp.getParamOrNull(params, (String)"sessionId"));
                if (sid == null) {
                    return SQAIServlet.apiErrorJSON((String)"sessionId is required", null);
                }
                SQAIProjectStore.unpin((String)sid);
                return "{\"success\":\"Session unpinned\"}";
            }
        }
        return SQAIServlet.apiErrorJSON((String)("Unknown action '" + action + "'"), null);
    }

    private String renameSession(Map<String, String[]> params) {
        String sid = SQAITurns.sanitizeSessionId((String)SQAIHttp.getParamOrNull(params, (String)"sessionId"));
        String name = SQAIHttp.getParamOrNull(params, (String)"name");
        if (sid == null || name == null || name.trim().isEmpty()) {
            return SQAIServlet.apiErrorJSON((String)"sessionId and name are required", null);
        }
        SQAISessionStore.rename((String)sid, (String)name);
        return "{\"success\":\"Session renamed\"}";
    }
}

