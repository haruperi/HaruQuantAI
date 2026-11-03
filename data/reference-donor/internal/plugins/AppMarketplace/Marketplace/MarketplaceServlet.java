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
package com.strategyquant.plugin.App.impl.Marketplace;

import com.strategyquant.lib.L;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.plugin.App.impl.Marketplace.MarketplaceDb;
import com.strategyquant.plugin.App.impl.Marketplace.MarketplaceFileMap;
import com.strategyquant.plugin.App.impl.Marketplace.MarketplaceManager;
import com.strategyquant.webguilib.servlet.HttpJSONServlet;
import java.io.File;
import java.util.LinkedHashMap;
import java.util.Map;
import org.json.JSONArray;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class MarketplaceServlet
extends HttpJSONServlet {
    private static final Logger Log = LoggerFactory.getLogger(MarketplaceServlet.class);
    private static MarketplaceFileMap fileMap = null;

    protected String execute(String command, Map<String, String[]> args, String method) throws Exception {
        switch (command) {
            case "installed": {
                return this.onInstalled(args);
            }
            case "install": {
                return this.onInstall(args);
            }
            case "recordShare": {
                return this.onRecordShare(args);
            }
            case "uninstall": {
                return this.onUninstall(args);
            }
            case "listShareable": {
                return this.onListShareable(args);
            }
            case "buildZip": {
                return this.onBuildZip(args);
            }
            case "upload": {
                return this.onUpload(args);
            }
            case "cleanup": {
                return this.onCleanup(args);
            }
        }
        throw new Exception(L.t((String)"Unknown command '%s'.", (Object[])new Object[]{command}));
    }

    private String onInstalled(Map<String, String[]> args) {
        JSONObject response = new JSONObject();
        response.put("installed", (Object)MarketplaceDb.get().listInstalled());
        response.put("success", (Object)"Installed products listed.");
        return response.toString();
    }

    private String onInstall(Map<String, String[]> args) {
        JSONObject response = new JSONObject();
        try {
            String slug = this.tryGetParam(args, "productSlug")[0];
            String downloadUrl = this.tryGetParam(args, "downloadUrl")[0];
            String sha256 = this.tryGetParam(args, "sha256")[0];
            String title = this.getParam(args, "title", slug);
            String version = this.getParam(args, "version", "");
            String fileName = this.getParam(args, "fileName", slug + ".zip");
            MarketplaceManager.installAsync(slug, title, version, downloadUrl, fileName, sha256);
            response.put("slug", (Object)slug);
        }
        catch (Exception e) {
            return MarketplaceServlet.apiErrorJSON((String)L.t((String)"Install failed.", (Object[])new Object[0]), (Throwable)e);
        }
        response.put("success", (Object)L.t((String)"Install started.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onRecordShare(Map<String, String[]> args) {
        JSONObject response = new JSONObject();
        try {
            String slug = this.tryGetParam(args, "productSlug")[0];
            if (slug.trim().isEmpty()) {
                throw new Exception(L.t((String)"Missing product slug.", (Object[])new Object[0]));
            }
            String title = this.getParam(args, "title", slug);
            String version = this.getParam(args, "version", "");
            String fileName = this.getParam(args, "fileName", "");
            String sha256 = this.getParam(args, "sha256", "");
            MarketplaceDb.get().recordInstall(slug, title, version, fileName, sha256, null);
            response.put("slug", (Object)slug);
        }
        catch (Exception e) {
            return MarketplaceServlet.apiErrorJSON((String)L.t((String)"Recording the shared product failed.", (Object[])new Object[0]), (Throwable)e);
        }
        response.put("success", (Object)L.t((String)"Shared product recorded.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onUninstall(Map<String, String[]> args) {
        JSONObject response;
        try {
            String slug = this.tryGetParam(args, "productSlug")[0];
            if (slug.trim().isEmpty()) {
                throw new Exception(L.t((String)"Missing product id.", (Object[])new Object[0]));
            }
            response = MarketplaceManager.uninstall(slug);
        }
        catch (Exception e) {
            return MarketplaceServlet.apiErrorJSON((String)L.t((String)"Removing the product failed.", (Object[])new Object[0]), (Throwable)e);
        }
        response.put("success", (Object)L.t((String)"Product removed.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onListShareable(Map<String, String[]> args) {
        JSONObject response = new JSONObject();
        try {
            String filter = this.getParam(args, "filter", "");
            LinkedHashMap<String, String> sourceDirs = new LinkedHashMap<String, String>();
            sourceDirs.put(MainApp.getDataPath() + "user", "user");
            int index = 0;
            response.put("id", index++);
            response.put("item", (Object)MarketplaceServlet.getFileMapInstance().generateTree(sourceDirs, filter, index));
            File userDir = new File(MainApp.getDataPath() + "user");
            JSONArray excluded = new JSONArray();
            for (String name : MarketplaceFileMap.excludedTopDirs()) {
                if (!new File(userDir, name).isDirectory()) continue;
                excluded.put((Object)name);
            }
            response.put("excluded", (Object)excluded);
            response.put("licenseOwner", (Object)MainApp.getLicenseInfo().getOwnerName());
        }
        catch (Exception e) {
            return MarketplaceServlet.apiErrorJSON((String)L.t((String)"Listing shareable files failed.", (Object[])new Object[0]), (Throwable)e);
        }
        response.put("success", (Object)"Sources listed.");
        return response.toString();
    }

    private static synchronized MarketplaceFileMap getFileMapInstance() {
        if (fileMap == null) {
            fileMap = new MarketplaceFileMap();
        }
        return fileMap;
    }

    private String onBuildZip(Map<String, String[]> args) {
        JSONObject response;
        try {
            String files = this.tryGetParam(args, "files")[0];
            String fileName = this.tryGetParam(args, "fileName")[0];
            String meta = this.getParam(args, "meta", "");
            if (files.trim().isEmpty()) {
                throw new Exception(L.t((String)"There are no files to share.", (Object[])new Object[0]));
            }
            response = MarketplaceManager.buildZip(files.split(","), fileName, meta);
        }
        catch (Exception e) {
            return MarketplaceServlet.apiErrorJSON((String)L.t((String)"Building the package failed.", (Object[])new Object[0]), (Throwable)e);
        }
        response.put("success", (Object)L.t((String)"Package built.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onUpload(Map<String, String[]> args) {
        JSONObject response = new JSONObject();
        try {
            String zipId = this.tryGetParam(args, "zipId")[0];
            String uploadUrl = this.tryGetParam(args, "uploadUrl")[0];
            MarketplaceManager.uploadAsync(zipId, uploadUrl);
        }
        catch (Exception e) {
            return MarketplaceServlet.apiErrorJSON((String)L.t((String)"Upload failed.", (Object[])new Object[0]), (Throwable)e);
        }
        response.put("success", (Object)L.t((String)"Upload started.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onCleanup(Map<String, String[]> args) {
        JSONObject response = new JSONObject();
        try {
            String zipId = this.tryGetParam(args, "zipId")[0];
            MarketplaceManager.cleanup(zipId);
        }
        catch (Exception e) {
            return MarketplaceServlet.apiErrorJSON((String)L.t((String)"Cleanup failed.", (Object[])new Object[0]), (Throwable)e);
        }
        response.put("success", (Object)L.t((String)"Package removed.", (Object[])new Object[0]));
        return response.toString();
    }
}

