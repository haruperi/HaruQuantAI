/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.snippets.compile.SQStructure
 *  org.apache.commons.io.comparator.NameFileComparator
 *  org.json.JSONArray
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.CodeEditor.impl.ImportExport;

import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.snippets.compile.SQStructure;
import java.io.File;
import java.util.Arrays;
import java.util.Map;
import java.util.concurrent.locks.Lock;
import java.util.concurrent.locks.ReentrantLock;
import org.apache.commons.io.comparator.NameFileComparator;
import org.json.JSONArray;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class ExtensionsFileMap {
    private static final Logger Log = LoggerFactory.getLogger(ExtensionsFileMap.class);
    private static final String KEY_MISSING = "missing";
    private static final String KEY_CONTENT = "content";
    private static final String KEY_INFO = "info";
    private static final String KEY_NAME = "name";
    private static final String KEY_FILE = "file";
    private static final String KEY_TYPE = "type";
    private static final String KEY_TYPES = "types";
    private static final String KEY_ID = "id";
    private static final String KEY_TEXT = "text";
    private static final String KEY_USERDATA = "userdata";
    private static final String KEY_ITEM = "item";
    private int index;
    private final Lock lock = new ReentrantLock();
    String userExtedDirPath = new File(SQStructure.USER_EXTEND).getAbsolutePath();
    String userLibsDirPath = new File(SQStructure.USER_LIBS).getAbsolutePath();

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public JSONArray generateTree(Map<String, String> sourceDirs, String filter, int startIndex) {
        this.lock.lock();
        try {
            this.index = startIndex;
            JSONArray itemArray = new JSONArray();
            for (Map.Entry<String, String> entry : sourceDirs.entrySet()) {
                this.parseFolder(entry.getKey(), filter, itemArray, entry.getValue());
            }
            JSONArray jSONArray = itemArray;
            return jSONArray;
        }
        finally {
            this.lock.unlock();
        }
    }

    private void parseFolder(String path, String filter, JSONArray itemArray, String topLevelDesc) {
        File f = new File(path);
        if (!f.exists()) {
            return;
        }
        this.prvParse(f, filter.trim().toLowerCase(), itemArray, true, topLevelDesc);
    }

    private JSONArray prvParse(File folder, String filter, JSONArray itemArray, boolean isTopLevel, String topLevelDesc) {
        File[] files = folder.listFiles();
        if (files == null) {
            return itemArray;
        }
        Arrays.sort(files, NameFileComparator.NAME_INSENSITIVE_COMPARATOR);
        JSONObject topObj = null;
        JSONArray topArr = null;
        for (File f : files) {
            if (!this.checkFile(f, filter)) continue;
            if (isTopLevel && topObj == null) {
                topObj = new JSONObject();
                topObj.put(KEY_ID, this.index++);
                topObj.put(KEY_TEXT, (Object)topLevelDesc);
                topArr = new JSONArray();
                topObj.put(KEY_ITEM, (Object)topArr);
                itemArray.put((Object)topObj);
            }
            JSONObject fileObj = new JSONObject();
            fileObj.put(KEY_ID, this.index++);
            fileObj.put(KEY_TEXT, (Object)f.getName());
            JSONArray userdataArray = new JSONArray();
            JSONObject userData = new JSONObject();
            userData.put(KEY_NAME, (Object)KEY_FILE);
            userData.put(KEY_CONTENT, (Object)f.getAbsolutePath());
            userdataArray.put((Object)userData);
            JSONObject userData2 = new JSONObject();
            userData2.put(KEY_NAME, (Object)"fileType");
            userData2.put(KEY_CONTENT, (Object)(f.isDirectory() ? "dir" : KEY_FILE));
            userdataArray.put((Object)userData2);
            fileObj.put(KEY_USERDATA, (Object)userdataArray);
            if (f.isDirectory()) {
                JSONArray item = this.prvParse(f, filter, new JSONArray(), false, null);
                File[] fileList = f.listFiles();
                if (fileList != null) {
                    if (fileList.length == 0) {
                        String icon = "folderClosed.gif";
                        fileObj.put("im0", (Object)icon);
                        fileObj.put("im1", (Object)icon);
                        fileObj.put("im2", (Object)icon);
                    }
                    fileObj.put(KEY_ITEM, (Object)item);
                }
            }
            if (topArr == null) {
                itemArray.put((Object)fileObj);
                continue;
            }
            topArr.put((Object)fileObj);
        }
        return itemArray;
    }

    private boolean checkFile(File f, String filter) {
        if (!f.getAbsolutePath().startsWith(this.userExtedDirPath) && !f.getAbsolutePath().startsWith(this.userLibsDirPath)) {
            return false;
        }
        if (filter.equals("")) {
            return true;
        }
        if (f.isDirectory()) {
            return this.containsFileByFilter(f, filter);
        }
        String name = SQUtils.stripExtension((String)f.getName().toLowerCase());
        return name.contains(filter);
    }

    private boolean containsFileByFilter(File dir, String filter) {
        File[] children = dir.listFiles();
        if (children == null) {
            return false;
        }
        for (File f : children) {
            String name;
            if (!(f.isDirectory() ? this.containsFileByFilter(f, filter) : (name = SQUtils.stripExtension((String)f.getName().toLowerCase())).contains(filter))) continue;
            return true;
        }
        return false;
    }
}

