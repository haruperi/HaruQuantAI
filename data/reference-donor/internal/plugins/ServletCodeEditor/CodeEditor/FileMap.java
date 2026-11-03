/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.app.MainApp
 *  com.strategyquant.lib.snippets.ProtectedSnippets
 *  com.strategyquant.lib.snippets.compile.SQStructure
 *  org.apache.commons.io.comparator.NameFileComparator
 *  org.json.JSONArray
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.Servlet.impl.CodeEditor;

import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.lib.snippets.ProtectedSnippets;
import com.strategyquant.lib.snippets.compile.SQStructure;
import java.io.File;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Comparator;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.concurrent.locks.Lock;
import java.util.concurrent.locks.ReentrantLock;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import org.apache.commons.io.comparator.NameFileComparator;
import org.json.JSONArray;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class FileMap {
    private static final Logger Log = LoggerFactory.getLogger(FileMap.class);
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
    private final File fileInternalDir;
    private final List<File> missingTemplateFiles = new ArrayList<File>();
    private final List<File> fileCodeBlockDirs = new ArrayList<File>();
    private final List<File> fileSnippetsBlocksDirs = new ArrayList<File>();
    static final Pattern patternForEngine = Pattern.compile("^@ForEngine\\(\\s*(?:value\\s*=\\s*)?\"([^\"]+)\"\\s*\\)", 8);

    public FileMap() {
        this.fileInternalDir = new File(SQStructure.getSnippetsBuiltinInternalDirPath());
        for (String dirName : SQStructure.getSnippetsSourceDirsWithSuffix((String)"SQ/Blocks")) {
            this.fileSnippetsBlocksDirs.add(new File(dirName));
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public String[] getCodeBlocksTypes() {
        this.lock.lock();
        try {
            HashSet<String> blockTypes = new HashSet<String>();
            for (File f : this.fileCodeBlockDirs) {
                File pf = f.getParentFile();
                if (pf == null) continue;
                blockTypes.add(pf.getName());
            }
            String[] stringArray = (String[])blockTypes.stream().sorted(String.CASE_INSENSITIVE_ORDER).toArray(String[]::new);
            return stringArray;
        }
        finally {
            this.lock.unlock();
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public void searchForMissingTemplateFiles() {
        this.lock.lock();
        try {
            this.missingTemplateFiles.clear();
            this.fileCodeBlockDirs.clear();
            String[] indyCodeDirs = SQStructure.getIndyCodeDirs();
            String[] sourceDirs = SQStructure.getSnippetsSourceDirsWithSuffix((String)"SQ/Blocks");
            for (int i = 0; i < indyCodeDirs.length; ++i) {
                ArrayList<File> cbDirs = new ArrayList<File>();
                String scanDir = indyCodeDirs[i];
                File fileCodes = new File(scanDir);
                File[] files = fileCodes.listFiles();
                if (files != null) {
                    for (File file : files) {
                        if (!file.isDirectory() || !this.dirContains(file, "blocks") || (i != 0 || !this.dirContains(file, "Main.tpl")) && i <= 0) continue;
                        cbDirs.add(new File(file, "blocks"));
                    }
                }
                this.searchForMissingTemplateFilesRecursively(new File(sourceDirs[i]), cbDirs);
                this.fileCodeBlockDirs.addAll(cbDirs);
            }
            this.fileCodeBlockDirs.sort(NameFileComparator.NAME_INSENSITIVE_COMPARATOR);
        }
        catch (Exception e) {
            Log.error("Exc.", (Throwable)e);
        }
        finally {
            this.lock.unlock();
        }
    }

    private void searchForMissingTemplateFilesRecursively(File f, List<File> blocksFiles) throws Exception {
        if (f.isDirectory()) {
            File[] files = f.listFiles();
            if (files != null) {
                Arrays.sort(files, NameFileComparator.NAME_INSENSITIVE_COMPARATOR);
                for (File fChild : files) {
                    this.searchForMissingTemplateFilesRecursively(fChild, blocksFiles);
                }
            }
        } else {
            String content = SQUtils.fileToString((File)f);
            if (!content.contains("@BuildingBlock")) {
                return;
            }
            String fileName = SQUtils.stripExtension((String)f.getName());
            String forEngine = null;
            Matcher m = patternForEngine.matcher(content);
            if (m.find()) {
                forEngine = m.group(1);
            }
            boolean reallyMissing = false;
            for (File fileBlocks : blocksFiles) {
                if (this.dirContains(fileBlocks, fileName + ".tpl") || forEngine != null && FileMap.isIntentionallyUnsupported(forEngine, fileBlocks.getParentFile().getName())) continue;
                reallyMissing = true;
            }
            if (reallyMissing) {
                this.missingTemplateFiles.add(f);
            }
        }
    }

    static boolean isIntentionallyUnsupported(String forEngine, String blocksDirName) {
        switch (blocksDirName) {
            case "EasyLanguage": {
                return !SQUtils.checkEngine((String)"TS", (String)forEngine) && !SQUtils.checkEngine((String)"MC", (String)forEngine);
            }
            case "MetaTrader4": {
                return !SQUtils.checkEngine((String)"MT4", (String)forEngine);
            }
            case "MetaTrader5": {
                return !SQUtils.checkEngine((String)"MT5", (String)forEngine);
            }
            case "NinjaTrader": {
                return !SQUtils.checkEngine((String)"NT", (String)forEngine);
            }
            case "JForex": {
                return !SQUtils.checkEngine((String)"JF", (String)forEngine);
            }
        }
        return false;
    }

    private boolean dirContains(File directory, String fileName) {
        return new File(directory, fileName).exists();
    }

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
            String icon;
            if (f.getAbsolutePath().equals(this.fileInternalDir.getAbsolutePath()) || !this.checkFile(f, filter)) continue;
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
            if (this.isSnippetsBlockSourceFile(f)) {
                JSONObject templates = this.checkTemplates(f);
                if (templates.getBoolean(KEY_MISSING)) {
                    fileObj.put(KEY_TEXT, (Object)(f.getName() + "<span class=\"missing-file\"></span>"));
                }
                JSONObject userData3 = new JSONObject();
                userData3.put(KEY_NAME, (Object)"templates");
                userData3.put(KEY_CONTENT, (Object)templates);
                userdataArray.put((Object)userData3);
            }
            fileObj.put(KEY_USERDATA, (Object)userdataArray);
            if (f.isDirectory()) {
                JSONArray item = this.prvParse(f, filter, new JSONArray(), false, null);
                File[] fileList = f.listFiles();
                if (fileList != null) {
                    if (fileList.length == 0) {
                        String icon2 = "folderClosed.gif";
                        fileObj.put("im0", (Object)icon2);
                        fileObj.put("im1", (Object)icon2);
                        fileObj.put("im2", (Object)icon2);
                    }
                    fileObj.put(KEY_ITEM, (Object)item);
                }
            } else if (this.isProtectedFile(f)) {
                icon = "ico-ce-lock.gif";
                fileObj.put("im0", (Object)icon);
                fileObj.put("im1", (Object)icon);
                fileObj.put("im2", (Object)icon);
                JSONObject userData4 = new JSONObject();
                userData4.put(KEY_NAME, (Object)"protected");
                userData4.put(KEY_CONTENT, true);
                userdataArray.put((Object)userData4);
            } else if (this.isJavaFile(f)) {
                icon = "nav-ico-uncomp.png";
                fileObj.put("im0", (Object)icon);
                fileObj.put("im1", (Object)icon);
                fileObj.put("im2", (Object)icon);
            }
            if (topArr == null) {
                itemArray.put((Object)fileObj);
                continue;
            }
            topArr.put((Object)fileObj);
        }
        return itemArray;
    }

    private boolean isProtectedFile(File f) {
        return ProtectedSnippets.getInstance().isProtected(f);
    }

    private boolean isJavaFile(File f) {
        return f.getAbsolutePath().toLowerCase().endsWith(".java");
    }

    private boolean checkFile(File f, String filter) {
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

    private JSONObject checkTemplates(File f) {
        JSONObject templates = new JSONObject();
        JSONArray infoArray = new JSONArray();
        String fileName = SQUtils.stripExtension((String)f.getName());
        boolean missing = this.isMissingTemplate(f);
        if (f.isDirectory()) {
            if (missing) {
                infoArray.put((Object)new JSONObject().put(KEY_ITEM, (Object)"Category contains building block snippets with missing templates."));
            }
        } else {
            JSONArray types = new JSONArray();
            ArrayList<String> missingFiles = new ArrayList<String>();
            String userDirPath = new File(SQStructure.getExtendUserDirPath()).getAbsolutePath();
            String builtinDirPath = new File(SQStructure.getExtendBuiltinDirPath()).getAbsolutePath();
            for (File fileBlocks : this.fileCodeBlockDirs) {
                if ((!f.getPath().startsWith(userDirPath) || !fileBlocks.getPath().startsWith(userDirPath)) && (!f.getPath().startsWith(builtinDirPath) || !fileBlocks.getPath().startsWith(builtinDirPath))) continue;
                boolean templateExists = this.dirContains(fileBlocks, fileName + ".tpl");
                String path = new File(fileBlocks.getAbsolutePath(), fileName + ".tpl").getAbsolutePath();
                JSONObject type = new JSONObject();
                type.put(KEY_TYPE, (Object)fileBlocks.getParentFile().getName());
                type.put(KEY_FILE, (Object)path);
                type.put(KEY_MISSING, !templateExists);
                if (MainApp.isRelease() && f.getPath().startsWith(builtinDirPath) && !templateExists) continue;
                if (!templateExists) {
                    String blocksName = fileBlocks.getParentFile().getName();
                    infoArray.put((Object)new JSONObject().put(KEY_ITEM, (Object)("<b>" + fileName + "</b> Missing code for this block in <b>" + blocksName + "</b>")));
                    missingFiles.add(path);
                }
                types.put((Object)type);
            }
            if (!missingFiles.isEmpty()) {
                JSONObject type = new JSONObject();
                type.put(KEY_TYPE, (Object)"addAllMissingTemplates");
                missingFiles.sort(Comparator.comparing(String::toString));
                type.put(KEY_FILE, (Object)String.join((CharSequence)",", missingFiles));
                type.put(KEY_MISSING, true);
                types.put((Object)type);
            }
            templates.put(KEY_TYPES, (Object)types);
        }
        templates.put(KEY_MISSING, missing);
        templates.put(KEY_INFO, (Object)infoArray);
        return templates;
    }

    private boolean isMissingTemplate(File checkedFile) {
        for (File missingTemplateFile : this.missingTemplateFiles) {
            if (!missingTemplateFile.getAbsolutePath().startsWith(checkedFile.getAbsolutePath())) continue;
            return true;
        }
        return false;
    }

    private boolean isSnippetsBlockSourceFile(File blockFile) {
        for (File dirF : this.fileSnippetsBlocksDirs) {
            if (!blockFile.getAbsolutePath().startsWith(dirF.getAbsolutePath())) continue;
            return true;
        }
        return false;
    }
}

