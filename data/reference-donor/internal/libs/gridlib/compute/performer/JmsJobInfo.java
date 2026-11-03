/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.gridlib.compute.performer;

import java.io.Serializable;
import java.util.Map;

public class JmsJobInfo
implements Serializable {
    private static final long serialVersionUID = 1L;
    private String className;
    private Map<String, Serializable> params;
    private int flag;

    public JmsJobInfo() {
    }

    public JmsJobInfo(String string, Map<String, Serializable> map, int n) {
        this.className = string;
        this.params = map;
        this.flag = n;
    }

    public String getClassName() {
        return this.className;
    }

    public void setClassName(String string) {
        this.className = string;
    }

    public Map<String, Serializable> getParams() {
        return this.params;
    }

    public void setParams(Map<String, Serializable> map) {
        this.params = map;
    }

    public int getFlag() {
        return this.flag;
    }

    public void setFlag(int n) {
        this.flag = n;
    }
}

