/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.app.MainApp
 *  org.apache.commons.io.FileUtils
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.backtest;

import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.app.MainApp;
import java.io.File;
import java.io.IOException;
import java.util.Collection;
import java.util.TreeMap;
import org.apache.commons.io.FileUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class TestfilesUtils {
    public static final Logger Log = LoggerFactory.getLogger((String)"TestfilesUtils");

    public static String getTestdataFile(int n) {
        return TestfilesUtils.getTestdataFile(n, true);
    }

    public static String getTestdataFile(int n, boolean bl) {
        String string;
        StringBuilder stringBuilder = new StringBuilder(MainApp.getDataPath());
        stringBuilder.append("/internal/testfiles");
        String string2 = Integer.toString(n);
        int n2 = 0;
        int n3 = 0;
        while (true) {
            string = string2.substring(n2, n2 + 1);
            ++n2;
            if (string.equals("-")) continue;
            stringBuilder.append("/");
            stringBuilder.append(string);
            if (++n3 >= 2) break;
        }
        string = stringBuilder.toString();
        stringBuilder.append("/c");
        stringBuilder.append(string2);
        String string3 = stringBuilder.toString();
        if (bl) {
            SQUtils.ensureDirExists((String)string);
        }
        return string3;
    }

    public static void deleteTestingFiles() {
        File file = new File(MainApp.getDataPath() + "internal/testfiles");
        file.mkdirs();
        Collection collection = FileUtils.listFiles((File)file, null, (boolean)true);
        if (collection == null) {
            return;
        }
        TreeMap<Long, Object> treeMap = new TreeMap<Long, Object>();
        long l = 0L;
        for (Object object : collection) {
            if (!((File)object).isFile()) continue;
            l += ((File)object).length();
            long l2 = ((File)object).lastModified();
            treeMap.put(l2, object);
        }
        if (l > 2000000000L && treeMap.size() > 20) {
            Object object;
            int n = treeMap.size() - 20;
            object = treeMap.keySet();
            Object[] objectArray = object.toArray();
            if (n > 0) {
                for (int i = 0; i < n; ++i) {
                    int n2 = treeMap.size() - i - 1;
                    File file2 = (File)treeMap.get(objectArray[n2]);
                    if (file2 == null) continue;
                    if (file2.delete()) {
                        Log.debug("Test file '" + file2.getName() + "' was deleted!");
                        continue;
                    }
                    Log.debug("Test file '" + file2.getName() + "' delete failed!");
                }
            }
        }
    }

    public static void deleteTempTestfile(String string) {
        if (string != null) {
            StringBuilder stringBuilder = new StringBuilder(MainApp.getDataPath());
            stringBuilder.append("/internal/testfiles/tmp/");
            stringBuilder.append(string);
            String string2 = stringBuilder.toString();
            File file = new File(string2);
            if (file.exists() && file.isDirectory()) {
                try {
                    FileUtils.deleteDirectory((File)file);
                }
                catch (IOException iOException) {
                    Log.error("Cannot x delete folder '" + string2 + "'.", (Throwable)iOException);
                }
            }
        }
    }
}

