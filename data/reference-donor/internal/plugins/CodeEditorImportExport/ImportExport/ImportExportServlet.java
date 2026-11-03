/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.app.MainApp
 *  com.strategyquant.webguilib.servlet.HttpJSONServlet
 *  org.json.JSONArray
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.CodeEditor.impl.ImportExport;

import com.strategyquant.lib.L;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.plugin.CodeEditor.impl.ImportExport.ExtensionManager;
import com.strategyquant.plugin.CodeEditor.impl.ImportExport.ExtensionsFileMap;
import com.strategyquant.webguilib.servlet.HttpJSONServlet;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.Map;
import org.json.JSONArray;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class ImportExportServlet
extends HttpJSONServlet {
    private static final Logger Log = LoggerFactory.getLogger(ImportExportServlet.class);
    private static ExtensionsFileMap fileMap = null;
    private static final String KEY_SUCCESS = "success";
    private static final String KEY_FILE = "file";
    private static final String KEY_FILES = "files";
    private static final String KEY_COMPILATION_RESULT = "compilationResult";
    private static final String KEY_INDICATORS = "indicators";
    private static final String KEY_TEMPLATE = "template";
    private static final String KEY_TEMPLATES = "templates";
    private static final String KEY_ID = "id";
    private static final String KEY_TEXT = "text";
    private static final String KEY_MATCHES = "matches";
    private static final String KEY_ITEM = "item";
    private static final String KEY_ITEMS = "items";
    private static final String KEY_NAME = "name";
    private static final String KEY_PROTECTED = "protected";
    private static final String KEY_TYPE = "type";
    private static final String KEY_DESCRIPTION = "description";
    private static final String KEY_DATA = "data";

    protected String execute(String command, Map<String, String[]> args, String method) throws Exception {
        switch (command) {
            case "import": {
                return this.onImport(args);
            }
            case "export": {
                return this.onExport(args);
            }
            case "overwrite": {
                return this.onOverwrite(args);
            }
            case "overwriteAlways": {
                return this.onOverwriteAlways(args);
            }
            case "skip": {
                return this.onSkip(args);
            }
            case "skipAlways": {
                return this.onSkipAlways(args);
            }
            case "cancel": {
                return this.onCancel(args);
            }
            case "list": {
                return this.onList(args);
            }
        }
        return ImportExportServlet.apiErrorJSON((String)L.t((String)"Execution failed. Unknown command '%s'.", (Object[])new Object[]{command}), null);
    }

    private String onList(Map<String, String[]> parameterMap) throws Exception {
        String filter = parameterMap.get("filter")[0];
        JSONObject response = new JSONObject();
        LinkedHashMap<String, String> sourceDirs = new LinkedHashMap<String, String>();
        sourceDirs.put(MainApp.getDataPath() + "user", "user");
        int index = 0;
        response.put(KEY_ID, index++);
        JSONArray itemArray = ImportExportServlet.getFileMapInstance().generateTree(sourceDirs, filter, index);
        response.put(KEY_ITEM, (Object)itemArray);
        response.put(KEY_SUCCESS, (Object)"Sources listed.");
        return response.toString();
    }

    private static synchronized ExtensionsFileMap getFileMapInstance() {
        if (fileMap == null) {
            fileMap = new ExtensionsFileMap();
        }
        return fileMap;
    }

    private String onImport(Map<String, String[]> args) {
        JSONObject response = new JSONObject();
        try {
            String files = this.tryGetParam(args, KEY_FILES)[0];
            String[] filePaths = files.split(",");
            ArrayList<String> createdFiles = ExtensionManager.install(filePaths);
            JSONArray newFiles = new JSONArray();
            for (int a = 0; a < createdFiles.size(); ++a) {
                String file = createdFiles.get(a);
                newFiles.put((Object)file);
            }
            JSONArray notImportedFiles = new JSONArray();
            for (Map.Entry<String, String> entry : ExtensionManager.notImportedMap.entrySet()) {
                notImportedFiles.put((Object)new JSONObject().put(KEY_NAME, (Object)entry.getKey()).put("reason", (Object)entry.getValue()));
            }
            response.put("newFiles", (Object)newFiles);
            response.put("notImportedFiles", (Object)notImportedFiles);
        }
        catch (Exception e) {
            return ImportExportServlet.apiErrorJSON((String)L.t((String)"Import failed.", (Object[])new Object[0]), (Throwable)e);
        }
        response.put(KEY_SUCCESS, (Object)L.t((String)"Extensions imported.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onExport(Map<String, String[]> args) {
        JSONObject response = new JSONObject();
        try {
            String files = this.tryGetParam(args, KEY_FILES)[0];
            String targetPath = this.tryGetParam(args, "targetPath")[0];
            if (files.trim().isEmpty()) {
                throw new Exception(L.t((String)"There are no files to export.", (Object[])new Object[0]));
            }
            String[] filePaths = files.split(",");
            ExtensionManager.export(filePaths, targetPath);
        }
        catch (Exception e) {
            return ImportExportServlet.apiErrorJSON((String)L.t((String)"Export failed.", (Object[])new Object[0]), (Throwable)e);
        }
        response.put(KEY_SUCCESS, (Object)L.t((String)"Extensions exported.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onOverwrite(Map<String, String[]> args) {
        JSONObject response = new JSONObject();
        ExtensionManager.overwrite();
        response.put(KEY_SUCCESS, (Object)L.t((String)"Import overwritten.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onOverwriteAlways(Map<String, String[]> args) {
        JSONObject response = new JSONObject();
        ExtensionManager.overwriteAlways();
        response.put(KEY_SUCCESS, (Object)L.t((String)"Import will always overwrite.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onSkip(Map<String, String[]> args) {
        JSONObject response = new JSONObject();
        ExtensionManager.skip();
        response.put(KEY_SUCCESS, (Object)L.t((String)"Import skipped.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onSkipAlways(Map<String, String[]> args) {
        JSONObject response = new JSONObject();
        ExtensionManager.skipAlways();
        response.put(KEY_SUCCESS, (Object)L.t((String)"Import will always skip.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onCancel(Map<String, String[]> args) {
        JSONObject response = new JSONObject();
        ExtensionManager.cancelImport();
        response.put(KEY_SUCCESS, (Object)L.t((String)"Import canceled.", (Object[])new Object[0]));
        return response.toString();
    }
}

