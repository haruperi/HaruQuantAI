/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib.taskImpl;

public class TaskException
extends Exception {
    public static final int ConfigNotInitialized = 1;
    public static final int NumberFormatException = 2;
    public static final int ParseException = 3;
    public static final int TaskPluginNotSet = 4;
    public static final int TaskPluginDoesntExist = 5;
    public static final int RegistrationError = 6;
    public static final int TaskInstantiationError = 7;
    public static final int ProjectNotInitialized = 8;
    public static final int TaskConfigError = 9;
    public static final int DataException = 10;
    private int code;

    public TaskException(String string) {
        super(string);
        this.code = 0;
    }

    public TaskException(int n, String string) {
        super(string);
        this.code = n;
    }

    public TaskException(int n, Exception exception) {
        super(exception);
        this.code = n;
    }

    public TaskException(int n, String string, Exception exception) {
        super(string, exception);
        this.code = n;
    }

    public int getCode() {
        return this.code;
    }
}

