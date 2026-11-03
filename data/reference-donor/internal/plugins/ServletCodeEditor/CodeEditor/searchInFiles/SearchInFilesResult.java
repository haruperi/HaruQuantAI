/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  org.json.JSONArray
 */
package com.strategyquant.plugin.Servlet.impl.CodeEditor.searchInFiles;

import org.json.JSONArray;

public class SearchInFilesResult {
    private final JSONArray items;
    private final int totalMatches;

    SearchInFilesResult(JSONArray items, int totalMatches) {
        this.items = items;
        this.totalMatches = totalMatches;
    }

    public JSONArray getItems() {
        return this.items;
    }

    public int getTotalMatchesCount() {
        return this.totalMatches;
    }
}

