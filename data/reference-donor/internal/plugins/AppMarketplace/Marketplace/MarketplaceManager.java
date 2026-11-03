/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.app.MainApp
 *  com.strategyquant.lib.snippets.compile.SQStructure
 *  com.strategyquant.lib.utils.network.DataDownloader
 *  com.strategyquant.tradinglib.project.websocket.DataToSend
 *  com.strategyquant.tradinglib.project.websocket.SQWebSocketManager
 *  org.apache.commons.codec.digest.DigestUtils
 *  org.apache.commons.io.FileUtils
 *  org.apache.http.HttpEntity
 *  org.apache.http.HttpResponse
 *  org.apache.http.client.methods.HttpPut
 *  org.apache.http.client.methods.HttpUriRequest
 *  org.apache.http.entity.ContentType
 *  org.apache.http.entity.FileEntity
 *  org.apache.http.impl.client.CloseableHttpClient
 *  org.apache.http.impl.client.HttpClientBuilder
 *  org.apache.http.util.EntityUtils
 *  org.json.JSONArray
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.App.impl.Marketplace;

import com.strategyquant.lib.L;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.lib.snippets.compile.SQStructure;
import com.strategyquant.lib.utils.network.DataDownloader;
import com.strategyquant.plugin.App.impl.Marketplace.MarketplaceDb;
import com.strategyquant.plugin.App.impl.Marketplace.MarketplaceFileMap;
import com.strategyquant.tradinglib.project.websocket.DataToSend;
import com.strategyquant.tradinglib.project.websocket.SQWebSocketManager;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.time.Instant;
import java.util.ArrayList;
import java.util.UUID;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.zip.ZipEntry;
import java.util.zip.ZipInputStream;
import java.util.zip.ZipOutputStream;
import org.apache.commons.codec.digest.DigestUtils;
import org.apache.commons.io.FileUtils;
import org.apache.http.HttpEntity;
import org.apache.http.HttpResponse;
import org.apache.http.client.methods.HttpPut;
import org.apache.http.client.methods.HttpUriRequest;
import org.apache.http.entity.ContentType;
import org.apache.http.entity.FileEntity;
import org.apache.http.impl.client.CloseableHttpClient;
import org.apache.http.impl.client.HttpClientBuilder;
import org.apache.http.util.EntityUtils;
import org.json.JSONArray;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class MarketplaceManager {
    private static final Logger Log = LoggerFactory.getLogger(MarketplaceManager.class);
    private static final String EVENT_INSTALL = "marketplaceInstall";
    private static final String EVENT_UPLOAD = "marketplaceUpload";
    private static final String RESTART_REQUIRED_PREFIX = "extend/Plugins/";
    private static final String CUSTOM_INDICATORS_PREFIX = "custom_indicators/";
    private static final String MANIFEST_ENTRY = "manifest.json";
    private static final AtomicBoolean installRunning = new AtomicBoolean(false);
    private static final AtomicBoolean uploadRunning = new AtomicBoolean(false);
    private static boolean tmpSwept = false;

    private MarketplaceManager() {
    }

    public static void installAsync(final String slug, final String title, final String version, final String downloadUrl, final String fileName, final String expectedSha256) throws Exception {
        if (!installRunning.compareAndSet(false, true)) {
            throw new Exception(L.t((String)"Another installation is already in progress.", (Object[])new Object[0]));
        }
        final File tmpZip = new File(MarketplaceManager.getTmpRoot(), "install-" + UUID.randomUUID() + ".zip");
        Thread worker = new Thread(new Runnable(){

            @Override
            public void run() {
                try {
                    MarketplaceManager.download(slug, downloadUrl, tmpZip);
                    MarketplaceManager.verifyChecksum(slug, tmpZip, expectedSha256);
                    MarketplaceManager.sendInstallEvent(slug, "installing", null);
                    InstallResult result = MarketplaceManager.unzipToUserDir(tmpZip);
                    MarketplaceDb.get().recordInstall(slug, title, version, fileName, expectedSha256, result.installedFiles);
                    JSONObject done = new JSONObject();
                    done.put("installedFiles", (Object)result.installedFiles);
                    done.put("skippedFiles", (Object)result.skippedFiles);
                    done.put("restartRequired", result.restartRequired);
                    done.put("installDir", (Object)new File(MainApp.getDataPath() + "user").getAbsolutePath());
                    MarketplaceManager.sendInstallEvent(slug, "done", done);
                }
                catch (Exception e) {
                    Log.error("Marketplace install of '" + slug + "' failed", (Throwable)e);
                    JSONObject error = new JSONObject();
                    error.put("error", (Object)e.getMessage());
                    MarketplaceManager.sendInstallEvent(slug, "error", error);
                }
                finally {
                    FileUtils.deleteQuietly((File)tmpZip);
                    installRunning.set(false);
                }
            }
        }, "MarketplaceInstall-" + slug);
        worker.setDaemon(true);
        worker.start();
    }

    public static JSONObject uninstall(String slug) throws Exception {
        JSONArray files = MarketplaceDb.get().getInstalledFiles(slug);
        File userRoot = new File(MainApp.getDataPath() + "user");
        File customIndicatorsRoot = MarketplaceManager.getCustomIndicatorsRoot();
        JSONArray removedFiles = new JSONArray();
        JSONArray failedFiles = new JSONArray();
        boolean restartRequired = false;
        for (int i = 0; i < files.length(); ++i) {
            String entryName = MarketplaceManager.normalizeEntryName(files.getString(i));
            File root = MarketplaceManager.entryRoot(entryName, userRoot, customIndicatorsRoot);
            File file = new File(root, MarketplaceManager.entryLocalPath(entryName));
            if (!file.getCanonicalPath().startsWith(root.getCanonicalPath() + File.separator) || !file.exists()) continue;
            if (file.isFile() && file.delete()) {
                removedFiles.put((Object)entryName);
                MarketplaceManager.deleteEmptyParents(file.getParentFile(), root);
            } else {
                failedFiles.put((Object)entryName);
            }
            if (!entryName.startsWith(RESTART_REQUIRED_PREFIX)) continue;
            restartRequired = true;
        }
        MarketplaceDb.get().deleteInstall(slug);
        JSONObject result = new JSONObject();
        result.put("slug", (Object)slug);
        result.put("removedFiles", (Object)removedFiles);
        result.put("failedFiles", (Object)failedFiles);
        result.put("restartRequired", restartRequired);
        return result;
    }

    private static void deleteEmptyParents(File dir, File root) throws Exception {
        String[] children;
        String rootCanonical = root.getCanonicalPath();
        while (dir != null && !dir.getCanonicalPath().equals(rootCanonical) && dir.getCanonicalPath().startsWith(rootCanonical + File.separator) && (children = dir.list()) != null && children.length <= 0 && dir.delete()) {
            dir = dir.getParentFile();
        }
    }

    private static void download(String slug, String downloadUrl, File tmpZip) throws Exception {
        MarketplaceManager.sendInstallEvent(slug, "downloading", new JSONObject().put("progress", 0));
        long[] lastSent = new long[]{-1L, 0L};
        new DataDownloader().toFile(downloadUrl, tmpZip.getAbsolutePath(), (pct, totalBytesRead, total, bytesRead) -> {
            long now = System.currentTimeMillis();
            if ((long)pct >= lastSent[0] + 2L || now - lastSent[1] >= 500L) {
                lastSent[0] = pct;
                lastSent[1] = now;
                MarketplaceManager.sendInstallEvent(slug, "downloading", new JSONObject().put("progress", pct));
            }
        });
    }

    private static void verifyChecksum(String slug, File tmpZip, String expectedSha256) throws Exception {
        MarketplaceManager.sendInstallEvent(slug, "verifying", null);
        String actual = MarketplaceManager.sha256(tmpZip);
        if (expectedSha256 == null || !actual.equalsIgnoreCase(expectedSha256)) {
            throw new Exception(L.t((String)"Checksum mismatch - the downloaded file is corrupted or tampered with.", (Object[])new Object[0]));
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private static InstallResult unzipToUserDir(File zipFile) throws Exception {
        InstallResult result = new InstallResult();
        File userRoot = new File(MainApp.getDataPath() + "user");
        File customIndicatorsRoot = MarketplaceManager.getCustomIndicatorsRoot();
        try (ZipInputStream zipInputStream = null;){
            zipInputStream = new ZipInputStream(new FileInputStream(zipFile));
            ZipEntry zipEntry = null;
            while ((zipEntry = zipInputStream.getNextEntry()) != null) {
                String entryName;
                if (zipEntry.isDirectory() || (entryName = MarketplaceManager.normalizeEntryName(zipEntry.getName())).equals(MANIFEST_ENTRY)) continue;
                File root = MarketplaceManager.entryRoot(entryName, userRoot, customIndicatorsRoot);
                File file = new File(root, MarketplaceManager.entryLocalPath(entryName));
                if (!file.getCanonicalPath().startsWith(root.getCanonicalPath() + File.separator)) {
                    throw new Exception(L.t((String)"Invalid package - entry '%s' points outside the user folder.", (Object[])new Object[]{entryName}));
                }
                File internalFile = new File(SQStructure.INTERNAL_DIR_PATH + entryName);
                if (root == userRoot && internalFile.exists()) {
                    result.skippedFiles.put((Object)new JSONObject().put("name", (Object)entryName).put("reason", (Object)L.t((String)"already exists in Builtin", (Object[])new Object[0])));
                    continue;
                }
                MarketplaceManager.writeToFile(file, zipInputStream);
                result.installedFiles.put((Object)entryName);
                if (!entryName.startsWith(RESTART_REQUIRED_PREFIX)) continue;
                result.restartRequired = true;
            }
        }
        return result;
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private static void writeToFile(File file, ZipInputStream zipIS) throws Exception {
        if (!file.getParentFile().exists() && !file.getParentFile().mkdirs()) {
            throw new Exception(L.t((String)"Cannot create dir %s", (Object[])new Object[]{file.getParentFile().getAbsolutePath()}));
        }
        FileOutputStream fos = null;
        try {
            fos = new FileOutputStream(file);
            byte[] data = new byte[4096];
            int length = 0;
            while ((length = zipIS.read(data)) > 0) {
                fos.write(data, 0, length);
            }
        }
        finally {
            zipIS.closeEntry();
            if (fos != null) {
                fos.close();
            }
        }
    }

    private static String normalizeEntryName(String name) {
        String entryName = name.replace('\\', '/');
        if (entryName.startsWith("user/")) {
            entryName = entryName.substring("user/".length());
        }
        return entryName;
    }

    private static boolean isCustomIndicatorsEntry(String entryName) {
        return entryName.startsWith(CUSTOM_INDICATORS_PREFIX);
    }

    private static File getCustomIndicatorsRoot() {
        return new File(MainApp.getDataPath() + "custom_indicators");
    }

    private static File entryRoot(String entryName, File userRoot, File customIndicatorsRoot) {
        return MarketplaceManager.isCustomIndicatorsEntry(entryName) ? customIndicatorsRoot : userRoot;
    }

    private static String entryLocalPath(String entryName) {
        return MarketplaceManager.isCustomIndicatorsEntry(entryName) ? entryName.substring(CUSTOM_INDICATORS_PREFIX.length()) : entryName;
    }

    public static JSONObject buildZip(String[] absolutePaths, String fileName, String meta) throws Exception {
        if (fileName == null || !fileName.toLowerCase().endsWith(".zip")) {
            throw new Exception(L.t((String)"File name must end with .zip", (Object[])new Object[0]));
        }
        if (!fileName.equals(new File(fileName).getName())) {
            throw new Exception(L.t((String)"Invalid file name.", (Object[])new Object[0]));
        }
        ArrayList<String> files = new ArrayList<String>();
        String userRoot = new File(SQStructure.USER_EXTEND).getParentFile().getCanonicalPath();
        for (String path : absolutePaths) {
            if (path.trim().isEmpty()) continue;
            File f = new File(path.trim());
            String canonical = f.getCanonicalPath();
            if (!canonical.startsWith(userRoot + File.separator) && !canonical.equals(userRoot)) {
                throw new Exception(L.t((String)"File '%s' is not inside the user folder.", (Object[])new Object[]{path}));
            }
            if (MarketplaceFileMap.isExcludedFromShare(f)) {
                throw new Exception(L.t((String)"File '%s' is in a folder that cannot be shared.", (Object[])new Object[]{path}));
            }
            if (!f.exists()) {
                throw new Exception(L.t((String)"File '%s' does not exist.", (Object[])new Object[]{path}));
            }
            MarketplaceManager.collectFiles(f, files);
        }
        if (files.isEmpty()) {
            throw new Exception(L.t((String)"There are no files to share.", (Object[])new Object[0]));
        }
        String zipId = UUID.randomUUID().toString();
        File zipDir = new File(MarketplaceManager.getTmpRoot(), zipId);
        if (!zipDir.mkdirs()) {
            throw new Exception(L.t((String)"Cannot create dir %s", (Object[])new Object[]{zipDir.getAbsolutePath()}));
        }
        String[] filePaths = files.toArray(new String[0]);
        String manifestJson = MarketplaceManager.buildManifest(meta, filePaths);
        File zipFile = new File(zipDir, fileName);
        MarketplaceManager.exportZip(filePaths, manifestJson, zipFile.getAbsolutePath());
        JSONObject result = new JSONObject();
        result.put("zipId", (Object)zipId);
        result.put("fileName", (Object)fileName);
        result.put("size", zipFile.length());
        result.put("build", (Object)MainApp.getAppVersion());
        return result;
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private static void exportZip(String[] filePaths, String manifestJson, String targetPath) throws Exception {
        File outputFile = new File(targetPath);
        try (ZipOutputStream out = null;){
            out = new ZipOutputStream(new FileOutputStream(outputFile));
            if (manifestJson != null) {
                out.putNextEntry(new ZipEntry(MANIFEST_ENTRY));
                byte[] manifestBytes = manifestJson.getBytes("UTF-8");
                out.write(manifestBytes, 0, manifestBytes.length);
                out.closeEntry();
            }
            for (int a = 0; a < filePaths.length; ++a) {
                String fullPath = MainApp.getDataPath() + SQUtils.trimFilePath((String)filePaths[a], (String)MainApp.getDataPath());
                ZipEntry e = new ZipEntry(MarketplaceManager.toEntryName(filePaths[a]));
                out.putNextEntry(e);
                byte[] data = SQUtils.fileToBytes((File)new File(fullPath));
                out.write(data, 0, data.length);
                out.closeEntry();
            }
        }
    }

    private static String toEntryName(String filePath) {
        String relativePath = SQUtils.trimFilePath((String)filePath, (String)MainApp.getDataPath());
        if (relativePath.startsWith("user/")) {
            relativePath = relativePath.replaceFirst("user/", "");
        }
        return relativePath;
    }

    private static String buildManifest(String meta, String[] filePaths) {
        String author;
        String version;
        String description;
        JSONObject src = meta != null && !meta.trim().isEmpty() ? new JSONObject(meta) : new JSONObject();
        JSONObject manifest = new JSONObject();
        manifest.put("schema", (Object)"sqx-marketplace/1");
        String title = src.optString("title", "").trim();
        if (!title.isEmpty()) {
            manifest.put("title", (Object)title);
        }
        if (!(description = src.optString("description", "").trim()).isEmpty()) {
            manifest.put("description", (Object)description);
        }
        if (!(version = src.optString("version", "").trim()).isEmpty()) {
            manifest.put("version", (Object)version);
        }
        if (!(author = src.optString("author", "").trim()).isEmpty()) {
            manifest.put("author", (Object)author);
        }
        String categoryId = src.optString("categoryId", "").trim();
        String categoryLabel = src.optString("categoryLabel", "").trim();
        if (!categoryId.isEmpty() || !categoryLabel.isEmpty()) {
            JSONObject category = new JSONObject();
            if (!categoryId.isEmpty()) {
                category.put("id", (Object)categoryId);
            }
            if (!categoryLabel.isEmpty()) {
                category.put("label", (Object)categoryLabel);
            }
            manifest.put("category", (Object)category);
        }
        JSONArray fileList = new JSONArray();
        for (String path : filePaths) {
            fileList.put((Object)MarketplaceManager.toEntryName(path));
        }
        manifest.put("files", (Object)fileList);
        manifest.put("generatedBy", (Object)MainApp.printFullAppVersion());
        manifest.put("generatedAt", (Object)Instant.now().toString());
        return manifest.toString(2);
    }

    private static void collectFiles(File f, ArrayList<String> files) {
        if (f.isDirectory()) {
            File[] children = f.listFiles();
            if (children == null) {
                return;
            }
            for (File child : children) {
                MarketplaceManager.collectFiles(child, files);
            }
        } else {
            files.add(f.getAbsolutePath());
        }
    }

    public static void uploadAsync(final String zipId, final String uploadUrl) throws Exception {
        final File zipFile = MarketplaceManager.findZip(zipId);
        if (!uploadRunning.compareAndSet(false, true)) {
            throw new Exception(L.t((String)"Another upload is already in progress.", (Object[])new Object[0]));
        }
        Thread worker = new Thread(new Runnable(){

            /*
             * WARNING - Removed try catching itself - possible behaviour change.
             */
            @Override
            public void run() {
                try {
                    MarketplaceManager.sendUploadEvent(zipId, "uploading", null);
                    CloseableHttpClient client = HttpClientBuilder.create().build();
                    HttpPut put = new HttpPut(uploadUrl);
                    put.setEntity((HttpEntity)new FileEntity(zipFile, ContentType.create((String)"application/zip")));
                    HttpResponse response = client.execute((HttpUriRequest)put);
                    int status = response.getStatusLine().getStatusCode();
                    EntityUtils.consumeQuietly((HttpEntity)response.getEntity());
                    if (status < 200 || status >= 300) {
                        throw new Exception(L.t((String)"Upload failed with HTTP status %s.", (Object[])new Object[]{"" + status}));
                    }
                    String sha256 = MarketplaceManager.sha256(zipFile);
                    JSONObject done = new JSONObject();
                    done.put("sha256", (Object)sha256);
                    MarketplaceManager.sendUploadEvent(zipId, "done", done);
                    MarketplaceManager.cleanup(zipId);
                }
                catch (Exception e) {
                    Log.error("Marketplace upload of '" + zipId + "' failed", (Throwable)e);
                    JSONObject error = new JSONObject();
                    error.put("error", (Object)e.getMessage());
                    MarketplaceManager.sendUploadEvent(zipId, "error", error);
                }
                finally {
                    uploadRunning.set(false);
                }
            }
        }, "MarketplaceUpload-" + zipId);
        worker.setDaemon(true);
        worker.start();
    }

    public static void cleanup(String zipId) throws Exception {
        File zipDir = new File(MarketplaceManager.getTmpRoot(), MarketplaceManager.validateZipId(zipId));
        FileUtils.deleteQuietly((File)zipDir);
    }

    private static File findZip(String zipId) throws Exception {
        File zipDir = new File(MarketplaceManager.getTmpRoot(), MarketplaceManager.validateZipId(zipId));
        File[] files = zipDir.listFiles();
        if (files != null) {
            for (File f : files) {
                if (!f.isFile() || !f.getName().toLowerCase().endsWith(".zip")) continue;
                return f;
            }
        }
        throw new Exception(L.t((String)"Package '%s' was not found. Submit the share form again.", (Object[])new Object[]{zipId}));
    }

    private static String validateZipId(String zipId) throws Exception {
        if (zipId == null || !zipId.matches("[0-9a-fA-F-]{36}")) {
            throw new Exception(L.t((String)"Invalid package id.", (Object[])new Object[0]));
        }
        return zipId;
    }

    private static String sha256(File file) throws Exception {
        try (FileInputStream is = null;){
            is = new FileInputStream(file);
            String string = DigestUtils.sha256Hex((InputStream)is);
            return string;
        }
    }

    private static synchronized File getTmpRoot() {
        File tmpRoot = new File(MainApp.getDataPath() + "internal/tmp/marketplace");
        if (!tmpSwept) {
            tmpSwept = true;
            if (tmpRoot.exists()) {
                try {
                    FileUtils.cleanDirectory((File)tmpRoot);
                }
                catch (Exception e) {
                    Log.warn("Cannot clean marketplace tmp dir", (Throwable)e);
                }
            }
        }
        if (!tmpRoot.exists() && !tmpRoot.mkdirs()) {
            Log.error("Cannot create folder '" + tmpRoot.getAbsolutePath() + "'");
        }
        return tmpRoot;
    }

    private static void sendInstallEvent(String slug, String status, JSONObject extra) {
        JSONObject data = extra != null ? extra : new JSONObject();
        data.put("slug", (Object)slug);
        data.put("status", (Object)status);
        SQWebSocketManager.addToDataQueue((DataToSend)new DataToSend(EVENT_INSTALL, data), (String[])new String[]{"MARKETPLACE"});
    }

    private static void sendUploadEvent(String zipId, String status, JSONObject extra) {
        JSONObject data = extra != null ? extra : new JSONObject();
        data.put("zipId", (Object)zipId);
        data.put("status", (Object)status);
        SQWebSocketManager.addToDataQueue((DataToSend)new DataToSend(EVENT_UPLOAD, data), (String[])new String[]{"MARKETPLACE"});
    }

    private static class InstallResult {
        final JSONArray installedFiles = new JSONArray();
        final JSONArray skippedFiles = new JSONArray();
        boolean restartRequired = false;

        private InstallResult() {
        }
    }
}

