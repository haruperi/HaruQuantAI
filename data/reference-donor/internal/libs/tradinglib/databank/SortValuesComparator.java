/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.utils.StringComparator
 */
package com.strategyquant.tradinglib.databank;

import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.utils.StringComparator;
import java.util.Comparator;
import java.util.Map;

public class SortValuesComparator
implements Comparator<Map.Entry<String, Object>> {
    private StringComparator stringComparator = new StringComparator();
    private boolean asc = true;
    private String dataType = "Text";

    @Override
    public int compare(Map.Entry<String, Object> entry, Map.Entry<String, Object> entry2) {
        try {
            switch (this.dataType) {
                case "Text": {
                    String string = SQUtils.removeHtmlTags((String)((String)entry.getValue()));
                    String string2 = SQUtils.removeHtmlTags((String)((String)entry2.getValue()));
                    int n = this.stringComparator.compare(string, string2);
                    if (this.asc) {
                        return n;
                    }
                    return -1 * n;
                }
            }
            double d = Double.parseDouble(SQUtils.extractNumber((String)SQUtils.removeHtmlTags((String)((String)entry.getValue()))));
            double d2 = Double.parseDouble(SQUtils.extractNumber((String)SQUtils.removeHtmlTags((String)((String)entry2.getValue()))));
            if (d < d2) {
                if (this.asc) {
                    return -1;
                }
                return 1;
            }
            if (d > d2) {
                if (this.asc) {
                    return 1;
                }
                return -1;
            }
            return 0;
        }
        catch (Exception exception) {
            String string = SQUtils.removeHtmlTags((String)String.valueOf(entry.getValue()));
            String string3 = SQUtils.removeHtmlTags((String)String.valueOf(entry2.getValue()));
            int n = this.stringComparator.compare(string, string3);
            if (this.asc) {
                return n;
            }
            return -1 * n;
        }
    }

    public void setAsc(boolean bl) {
        this.asc = bl;
    }

    public void setDataType(String string) {
        this.dataType = string;
    }
}

