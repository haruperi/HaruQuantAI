/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.datalib.basket;

public class BasketDto {
    private String name;
    private String desc;
    private int count;
    private int total;
    private Integer id;
    private boolean system;

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

    public int getCount() {
        return this.count;
    }

    public void setCount(int n) {
        this.count = n;
    }

    public Integer getId() {
        return this.id;
    }

    public void setId(Integer n) {
        this.id = n;
    }

    public boolean isSystem() {
        return this.system;
    }

    public void setSystem(boolean bl) {
        this.system = bl;
    }

    public int getTotal() {
        return this.total;
    }

    public void setTotal(int n) {
        this.total = n;
    }

    public boolean isDefault() {
        return this.name.startsWith("[[");
    }
}

