/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.gridlib.message;

import java.util.UUID;

public class JmsConnectionInfo {
    private String ident;
    private String target;

    public JmsConnectionInfo(String string) {
        this.target = string;
        this.ident = UUID.randomUUID().toString().replace("-", "");
    }

    public String getIdent() {
        return this.ident;
    }

    public void setIdent(String string) {
        this.ident = string;
    }

    public String getTarget() {
        return this.target;
    }

    public void setTarget(String string) {
        this.target = string;
    }
}

