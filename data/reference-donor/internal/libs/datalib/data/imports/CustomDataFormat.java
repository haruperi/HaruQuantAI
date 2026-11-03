/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.datalib.data.imports;

import com.strategyquant.datalib.data.io.columns.DefaultCol;
import java.util.HashMap;

public class CustomDataFormat {
    private String name;
    private String separator;
    private String dateFormat;
    private String timeFormat = null;
    private int skipRows;
    private int skipColumns;
    private boolean predefined = false;
    private HashMap<Integer, DefaultCol> columns = new HashMap();
    private int order = 0;

    public CustomDataFormat() {
        this(null);
    }

    public CustomDataFormat(String string) {
        this.name = string;
    }

    public CustomDataFormat(String string, String string2, String string3, int n, int n2) {
        this.name = string;
        this.separator = string2;
        this.dateFormat = string3;
        this.skipRows = n;
        this.skipColumns = n2;
    }

    public CustomDataFormat(String string, String string2, String string3, int n, int n2, HashMap<Integer, DefaultCol> hashMap) {
        this(string, string2, string3, n, n2);
        this.columns = hashMap;
    }

    public String getName() {
        return this.name;
    }

    public void setName(String string) {
        this.name = string;
    }

    public String getSeparator() {
        return this.separator;
    }

    public void setSeparator(String string) {
        this.separator = string;
    }

    public String getDateFormat() {
        return this.dateFormat;
    }

    public void setDateFormat(String string) {
        this.dateFormat = string;
    }

    public String getTimeFormat() {
        return this.timeFormat;
    }

    public void setTimeFormat(String string) {
        this.timeFormat = string;
    }

    public int getSkipRows() {
        return this.skipRows;
    }

    public void setSkipRows(int n) {
        this.skipRows = n;
    }

    public int getSkipColumns() {
        return this.skipColumns;
    }

    public void setSkipColumns(int n) {
        this.skipColumns = n;
    }

    public HashMap<Integer, DefaultCol> getColumns() {
        return this.columns;
    }

    public void setColumns(HashMap<Integer, DefaultCol> hashMap) {
        this.columns = hashMap;
    }

    public boolean isPredefined() {
        return this.predefined;
    }

    public void setPredefined(boolean bl) {
        this.predefined = bl;
    }

    public int getOrder() {
        return this.order;
    }

    public void setOrder(int n) {
        this.order = n;
    }

    public String toString() {
        return this.name;
    }

    public String columTypesToString() {
        String string = "";
        for (int n : this.columns.keySet()) {
            DefaultCol defaultCol = this.columns.get(n);
            string = string + defaultCol.getName() + ",";
        }
        return string.length() > 0 ? string.substring(0, string.length() - 1) : string;
    }
}

