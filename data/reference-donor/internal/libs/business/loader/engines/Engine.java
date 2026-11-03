/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.wizard.desktop.loader.engines;

public class Engine {
    private String name;
    private String url;

    public Engine(String string, String string2) {
        this.name = string;
        this.url = string2;
    }

    public String getName() {
        return this.name;
    }

    public String getUrl() {
        return this.url;
    }

    public String toJson() {
        return "{\"name\":\"" + this.name + "\",\"url\":\"" + this.url + "\"}";
    }
}

