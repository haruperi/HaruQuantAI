/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib.generator;

public class StrategyTemplateNotFoundException
extends Exception {
    private String templateFile = null;
    private String buildTaskName = null;

    public StrategyTemplateNotFoundException(String string, String string2) {
        super(String.format("Strategy template file '%s' for task name '%s' was not found.", string, string2));
        this.templateFile = string;
        this.buildTaskName = string2;
    }

    public String getTemplateFile() {
        return this.templateFile;
    }

    public String getTaskName() {
        return this.buildTaskName;
    }
}

