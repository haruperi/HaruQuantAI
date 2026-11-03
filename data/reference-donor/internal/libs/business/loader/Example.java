/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.wizard.desktop.loader;

public class Example {
    private String name;
    private String desc;
    private String file;
    private String image;
    private boolean cloud;

    public String getName() {
        return this.name;
    }

    public void setName(String string) {
        this.name = string;
    }

    public String getDesc() {
        return this.desc;
    }

    public void setDesc(String string) {
        this.desc = string;
    }

    public String getFile() {
        return this.file;
    }

    public void setFile(String string) {
        this.file = string;
    }

    public String getImage() {
        return this.image;
    }

    public void setImage(String string) {
        this.image = string;
    }

    public String toJson() {
        String string = String.valueOf(this.cloud);
        return "{\"name\":\"" + this.name + "\", \"desc\":\"" + this.desc + "\",\"id\":\"" + this.file + "\",\"image\":" + this.getImageJson() + ",\"tour\":null}";
    }

    private String getImageJson() {
        return this.image == null ? "null" : "\"" + this.image + "\"";
    }

    public boolean isCloud() {
        return this.cloud;
    }

    public void setCloud(boolean bl) {
        this.cloud = bl;
    }
}

