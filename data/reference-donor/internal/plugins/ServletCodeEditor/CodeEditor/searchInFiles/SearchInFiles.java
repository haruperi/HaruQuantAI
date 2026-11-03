/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.SQUtils
 *  org.json.JSONArray
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.Servlet.impl.CodeEditor.searchInFiles;

import com.strategyquant.lib.SQUtils;
import com.strategyquant.plugin.Servlet.impl.CodeEditor.CodeEditorServletException;
import com.strategyquant.plugin.Servlet.impl.CodeEditor.searchInFiles.SearchInFilesResult;
import com.strategyquant.plugin.Servlet.impl.CodeEditor.searchInFiles.SearchMatch;
import com.strategyquant.plugin.Servlet.impl.CodeEditor.searchInFiles.SearchMatches;
import java.io.File;
import java.util.HashMap;
import java.util.Map;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import org.json.JSONArray;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class SearchInFiles {
    private static final Logger Log = LoggerFactory.getLogger(SearchInFiles.class);
    private boolean matchCase;
    private boolean wholeWord;
    private boolean useRegex;
    private String searchString;
    private int index;
    private final HashMap<String, SearchMatches> matches = new HashMap();
    private int totalMatches;
    private static final String IMG_PAGING_PAGE = "paging_page.gif";
    private static final String IMG_MATCH = "ar_right_dis.gif";
    private static final String RESP_TAG_NAME = "name";
    private static final String RESP_TAG_CONTENT = "content";

    public synchronized SearchInFilesResult search(Map<String, String> sourceDirs, String text, boolean caseSensitive, boolean regex, boolean wholeWord) {
        this.matchCase = caseSensitive;
        this.wholeWord = wholeWord;
        this.useRegex = regex;
        this.searchString = text;
        if (!this.useRegex && !this.matchCase) {
            this.searchString = this.searchString.toLowerCase();
        }
        this.index = 0;
        this.matches.clear();
        this.totalMatches = 0;
        JSONArray itemArray = new JSONArray();
        for (Map.Entry<String, String> entry : sourceDirs.entrySet()) {
            File f = new File(entry.getKey());
            if (!f.exists()) continue;
            this.matchFiles(f);
            this.generateTree(f, itemArray, true, entry.getValue());
        }
        return new SearchInFilesResult(itemArray, this.totalMatches);
    }

    private JSONArray generateTree(File folder, JSONArray itemArray, boolean isTopLevel, String topLevelDesc) {
        File[] files = folder.listFiles();
        if (files == null) {
            return itemArray;
        }
        JSONObject topObj = null;
        JSONArray topArr = null;
        for (File f : files) {
            if (!this.checkFile(f)) continue;
            if (isTopLevel && topObj == null) {
                topObj = new JSONObject();
                topObj.put("id", this.index++);
                topObj.put("text", (Object)topLevelDesc);
                topArr = new JSONArray();
                topObj.put("item", (Object)topArr);
                itemArray.put((Object)topObj);
            }
            JSONObject fileObj = new JSONObject();
            fileObj.put("id", this.index++);
            if (f.isDirectory()) {
                fileObj.put("text", (Object)f.getName());
                JSONArray item = this.generateTree(f, new JSONArray(), false, null);
                fileObj.put("item", (Object)item);
            } else {
                SearchMatches matchList = this.matches.get(f.getAbsolutePath());
                this.totalMatches += matchList.size();
                fileObj.put("text", (Object)(f.getName() + " (" + matchList.size() + " matches)"));
                fileObj.put("im0", (Object)IMG_PAGING_PAGE);
                fileObj.put("im1", (Object)IMG_PAGING_PAGE);
                fileObj.put("im2", (Object)IMG_PAGING_PAGE);
                JSONArray userdataArray = new JSONArray();
                JSONObject userData = new JSONObject();
                userData.put(RESP_TAG_NAME, (Object)"file");
                userData.put(RESP_TAG_CONTENT, (Object)f.getAbsolutePath());
                userdataArray.put((Object)userData);
                JSONObject userData2 = new JSONObject();
                userData2.put(RESP_TAG_NAME, (Object)"line");
                userData2.put(RESP_TAG_CONTENT, ((SearchMatch)matchList.get(0)).getLine());
                userdataArray.put((Object)userData2);
                fileObj.put("userdata", (Object)userdataArray);
                JSONArray itemMatches = new JSONArray();
                for (SearchMatch match : matchList) {
                    ++this.index;
                    JSONObject itemMatch = new JSONObject();
                    itemMatch.put("id", this.index);
                    itemMatch.put("text", (Object)(match.getLine() + ": " + match.getText()));
                    itemMatch.put("im0", (Object)IMG_MATCH);
                    itemMatch.put("im1", (Object)IMG_MATCH);
                    itemMatch.put("im2", (Object)IMG_MATCH);
                    JSONArray userdataMatchArray = new JSONArray();
                    JSONObject userDataMatch = new JSONObject();
                    userDataMatch.put(RESP_TAG_NAME, (Object)"file");
                    userDataMatch.put(RESP_TAG_CONTENT, (Object)f.getAbsolutePath());
                    JSONObject userDataMatch2 = new JSONObject();
                    userDataMatch2.put(RESP_TAG_NAME, (Object)"line");
                    userDataMatch2.put(RESP_TAG_CONTENT, match.getLine());
                    userdataMatchArray.put((Object)userDataMatch);
                    userdataMatchArray.put((Object)userDataMatch2);
                    itemMatch.put("userdata", (Object)userdataMatchArray);
                    itemMatches.put((Object)itemMatch);
                }
                fileObj.put("item", (Object)itemMatches);
            }
            if (topArr == null) {
                itemArray.put((Object)fileObj);
                continue;
            }
            topArr.put((Object)fileObj);
        }
        return itemArray;
    }

    private void matchFiles(File directory) {
        File[] children = directory.listFiles();
        if (children == null) {
            return;
        }
        for (File f : children) {
            if (f.isDirectory()) {
                this.matchFiles(f);
                continue;
            }
            this.searchInFile(f);
        }
    }

    private void searchInFile(File file) {
        String path = file.getAbsolutePath();
        try {
            SearchMatches matchList;
            String content = SQUtils.fileToString((File)file);
            if (!this.matchCase) {
                content = content.toLowerCase();
            }
            if (!(matchList = this.useRegex ? this.doSearchRegex(content) : this.doSearchNoRegex(content)).isEmpty()) {
                this.matches.put(path, matchList);
            }
        }
        catch (Exception e) {
            Log.error("Exc.", (Throwable)e);
        }
    }

    private SearchMatches doSearchNoRegex(String content) throws CodeEditorServletException {
        SearchMatches result = new SearchMatches();
        int matchIndex = 0;
        int len = this.searchString.length();
        while ((matchIndex = content.indexOf(this.searchString, matchIndex)) != -1) {
            if (!this.wholeWord || this.isWholeWord(content, matchIndex, len)) {
                SearchMatch match = this.getMatch(content, matchIndex);
                result.add(match);
                matchIndex += len;
                continue;
            }
            ++matchIndex;
        }
        return result;
    }

    private SearchMatches doSearchRegex(String content) throws CodeEditorServletException {
        SearchMatches matchList = new SearchMatches();
        int flags = this.matchCase ? 0 : 66;
        Pattern pattern = Pattern.compile(this.searchString, flags);
        Matcher m = pattern.matcher(content);
        while (m.find()) {
            int start = m.start();
            int end = m.end();
            if (this.wholeWord && !this.isWholeWord(content, start, end - start)) continue;
            SearchMatch match = this.getMatch(content, this.index);
            matchList.add(match);
        }
        return matchList;
    }

    private SearchMatch getMatch(String content, int index) throws CodeEditorServletException {
        int pos;
        int lines = 0;
        int lastPos = 0;
        while ((pos = content.indexOf("\n", lastPos) + 1) != 0) {
            ++lines;
            if (pos >= index) {
                String text = content.substring(lastPos, pos);
                return new SearchMatch(lines, text.trim());
            }
            lastPos = pos;
        }
        throw new CodeEditorServletException(String.format("No match found. Index: %d.", index));
    }

    private boolean isWholeWord(CharSequence searchIn, int offset, int len) {
        boolean wsAfter;
        boolean wsBefore;
        try {
            wsBefore = Character.isWhitespace(searchIn.charAt(offset - 1));
        }
        catch (IndexOutOfBoundsException e) {
            wsBefore = true;
        }
        try {
            wsAfter = Character.isWhitespace(searchIn.charAt(offset + len));
        }
        catch (IndexOutOfBoundsException e) {
            wsAfter = true;
        }
        return wsBefore && wsAfter;
    }

    private boolean checkFile(File f) {
        if (f.isDirectory()) {
            return this.checkFiles(f);
        }
        return this.matches.containsKey(f.getAbsolutePath());
    }

    private boolean checkFiles(File dir) {
        File[] children = dir.listFiles();
        if (children == null) {
            return false;
        }
        for (File f : children) {
            if (f.isDirectory()) {
                if (!this.checkFiles(f)) continue;
                return true;
            }
            return this.matches.containsKey(f.getAbsolutePath());
        }
        return false;
    }
}

