/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.plugin.Servlet.impl.CodeEditor.searchInFiles;

public class SearchMatch {
    private final int line;
    private final String text;

    public SearchMatch(int line, String text) {
        this.line = line;
        this.text = text;
    }

    public int getLine() {
        return this.line;
    }

    public String getText() {
        return this.text;
    }
}

