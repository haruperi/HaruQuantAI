/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.constants.SQPaths
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.project;

import com.strategyquant.lib.constants.SQPaths;
import com.strategyquant.tradinglib.file.SQFileManager;
import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.Reader;
import java.util.HashMap;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class CustomConfigs {
    private static final Logger Log = LoggerFactory.getLogger(CustomConfigs.class);
    private static final String NameAttr = "name=\"";

    public static HashMap<String, String> list() {
        HashMap<String, String> hashMap = new HashMap<String, String>();
        try {
            File file = new File(SQPaths.configsDirPath);
            if (!file.exists()) {
                file.mkdirs();
            } else {
                CustomConfigs.loadFiles(file, hashMap);
            }
        }
        catch (Exception exception) {
            Log.error("Error while listing custom configs", (Throwable)exception);
        }
        return hashMap;
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private static void loadFiles(File file, HashMap<String, String> hashMap) {
        char[] cArray = new char[500];
        block9: for (File file2 : file.listFiles()) {
            if (file2.isDirectory()) {
                CustomConfigs.loadFiles(file2, hashMap);
                continue;
            }
            String string = file2.getAbsolutePath().replace("\\", "/");
            string = string.replace(SQPaths.configsDirPath.replace("\\", "/"), "").substring(1);
            try {
                Object object;
                if (string.endsWith("cfx")) {
                    object = SQFileManager.loadFile(file2.getAbsolutePath());
                    String string2 = CustomConfigs.getNameFromConfig((String)object);
                    if (string2 == null) {
                        Log.error("Cannot get name from CFX config");
                        continue;
                    }
                    if (!string2.isEmpty()) {
                        hashMap.put(string, string2);
                        continue;
                    }
                    Log.info("Config file " + file2.getName() + " skipped. Name is empty");
                    continue;
                }
                if (!string.endsWith(".xml")) continue;
                object = null;
                try {
                    object = new BufferedReader(new FileReader(file2));
                    for (int i = 0; i < 5; ++i) {
                        String string3;
                        String string4;
                        if (((Reader)object).read(cArray) <= 0 || (string4 = CustomConfigs.getNameFromConfig(string3 = new String(cArray))) == null) continue;
                        if (!string4.isEmpty()) {
                            hashMap.put(string, string4);
                            continue block9;
                        }
                        Log.info("File " + file2.getName() + " skipped. Name is empty");
                        continue block9;
                    }
                }
                finally {
                    if (object != null) {
                        try {
                            ((BufferedReader)object).close();
                        }
                        catch (Exception exception) {
                            Log.error("Unable to close reader", (Throwable)exception);
                        }
                    }
                }
            }
            catch (Exception exception) {
                Log.error("Cannot load config file '" + file2.getAbsolutePath() + "'. ", (Throwable)exception);
            }
        }
    }

    private static String getNameFromConfig(String string) {
        int n = string.indexOf(NameAttr);
        if (n <= 0) {
            return null;
        }
        int n2 = n + NameAttr.length();
        int n3 = string.indexOf("\"", n2);
        return string.substring(n2, n3);
    }
}

