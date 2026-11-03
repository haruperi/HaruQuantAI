/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib;

import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.debug.Debugger;
import java.util.ArrayList;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public abstract class CustomAnalysisMethod
extends Debugger {
    public static final Logger Log = LoggerFactory.getLogger(CustomAnalysisMethod.class);
    public static final int TYPE_PROCESS_DATABANK = 10;
    public static final int TYPE_FILTER_STRATEGY = 20;
    public static final int TYPE_BOTH = 30;
    public String name;
    private int type;
    protected String projectLogMessage;
    private String inputArgs;

    public CustomAnalysisMethod(String string, int n) {
        this.name = string;
        this.type = n;
    }

    public int getType() {
        return this.type;
    }

    public boolean filterStrategy(String string, String string2, String string3, ResultsGroup resultsGroup) throws Exception {
        return true;
    }

    public ArrayList<ResultsGroup> processDatabank(String string, String string2, String string3, ArrayList<ResultsGroup> arrayList) throws Exception {
        return arrayList;
    }

    public void setProjectLog(String string) {
        this.projectLogMessage = string;
    }

    public String getProjectLog() {
        return this.projectLogMessage;
    }

    public String getInputArgs() {
        return this.inputArgs;
    }

    public void setInputArgs(String string) {
        this.inputArgs = string;
    }
}

