/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.data.io.VersatileData
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.settings.IXMLAble
 *  org.jdom2.Element
 *  org.json.JSONObject
 */
package com.strategyquant.plugin.DataManager.impl.Data.csvexport.format;

import com.strategyquant.datalib.data.io.VersatileData;
import com.strategyquant.lib.L;
import com.strategyquant.lib.settings.IXMLAble;
import com.strategyquant.plugin.DataManager.impl.Data.csvexport.items.AbstractItem;
import com.strategyquant.plugin.DataManager.impl.Data.csvexport.items.Items;
import com.strategyquant.plugin.DataManager.impl.Data.csvexport.items.TextItem;
import com.strategyquant.plugin.DataManager.impl.Data.csvexport.items.Volume;
import java.util.ArrayList;
import java.util.regex.Pattern;
import org.jdom2.Element;
import org.json.JSONObject;

public class Format
implements IXMLAble {
    public String name;
    public String separator;
    public String header;
    public String items;
    public boolean includeHeader;
    public boolean predefined;
    private ArrayList<AbstractItem> itemsList = new ArrayList();
    private int volumeColumns = 0;

    public Format(String name, String separator, String[] header, String[] items, boolean includeHeader, boolean predefined) throws Exception {
        int i;
        this.name = name;
        this.separator = separator;
        this.includeHeader = includeHeader;
        this.predefined = predefined;
        if (header.length != items.length) {
            throw new Exception(L.t((String)"Header length <> Format length. Different delimiters!?", (Object[])new Object[0]));
        }
        this.header = "";
        for (int i2 = 0; i2 < header.length; ++i2) {
            this.header = i2 < header.length - 1 ? this.header + header[i2] + separator : this.header + header[i2];
        }
        this.items = "";
        for (i = 0; i < items.length; ++i) {
            String format;
            String key;
            String item = items[i];
            item = item.replaceAll(Pattern.quote("["), "");
            if ((item = item.replaceAll(Pattern.quote("]"), "")).contains(":")) {
                String[] itemData = item.split(":", 2);
                key = itemData[0];
                format = itemData[1];
            } else {
                key = item;
                format = null;
            }
            AbstractItem itemObject = Items.get().findByKey(key);
            if (itemObject != null) {
                itemObject = itemObject.clone();
                if (format != null) {
                    itemObject.setFormat(format);
                }
                this.itemsList.add(itemObject);
                if (itemObject instanceof Volume) {
                    ++this.volumeColumns;
                }
            } else {
                itemObject = new TextItem();
                itemObject.value = item;
                this.itemsList.add(itemObject);
                if (itemObject instanceof Volume) {
                    ++this.volumeColumns;
                }
            }
            this.items = i < items.length - 1 ? this.items + "[" + item + "]" + separator : this.items + "[" + item + "]";
        }
        if (this.volumeColumns > 1) {
            for (i = 0; i < this.itemsList.size(); ++i) {
                if (!(this.itemsList.get(i) instanceof Volume)) continue;
                this.itemsList.get((int)i).count = this.volumeColumns;
            }
        }
    }

    public JSONObject toJson() {
        return new JSONObject().put("name", (Object)this.name).put("header", (Object)this.header).put("items", (Object)this.items).put("includeHeader", this.includeHeader).put("predefined", this.predefined);
    }

    public void setFromXML(Element element) throws Exception {
    }

    public Element getXML() {
        return null;
    }

    public Format withIncludeHeader(boolean includeHeader) throws Exception {
        return new Format(this.name, this.separator, this.header.split(Pattern.quote(this.separator)), this.items.split(Pattern.quote(this.separator)), includeHeader, this.predefined);
    }

    public String printHeader() {
        return this.header.replaceAll(Pattern.quote("[Tab]"), "\t");
    }

    public String printData(String symbol, VersatileData data, int decimals) {
        String line = "";
        for (int i = 0; i < this.itemsList.size(); ++i) {
            line = i < this.itemsList.size() - 1 ? line + this.itemsList.get(i).printValue(symbol, data, decimals) + this.separator : line + this.itemsList.get(i).printValue(symbol, data, decimals);
        }
        return line.replaceAll(Pattern.quote("[Tab]"), "\t");
    }
}

