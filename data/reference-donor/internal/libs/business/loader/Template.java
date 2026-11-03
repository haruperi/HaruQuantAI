/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.wizard.desktop.loader;

public class Template {
    private String id;
    private String name;
    private String descriptions;
    private String extension;
    private String form;

    public String getName() {
        return this.name;
    }

    public void setName(String string) {
        this.name = string;
    }

    public String getDescriptions() {
        return this.descriptions;
    }

    public void setDescriptions(String string) {
        this.descriptions = string;
    }

    public String getExtension() {
        return this.extension;
    }

    public void setExtension(String string) {
        this.extension = string;
    }

    public String toJson() {
        String string = this.form;
        string = string != null ? string.replace("\t", "").replace("\n", "").replace("\r", "").replace("\"", "\\\"") : "";
        return "{\"id\":\"" + this.id + "\",\"name\":\"" + this.name + "\",\"description\":\"" + this.descriptions + "\",\"extension\":\"" + this.extension + "\", \"form\":\"<form>" + string + "</form>\"}";
    }

    public String getId() {
        return this.id;
    }

    public void setId(String string) {
        this.id = string;
    }

    public String getForm() {
        return this.form;
    }

    public void setForm(String string) {
        this.form = string;
    }
}

