/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.app.MainApp
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.datalib.data;

import com.strategyquant.datalib.DataInfo;
import com.strategyquant.datalib.data.DataManager;
import com.strategyquant.lib.app.MainApp;
import java.io.File;
import java.io.FileFilter;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedList;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.stream.Collectors;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class DataFolderSweeper {
    public static final Logger Log = LoggerFactory.getLogger(DataFolderSweeper.class);
    protected static final long DELAY_TIME = 180000L;
    private static DataFolderSweeper instance = new DataFolderSweeper();
    private Thread cleanerThread;
    private boolean skip = false;

    public static DataFolderSweeper get() {
        return instance;
    }

    private DataFolderSweeper() {
    }

    public synchronized void init() {
        if (MainApp.runInConsole()) {
            return;
        }
        if (this.cleanerThread != null) {
            throw new IllegalStateException("DataFolderSweeper was already initialized");
        }
        this.cleanerThread = new Thread(new Runnable(){

            @Override
            public void run() {
                try {
                    ArrayList<DataInfo> arrayList = DataManager.list();
                    Thread.sleep(180000L);
                    long l = System.currentTimeMillis();
                    Log.info("Data folder sweep started");
                    DataFolderSweeper.this.removeUnusedData(arrayList);
                    DataFolderSweeper.this.removeCopyFiles("History", arrayList);
                    long l2 = System.currentTimeMillis() - l;
                    Log.info("Data folder sweep finished in {}ms", (Object)l2);
                }
                catch (Exception exception) {
                    Log.error("Data folder sweep failed", (Throwable)exception);
                }
            }
        }, "DataFolderCleaner-thread");
        this.cleanerThread.start();
    }

    public void setSkip(boolean bl) {
        this.skip = bl;
    }

    private void removeUnusedData(ArrayList<DataInfo> arrayList) {
        try {
            HashMap<String, LinkedList<Object>> hashMap = new HashMap<String, LinkedList<Object>>();
            for (int i = 0; i < arrayList.size(); ++i) {
                DataInfo dataInfo2 = arrayList.get(i);
                List<Object> list = (List)hashMap.get(dataInfo2.connection);
                if (list == null) {
                    list = new LinkedList<Object>();
                    hashMap.put(dataInfo2.connection, (LinkedList<Object>)list);
                }
                list.add(dataInfo2);
            }
            Set set = hashMap.keySet();
            for (List<Object> list : set) {
                List list2 = (List)hashMap.get(list);
                Map<String, DataInfo> map = list2.stream().filter(dataInfo -> dataInfo.source == 6).collect(Collectors.toMap(dataInfo -> DataManager.fixFilename(dataInfo.symbol), dataInfo -> dataInfo));
                Map<String, DataInfo> map2 = list2.stream().filter(dataInfo -> dataInfo.source == 5).collect(Collectors.toMap(dataInfo -> DataManager.fixFilename(dataInfo.symbol), dataInfo -> dataInfo));
                Map<String, DataInfo> map3 = list2.stream().filter(dataInfo -> dataInfo.source != 5 && dataInfo.source != 6).collect(Collectors.toMap(dataInfo -> DataManager.fixFilename(dataInfo.symbol), dataInfo -> dataInfo));
                this.removeUnusedInFolder(new File(DataManager.get()._getDirectory(), (String)((Object)list)), map3, map2, map);
            }
        }
        catch (Exception exception) {
            Log.error("Cannot remove unused symbol files. ", (Throwable)exception);
        }
    }

    private void removeUnusedInFolder(File file, Map<String, DataInfo> map, Map<String, DataInfo> map2, Map<String, DataInfo> map3) {
        this.removeUnusedInFolder(file, map);
        for (char c = 'A'; c <= 'Z'; c = (char)(c + '\u0001')) {
            if (this.skip) {
                return;
            }
            File file2 = new File(file, "sq_futures/" + c);
            File file3 = new File(file, "sq_equity/" + c);
            if (!this.removeUnusedInFolder(file2, map3)) {
                this.deleteFolder(file2);
            }
            if (this.removeUnusedInFolder(file3, map2)) continue;
            this.deleteFolder(file3);
        }
    }

    private boolean removeUnusedInFolder(File file, Map<String, DataInfo> map) {
        File[] fileArray = file.listFiles(new FileFilter(){

            @Override
            public boolean accept(File file) {
                return file.isDirectory();
            }
        });
        if (fileArray == null) {
            return false;
        }
        boolean bl = false;
        for (File file2 : fileArray) {
            if (this.skip) {
                return true;
            }
            String string = file2.getName();
            if (string.equals("sq_equity") || string.equals("sq_futures")) continue;
            DataInfo dataInfo = map.get(string);
            if (dataInfo == null) {
                this.deleteFolder(file2);
                continue;
            }
            bl = true;
        }
        return bl;
    }

    private void deleteFolder(File file) {
        if (!Files.exists(file.toPath(), new LinkOption[0])) {
            return;
        }
        File[] fileArray = file.listFiles();
        if (fileArray != null) {
            for (File file2 : fileArray) {
                file2.delete();
            }
        }
        file.delete();
    }

    private void removeCopyFiles(String string, ArrayList<DataInfo> arrayList) throws IOException {
        for (DataInfo dataInfo : arrayList) {
            if (this.skip) {
                return;
            }
            String string2 = DataManager.getDataFileName(string, dataInfo.symbol, dataInfo.timeframe, "No Session");
            String string3 = string2 + ".copy";
            File file = new File(string3);
            Files.deleteIfExists(file.toPath());
        }
    }
}

