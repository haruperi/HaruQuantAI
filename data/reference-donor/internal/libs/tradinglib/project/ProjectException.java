/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib.project;

public class ProjectException
extends Exception {
    public static final int NotDirectory = 1;
    public static final int NotEmptyDirectory = 2;
    public static final int ProjectDoesntExist = 3;
    public static final int ProjectConfigError = 4;
    public static final int DuplicateProject = 5;
    public static final int AlreadyLoaded = 6;
    private int code;

    public ProjectException(int n, String string) {
        super(string);
        this.code = n;
    }

    public ProjectException(int n, Exception exception) {
        super(exception);
        this.code = n;
    }

    public ProjectException(int n, String string, Exception exception) {
        super(string, exception);
        this.code = n;
    }

    public int getCode() {
        return this.code;
    }
}

