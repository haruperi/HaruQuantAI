/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.snippets.compile.SQStructure
 *  org.apache.commons.io.comparator.NameFileComparator
 *  org.json.JSONArray
 *  org.json.JSONObject
 */
package com.strategyquant.plugin.App.impl.Marketplace;

import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.snippets.compile.SQStructure;
import java.io.File;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.locks.Lock;
import java.util.concurrent.locks.ReentrantLock;
import org.apache.commons.io.comparator.NameFileComparator;
import org.json.JSONArray;
import org.json.JSONObject;

public class MarketplaceFileMap {
    private static final String KEY_CONTENT = "content";
    private static final String KEY_NAME = "name";
    private static final String KEY_ID = "id";
    private static final String KEY_TEXT = "text";
    private static final String KEY_USERDATA = "userdata";
    private static final String KEY_ITEM = "item";
    private int index;
    private final Lock lock = new ReentrantLock();
    private final String userRootPath = new File(SQStructure.USER_EXTEND).getParentFile().getAbsolutePath();
    private static final Set<String> EXCLUDED_TOP_DIRS = new HashSet<String>(Arrays.asList("settings", "log", "logs", "data", "customdata", "temp", "tmp", "cache"));

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
            userData.put(KEY_NAME, (Object)"file");
            userData.put(KEY_CONTENT, (Object)f.getAbsolutePath());
            userdataArray.put((Object)userData);
            JSONObject userData2 = new JSONObject();
            userData2.put(KEY_NAME, (Object)"fileType");
            userData2.put(KEY_CONTENT, (Object)(f.isDirectory() ? "dir" : "file"));
            userdataArray.put((Object)userData2);
            fileObj.put(KEY_USERDATA, (Object)userdataArray);
            if (f.isDirectory()) {
                fileObj.put(KEY_ITEM, (Object)this.prvParse(f, filter, new JSONArray(), false, null));
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
        if (!f.getAbsolutePath().startsWith(this.userRootPath)) {
            return false;
        }
        if (MarketplaceFileMap.isExcludedFromShare(f)) {
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

    public static List<String> excludedTopDirs() {
        ArrayList<String> list = new ArrayList<String>(EXCLUDED_TOP_DIRS);
        Collections.sort(list);
        return list;
    }

    public static boolean isExcludedFromShare(File f) {
        String userRoot = new File(SQStructure.USER_EXTEND).getParentFile().getAbsolutePath();
        String abs = f.getAbsolutePath();
        if (!abs.startsWith(userRoot)) {
            return false;
        }
        String rel = abs.substring(userRoot.length()).replace('\\', '/');
        while (rel.startsWith("/")) {
            rel = rel.substring(1);
        }
        if (rel.isEmpty()) {
            return false;
        }
        int slash = rel.indexOf(47);
        String top = (slash >= 0 ? rel.substring(0, slash) : rel).toLowerCase();
        return EXCLUDED_TOP_DIRS.contains(top);
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

