/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.app.MainApp
 *  com.strategyquant.lib.snippets.compile.SQStructure
 *  com.strategyquant.tradinglib.project.websocket.DataToSend
 *  com.strategyquant.tradinglib.project.websocket.SQWebSocketManager
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.CodeEditor.impl.ImportExport;

import com.strategyquant.lib.L;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.lib.snippets.compile.SQStructure;
import com.strategyquant.tradinglib.project.websocket.DataToSend;
import com.strategyquant.tradinglib.project.websocket.SQWebSocketManager;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.zip.ZipEntry;
import java.util.zip.ZipInputStream;
import java.util.zip.ZipOutputStream;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class ExtensionManager {
    private static final Logger Log = LoggerFactory.getLogger(ExtensionManager.class);
    private static final byte STATE_DEFAULT = 0;
    private static final byte STATE_OVERWRITE = 1;
    private static final byte STATE_OVERWRITEALWAYS = 2;
    private static final byte STATE_SKIP = 3;
    private static final byte STATE_SKIPALWAYS = 4;
    private static final byte STATE_CANCEL = 5;
    private static volatile byte state = 0;
    private static Thread waitingThread = null;
    private static JSONObject confirmObj = new JSONObject();
    private static DataToSend dataToSend = new DataToSend("overwriteConfirmation", confirmObj);
    public static HashMap<String, String> notImportedMap = new HashMap();

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public static ArrayList<String> install(String[] filePaths) throws Exception {
        state = 0;
        notImportedMap.clear();
        String userDirPath = new File(MainApp.getDataPath() + "user").getAbsolutePath();
        ArrayList<String> createdFiles = new ArrayList<String>();
        for (int a = 0; a < filePaths.length; ++a) {
            try {
                String filePath = filePaths[a];
                if (!filePath.toLowerCase().endsWith(".sxp")) {
                    throw new Exception(L.t((String)"Expected file with extension .sxp", (Object[])new Object[0]));
                }
                try (ZipInputStream zipInputStream = null;){
                    zipInputStream = new ZipInputStream(new FileInputStream(filePath));
                    ZipEntry zipEntry = null;
                    block14: while ((zipEntry = zipInputStream.getNextEntry()) != null) {
                        if (zipEntry.isDirectory()) continue;
                        File file = new File(userDirPath + "/" + zipEntry.getName());
                        File internalFile = new File(SQStructure.INTERNAL_DIR_PATH + zipEntry.getName());
                        if (internalFile.exists()) {
                            notImportedMap.put(zipEntry.getName(), L.t((String)"already exists in Builtin", (Object[])new Object[0]));
                            continue;
                        }
                        if (file.exists()) {
                            switch (state) {
                                case 4: {
                                    notImportedMap.put(zipEntry.getName(), L.t((String)"skipped by user", (Object[])new Object[0]));
                                    continue block14;
                                }
                                case 2: {
                                    break;
                                }
                                default: {
                                    ExtensionManager.sendConfirmation(file.getAbsolutePath());
                                    ExtensionManager.waitForUserAction();
                                    switch (state) {
                                        case 3: 
                                        case 4: {
                                            notImportedMap.put(zipEntry.getName(), L.t((String)"skipped by user", (Object[])new Object[0]));
                                            continue block14;
                                        }
                                        case 5: {
                                            throw new Exception(L.t((String)"Canceled", (Object[])new Object[0]));
                                        }
                                    }
                                }
                            }
                            ExtensionManager.writeToFile(file, zipInputStream);
                            createdFiles.add(zipEntry.getName());
                            continue;
                        }
                        ExtensionManager.writeToFile(file, zipInputStream);
                        createdFiles.add(zipEntry.getName());
                    }
                    continue;
                }
            }
            catch (Exception e) {
                Log.error("Installing extension failed", (Throwable)e);
                throw e;
            }
        }
        return createdFiles;
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public static void export(String[] filePaths, String targetPath) throws Exception {
        File outputFile = new File(targetPath);
        try (ZipOutputStream out = null;){
            out = new ZipOutputStream(new FileOutputStream(outputFile));
            for (int a = 0; a < filePaths.length; ++a) {
                String relativePath = SQUtils.trimFilePath((String)filePaths[a], (String)MainApp.getDataPath());
                String fullPath = MainApp.getDataPath() + relativePath;
                if (relativePath.startsWith("user/")) {
                    relativePath = relativePath.replaceFirst("user/", "");
                }
                ZipEntry e = new ZipEntry(relativePath);
                out.putNextEntry(e);
                byte[] data = SQUtils.fileToBytes((File)new File(fullPath));
                out.write(data, 0, data.length);
                out.closeEntry();
            }
        }
    }

    public static void overwrite() {
        state = 1;
    }

    public static void overwriteAlways() {
        state = (byte)2;
    }

    public static void skip() {
        state = (byte)3;
    }

    public static void skipAlways() {
        state = (byte)4;
    }

    public static void cancelImport() {
        state = (byte)5;
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private static void writeToFile(File file, ZipInputStream zipIS) throws Exception {
        if (file.isDirectory()) {
            if (!file.exists() && !file.mkdirs()) {
                throw new Exception(L.t((String)"Cannot create dir %s", (Object[])new Object[]{file.getAbsolutePath()}));
            }
        } else if (!file.getParentFile().exists() && !file.getParentFile().mkdirs()) {
            throw new Exception(L.t((String)"Cannot create dir %s", (Object[])new Object[]{file.getParentFile().getAbsolutePath()}));
        }
        FileOutputStream fos = null;
        try {
            fos = new FileOutputStream(file);
            byte[] data = new byte[1024];
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

    private static void sendConfirmation(String filePath) {
        state = 0;
        confirmObj.put("filePath", (Object)filePath);
        SQWebSocketManager.addToDataQueue((DataToSend)dataToSend, (String[])new String[]{"SQEDITOR"});
    }

    private static void waitForUserAction() throws Exception {
        if (waitingThread != null && waitingThread.isAlive()) {
            throw new Exception(L.t((String)"Waiting for user action. Cannot continue until submitted", (Object[])new Object[0]));
        }
        waitingThread = new Thread(){

            @Override
            public void run() {
                long timeElapsed = 0L;
                int timeout = 200;
                while (state == 0) {
                    try {
                        Thread.sleep(200L);
                        timeElapsed += 200L;
                    }
                    catch (Exception exception) {
                        // empty catch block
                    }
                    if (timeElapsed <= 60000L) continue;
                    state = (byte)5;
                }
            }
        };
        waitingThread.start();
        waitingThread.join();
    }
}

