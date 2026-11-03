/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib.project;

public class GoToTaskException
extends Exception {
    public String taskName;

    public GoToTaskException(String string) {
        this.taskName = string;
    }
}

