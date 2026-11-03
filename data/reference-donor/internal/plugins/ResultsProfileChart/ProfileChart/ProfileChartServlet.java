/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.snippets.compile.SQStructure
 *  com.strategyquant.tradinglib.ResultsGroup
 *  com.strategyquant.tradinglib.databank.RecordNotFoundException
 *  com.strategyquant.tradinglib.results.IResultsGroupProvider
 *  com.strategyquant.tradinglib.results.SpecialValues
 *  com.strategyquant.webguilib.server.AbstractUIWebServer
 *  com.strategyquant.webguilib.servlet.HttpJSONServlet
 *  jakarta.servlet.ServletException
 *  jakarta.servlet.http.HttpServletRequest
 *  jakarta.servlet.http.HttpServletResponse
 *  org.json.JSONArray
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.Results.impl.ProfileChart;

import com.strategyquant.lib.L;
import com.strategyquant.lib.snippets.compile.SQStructure;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.databank.RecordNotFoundException;
import com.strategyquant.tradinglib.results.IResultsGroupProvider;
import com.strategyquant.tradinglib.results.SpecialValues;
import com.strategyquant.webguilib.server.AbstractUIWebServer;
import com.strategyquant.webguilib.servlet.HttpJSONServlet;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.io.File;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.net.URLDecoder;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.util.Map;
import org.json.JSONArray;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class ProfileChartServlet
extends HttpJSONServlet {
    private static final Logger Log = LoggerFactory.getLogger(ProfileChartServlet.class);
    private static final String LOCK_PROFILECHART = "ProfileChart";
    private final IResultsGroupProvider rgProvider;

    public ProfileChartServlet(IResultsGroupProvider rgProvider) {
        this.rgProvider = rgProvider;
    }

    protected void doGet(HttpServletRequest request, HttpServletResponse response) throws ServletException, IOException {
        String pathInfo = request.getPathInfo();
        if (pathInfo != null && pathInfo.startsWith("/view/")) {
            try {
                String svg = this.onView(pathInfo.substring(6));
                response.setCharacterEncoding("UTF-8");
                response.setContentType("image/svg+xml");
                response.setHeader("Access-Control-Allow-Origin", "*");
                response.getWriter().print(svg);
            }
            catch (Exception e) {
                Log.error("ProfileChart view failed", (Throwable)e);
                response.setStatus(404);
                response.getWriter().print(e.getMessage());
            }
            response.flushBuffer();
            return;
        }
        super.doGet(request, response);
    }

    protected String execute(String command, Map<String, String[]> parameterMap, String method) throws Exception {
        switch (command) {
            case "paths": {
                return this.onPaths(parameterMap);
            }
        }
        throw new Exception(L.t((String)"Unknown command '%s'.", (Object[])new Object[]{command}));
    }

    protected byte[] executeBinary(String command, Map<String, String[]> parameterMap, String method) throws Exception {
        if (command != null && command.startsWith("file/")) {
            return this.onFile(command.substring(5));
        }
        throw new Exception(L.t((String)"Unknown command '%s'.", (Object[])new Object[]{command}));
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private String onPaths(Map<String, String[]> parameterMap) {
        JSONObject response = new JSONObject();
        ResultsGroup resultsGroup = null;
        try {
            resultsGroup = this.rgProvider.get(parameterMap, LOCK_PROFILECHART);
            String pathsStr = resultsGroup.specialValues().getString(SpecialValues.ProfileChartPaths, "");
            JSONArray pathsArray = new JSONArray();
            if (pathsStr != null && !pathsStr.trim().isEmpty()) {
                for (String p : pathsStr.split(",")) {
                    String trimmed = p.trim();
                    if (trimmed.isEmpty()) continue;
                    int lastSep = Math.max(trimmed.lastIndexOf(47), trimmed.lastIndexOf(92));
                    String filename = lastSep >= 0 ? trimmed.substring(lastSep + 1) : trimmed;
                    pathsArray.put((Object)filename);
                }
            }
            response.put("profileChartPaths", (Object)pathsArray);
            response.put("baseUrl", (Object)(AbstractUIWebServer.getAppUrl() + "/profilechart/view/"));
        }
        catch (RecordNotFoundException e) {
            Log.info("onPaths: " + e.getMessage());
            String string = ProfileChartServlet.apiErrorJSONNoLog(null, (Exception)((Object)e));
            return string;
        }
        catch (Exception e) {
            String string = ProfileChartServlet.apiErrorJSON((String)L.t((String)"Getting profile chart paths failed", (Object[])new Object[0]), (Throwable)e);
            return string;
        }
        finally {
            if (resultsGroup != null) {
                resultsGroup.releaseLock(LOCK_PROFILECHART);
                resultsGroup = null;
            }
        }
        response.put("success", (Object)"ok");
        return response.toString();
    }

    private String onView(String encodedFilename) throws Exception {
        int end;
        String filename = URLDecoder.decode(encodedFilename, StandardCharsets.UTF_8);
        int lastSlash = Math.max(filename.lastIndexOf(47), filename.lastIndexOf(92));
        if (lastSlash >= 0) {
            filename = filename.substring(lastSlash + 1);
        }
        if (filename.contains("..") || filename.isEmpty()) {
            throw new IllegalArgumentException(L.t((String)"Invalid filename.", (Object[])new Object[0]));
        }
        File dir = new File(SQStructure.PROFILE_CHART_DIR);
        File file = new File(dir, filename);
        if (!file.getCanonicalPath().startsWith(dir.getCanonicalPath()) || !file.isFile()) {
            throw new FileNotFoundException(L.t((String)"Profile chart file not found.", (Object[])new Object[0]));
        }
        String svg = new String(Files.readAllBytes(file.toPath()), StandardCharsets.UTF_8);
        if (svg.startsWith("<?xml") && (end = svg.indexOf("?>")) >= 0) {
            svg = svg.substring(end + 2).trim();
        }
        return svg;
    }

    private byte[] onFile(String encodedFilename) throws Exception {
        String filename = URLDecoder.decode(encodedFilename, StandardCharsets.UTF_8);
        int lastSlash = Math.max(filename.lastIndexOf(47), filename.lastIndexOf(92));
        if (lastSlash >= 0) {
            filename = filename.substring(lastSlash + 1);
        }
        if (filename.contains("..") || filename.isEmpty()) {
            throw new IllegalArgumentException(L.t((String)"Invalid filename.", (Object[])new Object[0]));
        }
        File dir = new File(SQStructure.PROFILE_CHART_DIR);
        File file = new File(dir, filename);
        if (!file.getCanonicalPath().startsWith(dir.getCanonicalPath()) || !file.isFile()) {
            throw new FileNotFoundException(L.t((String)"Profile chart file not found.", (Object[])new Object[0]));
        }
        return Files.readAllBytes(file.toPath());
    }
}

